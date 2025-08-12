#!/usr/bin/env python3
"""
Setup script for Hebrew Coreference Resolution System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = (this_directory / "requirements.txt").read_text().splitlines()

setup(
    name="hebrew-coref-system",
    version="1.0.0",
    description="A comprehensive toolkit for Hebrew coreference resolution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Hebrew NLP Research Team",
    author_email="your.email@example.com",
    url="https://github.com/your-repo/hebrew-coref-system",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    keywords="hebrew, coreference, nlp, natural language processing",
    project_urls={
        "Bug Reports": "https://github.com/your-repo/hebrew-coref-system/issues",
        "Source": "https://github.com/your-repo/hebrew-coref-system",
        "Documentation": "https://github.com/your-repo/hebrew-coref-system/docs",
    },
    entry_points={
        "console_scripts": [
            "hebrew-coref=main:main",
        ],
    },
) 