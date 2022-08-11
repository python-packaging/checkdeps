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
            (pd / "mod").mkdir()
            (pd / "mod" / "foo.py").write_text(
                """\
import sys
import click
import black
import bar
from baz import fromimport
"""
            )

            runner = CliRunner()
            result = runner.invoke(main, ["--requirements=requirements.txt", d])
            output = MOD_RE.sub("[TEMPDIR]/mod", result.output)
            self.assertEqual(
                """\
[TEMPDIR]/mod/foo.py uses bar but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses baz.fromimport but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses black but 'black' not in requirements
""",
                output,
            )

            runner = CliRunner()
            result = runner.invoke(
                main, ["--requirements=requirements.txt", "--missing-projects-only", d]
            )
            output = MOD_RE.sub("[TEMPDIR]/mod", result.output)
            self.assertEqual(
                """\
[TEMPDIR]/mod/foo.py uses bar but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses baz.fromimport but there is nothing installed to provide it
['black']
""",
                output,
            )

            runner = CliRunner()
            result = runner.invoke(
                main, ["--requirements=requirements.txt", "--verbose", d]
            )
            output = MOD_RE.sub("[TEMPDIR]/mod", result.output)
            self.assertEqual(
                """\
[TEMPDIR]/mod/foo.py:
[TEMPDIR]/mod/foo.py uses bar but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses baz.fromimport but there is nothing installed to provide it
[TEMPDIR]/mod/foo.py uses black but 'black' not in requirements
  black available from ['black']
  click available from ['click']
  sys stdlib
""",
                output,
            )
