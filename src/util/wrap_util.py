import functools
import logging
import time

logger = logging.getLogger(__name__)

# 记录每个函数的调用数据
_func_stats = {}


def timeit(_func=None, *, ignore: int = 0):
    """耗时计时器，分别计算每个函数的平均耗时（跳过前 ignore 次调用）"""

    def decorator_timeit(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 初始化当前函数的计时数据
            if func not in _func_stats:
                _func_stats[func] = {"count": 0, "total_time": 0.0}

            stats = _func_stats[func]
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()

            elapsed_time = end_time - start_time
            stats["count"] += 1

            # 从第 ignore+1 次调用开始计算平均耗时
            if stats["count"] > ignore:
                stats["total_time"] += elapsed_time
                avg_time = stats["total_time"] / (stats["count"] - ignore)
                logger.debug(
                    f"{func.__name__} 耗时: {elapsed_time:.6f} 秒, 第 {stats['count']} 次调用平均耗时: {avg_time:.6f} 秒")
            else:
                logger.debug(f"{func.__name__} 耗时: {elapsed_time:.6f} 秒 (第{stats['count']}次不计入平均值)")
            return result

        return wrapper

    # 支持装饰器直接使用 @timeit 或者带参数使用 @timeit(ignore=2)
    if _func is None:
        return decorator_timeit
    else:
        return decorator_timeit(_func)
