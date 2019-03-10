import os

from setuptools import setup, Command
from setuptools.command.install import install
from distutils.util import convert_path

def get_version():
    d = {}
    with open('parselab/__init__.py') as fp:
        exec(fp.read(), d)

    return d["__version__"]

setup(name="parselab",
      description="Parselab helper module",
      license="Commercial",
      version=get_version(),
      maintainer="Andrei Zhidenkov",
      maintainer_email="pensnarik@gmail.com",
      url="http://parselab.ru",
      packages=['parselab'],
      install_requires=["psycopg2", "requests", "requests[socks]"]
)
