class CacheError(Exception): ...


class CacheLoadError(CacheError):
    def __init__(self, name: str):
        super().__init__(f"failed to load cache for '{name}'")
        self.name = name


class CacheSaveError(CacheError):
    def __init__(self, name: str):
        super().__init__(f"failed to save cache for '{name}'")
        self.name = name
