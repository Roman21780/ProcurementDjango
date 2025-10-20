from django.core.cache import cache
from cacheops import invalidate_model, invalidate_obj


def clear_all_cache():
    """Очистить весь кэш"""
    cache.clear()
    return {'status': 'success', 'message': 'All cache cleared'}


def clear_model_cache(model_class):
    """
    Очистить кэш для конкретной модели.

    Args:
        model_class: класс модели Django (например, Product)
    """
    invalidate_model(model_class)
    return {'status': 'success', 'message': f'Cache cleared for {model_class.__name__}'}


def clear_object_cache(obj):
    """
    Очистить кэш для конкретного объекта.

    Args:
        obj: экземпляр модели Django
    """
    invalidate_obj(obj)
    return {'status': 'success', 'message': f'Cache cleared for {obj}'}


def get_cache_stats():
    """Получить статистику кэша"""
    try:
        from cacheops import cache_getting, cache_setting

        total_hits = cache_getting.stats.get('hit', 0)
        total_misses = cache_getting.stats.get('miss', 0)
        total = total_hits + total_misses

        return {
            'cache_hits': total_hits,
            'cache_misses': total_misses,
            'total_requests': total,
            'hit_rate': total_hits / total if total > 0 else 0,
        }
    except Exception as e:
        return {'error': str(e)}
