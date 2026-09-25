# pip3-autoremove

[![image](https://img.shields.io/pypi/v/pip3-autoremove.svg)](https://pypi.python.org/pypi/pip3-autoremove/)
[![image](https://img.shields.io/pypi/dm/pip3-autoremove.svg)](https://pypi.python.org/pypi/pip3-autoremove/)
[![image](https://img.shields.io/pypi/l/pip3-autoremove.svg)](https://pypi.python.org/pypi/pip3-autoremove/)

This project has been rewritten from scratch to support new importlib implementation
for python 3.10+.

* I was inspired by the following projects:
    * https://github.com/enjoysoftware/pip3-autoremove
    * https://github.com/tresni/pip-autoremove
    * and https://github.com/invl/pip-autoremove

Remove a package and its unused dependencies.

Supports Python3 and Python2.7 (at least old builds).

This version also can remove packages listed in file like 'requirements.txt'.

## Usage

You can list and remove packages including their optional dependencies!

Usage:

> `pip-autoremove -f -e` to check leaf packages including extra packages.
>
> Helps with managing packages like `jupyterlab`.
>
> `pip-autoremove -y -e jupyterlab` to remove packages including their extra packages (recursive).

> `pip-autoremove -r requirements.txt` using listing of packages

You can call module directly with Python:

```
pip-autoremove
pip3-autoremove
py -m pip_autoremove
```


## How to install

* How to install pip3-autoremove for Python:

```
sudo pip install pip3-autoremove
```

## Full list of options:

```kotlin
Usage: pip_autoremove.py [OPTION]... [NAME]...

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -l, --list            list unused dependencies, but don't uninstall them.
  -L, --leaves          list leaves (packages, which are not used by any
                        others).
  -y, --yes             don't ask for confirmation of uninstall deletions.
  -e, --include-extras  include in search all extras (like
                        jsonschema[format]).
  -f, --freeze          list leaves (packages, which are not used by any
                        others) in file_test.txt format
  -r <FILE>, --read-file=<FILE>
                        read packages from file like file_test.txt
  -k <FILE>, --keep-file=<FILE>
                        read whitelist packages from file like
                        keep_requirements.txt
  --keep=<PACKAGE>,...  keep package(s) from uninstalling
```

To remove the globally installed package, add "sudo" before the pip-autoremove command.

## ⭐ Support

You can support the project by giving a ⭐ to this repository (top right of this page).

<a href="https://www.star-history.com/#MrMarvel/pip3-autoremove&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" 
srcset="https://api.star-history.com/svg?repos=MrMarvel/pip3-autoremove&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" 
srcset="https://api.star-history.com/svg?repos=MrMarvel/pip3-autoremove&type=date&legend=top-left" />
   <img alt="Star History Chart" 
src="https://api.star-history.com/svg?repos=MrMarvel/pip3-autoremove&type=date&legend=top-left" />
 </picture>
</a>
