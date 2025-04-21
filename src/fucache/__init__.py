"""Simple cache system.

This module provides simple cache system.

Cache is given an expiration header.

Header structure:
order: big-endian
[version: 1byte][created_at: 8byte][expiration_at: 8byte][data-length: 4byte]

Data structure:
[header][data]
"""

import hashlib
import io
import os
import shutil
import struct
import time
from pathlib import Path
from typing import Self

from fucache import exceptions


class FuCache:
    """Provides a cache system class.

    Calling classmethod without instance.

    Run `FuCache.init("YOUR_APP_NAME")` at the begin your code.
    For detail `init()`, check comment of `init()`

    """

    CACHE_DIR: Path = Path.home() / ".cache"
    APP_CACHE_DIR: str = "fucache"
    USE_HASH_FILENAME: bool = True
    EXPIRATION_SEC: int = 0

    @classmethod
    def init(cls, name: str, use_hash_filename: bool = True, expiration_sec: int = 0, cache_dir: Path | str = None):
        """Initialize cache config.

        If not call this method, will be used default config.
        Default config:
        - cache_directory : `~/.cache/fucache`
        - hash filename   : plain text (e.g. `file.txt` -> `~/.cache/fucache/file.txt`)
        - expriration_sec : 0

        Args:
            name (str): Appname. Use CacheDirectory Name.
            use_hash_filename (bool, optional): Use md5 hash to filename.
            expiration_sec (int, optional): Cache lifetime. if set 0, no auto delete.
            cache_dir(Path | str, optional): Change location of Parent Cache Directory. Not recommended to change.

        Raises:
            ValueError: empty name specified.
        """
        if not name:
            raise ValueError("Cache name cannot be empty")

        cls.APP_CACHE_DIR = name
        cls.USE_HASH_FILENAME = use_hash_filename
        cls.EXPIRATION_SEC = expiration_sec

        if cache_dir:
            cls.CACHE_DIR = Path(cache_dir)

    @classmethod
    def get_app_cache_dir(cls) -> Path:
        """Get app cache directory.

        If not exists, create directory.

        Returns:
            Path: app cache directory.
        """
        p = cls.CACHE_DIR / cls.APP_CACHE_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def create_cache_filename(cls, filename: str) -> str:
        """Create cache filename.

        If `USE_HASH_FILENAME` is set, return md5hashed name.
        If it is not set return unchanged name.

        Args:
            name (str): filename.

        Raises:
            exceptions.CacheError: Hash calculation failed.

        Returns:
            str: filename
        """

        if not cls.USE_HASH_FILENAME:
            return filename
        try:
            return hashlib.md5(filename.encode()).hexdigest()
        except Exception as e:
            raise exceptions.CacheError(f"failed to create hash {filename}") from e

    @classmethod
    def load_cache(cls, filename: str) -> bytes | None:
        """Load cahce from app cache dir.


        Args:
            name (str): filename.

        Raises:
            exceptions.CacheLoadError: Cache Load failed.

        Returns:
            bytes | None: Cache data bytes. None if Expired or not exists.
        """
        cache_name = cls.create_cache_filename(filename)

        p = cls.get_app_cache_dir() / cache_name

        if not p.exists():
            return None

        try:
            head, body = CacheHeader.parse_from_file(p)
            if head.is_expired():
                os.remove(p)
                return None
            return body
        except exceptions.CacheVersionError:
            os.remove(p)
            return None
        except Exception as e:
            raise exceptions.CacheLoadError(filename) from e

    @classmethod
    def save_cache(cls, filename: str, data: bytes):
        """Save cache for app cache dir.

        Args:
            name (str): filename.
            data (bytes): bytes to save.

        Raises:
            exceptions.CacheSaveError: Save failed.
        """
        cache_name = cls.create_cache_filename(filename)

        p = cls.get_app_cache_dir() / cache_name

        try:
            content = CacheHeader.add_header(data, cls.EXPIRATION_SEC)
            p.write_bytes(content)
        except Exception as e:
            raise exceptions.CacheSaveError(filename) from e

    @classmethod
    def clean_all(cls):
        """Clean All cachefiles."""
        p = cls.get_app_cache_dir()
        shutil.rmtree(p, ignore_errors=True)
        p.rmdir()

    @classmethod
    def clean_expired(cls):
        """Clean Expired cachefiles"""
        p = cls.get_app_cache_dir()
        for path in p.iterdir():
            try:
                header, _ = CacheHeader.parse_from_file(path)
                if header.is_expired():
                    os.remove(path)
                continue
            except exceptions.CacheError:
                pass

            try:
                os.remove(path)
            except Exception as e:
                print(e)


_HEADER_VERSION = 1
_HEADER_FORMAT = ">BQQI"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)


class CacheHeader:
    """This class provides expiration hader

    Header structure:
    order: big-endian
    [version: 1byte][created_at: 8byte][expiration_at: 8byte][data-length: 4byte]
    """

    def __init__(self, version: int, created_at: int, expiration_at: int, data_length: int):
        self.version = version
        self.created_at = created_at
        self.expiration_at = expiration_at
        self.data_length = data_length

    def is_expired(self) -> bool:
        """Get if header expired.

        Returns:
            bool: True if expired.
        """
        if self.expiration_at == 0:
            return False
        return int(time.time()) > self.expiration_at

    @staticmethod
    def add_header(data: bytes, expiration_sec: int = 0) -> bytes:
        """Add Header.

        Args:
            data (bytes): Original Data.
            expiration_sec (int, optional): expiration second. default 0(infinity).

        Returns:
            bytes: data with header added.
        """
        created_at = int(time.time())
        if expiration_sec:
            expiration_at = created_at + expiration_sec
        else:
            expiration_at = 0

        header = struct.pack(_HEADER_FORMAT, _HEADER_VERSION, created_at, expiration_at, len(data))
        return header + data

    @classmethod
    def parse_from_bytes(cls, data: bytes) -> tuple[Self, bytes]:
        """Split header and body.

        Args:
            data (bytes): data to be analyzed.

        Raises:
            exceptions.CacheHeaderError: DataSize < HeaderSize.
            exceptions.CacheVersionError: Cache version is different.
            exceptions.CacheSizeError: The cache size is wrong or corrupted.

        Returns:
            tuple[Self, bytes]: tuple of header and original data.
        """
        if len(data) < _HEADER_SIZE:
            raise exceptions.CacheHeaderError()

        with io.BytesIO(data) as bf:
            head_byte = bf.read(_HEADER_SIZE)
            header = cls(*struct.unpack(_HEADER_FORMAT, head_byte))
            if header.version != _HEADER_VERSION:
                raise exceptions.CacheVersionError(header.version, _HEADER_VERSION)

            body = bf.read(header.data_length)
            if len(body) < header.data_length:
                raise exceptions.CacheSizeError(header.data_length, len(body))

            return header, body

    @classmethod
    def parse_from_file(cls, filename: Path | str) -> tuple[Self, bytes]:
        """Split header and body from file.

        Args:
            file_name (Path | str): cache filename.

        Raises:
            exceptions.CacheHeaderError: DataSize < HeaderSize.
            exceptions.CacheVersionError: Cache version is different.
            exceptions.CacheSizeError: The cache size is wrong or corrupted.

        Returns:
            tuple[Self, bytes]: tuple of header and original data.
        """
        with open(filename, "rb") as f:
            return cls.parse_from_bytes(f.read())

    def __repr__(self) -> str:
        return f"CacheHeader(version={self.version}, created_at={self.created_at}, expiration_at={self.expiration_at}, data_length={self.data_length})"
