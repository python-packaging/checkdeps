import logging
import sys
from pathlib import Path
from typing import Optional, Set

import click

import trailrunner
from stdlibs import stdlib_module_names

from .distinfo import iter_all_distinfo_dirs, iter_distinfo_dirs

from .distinfo_inference import Allowed, analyze, Dist, DistSet, Namespace, Stdlib

from .import_parser import get_imports
from .metadata import get_metadata_requirement_names
from .requirements import iter_glob_all_requirement_names

STDLIB_MODULE_NAMES = stdlib_module_names()  # for the running version only
LOG = logging.getLogger(__name__)


@click.command()
@click.option(
    "--requirements",
    default="requirements*.txt",
    help="Patterns for finding files from which to read requirements (comma-separated), if using --no-metadata mode",
    show_default=True,
)
@click.option("--metadata-extras", help="Names of extras to consider (comma-separated")
@click.option(
    "--no-metadata",
    is_flag=True,
    help="Read deps from requirements instead of metadata",
)
@click.option("--verbose", "-v", is_flag=True, help="Show more logging")
@click.option("--details", is_flag=True, help="Show more output")
@click.option(
    "--installed-path",
    help="Where to look for distinfo if not sys.path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--project-root",
    help="Override automatic root detection -- where you could pip install . and have it work.",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--allow-names",
    help="Minimal names to consider satisfied, such as the current project top-level name (comma-separated)",
)
@click.option(
    "--missing-projects-only", is_flag=True, help="Show names of missing projects only"
)
@click.option(
    "--excludes", help="Comma-separated gitignore-style paths to exclude from checking"
)
@click.argument("target_dir", type=click.Path(exists=True, path_type=Path))
def main(
    requirements: str,
    target_dir: Path,
    installed_path: Optional[Path],
    project_root: Optional[Path],
    allow_names: Optional[str],
    verbose: bool,
    details: bool,
    missing_projects_only: bool,
    no_metadata: bool,
    metadata_extras: Optional[str],
    excludes: Optional[str],
) -> None:
    requirement_names: Set[Optional[str]] = {None}

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.ERROR,
        format="%(asctime)-15s %(levelname)-8s %(name)s:%(lineno)s %(message)s",
    )

    # Part 0
    if project_root is None:
        project_root = trailrunner.project_root(target_dir)

    # Part 1
    if no_metadata:
        requirement_names = set(
            iter_glob_all_requirement_names(requirements, project_root)
        )
    else:
        metadata_requirements = get_metadata_requirement_names(project_root)
        requirement_names |= set(metadata_requirements.get("", ()))
        if metadata_extras:
            for extra in metadata_extras.split(","):
                extra_requirements = set(metadata_requirements.get(extra.strip(), ()))
                LOG.info("extra %s: %s", extra, extra_requirements)
                requirement_names |= extra_requirements

    # Part 2
    distset = DistSet()
    if not installed_path:
        for p, v, d in iter_all_distinfo_dirs():
            dist = analyze(d, p)
            distset.add_dist(dist)
            LOG.debug("distinfo: %r", dist)
    else:  # pragma: no cover
        for p, v, d in iter_distinfo_dirs(Path(installed_path)):
            dist = analyze(d, p)
            distset.add_dist(dist)
            LOG.debug("distinfo: %r", dist)

    # Part 2b (first-party names, even if they're installed)
    if allow_names:
        for name in allow_names.split(","):
            distset.add_explicit(name, Allowed(name))

    # Part 2c (stdlib)
    for name in STDLIB_MODULE_NAMES:
        distset.add_explicit(name, Stdlib(name))

    # Part 3
    missing_projects: Set[Dist] = set()
    for path in trailrunner.walk(
        Path(target_dir), excludes=(excludes.split(",") if excludes else None)
    ):
        if details:
            print(f"{path.as_posix()}:")
        imports = get_imports(path)
        for i in sorted(imports):
            prov = distset.find_provider(i)
            # Allow and Stdlib get a pass for now
            if isinstance(prov, Dist):
                if prov.name not in requirement_names:
                    missing_projects.add(prov)
                    if not missing_projects_only:
                        click.echo(
                            f"{path.as_posix()} uses "
                            + click.style(i, bold=True)
                            + " but "
                            + click.style(repr(prov.name), bold=True, fg="red")
                            + " not in requirements",
                        )
                if details:
                    click.secho(f"  {i} available from {prov.name!r}", fg="blue")
            elif isinstance(prov, Stdlib):
                if details:
                    click.secho(f"  {i} stdlib", fg="green")
            elif isinstance(prov, Allowed):
                if details:
                    click.secho(f"  {i} allow_names", fg="yellow")
            elif isinstance(prov, Namespace):
                click.echo(
                    f"{path.as_posix()} uses "
                    + click.style(i, bold=True)
                    + f" but this appears to be a namespace package from {prov.name}"
                    + " without a more specific provider"
                )
            else:
                # TODO this might go to stderr, especially for
                # missing-projects-only mode
                click.echo(
                    f"{path.as_posix()} uses "
                    + click.style(i, bold=True)
                    + " but there is "
                    + click.style("nothing installed", fg="red")
                    + " to provide it",
                )
    if missing_projects_only:
        print(sorted([p.name for p in missing_projects]))
    if missing_projects:
        sys.exit(1)


if __name__ == "__main__":
    main()
