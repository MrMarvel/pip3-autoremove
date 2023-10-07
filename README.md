# pip3-autoremove


* This repository based on
  * https://github.com/enjoysoftware/pip3-autoremove
  * https://github.com/tresni/pip-autoremove
  * and https://github.com/invl/pip-autoremove

Remove a package and its unused dependencies.  
Supports both Python2 and Python3.

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
* How to install pip3-autoremove for Python3:
```
sudo pip3 install pip3-autoremove
```

* How to install pip3-autoremove for Python2:
```
sudo pip install pip3-autoremove
```

## Usage
```
pip-autoremove packages-to-uninstall
pip3-autoremove packages-to-uninstall
pip-autoremove -r requirements.txt
```

To remove the globally installed package, add "sudo" before the pip-autoremove command.