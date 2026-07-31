import os


def get_env(key):
    value = os.environ.get(key)
    if value is None or value == '':
        raise ValueError(f"Missing required environment variable: {key}")
    return value
