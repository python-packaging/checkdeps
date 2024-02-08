import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, Generator, Optional, Set

LOG = logging.getLogger(__name__)


@dataclass(eq=True, frozen=True)
class BaseProvider:
    name: str


@dataclass(eq=True, frozen=True)
class Dist(BaseProvider):
    distinfo_dir: Path
    provided_names: FrozenSet[str]
    namespace_names: FrozenSet[str]


@dataclass(eq=True, frozen=True)
class Allowed(BaseProvider):
    pass


@dataclass(eq=True, frozen=True)
class Stdlib(BaseProvider):
    pass


@dataclass(eq=True, frozen=True)
class Namespace(BaseProvider):
    pass


@dataclass
class DistSet:
    provided_names: Dict[str, BaseProvider] = field(default_factory=dict)

    def add_dist(self, dist: Dist) -> None:
        for n in dist.provided_names:
            if item := self.provided_names.get(n):
                LOG.warning(
                    "Duplicate provider for %s: %s and %s",
                    n,
                    dist.name,
                    self.provided_names[n],
                )
            self.provided_names[n] = dist
        for n in dist.namespace_names:
            if item := self.provided_names.get(n):
                if not isinstance(item, Namespace):
                    LOG.warning("Namespace type conflict for %s", n)
            self.provided_names[n] = Namespace(dist.name)

    def add_explicit(self, dotted_name: str, provider: BaseProvider) -> None:
        self.provided_names[dotted_name] = provider
        # Ensure there are no more specific references to this (preumably
        # top-level) name.
        to_delete = []
        for k in self.provided_names.keys():
            if k.startswith(dotted_name + "."):
                to_delete.append(k)
        for k in to_delete:
            del self.provided_names[k]

    def find_provider(self, dotted_name: str) -> Optional[BaseProvider]:
        # TODO there could be more than one project that provides the same name,
        # e.g. a foo.pyc and a foo.py
        for possibility in iterparents(dotted_name + "."):
            if possibility in self.provided_names:
                LOG.info("Matched %s from prefix %s", dotted_name, possibility)
                return self.provided_names[possibility]
        return None


def iterparents(f: str) -> Generator[str, None, None]:
    while "." in f:
        f = f.rsplit(".", 1)[0]
        yield f


def analyze(distinfo_dir: Path, name: str) -> Dist:
    packages: Set[str] = set()
    namespace_packages: Set[str] = set()
    egg_info_mode: bool = False
    record_path: Path

    if distinfo_dir.name.endswith(".egg-info"):
        # installed-files is better than SOURCES.txt because it already includes
        # src/ prefix removal, and doesn't include setup.py from the root dir.
        record_path = distinfo_dir / "installed-files.txt"
        egg_info_mode = True
    else:
        record_path = distinfo_dir / "RECORD"

    # This is in two phases because otherwise we'd need to set __init__.py
    # before all other .py entries under a dir
    for line in record_path.read_text().splitlines(True):
        if egg_info_mode:
            filename = line.strip()
            if filename.startswith("../"):
                filename = filename[3:]
            else:
                continue
        else:
            filename, _ = line.split(",", 1)

        if ".." in filename:
            # docutils 0.18.1 seems to include a bin dir this way
            continue

        # TODO pyc-only dists
        # TODO .so, .dll, maybe even .dylib
        # TODO platform tag removal
        if filename.endswith(".py"):
            # TODO PEP 376 says this is full-blown CSV
            package = filename[:-3].replace("/", ".")  # TODO is this right?
            if package.endswith(".__init__"):
                package = package[: -len(".__init__")]
            packages.add(package)

    for package in sorted(packages):
        # Dragons: this is intended to detect new-style namespaces that are
        # _subdirs_ not individual files.  This isn't true for
        # googleapis-common-protos 1.56.2 (and is arguably a bug) but
        # consider this "best effort" code without perfect knowledge.
        for p in iterparents(package):
            if p not in packages:
                # print(f"add namespace for {p} {packages}")
                namespace_packages.add(p)

    namespace_package_file = distinfo_dir / "namespace_packages.txt"
    if namespace_package_file.exists():
        text = namespace_package_file.read_text()
        # pycodestyle==2.8.0 has just newlines in this file
        for line in text.splitlines():
            line = line.strip()
            if line:
                namespace_packages.add(line)

    return Dist(
        name,
        distinfo_dir,
        frozenset(packages - namespace_packages),
        frozenset(namespace_packages),
    )


def main(dirname: str) -> None:  # pragma: no cover
    dist = analyze(Path(dirname), "(unknown)")
    print("provided names=")
    for p in sorted(dist.provided_names):
        print(f"  {p}")
    print("namespace_names=")
    for p in sorted(dist.namespace_names):
        print(f"  {p}")


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1])
