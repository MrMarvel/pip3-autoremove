# pip3-autoremove

[![image](https://img.shields.io/pypi/dm/pip3-autoremove.svg)](https://pypi.python.org/pypi/pip3-autoremove/)

[![image](https://img.shields.io/pypi/v/pip3-autoremove.svg)](https://pypi.python.org/pypi/pip3-autoremove/)

[![image](https://img.shields.io/pypi/l/pip3-autoremove.svg)](https://pypi.python.org/pypi/pip3-autoremove/)

This project has been rewritten from scratch to support new importlib implementation 
for python 3.10+.

* I was inspired by the following projects:
  * https://github.com/enjoysoftware/pip3-autoremove
  * https://github.com/tresni/pip-autoremove
  * and https://github.com/invl/pip-autoremove

Remove a package and its unused dependencies.  
Supports Python3 and Python2.7(at least old builds).

This version also can remove packages listed in file 
like 'requirements.txt'.

## Special Feature!
You can list and remove packages including their optional dependencies!

Usage:
> `pip-autoremove -f -e` to check leaf packages including extra packages.
> Helps with managing packages like `jupyterlab`.
> 
> `pip-autoremove -y -e jupyterlab` to remove packages including their extra packages (recursive).

## How to install
* How to install pip3-autoremove for Python:
```
sudo pip install pip3-autoremove
```


## Usage
```
pip-autoremove packages-to-uninstall
pip3-autoremove packages-to-uninstall
pip-autoremove -r requirements.txt
py -m pip_autoremove -ef
```

To remove the globally installed package, add "sudo" before the pip-autoremove command.