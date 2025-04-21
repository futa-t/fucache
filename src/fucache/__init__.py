import hashlib
import io
import struct
import time
from pathlib import Path
from typing import Self

from fucache import exceptions


class FuCache:
    CACHE_DIR: Path = Path.home() / ".cache"
    APP_CACHE_DIR: str = "fucache"
    USE_HASH_FILENAME: bool = True
    EXPIRATION_SEC: int = 0

    @classmethod
    def init(cls, name: str, use_hash_filename: bool = True, expired_sec: int = 0):
        if not name:
            raise ValueError("Cache name cannot be empty")

        cls.APP_CACHE_DIR = name
        cls.USE_HASH_FILENAME = use_hash_filename
        cls.EXPIRATION_SEC = expired_sec

    @classmethod
    def get_app_cache_dir(cls) -> Path:
        p = cls.CACHE_DIR / cls.APP_CACHE_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def create_cache_filename(cls, name: str) -> str:
        if not cls.USE_HASH_FILENAME:
            return name
        try:
            return hashlib.md5(name.encode()).hexdigest()
        except Exception as e:
            raise exceptions.CacheError(f"failed to create hash {name}") from e

    @classmethod
    def load_cache(cls, name: str) -> bytes | None:
        cache_name = cls.create_cache_filename(name)

        p = cls.get_app_cache_dir() / cache_name

        if not p.exists():
            return None

        try:
            with p.open("rb") as f:
                return f.read()
        except Exception as e:
            raise exceptions.CacheLoadError(name) from e

    @classmethod
    def save_cache(cls, name: str, data: bytes):
        cache_name = cls.create_cache_filename(name)

        p = cls.get_app_cache_dir() / cache_name

        try:
            content = CacheHeader.add_header(data, cls.EXPIRATION_SEC)
            with p.open("wb") as f:
                f.write(content)
        except Exception as e:
            raise exceptions.CacheSaveError(name) from e


_HEADER_VERSION = 1
_HEADER_FORMAT = ">BQQI"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)


class CacheHeader:
    def __init__(self, version: int, created_at: int, expiration_at: int, data_length: int):
        self.version = version
        self.created_at = created_at
        self.expiration_at = expiration_at
        self.data_length = data_length

    def is_expired(self) -> bool:
        if self.expiration_at == 0:
            return False
        return int(time.time()) > self.expiration_at

    @staticmethod
    def add_header(data: bytes, expiration_sec: int = 0) -> bytes:
        created_at = int(time.time())
        if expiration_sec:
            expiration_at = created_at + expiration_sec
        else:
            expiration_at = 0

        header = struct.pack(_HEADER_FORMAT, _HEADER_VERSION, created_at, expiration_at, len(data))
        return header + data

    @classmethod
    def parse(cls, data: bytes) -> tuple[Self, bytes]:
        with io.BytesIO(data) as bf:
            head_byte = bf.read(_HEADER_SIZE)
            header = cls(*struct.unpack(_HEADER_FORMAT, head_byte))
            if header.version != _HEADER_VERSION:
                raise exceptions.CacheVersionError(header.version, _HEADER_VERSION)

            body = bf.read(header.data_length)
            if len(body) < header.data_length:
                raise exceptions.CacheSizeError(header.data_length, len(body))

            return header, body

    def __repr__(self) -> str:
        return f"CacheHeader(version={self.version}, created_at={self.created_at}, expiration_at={self.expiration_at}, data_length={self.data_length})"
