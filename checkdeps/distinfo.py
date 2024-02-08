# There are multiple projects that can answer the same questions this module
# does, but they are generally complex and have complex deps.
#
# For the goal of running this against a venv on CI, we don't need any of that
# and can rely on files being materialized on disk.

import re
import sys
from pathlib import Path
from typing import Generator, Tuple

from packaging.utils import canonicalize_name

DISTINFO_RE = re.compile(r"([^-]+)-(.*?)\.dist-info$")
EGGINFO_RE = re.compile(r"([^-]+)-([^-]+)-([^-]+)\.egg-info$")


def iter_all_distinfo_dirs() -> Generator[Tuple[str, str, Path], None, None]:
    for p in sys.path:
        path = Path(p)
        if path.is_dir():
            yield from iter_distinfo_dirs(path)


def iter_distinfo_dirs(path: Path) -> Generator[Tuple[str, str, Path], None, None]:
    for subdir in path.iterdir():
        # TODO .pth files?
        if subdir.name.endswith(".dist-info") and subdir.is_dir():
            m = DISTINFO_RE.match(subdir.name)
            if not m:  # pragma: no cover
                continue
            (project, version) = m.groups()

            # Change from underscores to dashes
            project = canonicalize_name(project)

            yield project, version, subdir
        elif subdir.name.endswith(".egg-info") and subdir.is_dir():
            m = EGGINFO_RE.match(subdir.name)
            if not m:  # pragma: no cover
                continue
            (project, version, pyver) = m.groups()

            # Change from underscores to dashes
            project = canonicalize_name(project)

            yield project, version, subdir


if __name__ == "__main__":  # pragma: no cover
    for x in iter_all_distinfo_dirs():
        print(x)
