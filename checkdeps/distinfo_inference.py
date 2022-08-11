import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Set


@dataclass
class Dist:
    provided_names: Set[str]
    namespace_names: Set[str]

    @property
    def minimal_names(self) -> Set[str]:
        # This heuristic is based on looking at real-world examples, in
        # particular the google-api-* and google-cloud-* projects.
        done: Set[str] = set()
        for p in sorted(self.provided_names):
            for x in reversed(list(iterparents(p))):
                if x not in self.namespace_names and not any(
                    n.startswith(f"{x}.") for n in self.namespace_names
                ):
                    done.add(x)
                    break
            else:
                if (
                    p not in self.namespace_names
                    and not any(n.startswith(f"{p}.") for n in self.namespace_names)
                    and p not in done
                ):
                    done.add(p)
        return done


def iterparents(f: str) -> Generator[str, None, None]:
    while "." in f:
        f = f.rsplit(".", 1)[0]
        yield f


def analyze(distinfo_dir: Path) -> Dist:
    packages: Set[str] = set()
    namespace_packages: Set[str] = set()

    # This is in two phases because otherwise we'd need to set __init__.py
    # before all other .py entries under a dir
    for line in (distinfo_dir / "RECORD").read_text().splitlines(True):
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

    return Dist(packages - namespace_packages, namespace_packages)


def main(dirname: str) -> None:  # pragma: no cover
    dist = analyze(Path(dirname))
    print("provided names=")
    for p in sorted(dist.provided_names):
        print(f"  {p}")
    print("namespace_names=")
    for p in sorted(dist.namespace_names):
        print(f"  {p}")
    print("minimal_names=")
    for p in sorted(dist.minimal_names):
        print(f"  {p}")


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1])
