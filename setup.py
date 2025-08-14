from setuptools import setup

import pip_autoremove


setup(
    name="pip3-autoremove",
    version=pip_autoremove.__version__,
    description="Remove a package and its unused dependencies(Supports Python3)",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    packages=['extra'],
    py_modules=["pip_autoremove"],
    license='Apache License 2.0',
    url='https://github.com/mrmarvel/pip3-autoremove',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    install_requires=[
        'pip',
        'setuptools',
    ]
)