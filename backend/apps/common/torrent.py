from __future__ import annotations

import hashlib
from dataclasses import dataclass

from apps.common.exceptions import BusinessException


class TorrentDecodeError(ValueError):
    pass


@dataclass(slots=True)
class TorrentFileEntry:
    path: str
    size_bytes: int


@dataclass(slots=True)
class TorrentMetadata:
    infohash: str
    files: list[TorrentFileEntry]
    size_bytes: int
    is_private: bool
    name: str


def _parse(data: bytes, index: int = 0):
    token = data[index:index + 1]
    if token == b"i":
        end = data.index(b"e", index)
        return int(data[index + 1:end]), end + 1
    if token == b"l":
        index += 1
        items = []
        while data[index:index + 1] != b"e":
            item, index = _parse(data, index)
            items.append(item)
        return items, index + 1
    if token == b"d":
        index += 1
        items = {}
        while data[index:index + 1] != b"e":
            key, index = _parse(data, index)
            value, index = _parse(data, index)
            items[key] = value
        return items, index + 1
    if token.isdigit():
        colon = data.index(b":", index)
        length = int(data[index:colon])
        start = colon + 1
        end = start + length
        return data[start:end], end
    raise TorrentDecodeError("unsupported bencode token")


def bdecode(data: bytes):
    value, index = _parse(data, 0)
    if index != len(data):
        raise TorrentDecodeError("unexpected trailing data")
    return value


def bencode(value) -> bytes:
    if isinstance(value, int):
        return f"i{value}e".encode()
    if isinstance(value, bytes):
        return str(len(value)).encode() + b":" + value
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return str(len(encoded)).encode() + b":" + encoded
    if isinstance(value, (list, tuple)):
        return b"l" + b"".join(bencode(item) for item in value) + b"e"
    if isinstance(value, dict):
        encoded_items = []
        for key in sorted(value.keys()):
            encoded_items.append(bencode(key))
            encoded_items.append(bencode(value[key]))
        return b"d" + b"".join(encoded_items) + b"e"
    raise TorrentDecodeError(f"unsupported type: {type(value)!r}")


def _decode_text(value: bytes | str) -> str:
    if isinstance(value, str):
        return value
    return value.decode("utf-8", errors="replace")


def parse_torrent(data: bytes) -> TorrentMetadata:
    try:
        payload = bdecode(data)
    except (ValueError, IndexError) as exc:
        raise BusinessException("无效的 torrent 文件。") from exc

    if not isinstance(payload, dict) or b"info" not in payload:
        raise BusinessException("torrent 缺少 info 字段。")

    info = payload[b"info"]
    if not isinstance(info, dict):
        raise BusinessException("torrent info 字段格式非法。")

    infohash = hashlib.sha1(bencode(info)).hexdigest()
    is_private = bool(info.get(b"private", 0) == 1)
    files: list[TorrentFileEntry] = []
    total_size = 0

    if b"files" in info:
        for file_info in info[b"files"]:
            parts = [_decode_text(part) for part in file_info.get(b"path", [])]
            size = int(file_info.get(b"length", 0))
            files.append(TorrentFileEntry(path="/".join(parts), size_bytes=size))
            total_size += size
    else:
        name = _decode_text(info.get(b"name", b"download"))
        size = int(info.get(b"length", 0))
        files.append(TorrentFileEntry(path=name, size_bytes=size))
        total_size += size

    return TorrentMetadata(
        infohash=infohash,
        files=files,
        size_bytes=total_size,
        is_private=is_private,
        name=_decode_text(info.get(b"name", b"download")),
    )


def inject_announce(data: bytes, announce_url: str) -> bytes:
    payload = bdecode(data)
    if not isinstance(payload, dict):
        raise BusinessException("torrent 顶层结构非法。")
    announce_bytes = announce_url.encode("utf-8")
    payload[b"announce"] = announce_bytes
    payload[b"announce-list"] = [[announce_bytes]]
    return bencode(payload)
