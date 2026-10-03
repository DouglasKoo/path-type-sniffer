# Path Type Sniffer

Classifies a path as `file`, `directory`, `symlink`, `broken_symlink`, `socket`, `fifo`, `device`, or `missing` without raising on absent entries.

```python
from path_type_sniffer import classify, PathType

kind = classify("/some/path")
if kind is PathType.BROKEN_SYMLINK:
    print("points nowhere")
elif kind is PathType.MISSING:
    print("nothing there")
```

`classify(path)` returns a `PathType` member (a `str` enum, so `kind == "file"` works). It uses `os.lstat`, so a symlink is reported on its own merits — as `symlink` if its target exists, or `broken_symlink` if it does not — rather than being silently followed.

The library exists because the obvious approach (`os.path.isfile` / `isdir` / `islink`) needs several calls and still leaves broken symlinks and special files (sockets, fifos, devices) in an ambiguous bucket. One `lstat` plus one `stat` (only for symlinks) gives a complete answer in a single call.

The edge to know about: any `OSError` from `lstat` — including `EACCES` on a parent directory — is reported as `MISSING`. If you need to distinguish "does not exist" from "permission denied", call `os.lstat` yourself. The trade-off here is a simpler, never-raising API at the cost of that distinction.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

