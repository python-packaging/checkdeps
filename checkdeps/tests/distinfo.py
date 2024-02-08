import tempfile
import unittest
from pathlib import Path

from ..distinfo import iter_all_distinfo_dirs, iter_distinfo_dirs
from ..distinfo_inference import analyze, Dist, DistSet


class IterDistinfoDirsTest(unittest.TestCase):
    def test_basic(self) -> None:
        for project, version, subdir in iter_all_distinfo_dirs():
            if project == "click":
                break
        else:
            self.fail("Could not find (live) click distinfo")

        dist = analyze(subdir, "click")
        ds = DistSet()
        ds.add_dist(dist)
        self.assertIsInstance(ds.find_provider("click.foo"), Dist)
        self.assertIsInstance(ds.find_provider("click"), Dist)

    def test_iter_distinfo_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d)
            cd = pd / "click-8.1.7.dist-info"
            cd.mkdir()
            gd = pd / "google_ads-23.0.0-py3.10.egg-info"
            gd.mkdir()

            self.assertEqual(
                [
                    ("click", "8.1.7", cd),
                    ("google-ads", "23.0.0", gd),
                ],
                sorted(iter_distinfo_dirs(pd)),
            )
