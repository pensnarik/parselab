import os

from setuptools import setup, Command
from setuptools.command.install import install
from distutils.util import convert_path

with open("README.md", "r") as fh:
    long_description = fh.read()

def get_version():
    d = {}
    with open('parselab/__init__.py') as fp:
        exec(fp.read(), d)

    return d["__version__"]

setup(name="parselab",
      description="Parselab helper module",
      long_description=long_description,
      long_description_content_type="text/markdown",
      license="BSD3",
      version=get_version(),
      maintainer="Andrei Zhidenkov",
      maintainer_email="pensnarik@gmail.com",
      url="http://parselab.ru",
      packages=['parselab'],
      install_requires=["psycopg2", "requests", "requests[socks]"]
)
