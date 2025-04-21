class CacheError(Exception): ...


class CacheLoadError(CacheError):
    def __init__(self, name: str):
        super().__init__(f"failed to load cache for '{name}'")
        self.name = name


class CacheSaveError(CacheError):
    def __init__(self, name: str):
        super().__init__(f"failed to save cache for '{name}'")
        self.name = name


class CacheVersionError(CacheError):
    def __init__(self, cache_version: int, current_version: int):
        super().__init__(
            f"unsupported cache version: cache version is {cache_version}, current version is {current_version}"
        )


class CacheSizeError(CacheError):
    def __init__(self, expected_length: int, actual_length: int):
        super().__init__(f"expected {expected_length} bytes, but {actual_length} is given")


class CacheHeaderError(CacheError):
    def __init__(self):
        super().__init__("cache header is invalid")
