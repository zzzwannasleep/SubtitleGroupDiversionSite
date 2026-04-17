from __future__ import annotations

from dataclasses import dataclass

from torf import BdecodeError, MetainfoError, ReadError, Torrent, TorfError

from apps.common.exceptions import BusinessException


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


def _read_torrent(data: bytes) -> Torrent:
    try:
        return Torrent.read_stream(data, validate=False)
    except (BdecodeError, MetainfoError, ReadError, TorfError, TypeError, ValueError) as exc:
        raise BusinessException("无效的 torrent 文件。") from exc


def _build_metadata(torrent: Torrent) -> TorrentMetadata:
    info = torrent.metainfo.get("info")
    if not isinstance(info, dict):
        raise BusinessException("torrent 缺少 info 字段。")

    name = str(info.get("name") or "download")
    files: list[TorrentFileEntry] = []
    total_size = 0

    if "files" in info:
        for file_info in info["files"]:
            if not isinstance(file_info, dict):
                continue
            parts = [str(part) for part in file_info.get("path", [])]
            size = int(file_info.get("length", 0) or 0)
            files.append(TorrentFileEntry(path="/".join(parts), size_bytes=size))
            total_size += size
    else:
        size = int(info.get("length", 0) or 0)
        files.append(TorrentFileEntry(path=name, size_bytes=size))
        total_size += size

    return TorrentMetadata(
        infohash=torrent.infohash,
        files=files,
        size_bytes=total_size,
        is_private=bool(torrent.private),
        name=name,
    )


def parse_torrent(data: bytes) -> TorrentMetadata:
    return _build_metadata(_read_torrent(data))
