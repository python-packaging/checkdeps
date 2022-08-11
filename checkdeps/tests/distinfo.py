import unittest

from ..distinfo import iter_all_distinfo_dirs
from ..distinfo_inference import analyze


class IterDistinfoDirsTest(unittest.TestCase):
    def test_basic(self) -> None:
        for project, version, subdir in iter_all_distinfo_dirs():
            if project == "click":
                break
        else:
            self.fail("Could not find click distinfo")

        dist = analyze(subdir)
        self.assertEqual({"click"}, dist.minimal_names)
