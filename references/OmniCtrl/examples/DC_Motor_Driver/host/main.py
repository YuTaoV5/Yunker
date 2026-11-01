import sys
from PyQt5.QtWidgets import QApplication
from PyQt.main_window import MainWindow  # 导入实际功能窗口类

if __name__ == '__main__':
    # 创建应用实例
    app = QApplication(sys.argv)
    # 实例化主窗口（已包含UI初始化和功能逻辑）
    main_window = MainWindow()
    # 显示窗口
    main_window.show()
    # 启动应用事件循环
    sys.exit(app.exec_())
