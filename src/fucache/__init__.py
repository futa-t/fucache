import hashlib
from pathlib import Path

from fucache import exceptions


class FuCache:
    CACHE_DIR: Path = Path.home() / ".cache"
    APP_CACHE_DIR: str = "fucache"
    USE_HASH_FILENAME: bool = True

    @classmethod
    def init(cls, name: str, use_hash_filename: bool = True):
        if not name:
            raise ValueError("Cache name cannot be empty")

        cls.APP_CACHE_DIR = name
        cls.USE_HASH_FILENAME = use_hash_filename

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
            with p.open("wb") as f:
                f.write(data)
        except Exception as e:
            raise exceptions.CacheSaveError(name) from e
