import os


def get_env_var(name: str) -> str:
    """Get an environment variable."""
    value = os.environ.get(name)
    if value is None:
        raise ValueError(f"Environment variable {name} is not set")
    return value
