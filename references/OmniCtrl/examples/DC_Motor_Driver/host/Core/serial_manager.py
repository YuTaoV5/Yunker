import threading
import time
from typing import Callable, List, Optional

import serial
import serial.tools.list_ports


class SerialManager:
    """Thin serial transport with background RX thread."""

    def __init__(self):
        self.serial_port: Optional[serial.Serial] = None
        self.port_name = ""
        self.baud_rate = 115200
        self.is_connected = False

        self.read_thread: Optional[threading.Thread] = None
        self.read_callback: Optional[Callable[[bytes], None]] = None

        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def get_ports(self) -> List[str]:
        ports = serial.tools.list_ports.comports()
        return sorted([p.device for p in ports])

    def connect(self, port: str, baud_rate: int = 115200, timeout: float = 0.1) -> bool:
        if not port:
            return False

        self.disconnect()
        try:
            serial_port = serial.Serial(
                port=port,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
            )
        except Exception as exc:
            print(f"Serial connect failed: {exc}")
            return False

        with self._lock:
            self.serial_port = serial_port
            self.port_name = port
            self.baud_rate = int(baud_rate)
            self.is_connected = bool(serial_port.is_open)

        self._stop_event.clear()
        self._start_read_thread()
        return self.is_connected

    def disconnect(self):
        self._stop_event.set()

        thread = self.read_thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.0)

        with self._lock:
            serial_port = self.serial_port
            self.serial_port = None
            self.is_connected = False
            self.port_name = ""
            self.baud_rate = 115200

        if serial_port is not None:
            try:
                if serial_port.is_open:
                    serial_port.close()
            except Exception:
                pass

    def _start_read_thread(self):
        if self.read_thread and self.read_thread.is_alive():
            return
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()

    def _read_loop(self):
        while not self._stop_event.is_set():
            with self._lock:
                serial_port = self.serial_port
                callback = self.read_callback

            if serial_port is None or not serial_port.is_open:
                time.sleep(0.05)
                continue

            try:
                waiting = serial_port.in_waiting
                if waiting > 0:
                    data = serial_port.read(waiting)
                    if data and callback is not None:
                        callback(bytes(data))
                else:
                    time.sleep(0.01)
            except Exception as exc:
                print(f"Serial read failed: {exc}")
                break

        # Ensure status is reset when read loop exits unexpectedly.
        with self._lock:
            self.is_connected = False

    def send_data(self, data: bytes) -> bool:
        if not data:
            return False

        with self._lock:
            serial_port = self.serial_port

        if serial_port is None or not serial_port.is_open:
            return False

        try:
            serial_port.write(data)
            return True
        except Exception as exc:
            print(f"Serial write failed: {exc}")
            return False

    def set_read_callback(self, callback: Callable[[bytes], None]):
        self.read_callback = callback

    def get_connection_status(self) -> bool:
        with self._lock:
            return self.is_connected and self.serial_port is not None and self.serial_port.is_open

    def get_port_info(self) -> dict:
        with self._lock:
            return {
                "port": self.port_name,
                "baudrate": self.baud_rate,
                "connected": self.is_connected,
            }

    def __del__(self):
        self.disconnect()


global_serial_manager = SerialManager()
