import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union


class ParityMode(str, Enum):
    NONE = "None"
    MARK_4B = "0x4B"
    CRC = "CRC"


@dataclass
class ProtocolFrame:
    addr: int
    func: int
    reg: int
    payload: bytes
    raw: bytes


@dataclass
class ProtocolLog:
    text: str


ProtocolMessage = Union[ProtocolFrame, ProtocolLog]


class ProtocolCodec:
    """Protocol codec for board communication and OmniCtrl graph blob checks."""

    GRAPH_MAGIC = b"\x20\x13\x14"
    MAX_GRAPH_FRAME_SIZE = 100

    REG_MOTOR_STATE = 0x01
    REG_MOTOR_TARGET = 0x02
    REG_SYSTEM_BASE = 0x10

    _HEX_PATTERN = re.compile(r"Hex Result:\s*0x([0-9A-Fa-f]+)")

    def __init__(self, parity: Union[str, ParityMode] = ParityMode.CRC):
        self._buffer = bytearray()
        self._parity = self.normalize_parity(parity)

    @staticmethod
    def normalize_parity(parity: Union[str, ParityMode]) -> ParityMode:
        if isinstance(parity, ParityMode):
            return parity
        parity_text = str(parity).strip().upper()
        if parity_text in {"NONE", "NULL"}:
            return ParityMode.NONE
        if parity_text in {"0X4B", "4B", "MARK_4B"}:
            return ParityMode.MARK_4B
        return ParityMode.CRC

    def set_parity(self, parity: Union[str, ParityMode]) -> None:
        self._parity = self.normalize_parity(parity)

    @staticmethod
    def crc16_modbus(data: bytes) -> int:
        crc = 0xFFFF
        for value in data:
            crc ^= value
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc & 0xFFFF

    @staticmethod
    def crc32_host(data: bytes) -> int:
        crc = 0xFFFFFFFF
        for value in data:
            crc ^= value
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc >>= 1
        return crc & 0xFFFFFFFF

    @classmethod
    def parity_tail_size(cls, parity: Union[str, ParityMode]) -> int:
        mode = cls.normalize_parity(parity)
        if mode == ParityMode.NONE:
            return 0
        if mode == ParityMode.MARK_4B:
            return 1
        return 2

    @classmethod
    def append_parity(cls, frame: bytes, parity: Union[str, ParityMode]) -> bytes:
        mode = cls.normalize_parity(parity)
        if mode == ParityMode.NONE:
            return frame
        if mode == ParityMode.MARK_4B:
            return frame + b"\x4B"
        crc = cls.crc16_modbus(frame)
        return frame + bytes((crc & 0xFF, (crc >> 8) & 0xFF))

    @classmethod
    def verify_parity(cls, frame: bytes, parity: Union[str, ParityMode]) -> bool:
        mode = cls.normalize_parity(parity)
        if mode == ParityMode.NONE:
            return True
        if mode == ParityMode.MARK_4B:
            return len(frame) >= 1 and frame[-1] == 0x4B
        if len(frame) < 3:
            return False
        body = frame[:-2]
        recv_crc = frame[-2] | (frame[-1] << 8)
        return cls.crc16_modbus(body) == recv_crc

    def build_read(self, addr: int, reg: int,
                   parity: Optional[Union[str, ParityMode]] = None) -> bytes:
        mode = self._parity if parity is None else self.normalize_parity(parity)
        frame = bytes((addr & 0xFF, 0x03, reg & 0xFF))
        return self.append_parity(frame, mode)

    def build_write(self, addr: int, reg: int, payload: bytes,
                    parity: Optional[Union[str, ParityMode]] = None) -> bytes:
        mode = self._parity if parity is None else self.normalize_parity(parity)
        frame = bytes((addr & 0xFF, 0x06, reg & 0xFF)) + bytes(payload)
        return self.append_parity(frame, mode)

    def feed_rx(self, data: bytes) -> List[ProtocolMessage]:
        if not data:
            return []

        self._buffer.extend(data)
        messages: List[ProtocolMessage] = []

        while self._buffer:
            if self._buffer[0] == ord("["):
                consumed, log_text = self._extract_log_line(require_bracket=True)
                if consumed == 0:
                    break
                del self._buffer[:consumed]
                if log_text:
                    messages.append(ProtocolLog(log_text))
                continue

            parse_status, frame, consumed = self._extract_frame()
            if parse_status == "parsed" and frame is not None:
                del self._buffer[:consumed]
                messages.append(frame)
                continue
            if parse_status == "need_more":
                break

            consumed, log_text = self._extract_log_line(require_bracket=False)
            if consumed > 0:
                del self._buffer[:consumed]
                if log_text:
                    messages.append(ProtocolLog(log_text))
                continue

            del self._buffer[0]

        # Keep bounded buffer size under long noise stream.
        if len(self._buffer) > 4096:
            self._buffer = self._buffer[-1024:]

        return messages

    def _extract_frame(self) -> Tuple[str, Optional[ProtocolFrame], int]:
        tail_len = self.parity_tail_size(self._parity)
        if len(self._buffer) < 3 + tail_len:
            return "need_more", None, 0

        addr = self._buffer[0]
        func = self._buffer[1]
        reg = self._buffer[2]
        if func not in (0x03, 0x06, 0x11):
            return "invalid", None, 1

        if self._looks_like_repeated_read_echo(func, reg):
            return "invalid", None, 3

        base_len = self._guess_base_length(func, reg)
        full_len = base_len + tail_len
        if len(self._buffer) < full_len:
            return "need_more", None, 0

        raw = bytes(self._buffer[:full_len])
        if not self.verify_parity(raw, self._parity):
            return "invalid", None, 1

        payload = raw[3:base_len]
        frame = ProtocolFrame(addr=addr, func=func, reg=reg, payload=payload, raw=raw)
        return "parsed", frame, full_len

    def _looks_like_repeated_read_echo(self, func: int, reg: int) -> bool:
        if self._parity != ParityMode.NONE:
            return False
        if func != 0x03 or reg != self.REG_SYSTEM_BASE:
            return False
        if len(self._buffer) < 6:
            return False
        return bytes(self._buffer[:3]) == bytes(self._buffer[3:6])

    @classmethod
    def _guess_base_length(cls, func: int, reg: int) -> int:
        if func == 0x11:
            return 6
        if reg in (cls.REG_MOTOR_STATE, cls.REG_MOTOR_TARGET):
            return 7
        if reg == cls.REG_SYSTEM_BASE:
            # system param block: 3 header + 10 x uint16 (20 bytes)
            return 23
        return 5

    def _extract_log_line(self, require_bracket: bool) -> Tuple[int, Optional[str]]:
        if require_bracket and (not self._buffer or self._buffer[0] != ord("[")):
            return 0, None

        newline_index = -1
        for idx, value in enumerate(self._buffer):
            if value in (0x0A, 0x0D):
                newline_index = idx
                break

        if newline_index < 0:
            if len(self._buffer) >= 128 and self._looks_printable(self._buffer[:64]):
                chunk = bytes(self._buffer[:64])
                text = chunk.decode("utf-8", errors="ignore").strip()
                return 64, text or None
            return 0, None

        chunk = bytes(self._buffer[:newline_index + 1])
        text = chunk.decode("utf-8", errors="ignore").strip()
        return newline_index + 1, text or None

    @staticmethod
    def _looks_printable(data: bytes) -> bool:
        return all((32 <= value <= 126) or value in (9, 10, 13) for value in data)

    @classmethod
    def parse_graph_hex(cls, text: str) -> Optional[bytes]:
        if not text:
            return None
        matches = cls._HEX_PATTERN.findall(text)
        if not matches:
            return None
        try:
            return bytes.fromhex(matches[-1])
        except ValueError:
            return None

    @classmethod
    def validate_graph_blob(cls, graph_bytes: bytes) -> Tuple[bool, str]:
        if not graph_bytes:
            return False, "图结构为空"
        if len(graph_bytes) < 11:
            return False, "图结构长度过短"
        if graph_bytes[:3] != cls.GRAPH_MAGIC:
            return False, "图结构魔术字错误"

        frame_length = int.from_bytes(graph_bytes[3:7], byteorder="big", signed=False)
        if frame_length != len(graph_bytes) - 1:
            return False, f"长度字段不一致: header={frame_length}, actual={len(graph_bytes)}"
        if frame_length > cls.MAX_GRAPH_FRAME_SIZE:
            return False, f"图结构超长: {frame_length} > {cls.MAX_GRAPH_FRAME_SIZE}"

        recv_crc = int.from_bytes(graph_bytes[-4:], byteorder="little", signed=False)
        calc_crc = cls.crc32_host(graph_bytes[:-4])
        if recv_crc != calc_crc:
            return False, f"CRC32错误: recv=0x{recv_crc:08X}, calc=0x{calc_crc:08X}"

        return True, "OK"
