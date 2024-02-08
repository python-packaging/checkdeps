import re
import tempfile

import unittest
from pathlib import Path

from click.testing import CliRunner

from ..cli import main

MOD_RE = re.compile(r"^.*\/mod", re.M)


class CliTest(unittest.TestCase):
    def test_basic(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d).resolve()
            (pd / ".git").mkdir()  # for automatic project_root
            (pd / "mod").mkdir()
            (pd / "mod" / "foo.py").write_text(
                """\
import sys
import bar
import click
from baz import fromimport
"""
            )
            (pd / "requirements.txt").write_text("")

            runner = CliRunner()
            result = runner.invoke(
                main, ["--requirements=requirements.txt", "--no-metadata", d]
            )
            output = MOD_RE.sub("[TEMPDIR]/mod", result.output)
            self.assertEqual(
                """\
[TEMPDIR]/mod/foo.py uses bar but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses baz.fromimport but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses click but 'click' not in requirements
""",
                output,
            )

            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--requirements=requirements.txt",
                    "--missing-projects-only",
                    "--no-metadata",
                    d,
                ],
            )
            output = MOD_RE.sub("[TEMPDIR]/mod", result.output)
            self.assertEqual(
                """\
[TEMPDIR]/mod/foo.py uses bar but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses baz.fromimport but there is nothing installed to provide it
['click']
""",
                output,
            )

            (pd / "requirements.txt").write_text("click==9\n# comment\n")
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--requirements=requirements.txt",
                    "--no-metadata",
                    "--details",
                    d,
                ],
            )
            output = MOD_RE.sub("[TEMPDIR]/mod", result.output)
            self.assertEqual(
                """\
[TEMPDIR]/mod/foo.py:
[TEMPDIR]/mod/foo.py uses bar but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses baz.fromimport but there is nothing installed to provide it
  click available from 'click'
  sys stdlib
""",
                output,
            )

    def test_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pd = Path(d).resolve()
            (pd / "mod").mkdir()
            (pd / "mod" / "foo.py").write_text(
                """\
import sys
import bar
import click
from baz import fromimport
"""
            )
            (pd / "pyproject.toml").write_text("[project]\n")

            runner = CliRunner()
            result = runner.invoke(main, [d])
            output = MOD_RE.sub("[TEMPDIR]/mod", result.output)
            self.assertEqual(
                """\
[TEMPDIR]/mod/foo.py uses bar but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses baz.fromimport but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses click but 'click' not in requirements
""",
                output,
            )

            (pd / "pyproject.toml").write_text(
                "[project]\ndependencies = ['click', 'bar']"
            )

            runner = CliRunner()
            result = runner.invoke(main, [d])
            output = MOD_RE.sub("[TEMPDIR]/mod", result.output)
            self.assertEqual(
                """\
[TEMPDIR]/mod/foo.py uses bar but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses baz.fromimport but there is nothing installed to provide it
""",
                output,
            )
