import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, Optional, Tuple

from .protocol import ParityMode, ProtocolCodec, ProtocolFrame, ProtocolLog


@dataclass
class RequestResult:
    name: str
    success: bool
    timeout: bool = False
    retries: int = 0
    frame: Optional[ProtocolFrame] = None
    error: str = ""


@dataclass
class _PendingRequest:
    name: str
    packet: bytes
    matcher: Optional[Callable[[ProtocolFrame], bool]]
    callback: Optional[Callable[[RequestResult], None]]
    timeout_s: float
    retries_left: int
    raw_echo: Optional[bytes] = None
    send_count: int = 0
    deadline: float = 0.0


class DeviceClient:
    """Queue-based request client over SerialManager transport."""

    def __init__(self, send_func: Optional[Callable[[bytes], bool]] = None):
        self._codec = ProtocolCodec(ParityMode.CRC)
        self._send_func = send_func
        self._board_id = 1

        self._queue: Deque[_PendingRequest] = deque()
        self._active: Optional[_PendingRequest] = None

        self._raw_window = bytearray()

        self.frame_listener: Optional[Callable[[ProtocolFrame], None]] = None
        self.log_listener: Optional[Callable[[str], None]] = None

    def set_transport(self, send_func: Callable[[bytes], bool]) -> None:
        self._send_func = send_func

    def set_board_id(self, board_id: int) -> None:
        self._board_id = int(board_id) & 0xFF

    def set_parity(self, parity: str) -> None:
        self._codec.set_parity(parity)

    def clear(self) -> None:
        self._queue.clear()
        self._active = None
        self._raw_window.clear()

    def pending_count(self) -> int:
        return len(self._queue) + (1 if self._active else 0)

    def feed_serial(self, data: bytes) -> None:
        if not data:
            return

        self._raw_window.extend(data)
        if len(self._raw_window) > 4096:
            self._raw_window = self._raw_window[-1024:]

        if self._active is not None and self._active.raw_echo:
            if self._active.raw_echo in self._raw_window:
                self._finish_active(success=True)

        messages = self._codec.feed_rx(data)
        for message in messages:
            if isinstance(message, ProtocolLog):
                if self.log_listener:
                    self.log_listener(message.text)
                continue

            if self.frame_listener:
                self.frame_listener(message)

            if self._active is None:
                continue
            if self._active.raw_echo is not None:
                continue
            if self._active.matcher is None:
                continue
            if self._active.matcher(message):
                self._finish_active(success=True, frame=message)

    def tick(self) -> None:
        if self._active is None:
            self._start_next()
            return

        if self._active.deadline <= 0:
            return

        if time.monotonic() < self._active.deadline:
            return

        if self._active.retries_left > 0:
            self._active.retries_left -= 1
            self._send_active()
            return

        self._finish_active(
            success=False,
            timeout=True,
            error=f"{self._active.name} timeout",
        )

    def request_current_speed(
        self,
        callback: Optional[Callable[[RequestResult], None]] = None,
        timeout_s: float = 0.3,
        retries: int = 2,
    ) -> None:
        packet = self._codec.build_read(self._board_id, ProtocolCodec.REG_MOTOR_STATE)
        self._queue_request(
            _PendingRequest(
                name="read_current_speed",
                packet=packet,
                matcher=lambda frame: frame.func == 0x03 and frame.reg == ProtocolCodec.REG_MOTOR_STATE,
                callback=callback,
                timeout_s=timeout_s,
                retries_left=max(0, int(retries)),
            )
        )

    def request_target_speed(
        self,
        callback: Optional[Callable[[RequestResult], None]] = None,
        timeout_s: float = 0.3,
        retries: int = 2,
    ) -> None:
        packet = self._codec.build_read(self._board_id, ProtocolCodec.REG_MOTOR_TARGET)
        self._queue_request(
            _PendingRequest(
                name="read_target_speed",
                packet=packet,
                matcher=lambda frame: frame.func == 0x03 and frame.reg == ProtocolCodec.REG_MOTOR_TARGET,
                callback=callback,
                timeout_s=timeout_s,
                retries_left=max(0, int(retries)),
            )
        )

    def set_target_speed(
        self,
        speed_a: int,
        speed_b: int,
        callback: Optional[Callable[[RequestResult], None]] = None,
        timeout_s: float = 0.3,
        retries: int = 1,
    ) -> None:
        payload = self._pack_i16(speed_a) + self._pack_i16(speed_b)
        packet = self._codec.build_write(self._board_id, ProtocolCodec.REG_MOTOR_TARGET, payload, parity=ParityMode.MARK_4B)
        self._queue_request(
            _PendingRequest(
                name="set_target_speed",
                packet=packet,
                matcher=lambda frame: frame.func == 0x06 and frame.reg == ProtocolCodec.REG_MOTOR_TARGET,
                callback=callback,
                timeout_s=timeout_s,
                retries_left=max(0, int(retries)),
            )
        )

    def read_system_params(
        self,
        callback: Optional[Callable[[RequestResult], None]] = None,
        timeout_s: float = 0.5,
        retries: int = 1,
    ) -> None:
        """Read all system parameters as a single block (reg 0x10)."""
        packet = self._codec.build_read(self._board_id, ProtocolCodec.REG_SYSTEM_BASE)
        self._queue_request(
            _PendingRequest(
                name="read_system_params",
                packet=packet,
                matcher=lambda frame: frame.func == 0x03 and frame.reg == ProtocolCodec.REG_SYSTEM_BASE,
                callback=callback,
                timeout_s=timeout_s,
                retries_left=max(0, int(retries)),
            )
        )

    def write_system_params(
        self,
        values: Tuple[int, ...],
        callback: Optional[Callable[[RequestResult], None]] = None,
        timeout_s: float = 0.5,
        retries: int = 1,
    ) -> None:
        """Write all system parameters as a single block (reg 0x10).
        values: tuple of 10 uint16 in order:
          serial, baud, parity, response, dir, display_sleep,
          sleep_hi, sleep_lo, hostif_en, hostif_motor_en
        """
        payload = b"".join(int(v & 0xFFFF).to_bytes(2, byteorder="big") for v in values)
        packet = self._codec.build_write(self._board_id, ProtocolCodec.REG_SYSTEM_BASE, payload)
        self._queue_request(
            _PendingRequest(
                name="write_system_params",
                packet=packet,
                matcher=lambda frame: frame.func == 0x06 and frame.reg == ProtocolCodec.REG_SYSTEM_BASE,
                callback=callback,
                timeout_s=timeout_s,
                retries_left=max(0, int(retries)),
            )
        )

    @staticmethod
    def parse_system_payload(payload: bytes) -> Optional[Tuple[int, ...]]:
        """Parse system param block payload (20 bytes = 10 x uint16 big-endian)."""
        if len(payload) < 20:
            return None
        return tuple(
            int.from_bytes(payload[i*2:i*2+2], byteorder="big", signed=False)
            for i in range(10)
        )

    def download_graph(
        self,
        graph_bytes: bytes,
        callback: Optional[Callable[[RequestResult], None]] = None,
        timeout_s: float = 0.5,
        retries: int = 0,
    ) -> None:
        valid, reason = ProtocolCodec.validate_graph_blob(graph_bytes)
        if not valid:
            if callback:
                callback(
                    RequestResult(
                        name="download_graph",
                        success=False,
                        timeout=False,
                        retries=0,
                        error=reason,
                    )
                )
            return

        self._queue_request(
            _PendingRequest(
                name="download_graph",
                packet=bytes(graph_bytes),
                matcher=None,
                callback=callback,
                timeout_s=timeout_s,
                retries_left=max(0, int(retries)),
                raw_echo=bytes(graph_bytes),
            )
        )

    def _queue_request(self, request: _PendingRequest) -> None:
        self._queue.append(request)
        self.tick()

    def _start_next(self) -> None:
        if self._active is not None or not self._queue:
            return
        self._active = self._queue.popleft()
        self._send_active()

    def _send_active(self) -> None:
        if self._active is None:
            return

        if not self._send_packet(self._active.packet):
            self._finish_active(
                success=False,
                timeout=False,
                error=f"{self._active.name} send failed",
            )
            return

        self._active.send_count += 1
        if self._active.name in ("set_target_speed", "write_system_params"):
            self._finish_active(success=True)
            return
        self._active.deadline = time.monotonic() + self._active.timeout_s

    def _finish_active(
        self,
        success: bool,
        frame: Optional[ProtocolFrame] = None,
        timeout: bool = False,
        error: str = "",
    ) -> None:
        finished = self._active
        self._active = None

        if finished and finished.callback:
            finished.callback(
                RequestResult(
                    name=finished.name,
                    success=success,
                    timeout=timeout,
                    retries=max(0, finished.send_count - 1),
                    frame=frame,
                    error=error,
                )
            )

        self._start_next()

    def _send_packet(self, packet: bytes) -> bool:
        if self._send_func is None:
            return False
        try:
            return bool(self._send_func(packet))
        except Exception:
            return False

    @staticmethod
    def parse_motor_payload(payload: bytes) -> Optional[Tuple[int, int]]:
        if len(payload) < 4:
            return None
        speed_a = int.from_bytes(payload[0:2], byteorder="big", signed=True)
        speed_b = int.from_bytes(payload[2:4], byteorder="big", signed=True)
        return speed_a, speed_b

    @staticmethod
    def parse_hostif_motor_frame(frame: ProtocolFrame) -> Optional[Tuple[int, int]]:
        if frame.func != 0x11:
            return None
        return DeviceClient.parse_motor_payload(bytes((frame.reg & 0xFF,)) + frame.payload)

    @staticmethod
    def parse_u16_payload(payload: bytes) -> Optional[int]:
        if len(payload) < 2:
            return None
        return int.from_bytes(payload[:2], byteorder="big", signed=False)

    @staticmethod
    def _pack_i16(value: int) -> bytes:
        val = int(value)
        if val > 32767:
            val = 32767
        if val < -32768:
            val = -32768
        return val.to_bytes(2, byteorder="big", signed=True)
