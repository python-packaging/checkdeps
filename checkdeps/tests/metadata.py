import tempfile
import unittest

from pathlib import Path

from ..metadata import get_metadata_requirement_names


class MetadataRequirementsTest(unittest.TestCase):
    def test_empty_setup_cfg(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d)
            (pd / "setup.cfg").write_text("")
            names = get_metadata_requirement_names(pd)
            self.assertEqual({}, names)

    def test_setup_cfg(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d)
            (pd / "setup.cfg").write_text(
                """
[options]
install_requires =
    Foo
    Bar

[options.extras_require]
dev =
    temp
"""
            )
            names = get_metadata_requirement_names(pd)
            self.assertEqual({"foo", "bar"}, names[""])
            self.assertEqual({"temp"}, names["dev"])

    def test_empty_pyproject_toml(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d)
            (pd / "pyproject.toml").write_text("")
            names = get_metadata_requirement_names(pd)
            self.assertEqual({}, names)

    def test_pyproject_toml(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d)
            (pd / "pyproject.toml").write_text(
                """
[project]
dependencies = ["Foo", "Bar"]

[project.optional-dependencies]
dev = ["temp"]
"""
            )
            names = get_metadata_requirement_names(pd)
            self.assertEqual({"foo", "bar"}, names[""])
            self.assertEqual({"temp"}, names["dev"])
