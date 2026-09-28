from __future__ import annotations

import enum
import os
import stat


class PathType(str, enum.Enum):
    """The kind of thing a path resolves to.

    Inherits from ``str`` so the value is directly comparable and serialisable
    without callers having to reach for ``.value`` everywhere. The string form
    is the canonical, human-readable label for the type.
    """

    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    BROKEN_SYMLINK = "broken_symlink"
    SOCKET = "socket"
    FIFO = "fifo"
    DEVICE = "device"
    MISSING = "missing"


def classify(path: str | os.PathLike[str]) -> PathType:
    """Classify *path* without raising on missing entries.

    The classification is based on ``os.lstat`` so that a symlink is reported
    as a symlink (or a broken symlink) rather than being transparently
    followed to its target. This matters because callers asking "what is at
    this path?" usually want to know about the path itself, not whatever it
    happens to point at — following links would hide broken symlinks and
    conflate link and target.

    Returns :data:`PathType.MISSING` when nothing exists at *path* (including
    when a parent directory is absent). Any other ``OSError`` from ``lstat``
    — for example ``EACCES`` — is also mapped to ``MISSING``. The contract of
    this function is "tell me what is there, or say missing"; surfacing
    permission errors as a distinct category would be a different, narrower
    library.
    """
    try:
        st = os.lstat(os.fspath(path))
    except OSError:
        return PathType.MISSING

    mode = st.st_mode

    if stat.S_ISLNK(mode):
        # lstat never follows the final component, so a symlink reaching here
        # may or may not resolve. Distinguish the two cases explicitly: a
        # broken symlink is operationally very different from a working one.
        try:
            os.stat(os.fspath(path))
        except OSError:
            return PathType.BROKEN_SYMLINK
        return PathType.SYMLINK

    if stat.S_ISDIR(mode):
        return PathType.DIRECTORY
    if stat.S_ISREG(mode):
        return PathType.FILE
    if stat.S_ISSOCK(mode):
        return PathType.SOCKET
    if stat.S_ISFIFO(mode):
        return PathType.FIFO
    if stat.S_ISCHR(mode) or stat.S_ISBLK(mode):
        return PathType.DEVICE

    # Anything else (e.g. a door on Solaris) is reported as a regular file.
    # Pretending to know about every niche ``S_IFMT`` value would be worse
    # than a honest fallback; callers who care can call ``os.lstat`` directly.
    return PathType.FILE
