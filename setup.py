#!/usr/bin/env python3
"""
AnonSuite Setup Script
Backward compatibility setup.py for older pip versions
"""

import os
import sys

from setuptools import find_packages, setup

# Ensure we're running on a supported Python version
if sys.version_info < (3, 8):
    sys.exit("AnonSuite requires Python 3.8 or higher")

# Read long description from README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    try:
        with open(readme_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Unified Security Toolkit for Privacy Professionals"

# Read requirements from requirements.txt
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    try:
        with open(req_path, encoding="utf-8") as f:
            return [line.strip() for line in f
                   if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "click>=8.0.0",
            "colorama>=0.4.4",
            "requests>=2.28.0",
            "pyyaml>=6.0",
            "psutil>=5.8.0"
        ]

setup(
    name="anonsuite",
    version="2.0.0",
    description="Unified Security Toolkit for Privacy Professionals",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Marcus",
    author_email="security@anonsuite.dev",
    maintainer="morningstarxcdcode",
    maintainer_email="contact@morningstarxcdcode.dev",
    url="https://github.com/morningstarxcdcode/AnonSuite",
    project_urls={
        "Documentation": "https://github.com/morningstarxcdcode/AnonSuite/docs",
        "Source": "https://github.com/morningstarxcdcode/AnonSuite",
        "Tracker": "https://github.com/morningstarxcdcode/AnonSuite/issues",
    },
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "anonsuite": ["*.json", "*.yaml", "*.yml", "*.conf"],
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "wifi": ["scapy>=2.4.5", "netfilterqueue>=0.8.1"],
        "gui": ["PyQt5>=5.15.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
            "bandit>=1.7.0"
        ],
        "docs": ["mkdocs>=1.4.0", "mkdocs-material>=8.0.0"]
    },
    entry_points={
        "console_scripts": [
            "anonsuite=anonsuite:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: System :: Networking",
        "Topic :: Utilities",
    ],
    keywords="security anonymity tor wifi penetration-testing privacy networking",
    zip_safe=False,
)
