#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ffproc",
    version="1.0",
    author="Alex Roth",
    author_email="alex@magmastone.net",
    description=(
        "A batch transcoding system. Supports multiple remote workers."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/magmastonealex/ffproc",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "Topic :: Multimedia :: Video :: Conversion",
    ],
)
