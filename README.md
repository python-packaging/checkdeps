# checkdeps

It's really easy to accidentally use your transitive deps by accident.  This
project allows you to check (given a working venv) that everything you import
actually comes from either relative imports, your explicit first-order deps, or
stdlib.

Usage:

```
# Run within a working venv
# For CI
$ python -m checkdeps checkdeps

# If you use non-relative imports for your own project's code, also add
$ python -m checkdeps checkdeps --allow-names checkdeps

# For humans, pass --details
$ python -m checkdeps --details checkdeps/cli.py
checkdeps/cli.py:
checkdeps/cli.py:
  click available from 'click'
  logging stdlib
  pathlib.Path stdlib
  stdlibs.stdlib_module_names available from 'stdlibs'
  sys stdlib
  trailrunner available from 'trailrunner'
  typing.Optional stdlib
  typing.Set stdlib
```

Exits nonzero if there are any issues.

# But what if I don't want to run it from the same venv

Make sure you specify `--installed-path` to the site-packages dir and run from the same
python version.  A parent of your `target_dir` should be obviously the root of your
project (`pyproject.toml`, `.git`, etc), which is what the `requirements` are relative to.

# But aren't there projects that do this already?

I've looked at them, and I don't like the assumptions they make about top-level
names, stdlib, or namespace packages.  I think this project is more correct and
more self-contained.

# Future work

* Ensure metadata and requirements match
* Offer to add missing deps
* Better handling of version-dependent deps in an `if` or `try`/`except`

# Version Compat

Usage of this library should work back to 3.8, but development (and mypy
compatibility) only on 3.10-3.12.  Linting requires 3.12 for full fidelity.

# Versioning

This library follows [meanver](https://meanver.org/) which basically means
[semver](https://semver.org/) along with a promise to rename when the major
version changes.

# License

checkdeps is copyright [Tim Hatch](https://timhatch.com/), and licensed under
the MIT license.  See the `LICENSE` file for details.
