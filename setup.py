from setuptools import setup
import os


def get_version():
    base_dir = os.path.dirname(__file__)
    version_path = os.path.join(base_dir, "pyproxy", "__init__.py")
    version_ns = {}
    with open(version_path, "r") as f:
        exec(f.read(), version_ns)
    return version_ns["__version__"]


setup(version=get_version())
