# parselab

This package contains classes that help to write parsers in Python.

## Usage

To use `parelab` just create a class derived from `BasicParser`.

```python
from parselab.cache import FileCache
from parselab.network import NetworkManager
from parselab.parsing import BasicParser

class MyParser(BasicParser):

    def __init__(self):
        self.cache = FileCache(namespace='my-parser', path=os.environ.get('CACHE_PATH'))
        self.net = NetworkManager()
        db.connect(os.environ['PARSINGDB'])
        db.setup_project('my-project')
```

After that you will be able to download pages using `BasicParser.get_page()` method:

```python
class MyParser(BasicParser):
    ...

    def run(self):
        page = self.get_page('https://google.com')
```

`BasicParser` will use network manager specified in `__init__` method and will save all
downloaded pages into directory specified by your `$CACHE_PATH` environment variable.
Next time you invoke `get_page()` method it will get the requested page from cache
if available.