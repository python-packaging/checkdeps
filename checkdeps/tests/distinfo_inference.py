import tempfile
import unittest
from pathlib import Path

from ..distinfo_inference import analyze, Dist, DistSet, iterparents, Namespace


class DistinfoInferenceTest(unittest.TestCase):
    def test_iterparents(self) -> None:
        self.assertEqual(["bad.wolf", "bad"], list(iterparents("bad.wolf.foo")))
        self.assertEqual(
            ["bad.wolf.foo", "bad.wolf", "bad"], list(iterparents("bad.wolf.foo."))
        )

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
            dist = analyze(pd, "foo")
            self.assertEqual({"foo", "foo.bar"}, dist.provided_names)
            self.assertEqual(set(), dist.namespace_names)

    def test_analyze_new_namespace_packages(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d)
            (pd / "RECORD").write_text(
                """\
foo/bar/baz.py,
foo/__init__.py,
"""
            )
            dist = analyze(pd, "foo")
            self.assertEqual({"foo", "foo.bar.baz"}, dist.provided_names)
            self.assertEqual({"foo.bar"}, dist.namespace_names)

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
            dist = analyze(pd, "foo")
            self.assertEqual({"foo.bar.baz"}, dist.provided_names)
            self.assertEqual({"foo", "foo.bar"}, dist.namespace_names)

    def test_analyze_egginfo(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d)
            egginfo = pd / "foo.egg-info"
            egginfo.mkdir()
            (egginfo / "installed-files.txt").write_text(
                """\
../google/ads/googleads/__init__.py
../google/ads/googleads/client.py
foo.egg-info/installed-files.txt
"""
            )
            (egginfo / "namespace_packages.txt").write_text("google\ngoogle.ads\n")
            dist = analyze(egginfo, "google-ads")
            self.maxDiff = None
            self.assertCountEqual(
                {"google.ads.googleads", "google.ads.googleads.client"},
                dist.provided_names,
            )
            self.assertCountEqual({"google", "google.ads"}, dist.namespace_names)

    def test_distset_libcst(self) -> None:
        dist = Dist(
            "libcst",
            Path(),
            provided_names=frozenset({"libcst", "libcst.tests.foo"}),
            namespace_names=frozenset({"libcst.tests.pyre"}),
        )
        ds = DistSet()
        ds.add_dist(dist)
        self.assertEqual(dist, ds.find_provider("libcst.tests.foo"))
        self.assertEqual(dist, ds.find_provider("libcst.tests"))
        self.assertEqual(dist, ds.find_provider("libcst"))
        self.assertEqual(dist, ds.find_provider("libcst.tests"))
        self.assertEqual(dist, ds.find_provider("libcst.tests.foo"))
        self.assertEqual(Namespace("libcst"), ds.find_provider("libcst.tests.pyre"))
        self.assertEqual(Namespace("libcst"), ds.find_provider("libcst.tests.pyre.foo"))
