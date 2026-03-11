from __future__ import annotations

import hashlib
from dataclasses import dataclass


class TorrentParseError(ValueError):
    """Raised when torrent metadata is invalid or unsupported."""


@dataclass(slots=True)
class ParsedTorrentFile:
    file_path: str
    file_size_bytes: int


@dataclass(slots=True)
class ParsedTorrent:
    info_hash: str
    torrent_name: str
    size_bytes: int
    files: list[ParsedTorrentFile]
    piece_length: int | None = None


class _BencodeParser:
    def __init__(self, data: bytes):
        self.data = data
        self.info_slice: bytes | None = None

    def parse_root(self) -> dict[bytes, object]:
        value, next_index = self._parse_root_dict(0)
        if next_index != len(self.data):
            raise TorrentParseError("Unexpected trailing data in torrent file")
        return value

    def _parse_root_dict(self, index: int) -> tuple[dict[bytes, object], int]:
        if self.data[index:index + 1] != b"d":
            raise TorrentParseError("Torrent root must be a bencoded dictionary")
        index += 1
        result: dict[bytes, object] = {}

        while True:
            self._ensure_in_bounds(index)
            if self.data[index:index + 1] == b"e":
                break
            key, index = self._parse_bytes(index)
            if key == b"info":
                info_start = index
                value, index = self._parse_value(index)
                self.info_slice = self.data[info_start:index]
            else:
                value, index = self._parse_value(index)
            result[key] = value

        return result, index + 1

    def _parse_value(self, index: int) -> tuple[object, int]:
        token = self.data[index:index + 1]
        if token == b"i":
            return self._parse_int(index)
        if token == b"l":
            return self._parse_list(index)
        if token == b"d":
            return self._parse_dict(index)
        if token.isdigit():
            return self._parse_bytes(index)
        raise TorrentParseError("Invalid bencode token")

    def _parse_int(self, index: int) -> tuple[int, int]:
        end = self.data.find(b"e", index)
        if end == -1:
            raise TorrentParseError("Invalid integer encoding")
        try:
            value = int(self.data[index + 1:end].decode("ascii"))
        except ValueError as exc:
            raise TorrentParseError("Invalid integer value") from exc
        return value, end + 1

    def _parse_list(self, index: int) -> tuple[list[object], int]:
        index += 1
        values: list[object] = []
        while True:
            self._ensure_in_bounds(index)
            if self.data[index:index + 1] == b"e":
                break
            value, index = self._parse_value(index)
            values.append(value)
        return values, index + 1

    def _parse_dict(self, index: int) -> tuple[dict[bytes, object], int]:
        index += 1
        values: dict[bytes, object] = {}
        while True:
            self._ensure_in_bounds(index)
            if self.data[index:index + 1] == b"e":
                break
            key, index = self._parse_bytes(index)
            value, index = self._parse_value(index)
            values[key] = value
        return values, index + 1

    def _parse_bytes(self, index: int) -> tuple[bytes, int]:
        colon_index = self.data.find(b":", index)
        if colon_index == -1:
            raise TorrentParseError("Invalid byte string encoding")
        try:
            length = int(self.data[index:colon_index].decode("ascii"))
        except ValueError as exc:
            raise TorrentParseError("Invalid byte string length") from exc
        start = colon_index + 1
        end = start + length
        if end > len(self.data):
            raise TorrentParseError("Byte string exceeds file length")
        return self.data[start:end], end

    def _ensure_in_bounds(self, index: int) -> None:
        if index >= len(self.data):
            raise TorrentParseError("Unexpected end of torrent file")


def _decode_text(value: object) -> str:
    if not isinstance(value, bytes):
        raise TorrentParseError("Expected byte string value in torrent metadata")
    return value.decode("utf-8", errors="replace")


def _get_text(mapping: dict[bytes, object], preferred_key: bytes, fallback_key: bytes | None = None) -> str:
    if preferred_key in mapping:
        return _decode_text(mapping[preferred_key])
    if fallback_key is not None and fallback_key in mapping:
        return _decode_text(mapping[fallback_key])
    raise TorrentParseError(f"Missing required key: {preferred_key!r}")


def _get_int(mapping: dict[bytes, object], key: bytes) -> int:
    value = mapping.get(key)
    if not isinstance(value, int):
        raise TorrentParseError(f"Expected integer value for key: {key!r}")
    return value


def _parse_file_list(info_dict: dict[bytes, object]) -> list[ParsedTorrentFile]:
    files_value = info_dict.get(b"files")
    if isinstance(files_value, list):
        files: list[ParsedTorrentFile] = []
        for item in files_value:
            if not isinstance(item, dict):
                raise TorrentParseError("Invalid file entry in torrent metadata")
            length = _get_int(item, b"length")
            path_value = item.get(b"path.utf-8", item.get(b"path"))
            if not isinstance(path_value, list) or not path_value:
                raise TorrentParseError("Invalid file path in torrent metadata")
            segments = [_decode_text(segment) for segment in path_value]
            files.append(ParsedTorrentFile(file_path="/".join(segments), file_size_bytes=length))
        return files

    file_name = _get_text(info_dict, b"name.utf-8", b"name")
    return [ParsedTorrentFile(file_path=file_name, file_size_bytes=_get_int(info_dict, b"length"))]


def parse_torrent_bytes(data: bytes) -> ParsedTorrent:
    if not data:
        raise TorrentParseError("Torrent file is empty")

    parser = _BencodeParser(data)
    root = parser.parse_root()
    info_dict = root.get(b"info")

    if not isinstance(info_dict, dict):
        raise TorrentParseError("Torrent file does not contain a valid info dictionary")
    if parser.info_slice is None:
        raise TorrentParseError("Unable to extract raw info dictionary bytes")

    files = _parse_file_list(info_dict)
    torrent_name = _get_text(info_dict, b"name.utf-8", b"name")
    size_bytes = sum(item.file_size_bytes for item in files)
    piece_length = info_dict.get(b"piece length")
    if piece_length is not None and not isinstance(piece_length, int):
        raise TorrentParseError("Invalid piece length in torrent metadata")

    return ParsedTorrent(
        info_hash=hashlib.sha1(parser.info_slice).hexdigest(),
        torrent_name=torrent_name,
        size_bytes=size_bytes,
        files=files,
        piece_length=piece_length if isinstance(piece_length, int) else None,
    )


def decode_torrent_document(data: bytes) -> dict[bytes, object]:
    parser = _BencodeParser(data)
    return parser.parse_root()


def bencode_encode(value: object) -> bytes:
    if isinstance(value, int):
        return b"i" + str(value).encode("ascii") + b"e"
    if isinstance(value, bytes):
        return str(len(value)).encode("ascii") + b":" + value
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return str(len(encoded)).encode("ascii") + b":" + encoded
    if isinstance(value, list):
        return b"l" + b"".join(bencode_encode(item) for item in value) + b"e"
    if isinstance(value, dict):
        chunks: list[bytes] = [b"d"]
        for key, item in value.items():
            if not isinstance(key, bytes):
                raise TorrentParseError("Bencode dictionary keys must be bytes")
            chunks.append(bencode_encode(key))
            chunks.append(bencode_encode(item))
        chunks.append(b"e")
        return b"".join(chunks)
    raise TorrentParseError(f"Unsupported value type for bencode encoding: {type(value)!r}")
