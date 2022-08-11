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

# For humans, pass -v
$ python -m checkdeps -v checkdeps/cli.py
checkdeps/cli.py:
  click available from ['click']
  pathlib.Path stdlib
  stdlibs.stdlib_module_names available from ['stdlibs']
  sys stdlib
  trailrunner available from ['trailrunner']
  typing.Dict stdlib
  typing.List stdlib
  typing.Optional stdlib
  typing.Set stdlib
```

Exits nonzero if there are any issues.

# But aren't there projects that do this already?

I've looked at them, and I don't like the assumptions they make about top-level
names, stdlib, or namespace packages.  I think this project is more correct and
more self-contained.

# Future work

* Read project metadata instead of requirements
* Ensure metadata and requirements match
* Offer to add missing deps
* Better handling of version-dependent deps in an `if` or `try`/`except`

# License

checkdeps is copyright [Tim Hatch](https://timhatch.com/), and licensed under
the MIT license.  I am providing code in this repository to you under an open
source license.  This is my personal repository; the license you receive to
my code is from me and not from my employer. See the `LICENSE` file for details.
