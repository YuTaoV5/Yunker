import sys
from pathlib import Path
from typing import Dict, Optional

from PyQt5.QtChart import QChart, QLineSeries, QValueAxis
from PyQt5.QtCore import QObject, QProcess, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QColor, QFontMetrics
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from Core.device_client import DeviceClient, RequestResult
from Core.protocol import ProtocolCodec, ProtocolFrame
from Core.serial_manager import global_serial_manager
from PyQt.ui import Ui_MainWindow


class _UiBridge(QObject):
    serial_data = pyqtSignal(bytes)


class MainWindow(QMainWindow, Ui_MainWindow):
    STATE_DISCONNECTED = "Disconnected"
    STATE_CONNECTED_NO_GRAPH = "Connected_NoGraph"
    STATE_RUNNING = "Running"

    REG_SERIAL = 0x10
    REG_BAUD = 0x11
    REG_PARITY = 0x12
    REG_RESPONSE = 0x13
    REG_DIR = 0x14
    REG_DISPLAY_SLEEP = 0x15
    REG_SLEEP_TIME_HI = 0x16
    REG_SLEEP_TIME_LO = 0x17
    REG_HOSTIF_EN = 0x18
    REG_HOSTIF_MOTOR_EN = 0x19
    MODULE_MARGIN_LEFT = 12
    MODULE_MARGIN_TOP = 10
    MODULE_MARGIN_RIGHT = 12
    MODULE_MARGIN_BOTTOM = 10
    BUTTON_ROW_SIDE_MARGIN = 12
    SYS_SCROLL_SAFE_GAP = 6

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.resize(1200, 780)

        self.max_data_points = 300
        self.data_counter = 0
        self.last_ports = []

        self.latest_current_a = 0
        self.latest_current_b = 0
        self.latest_target_a = 0
        self.latest_target_b = 0
        self._monitor_sample_pending = False

        self.recent_graph_bytes: bytes = b""
        self.omni_output_text = ""
        self.omni_process: Optional[QProcess] = None

        self._sleep_time_hi = 0
        self._sleep_time_lo = 0

        self._sys_batch_mode = ""
        self._sys_batch_total = 0
        self._sys_batch_pending = 0
        self._sys_batch_failed = 0

        self.poll_phase = 0
        self.run_state = self.STATE_DISCONNECTED

        self._sys_params_loaded = False

        self.serial_bridge = _UiBridge(self)
        self.serial_bridge.serial_data.connect(self._on_serial_bytes)

        self.device_client = DeviceClient(send_func=global_serial_manager.send_data)
        self.device_client.frame_listener = self._on_protocol_frame
        self.device_client.log_listener = self._on_protocol_log

        self._setup_content_layout()
        self._setup_section_groups()
        self._setup_base_controls()
        self._build_extra_panels()
        self._init_chart()
        self._bind_signals()
        self._init_timers()

        global_serial_manager.set_read_callback(self.serial_bridge.serial_data.emit)

        self._refresh_ports(force=True)
        self.device_client.set_board_id(self.Board_ID.value())
        self.device_client.set_parity(self.Check_Byte.currentText())

        self._set_state(self.STATE_DISCONNECTED)
        self._update_adaptive_widths()

    def _setup_base_controls(self):
        self.Baud_Rate.clear()
        self.Baud_Rate.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.Baud_Rate.setCurrentText("115200")

        self.Check_Byte.clear()
        self.Check_Byte.addItems(["None", "0x4B", "CRC"])
        self.Check_Byte.setCurrentText("None")

        self.Board_ID.setRange(0, 255)
        self.Board_ID.setValue(1)

        self.label_2.setText("端口")
        self.label_3.setText("波特率")
        self.label_4.setText("板ID")
        self.label_5.setText("校验")

        for label in [self.label_2, self.label_3, self.label_4, self.label_5]:
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        for editor in [self.Uart_Port, self.Baud_Rate, self.Board_ID, self.Check_Byte]:
            editor.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.Uart_Port.setMinimumWidth(120)
        self.Baud_Rate.setMinimumWidth(120)
        self.Check_Byte.setMinimumWidth(120)
        self.Board_ID.setMinimumWidth(120)
        self.Uart_Port.setMaximumWidth(168)
        self.Baud_Rate.setMaximumWidth(168)
        self.Check_Byte.setMaximumWidth(168)
        self.Board_ID.setMaximumWidth(168)
        self.Uart_En.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._fit_button_width(self.Uart_En)

    def _setup_content_layout(self):
        self.gridLayout.setContentsMargins(8, 8, 8, 8)
        self.gridLayout.setHorizontalSpacing(8)
        self.gridLayout.setVerticalSpacing(6)

        # Remove the generated middle spacer column to let content span full width.
        for index in range(self.gridLayout.count() - 1, -1, -1):
            item = self.gridLayout.itemAt(index)
            row, col, row_span, col_span = self.gridLayout.getItemPosition(index)
            if col == 1 and item.spacerItem() is not None:
                self.gridLayout.takeAt(index)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(2, 11)

        # Remove left side expanding spacers so controls can use vertical space efficiently.
        for index in range(self.verticalLayout.count() - 1, -1, -1):
            item = self.verticalLayout.itemAt(index)
            if item.spacerItem() is not None:
                self.verticalLayout.takeAt(index)

        self.verticalLayout.setSpacing(8)
        self.verticalLayout_2.setSpacing(8)

    def _setup_section_groups(self):
        self.connection_group = QGroupBox("驱动器连接", self.centralwidget)
        self.connection_group_layout = QVBoxLayout(self.connection_group)
        self.connection_group_layout.setContentsMargins(
            self.MODULE_MARGIN_LEFT,
            6,
            self.MODULE_MARGIN_RIGHT,
            6,
        )
        self.connection_group_layout.setSpacing(4)
        self.connection_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.connection_group.setMinimumHeight(0)

        self.verticalLayout.removeItem(self.horizontalLayout)
        self.label.hide()
        self._rebuild_connection_panel()
        self.verticalLayout.insertWidget(0, self.connection_group)

        self.monitor_group = QGroupBox("实时监控", self.centralwidget)
        self.monitor_group_layout = QVBoxLayout(self.monitor_group)
        self.monitor_group_layout.setContentsMargins(
            self.MODULE_MARGIN_LEFT,
            self.MODULE_MARGIN_TOP,
            self.MODULE_MARGIN_RIGHT,
            self.MODULE_MARGIN_BOTTOM,
        )
        self.monitor_group_layout.setSpacing(8)

        self.verticalLayout_2.removeItem(self.horizontalLayout_8)
        self.label_7.hide()
        self.verticalLayout_2.removeWidget(self.chart_window)
        self.verticalLayout_2.removeItem(self.horizontalLayout_7)

        self.monitor_group_layout.addWidget(self.chart_window)
        self.monitor_group_layout.addLayout(self.horizontalLayout_7)
        self.verticalLayout_2.insertWidget(0, self.monitor_group, 1)

    def _rebuild_connection_panel(self):
        for row_layout in [
            self.horizontalLayout_2,
            self.horizontalLayout_3,
            self.horizontalLayout_4,
            self.horizontalLayout_5,
            self.horizontalLayout_6,
        ]:
            self.verticalLayout.removeItem(row_layout)

        self.label_6.hide()

        form_host = QWidget(self.connection_group)
        form_host.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        form = QFormLayout(form_host)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(4)

        form.addRow(self.label_2, self.Uart_Port)
        form.addRow(self.label_3, self.Baud_Rate)
        form.addRow(self.label_4, self.Board_ID)
        form.addRow(self.label_5, self.Check_Byte)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(self.BUTTON_ROW_SIDE_MARGIN, 2, self.BUTTON_ROW_SIDE_MARGIN, 0)
        button_row.addStretch(1)
        button_row.addWidget(self.Uart_En)
        button_row.addStretch(1)
        form.addRow(button_row)

        self.connection_group_layout.addWidget(form_host, 0, Qt.AlignHCenter | Qt.AlignTop)

    def _update_adaptive_widths(self):
        if self.centralwidget is None:
            return
        total_width = max(1, self.centralwidget.width())
        left_target = int(total_width * 0.24)
        left_target = max(280, left_target)
        self.gridLayout.setColumnMinimumWidth(0, left_target)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_adaptive_widths()

    def _build_extra_panels(self):
        # Keep existing generated UI unchanged, only append controls dynamically.
        self.speed_value_label = QLabel("A当前: 0  A目标: 0  B当前: 0  B目标: 0", self.centralwidget)
        self.speed_value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.monitor_group_layout.addWidget(self.speed_value_label)

        self._build_omnictrl_panel()
        self._build_template_speed_panel()
        self._build_system_param_panel()
        self._setup_left_panel_spacing()

    def _build_omnictrl_panel(self):
        panel = QGroupBox("OmniCtrl", self.centralwidget)
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        panel.setMinimumHeight(0)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(
            self.MODULE_MARGIN_LEFT,
            6,
            self.MODULE_MARGIN_RIGHT,
            6,
        )
        layout.setSpacing(4)

        row = QHBoxLayout()
        row.setContentsMargins(0, 2, 0, 0)
        row.setSpacing(10)
        self.btn_open_omnictrl = QPushButton("打开 OmniCtrl", panel)
        self.btn_download_graph = QPushButton("下载图结构", panel)
        self.btn_open_omnictrl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_download_graph.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._fit_button_width(self.btn_open_omnictrl)
        self._fit_button_width(self.btn_download_graph)
        row.addStretch(1)
        row.addWidget(self.btn_open_omnictrl)
        row.addWidget(self.btn_download_graph)
        row.addStretch(1)

        self.graph_status_label = QLabel("最近图结构: 未加载", panel)
        self.graph_status_label.setWordWrap(True)
        self.graph_status_label.setAlignment(Qt.AlignCenter)

        layout.addLayout(row)
        layout.addWidget(self.graph_status_label, 0, Qt.AlignCenter)

        self.omnictrl_group = panel
        self.verticalLayout.addWidget(panel)

    def _build_template_speed_panel(self):
        panel = QGroupBox("模板速度", self.centralwidget)
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        panel.setMinimumHeight(0)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(
            self.MODULE_MARGIN_LEFT,
            6,
            self.MODULE_MARGIN_RIGHT,
            6,
        )
        panel_layout.setSpacing(4)

        form_host = QWidget(panel)
        form = QFormLayout(form_host)
        form.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(4)

        self.template_speed_a = QSpinBox(panel)
        self.template_speed_b = QSpinBox(panel)
        self.template_speed_a.setMaximumWidth(168)
        self.template_speed_b.setMaximumWidth(168)
        self.template_speed_a.setRange(-32768, 32767)
        self.template_speed_b.setRange(-32768, 32767)
        self.template_speed_a.setValue(0)
        self.template_speed_b.setValue(0)

        self.btn_send_template_speed = QPushButton("下发模板速度", panel)
        self.btn_send_template_speed.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._fit_button_width(self.btn_send_template_speed)
        self.template_speed_status_label = QLabel("未下发", panel)

        form.addRow("A速度", self.template_speed_a)
        form.addRow("B速度", self.template_speed_b)
        form.addRow("状态", self.template_speed_status_label)

        content_host = QWidget(panel)
        content_host.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        content_layout = QVBoxLayout(content_host)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        content_layout.addWidget(form_host)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(self.BUTTON_ROW_SIDE_MARGIN, 2, self.BUTTON_ROW_SIDE_MARGIN, 0)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_send_template_speed)
        btn_row.addStretch(1)
        content_layout.addLayout(btn_row)

        panel_layout.addWidget(content_host, 0, Qt.AlignHCenter | Qt.AlignTop)

        self.template_group = panel
        self.verticalLayout.addWidget(panel)

    def _build_system_param_panel(self):
        panel = QGroupBox("系统参数", self.centralwidget)
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        panel.setMinimumHeight(0)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(
            self.MODULE_MARGIN_LEFT,
            6,
            self.MODULE_MARGIN_RIGHT,
            6,
        )
        panel_layout.setSpacing(4)

        form_host = QWidget(panel)
        form = QFormLayout(form_host)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.DontWrapRows)
        form.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(4)
        form_host.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.sys_form_layout = form

        self.sys_serial = self._build_enum_combo([
            ("UART", 0),
            ("RS485", 1),
            ("UART+RS485", 2),
        ])
        self.sys_baud = self._build_enum_combo([
            ("9600", 0),
            ("19200", 1),
            ("38400", 2),
            ("57600", 3),
            ("115200", 4),
        ])
        self.sys_parity = self._build_enum_combo([
            ("None", 0),
            ("CRC", 1),
            ("0x4B", 2),
        ])
        self.sys_response = self._build_enum_combo([
            ("None", 0),
            ("Done", 1),
            ("Repeat", 2),
        ])
        self.sys_dir = self._build_enum_combo([
            ("CW", 0),
            ("CCW", 1),
        ])
        self.sys_display_sleep = self._build_enum_combo([
            ("On", 0),
            ("Off", 1),
        ])
        self.sys_hostif_en = self._build_enum_combo([
            ("Disable", 0),
            ("Enable", 1),
        ])
        self.sys_hostif_motor_en = self._build_enum_combo([
            ("Disable", 0),
            ("Enable", 1),
        ])

        self.sys_sleep_time = QSpinBox(panel)
        self.sys_sleep_time.setMaximumWidth(168)
        self.sys_sleep_time.setRange(0, 2147483647)
        self.sys_sleep_time.setSingleStep(100)
        self.sys_sleep_time.setValue(0)

        self.btn_read_sys_params = QPushButton("读取参数", panel)
        self.btn_write_sys_params = QPushButton("写入参数", panel)
        self.btn_read_sys_params.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_write_sys_params.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._fit_button_width(self.btn_read_sys_params)
        self._fit_button_width(self.btn_write_sys_params)
        self.sys_param_status_label = QLabel("请先获取系统参数", panel)
        self.sys_param_status_label.setWordWrap(True)
        self.sys_param_status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        form.addRow("通信接口", self.sys_serial)
        form.addRow("波特率", self.sys_baud)
        form.addRow("校验", self.sys_parity)
        form.addRow("响应模式", self.sys_response)
        form.addRow("方向", self.sys_dir)
        form.addRow("自动息屏", self.sys_display_sleep)
        form.addRow("息屏时间(ms)", self.sys_sleep_time)
        form.addRow("HostIF使能", self.sys_hostif_en)
        form.addRow("HostIF电机", self.sys_hostif_motor_en)
        form.addRow("状态", self.sys_param_status_label)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(self.BUTTON_ROW_SIDE_MARGIN, 2, self.BUTTON_ROW_SIDE_MARGIN, 0)
        button_row.addStretch(1)
        button_row.addWidget(self.btn_read_sys_params)
        button_row.addSpacing(10)
        button_row.addWidget(self.btn_write_sys_params)
        button_row.addStretch(1)
        button_host = QWidget(form_host)
        button_host.setLayout(button_row)
        form.addRow(button_host)

        scroll = QScrollArea(panel)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setWidget(form_host)
        self.sys_scroll_area = scroll
        self.sys_scroll_area.verticalScrollBar().rangeChanged.connect(self._update_sys_scroll_safe_padding)

        panel_layout.addWidget(scroll, 0, Qt.AlignHCenter | Qt.AlignTop)
        self._update_sys_scroll_safe_padding()

        self.sys_param_widgets: Dict[int, QComboBox] = {
            self.REG_SERIAL: self.sys_serial,
            self.REG_BAUD: self.sys_baud,
            self.REG_PARITY: self.sys_parity,
            self.REG_RESPONSE: self.sys_response,
            self.REG_DIR: self.sys_dir,
            self.REG_DISPLAY_SLEEP: self.sys_display_sleep,
            self.REG_HOSTIF_EN: self.sys_hostif_en,
            self.REG_HOSTIF_MOTOR_EN: self.sys_hostif_motor_en,
        }

        self.system_group = panel
        self.verticalLayout.addWidget(panel)

    def _setup_left_panel_spacing(self):
        # Keep all modules at content height, put remaining blank outside frames.
        widgets = [
            self.connection_group,
            self.omnictrl_group,
            self.template_group,
            self.system_group,
        ]
        stretches = [0, 0, 0, 0]

        while self.verticalLayout.count():
            self.verticalLayout.takeAt(0)

        for index, group in enumerate(widgets):
            self.verticalLayout.addWidget(group, stretches[index])
            self.verticalLayout.setStretch(index, stretches[index])
        self.verticalLayout.addStretch(1)

    def _fit_button_width(self, button: QPushButton, side_chars: int = 2):
        fm = QFontMetrics(button.font())
        text = button.text() or ""
        text_width = fm.horizontalAdvance(text)
        char_width = max(6, fm.horizontalAdvance("0"))
        width = text_width + (side_chars * 2 * char_width) + 16
        button.setFixedWidth(max(80, width))

    def _update_sys_scroll_safe_padding(self, *_args):
        if not hasattr(self, "sys_scroll_area") or not hasattr(self, "sys_form_layout"):
            return
        bar = self.sys_scroll_area.verticalScrollBar()
        right_gap = self.SYS_SCROLL_SAFE_GAP
        if bar.maximum() > 0:
            right_gap += bar.sizeHint().width() + 2
        self.sys_form_layout.setContentsMargins(0, 0, right_gap, 0)

    @staticmethod
    def _build_enum_combo(options):
        combo = QComboBox()
        combo.setMinimumWidth(120)
        combo.setMaximumWidth(168)
        combo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        for text, value in options:
            combo.addItem(text, value)
        return combo

    def _bind_signals(self):
        self.Uart_En.clicked.connect(self.toggle_serial_connection)
        self.Check_Byte.currentTextChanged.connect(self.device_client.set_parity)
        self.Board_ID.valueChanged.connect(self.device_client.set_board_id)

        self.btn_open_omnictrl.clicked.connect(self.open_omnictrl)
        self.btn_download_graph.clicked.connect(self.download_graph)

        self.btn_send_template_speed.clicked.connect(self.send_template_speed)

        self.btn_read_sys_params.clicked.connect(self.read_system_params)
        self.btn_write_sys_params.clicked.connect(self.write_system_params)

    def _init_timers(self):
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(200)

        self.port_refresh_timer = QTimer(self)
        self.port_refresh_timer.timeout.connect(self._refresh_ports_tick)
        self.port_refresh_timer.start(1000)

        self.client_timer = QTimer(self)
        self.client_timer.timeout.connect(self.device_client.tick)
        self.client_timer.start(50)

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._poll_device)
        self.poll_timer.setInterval(120)

        self.chart_timer = QTimer(self)
        self.chart_timer.timeout.connect(self._append_chart_point)
        self.chart_timer.setInterval(100)

    def _init_chart(self):
        self.chart = QChart()
        self.chart_window.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chart_window.setMinimumHeight(420)

        self.series_current_a = QLineSeries()
        self.series_target_a = QLineSeries()
        self.series_current_b = QLineSeries()
        self.series_target_b = QLineSeries()

        self.series_current_a.setName("A当前")
        self.series_target_a.setName("A目标")
        self.series_current_b.setName("B当前")
        self.series_target_b.setName("B目标")

        self.series_current_a.setColor(Qt.red)
        self.series_target_a.setColor(QColor(255, 140, 0))
        self.series_current_b.setColor(Qt.blue)
        self.series_target_b.setColor(QColor(0, 170, 255))

        self.chart.addSeries(self.series_current_a)
        self.chart.addSeries(self.series_target_a)
        self.chart.addSeries(self.series_current_b)
        self.chart.addSeries(self.series_target_b)

        self.axis_x = QValueAxis()
        self.axis_y = QValueAxis()
        self.axis_x.setTitleText("采样点")
        self.axis_y.setTitleText("速度")
        self.axis_x.setRange(0, self.max_data_points)
        self.axis_y.setRange(-150, 150)
        self.axis_x.setGridLineVisible(True)
        self.axis_y.setGridLineVisible(True)

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        for series in [self.series_current_a, self.series_target_a, self.series_current_b, self.series_target_b]:
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)

        self.chart.legend().setVisible(True)
        self.chart_window.setChart(self.chart)

        self.chart_motor1_speed_en.setText("A当前")
        self.chart_motor2_speed_en.setText("B当前")

        self.chart_target_a_en = QCheckBox("A目标", self.centralwidget)
        self.chart_target_b_en = QCheckBox("B目标", self.centralwidget)
        self.chart_target_a_en.setChecked(True)
        self.chart_target_b_en.setChecked(True)

        insert_pos = max(0, self.horizontalLayout_7.count() - 1)
        self.horizontalLayout_7.insertWidget(insert_pos, self.chart_target_a_en)
        self.horizontalLayout_7.insertWidget(insert_pos + 1, self.chart_target_b_en)

        self.chart_motor1_speed_en.stateChanged.connect(
            lambda state: self.series_current_a.setVisible(bool(state))
        )
        self.chart_motor2_speed_en.stateChanged.connect(
            lambda state: self.series_current_b.setVisible(bool(state))
        )
        self.chart_target_a_en.stateChanged.connect(
            lambda state: self.series_target_a.setVisible(bool(state))
        )
        self.chart_target_b_en.stateChanged.connect(
            lambda state: self.series_target_b.setVisible(bool(state))
        )

        # Right side: title / chart / legend / value text.
        self.monitor_group_layout.setStretch(0, 10)
        self.monitor_group_layout.setStretch(1, 0)
        self.monitor_group_layout.setStretch(2, 0)

    def toggle_serial_connection(self):
        if global_serial_manager.get_connection_status():
            self.close_serial()
        else:
            self.open_serial()

    def open_serial(self):
        port = self.Uart_Port.currentText().strip()
        if not port:
            QMessageBox.warning(self, "错误", "未检测到可用串口")
            return

        baud_rate = int(self.Baud_Rate.currentText())

        if not global_serial_manager.connect(port, baud_rate):
            QMessageBox.warning(self, "错误", f"串口打开失败: {port}")
            return

        self.device_client.set_transport(global_serial_manager.send_data)
        self.device_client.clear()
        self.device_client.set_board_id(self.Board_ID.value())
        self.device_client.set_parity(self.Check_Byte.currentText())

        self._set_state(self.STATE_CONNECTED_NO_GRAPH)
        self._sys_params_loaded = False
        self.statusBar().showMessage(f"已连接 {port} @ {baud_rate}")

    def close_serial(self):
        global_serial_manager.disconnect()
        self.device_client.clear()
        self._set_state(self.STATE_DISCONNECTED)
        self._sys_params_loaded = False
        self.statusBar().showMessage("串口已断开")

    def _set_state(self, state: str):
        self.run_state = state

        self.poll_timer.stop()
        if state != self.STATE_DISCONNECTED:
            self.poll_timer.start()
            if not self.chart_timer.isActive():
                self.chart_timer.start()
        else:
            self.chart_timer.stop()
            self._monitor_sample_pending = False

        if state == self.STATE_DISCONNECTED:
            self.Uart_En.setText("打开串口")
            self._fit_button_width(self.Uart_En)
            self.device_client.clear()
        else:
            self.Uart_En.setText("关闭串口")
            self._fit_button_width(self.Uart_En)

        self._update_control_enabled_state()

    def _update_control_enabled_state(self):
        connected = self.run_state != self.STATE_DISCONNECTED
        has_graph = bool(self.recent_graph_bytes)

        self.btn_download_graph.setEnabled(connected and has_graph)
        self.btn_send_template_speed.setEnabled(connected)
        self.btn_read_sys_params.setEnabled(connected)
        self.btn_write_sys_params.setEnabled(connected)

        if self.run_state == self.STATE_RUNNING:
            self.statusBar().showMessage("状态: Running")
        elif self.run_state == self.STATE_CONNECTED_NO_GRAPH:
            self.statusBar().showMessage("状态: Connected_NoGraph（请先下载图结构）")
        else:
            self.statusBar().showMessage("状态: Disconnected")

    def update_status(self):
        connected = global_serial_manager.get_connection_status()
        if not connected and self.run_state != self.STATE_DISCONNECTED:
            self._set_state(self.STATE_DISCONNECTED)

    def _refresh_ports_tick(self):
        if self.run_state == self.STATE_DISCONNECTED:
            self._refresh_ports(force=False)

    def _refresh_ports(self, force: bool):
        ports = global_serial_manager.get_ports()
        if not force and ports == self.last_ports:
            return

        current = self.Uart_Port.currentText()
        self.Uart_Port.blockSignals(True)
        self.Uart_Port.clear()
        for port in ports:
            self.Uart_Port.addItem(port)
        if current in ports:
            self.Uart_Port.setCurrentText(current)
        self.Uart_Port.blockSignals(False)

        self.last_ports = ports

    def _on_serial_bytes(self, data: bytes):
        self.device_client.feed_serial(data)

    def _on_protocol_frame(self, frame: ProtocolFrame):
        board_id = self.Board_ID.value() & 0xFF
        if frame.addr not in (board_id, 0):
            return

        if frame.func == 0x11:
            parsed = DeviceClient.parse_hostif_motor_frame(frame)
            if parsed is not None:
                self.latest_current_a, self.latest_current_b = parsed
                self._update_speed_values_text()
                if self.run_state != self.STATE_DISCONNECTED:
                    self._monitor_sample_pending = True
            return

        if frame.func == 0x03 and frame.reg == ProtocolCodec.REG_MOTOR_STATE:
            return

        if frame.func == 0x03 and frame.reg == ProtocolCodec.REG_MOTOR_TARGET:
            parsed = DeviceClient.parse_motor_payload(frame.payload)
            if parsed is not None:
                self.latest_target_a, self.latest_target_b = parsed
                self._update_speed_values_text()
            return

        if frame.func == 0x06 and frame.reg == ProtocolCodec.REG_MOTOR_TARGET:
            return

        if frame.func == 0x03 and frame.reg == ProtocolCodec.REG_SYSTEM_BASE:
            self._on_read_system_params_done(
                type('R', (), {'success': True, 'frame': frame})())

    def _on_protocol_log(self, text: str):
        if text:
            self.statusBar().showMessage(text[:140])

    def _poll_device(self):
        if self.run_state == self.STATE_DISCONNECTED:
            return
        elif not self._sys_params_loaded:
            return
        
        # Keep chart "target" data bound to MCU-side values:
        # poll target register periodically to refresh latest_target_*.
        if self.poll_phase == 0:
            self.device_client.request_target_speed()
            self.poll_phase = 1
        else:
            self.poll_phase = 0

    def _append_chart_point(self):
        if self.run_state == self.STATE_DISCONNECTED or not self._monitor_sample_pending:
            return

        self._monitor_sample_pending = False

        x = self.data_counter
        self.series_current_a.append(x, self.latest_current_a)
        self.series_target_a.append(x, self.latest_target_a)
        self.series_current_b.append(x, self.latest_current_b)
        self.series_target_b.append(x, self.latest_target_b)

        self.data_counter += 1
        if self.data_counter > self.max_data_points:
            self.axis_x.setRange(self.data_counter - self.max_data_points, self.data_counter)

        for series in [
            self.series_current_a,
            self.series_target_a,
            self.series_current_b,
            self.series_target_b,
        ]:
            if len(series.pointsVector()) > self.max_data_points:
                series.remove(0, 1)

        self._update_axis_y()

    def _update_axis_y(self):
        values = [
            self.latest_current_a,
            self.latest_target_a,
            self.latest_current_b,
            self.latest_target_b,
        ]
        bound = max(200, int(max(abs(v) for v in values) * 1.2) + 10)
        self.axis_y.setRange(-bound, bound)

    def _update_speed_values_text(self):
        self.speed_value_label.setText(
            f"A当前: {self.latest_current_a}  A目标: {self.latest_target_a}  "
            f"B当前: {self.latest_current_b}  B目标: {self.latest_target_b}"
        )

    def open_omnictrl(self):
        if self.omni_process is not None and self.omni_process.state() != QProcess.NotRunning:
            QMessageBox.information(self, "提示", "OmniCtrl 已在运行")
            return

        project_root = Path(__file__).resolve().parents[4]
        script_path = project_root / "OmniCtrl" / "studio" /"OmniCtrl" / "main.py"
        if not script_path.exists():
            QMessageBox.warning(self, "错误", f"未找到 OmniCtrl: {script_path}")
            return

        self.omni_output_text = ""
        process = QProcess(self)
        process.setProgram(sys.executable)
        process.setArguments([str(script_path)])
        process.setWorkingDirectory(str(script_path.parent))
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyReadStandardOutput.connect(self._on_omnictrl_output)
        process.finished.connect(self._on_omnictrl_finished)
        process.errorOccurred.connect(self._on_omnictrl_error)
        process.start()

        if not process.waitForStarted(3000):
            QMessageBox.warning(self, "错误", "OmniCtrl 启动失败")
            process.deleteLater()
            return

        self.omni_process = process
        self._sys_params_loaded = False
        self.graph_status_label.setText("最近图结构: OmniCtrl 运行中，关闭后自动解析")

    def _on_omnictrl_output(self):
        if self.omni_process is None:
            return
        chunk = bytes(self.omni_process.readAllStandardOutput()).decode("utf-8", errors="ignore")
        if chunk:
            self.omni_output_text += chunk

    def _on_omnictrl_finished(self, _exit_code: int, _exit_status: int):
        graph = ProtocolCodec.parse_graph_hex(self.omni_output_text)
        self.omni_process = None

        if graph is None:
            self.graph_status_label.setText("最近图结构: 未在 OmniCtrl 输出中找到 Hex Result")
            self._update_control_enabled_state()
            return

        valid, reason = ProtocolCodec.validate_graph_blob(graph)
        if not valid:
            self.recent_graph_bytes = b""
            self.graph_status_label.setText(f"最近图结构: 无效 ({reason})")
            self._update_control_enabled_state()
            return

        self.recent_graph_bytes = graph
        self.graph_status_label.setText(f"最近图结构: 已加载 ({len(graph)} bytes)")
        self._update_control_enabled_state()

    def _on_omnictrl_error(self, _error):
        self.graph_status_label.setText("最近图结构: OmniCtrl 运行异常")

    def download_graph(self):
        if self.run_state == self.STATE_DISCONNECTED:
            QMessageBox.warning(self, "错误", "请先连接串口")
            return

        if not self.recent_graph_bytes:
            QMessageBox.warning(self, "错误", "尚未加载图结构")
            return

        self.graph_status_label.setText("最近图结构: 下载中...")
        self.device_client.clear()
        self.device_client.download_graph(self.recent_graph_bytes, callback=self._on_graph_download_done)

    def _on_graph_download_done(self, result: RequestResult):
        if result.success:
            self.graph_status_label.setText("最近图结构: 下载成功")
            self._set_state(self.STATE_RUNNING)
            return

        text = result.error or "下载失败"
        self.graph_status_label.setText(f"最近图结构: {text}")
        if self.run_state == self.STATE_RUNNING:
            self._set_state(self.STATE_CONNECTED_NO_GRAPH)

    def send_template_speed(self):
        if self.run_state == self.STATE_DISCONNECTED:
            QMessageBox.warning(self, "错误", "请先连接串口")
            return

        speed_a = self.template_speed_a.value()
        speed_b = self.template_speed_b.value()

        self.template_speed_status_label.setText("下发中...")
        self.device_client.set_target_speed(speed_a, speed_b, callback=self._on_template_speed_done)

    def _on_template_speed_done(self, result: RequestResult):
        if result.success:
            self.template_speed_status_label.setText("下发成功")
            self.device_client.request_target_speed()
            return
        text = result.error or "下发失败"
        if result.timeout:
            text = "下发超时"
        self.template_speed_status_label.setText(text)

    def read_system_params(self):
        if self.run_state == self.STATE_DISCONNECTED:
            QMessageBox.warning(self, "错误", "请先连接串口")
            return
        self.sys_param_status_label.setText("读取中...")
        self.device_client.read_system_params(callback=self._on_read_system_params_done)

    def _on_read_system_params_done(self, result):
        if not result.success or result.frame is None:
            self.sys_param_status_label.setText("读取失败，请重试")
            return
        parsed = DeviceClient.parse_system_payload(result.frame.payload)
        if parsed is None:
            self.sys_param_status_label.setText("读取失败：数据长度不足")
            return
        serial, baud, parity, response, dire, display_sleep, sleep_hi, sleep_lo, hostif_en, hostif_motor_en = parsed
        self._set_combo_value(self.sys_serial, serial)
        self._set_combo_value(self.sys_baud, baud)
        self._set_combo_value(self.sys_parity, parity)
        self._set_combo_value(self.sys_response, response)
        self._set_combo_value(self.sys_dir, dire)
        self._set_combo_value(self.sys_display_sleep, display_sleep)
        self.sys_sleep_time.setValue(int(((sleep_hi << 16) | sleep_lo) & 0x7FFFFFFF))
        self._set_combo_value(self.sys_hostif_en, hostif_en)
        self._set_combo_value(self.sys_hostif_motor_en, hostif_motor_en)
        self.sys_param_status_label.setText("读取完成")

        # 开启轮询电机状态(下载时需要关闭)
        if(self.sys_hostif_en and self.sys_hostif_motor_en):
            self._sys_params_loaded = True
        else:
            self._sys_params_loaded = False

    def write_system_params(self):
        if self.run_state == self.STATE_DISCONNECTED:
            QMessageBox.warning(self, "错误", "请先连接串口")
            return
        sleep_value = int(self.sys_sleep_time.value())
        values = (
            self._combo_value(self.sys_serial),
            self._combo_value(self.sys_baud),
            self._combo_value(self.sys_parity),
            self._combo_value(self.sys_response),
            self._combo_value(self.sys_dir),
            self._combo_value(self.sys_display_sleep),
            (sleep_value >> 16) & 0xFFFF,
            sleep_value & 0xFFFF,
            self._combo_value(self.sys_hostif_en),
            self._combo_value(self.sys_hostif_motor_en),
        )
        self.sys_param_status_label.setText("写入中...")
        self.device_client.write_system_params(values, callback=self._on_write_system_params_done)
        
    def _on_write_system_params_done(self, result):
        if result.success:
            parity_synced = self._sync_transport_parity_from_system_params()
            self.sys_param_status_label.setText("写入完成")
            if parity_synced:
                self.statusBar().showMessage(
                    f"系统参数已写入，协议校验已同步到 {self.Check_Byte.currentText()}。若修改了端口类型或波特率，请按新配置连接。"
                )
            else:
                self.statusBar().showMessage(
                    "系统参数已写入，若修改了端口类型或波特率，请按新配置重新连接。"
                )
        else:
            self.sys_param_status_label.setText(result.error or "写入失败")

    def _sync_transport_parity_from_system_params(self) -> bool:
        parity_text = self.sys_parity.currentText().strip()
        if not parity_text or self.Check_Byte.currentText() == parity_text:
            return False

        # Drop queued packets encoded with the old parity before switching codec mode.
        self.device_client.clear()
        self.Check_Byte.setCurrentText(parity_text)
        return True

    @staticmethod
    def _combo_value(combo: QComboBox) -> int:
        value = combo.currentData()
        if value is None:
            return 0
        return int(value)

    def _set_combo_value(self, combo: QComboBox, value: int):
        for idx in range(combo.count()):
            if int(combo.itemData(idx)) == int(value):
                combo.setCurrentIndex(idx)
                return

    def _apply_system_param_readback(self, reg: int, payload: bytes):
        value = DeviceClient.parse_u16_payload(payload)
        if value is None:
            return

        if reg == self.REG_SLEEP_TIME_HI:
            self._sleep_time_hi = value
            self.sys_sleep_time.setValue((self._sleep_time_hi << 16) | self._sleep_time_lo)
            return

        if reg == self.REG_SLEEP_TIME_LO:
            self._sleep_time_lo = value
            self.sys_sleep_time.setValue((self._sleep_time_hi << 16) | self._sleep_time_lo)
            return

        widget = self.sys_param_widgets.get(reg)
        if widget is not None:
            self._set_combo_value(widget, value)

    def _start_system_batch(self, mode: str, total: int):
        self._sys_batch_mode = mode
        self._sys_batch_total = total
        self._sys_batch_pending = total
        self._sys_batch_failed = 0
        self.sys_param_status_label.setText(f"{mode}中...")

    def _on_system_batch_result(self, reg: int, result: RequestResult):
        if self._sys_batch_pending <= 0:
            return

        if result.success and result.frame is not None and self._sys_batch_mode == "read":
            self._apply_system_param_readback(reg, result.frame.payload)
        else:
            self._sys_batch_failed += 1

        self._sys_batch_pending -= 1
        if self._sys_batch_pending > 0:
            return

        if self._sys_batch_failed == 0:
            self.sys_param_status_label.setText(f"{self._sys_batch_mode}完成")
            return

        self.sys_param_status_label.setText(
            f"{self._sys_batch_mode}完成: {self._sys_batch_failed}/{self._sys_batch_total} 失败，等待 MCU 适配"
        )

    def closeEvent(self, event: QCloseEvent):
        if self.omni_process is not None and self.omni_process.state() != QProcess.NotRunning:
            self.omni_process.kill()
            self.omni_process.waitForFinished(1000)
        global_serial_manager.disconnect()
        event.accept()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
