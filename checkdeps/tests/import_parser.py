import tempfile
import unittest
from pathlib import Path

from ..import_parser import get_imports


class ImportParserTest(unittest.TestCase):
    def test_imports(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d)
            (pd / "foo.py").write_text(
                """\
import a
import a.b
from a.b.c import z
from . import x  # relative imports are not parsed
from .x import y

def func():
    import d
"""
            )
            self.assertEqual({"a", "a.b", "a.b.c.z", "d"}, get_imports(pd / "foo.py"))
