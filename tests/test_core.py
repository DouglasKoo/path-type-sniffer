import os
import socket
import stat
import tempfile
import unittest

from path_type_sniffer import PathType, classify


class ClassifyTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.root = self._dir.name

    def _p(self, name: str) -> str:
        return os.path.join(self.root, name)

    def test_missing_path(self):
        self.assertEqual(classify(self._p("nope")), PathType.MISSING)

    def test_missing_parent(self):
        # A path whose parent does not exist must also be MISSING, not raise.
        self.assertEqual(
            classify(os.path.join(self.root, "sub", "deep", "file")),
            PathType.MISSING,
        )

    def test_regular_file(self):
        p = self._p("f.txt")
        with open(p, "w") as fh:
            fh.write("x")
        self.assertEqual(classify(p), PathType.FILE)

    def test_empty_regular_file(self):
        p = self._p("empty")
        open(p, "w").close()
        self.assertEqual(classify(p), PathType.FILE)

    def test_directory(self):
        p = self._p("sub")
        os.mkdir(p)
        self.assertEqual(classify(p), PathType.DIRECTORY)

    def test_symlink_to_file(self):
        target = self._p("target")
        open(target, "w").close()
        link = self._p("link")
        os.symlink(target, link)
        self.assertEqual(classify(link), PathType.SYMLINK)

    def test_symlink_to_directory(self):
        target = self._p("dir")
        os.mkdir(target)
        link = self._p("link")
        os.symlink(target, link)
        self.assertEqual(classify(link), PathType.SYMLINK)

    def test_broken_symlink(self):
        link = self._p("dangling")
        os.symlink(self._p("does_not_exist"), link)
        self.assertEqual(classify(link), PathType.BROKEN_SYMLINK)

    def test_fifo(self):
        p = self._p("pipe")
        os.mkfifo(p)
        self.assertEqual(classify(p), PathType.FIFO)

    def test_unix_socket(self):
        p = self._p("sock")
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(s.close)
        s.bind(p)
        self.assertEqual(classify(p), PathType.SOCKET)

    def test_accepts_pathlike(self):
        p = self._p("f")
        open(p, "w").close()
        self.assertEqual(classify(os.path.join(self.root, "f")), PathType.FILE)

    def test_pathtype_is_str(self):
        # The enum subclasses str so the value is usable directly as a string.
        self.assertEqual(PathType.FILE, "file")
        self.assertEqual(PathType.MISSING.value, "missing")

    def test_unreadable_parent_directory_is_missing(self):
        # When lstat cannot even be attempted due to permissions on a parent,
        # OSError is raised and we report MISSING rather than crashing.
        inner = self._p("inner")
        os.mkdir(inner)
        os.chmod(inner, 0o000)
        try:
            self.assertEqual(
                classify(os.path.join(inner, "anything")),
                PathType.MISSING,
            )
        finally:
            os.chmod(inner, 0o700)


if __name__ == "__main__":
    unittest.main()
