import functools

def logged(func):
    @functools.wraps(func)     # ← この行をコメントアウトして実行
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@logged
def add(a: int, b: int) -> int:
    """2つの数を足す"""
    return a + b

print(add.__name__)   # あり: add / なし: wrapper
print(add.__doc__)    # あり: 2つの数を足す / なし: None