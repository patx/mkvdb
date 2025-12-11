**[mkvDB](https://github.com/patx/mkvdb)** is a fast, easy to use, Python key-value store with first-class
asynchronous support. It stands on the shoulders of [motor](https://motor.readthedocs.io/)
and is safe across multiple processes and workers thanks to MongoDB’s concurrency model.

Is it a little pointless if you already know Mongo? Yeah. But if ya just want to
`set` and `get` without thinking about collections or schemas, it’s perfect. I made this
because [pickleDB](https://patx.github.io/pickledb) doesn't play nice with ASGI but I
like its dumb API anyway :) There's no docs yet, so just look at the source code - 
its really short I promise.

```python
from mkvdb import Mkv

db = Mkv("mongodb://localhost:27017")

db.set("key", "value")
db.get("key")  # returns "value"
```

Note: You can also `await db.set` or `db.whatever` for async usage. 
