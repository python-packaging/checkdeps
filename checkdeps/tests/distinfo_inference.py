import tempfile
import unittest
from pathlib import Path

from ..distinfo_inference import analyze, iterparents


class DistinfoInferenceTest(unittest.TestCase):
    def test_iterparents(self) -> None:
        self.assertEqual(["bad.wolf", "bad"], list(iterparents("bad.wolf.foo")))

    def test_analyze_basic(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d)
            (pd / "RECORD").write_text(
                """\
foo/bar.py,
foo/__init__.py,
../x.py,
"""
            )
            dist = analyze(pd)
            self.assertEqual({"foo", "foo.bar"}, dist.provided_names)
            self.assertEqual(set(), dist.namespace_names)
            self.assertEqual({"foo"}, dist.minimal_names)

    def test_analyze_new_namespace_packages(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d)
            (pd / "RECORD").write_text(
                """\
foo/bar/baz.py,
foo/__init__.py,
"""
            )
            dist = analyze(pd)
            self.assertEqual({"foo", "foo.bar.baz"}, dist.provided_names)
            self.assertEqual({"foo.bar"}, dist.namespace_names)
            # TODO: not sure I'm 100% confident in this; it needs a docstring to
            # better define what "minimal names" means when there's a
            # non-toplevel namespace.
            self.assertEqual({"foo.bar.baz"}, dist.minimal_names)

    def test_analyze_setuptools_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d)
            (pd / "RECORD").write_text(
                """\
foo/bar/baz.py,
foo/bar/__init__.py,
foo/__init__.py,
"""
            )
            (pd / "namespace_packages.txt").write_text(
                """\
foo
foo.bar



"""
            )  # some extra newlines on purpose
            dist = analyze(pd)
            self.assertEqual({"foo.bar.baz"}, dist.provided_names)
            self.assertEqual({"foo", "foo.bar"}, dist.namespace_names)
            self.assertEqual({"foo.bar.baz"}, dist.minimal_names)
