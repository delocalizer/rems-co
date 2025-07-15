from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("rems-co")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"
