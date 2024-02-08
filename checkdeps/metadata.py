"""
This is a low-deps simplified version of dowsing that only supports pep 621
and setup.cfg metadata for requirements.  There's probably a need for dowsing-lite (or
making dowsing itself the lite version) as well as performing automated edits.
"""

import logging

# TODO consider using imperfect and tomlkit if someday this might have a --fix
# type option
from configparser import ConfigParser, NoOptionError, NoSectionError
from pathlib import Path
from typing import Dict, Generator, Sequence

try:
    from tomllib import loads as toml_loads
except ImportError:
    from toml import loads as toml_loads  # type: ignore[assignment,unused-ignore]
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

LOG = logging.getLogger(__name__)


def handle_multiline(s: str) -> Generator[Requirement, None, None]:
    LOG.debug("handle_multiline: %r", s)
    for line in s.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue

        # N.b. Requirement does not canonicalize its name
        yield Requirement(line)


def get_metadata_requirement_names(target_dir: Path) -> Dict[str, Sequence[str]]:
    md = get_metadata_requirements(target_dir)
    return {k: set(canonicalize_name(i.name) for i in v) for k, v in md.items()}  # type: ignore


def get_metadata_requirements(target_dir: Path) -> Dict[str, Sequence[Requirement]]:
    # TODO do these merge?

    ret: Dict[str, Sequence[Requirement]] = {}
    setup_cfg = target_dir / "setup.cfg"
    if setup_cfg.exists():
        c = ConfigParser()
        c.read([setup_cfg])
        try:
            ret[""] = list(handle_multiline(c.get("options", "install_requires")))
        except (NoOptionError, NoSectionError):
            pass

        try:
            for extra in c.options("options.extras_require"):
                ret[extra] = list(
                    handle_multiline(c.get("options.extras_require", extra))
                )
        except NoSectionError:
            pass

    pyproject_toml = target_dir / "pyproject.toml"
    if pyproject_toml.exists():
        doc = toml_loads(pyproject_toml.read_text())

        # PEP 621
        project = doc.get("project", {})
        deps = project.get("dependencies")
        if deps:
            ret[""] = [Requirement(i) for i in deps]
        for k, v in project.get("optional-dependencies", {}).items():
            ret[k] = [Requirement(i) for i in v]

        # Flit
        deps = doc.get("tool", {}).get("flit", {}).get("metadata", {}).get("requires")
        if deps:
            ret[""] = [Requirement(i) for i in deps]
        for k, v in (
            doc.get("tool", {})
            .get("flit", {})
            .get("metadata", {})
            .get("requires-extra", {})
            .items()
        ):
            ret[k] = [Requirement(i) for i in v]

    return ret


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(get_metadata_requirement_names(Path())))
