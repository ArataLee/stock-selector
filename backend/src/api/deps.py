from functools import lru_cache


@lru_cache
def _cached_bootstrap():
    from src.bootstrap import bootstrap
    return bootstrap()


def _clear_bootstrap_cache():
    _cached_bootstrap.cache_clear()
