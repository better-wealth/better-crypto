# better-crypto

Better tools for managing crypto data.


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Setup](#setup)
- [Dependency management](#dependency-management)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


# Setup

```sh
# Install dependencies
pipenv install - -dev

# Setup pre-commit and pre-push hooks
pipenv run pre - commit install - t pre - commit
pipenv run pre - commit install - t pre - push
```

# Dependency management

This project uses[pip - compile - multi](https: // pypi.org / project / pip - compile - multi /) for hard - pinning dependencies versions.
Please see its documentation for usage instructions.
In short, `requirements / base. in ` contains the list of direct requirements with occasional version constraints(like `Django < 2`)
and `requirements / base.txt` is automatically generated from it by adding recursive tree of dependencies with fixed versions.
The same goes for `test` and `dev`.

To upgrade dependency versions, run `pip - compile - multi`.

To add a new dependency without upgrade, add it to `requirements / base. in ` and run `pip - compile - multi - -no - upgrade`.

For installation always use `.txt` files. For example, command `pip install - Ue . -r requirements / dev.txt` will install
this project in development mode, testing requirements and development tools.
Another useful command is `pip - sync requirements / dev.txt`, it uninstalls packages from your virtualenv that aren't listed in the file.
