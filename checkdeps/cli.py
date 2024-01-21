import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

import click

import trailrunner
from stdlibs import stdlib_module_names

from .distinfo import iter_all_distinfo_dirs, iter_distinfo_dirs

from .distinfo_inference import analyze, iterparents

from .import_parser import get_imports
from .metadata import get_metadata_requirement_names
from .requirements import iter_glob_all_requirement_names

STDLIB_MODULE_NAMES = stdlib_module_names()  # for the running version only


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
    missing_projects_only: bool,
    no_metadata: bool,
    metadata_extras: Optional[str],
    excludes: Optional[str],
) -> None:
    available_names: Dict[str, Optional[str]] = {}
    requirement_names: Set[Optional[str]] = {None}

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
                requirement_names |= set(metadata_requirements.get(extra.strip(), ()))

    # Part 2
    if not installed_path:
        for p, v, d in iter_all_distinfo_dirs():
            dist = analyze(d)
            for name in dist.minimal_names:
                available_names[name] = p
    else:  # pragma: no cover
        for p, v, d in iter_distinfo_dirs(Path(installed_path)):
            dist = analyze(d)
            for name in dist.minimal_names:
                available_names[name] = p

    # Part 2b (first-party names, even if they're installed)
    if allow_names:
        for name in allow_names.split(","):
            available_names[name] = None

    # Part 3
    missing_projects: Set[str] = set()
    for path in trailrunner.walk(
        Path(target_dir), excludes=(excludes.split(",") if excludes else None)
    ):
        if verbose:
            print(f"{path.as_posix()}:")
        imports = get_imports(path)
        for i in sorted(imports):
            if i in available_names or any(
                x in available_names for x in iterparents(i)
            ):
                providers: List[Optional[str]] = []
                for name in (i,) + tuple(iterparents(i)):
                    if name in available_names:
                        providers.append(available_names[name])

                if None in providers:  # first-party probably
                    continue

                if not any(p in requirement_names for p in providers):
                    # mypy doesn't know we've already checked for None above
                    missing_projects.update(providers)  # type: ignore
                    if not missing_projects_only:
                        if len(providers) == 1:
                            click.echo(
                                f"{path.as_posix()} uses "
                                + click.style(i, bold=True)
                                + " but "
                                + click.style(repr(providers[0]), bold=True)
                                + " not in requirements"
                            )
                        else:
                            click.echo(
                                f"{path.as_posix()} uses "
                                + click.style(i, bold=True)
                                + " but "
                                + click.style(repr(providers), bold=True)
                                + " not all in requirements"
                            )
                if verbose:
                    print(f"  {i} available from {providers}")
            elif i.split(".")[0] in STDLIB_MODULE_NAMES:
                if verbose:
                    print(f"  {i} stdlib")
            else:
                # TODO this might go to stderr, especially for
                # missing-projects-only mode
                click.echo(
                    f"{path.as_posix()} uses "
                    + click.style(i, bold=True)
                    + " but there is nothing installed to provide it"
                )
    if missing_projects_only:
        print(sorted(missing_projects))
    if missing_projects:
        sys.exit(1)


if __name__ == "__main__":
    main()
