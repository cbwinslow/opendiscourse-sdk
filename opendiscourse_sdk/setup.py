"""
Setup configuration for OpenDiscourse SDK.

This file enables the SDK to be installed via pip and distributed on PyPI.

Author: OpenDiscourse Team
License: MIT
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read version from __init__.py
version = "1.0.0"

setup(
    name="opendiscourse-sdk",
    version=version,
    author="OpenDiscourse Team",
    author_email="team@opendiscourse.org",
    description="Python SDK for Congress.gov, GovInfo.gov, and OpenStates APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cbwinslow/opendiscourse",
    project_urls={
        "Bug Tracker": "https://github.com/cbwinslow/opendiscourse/issues",
        "Documentation": "https://github.com/cbwinslow/opendiscourse/tree/main/docs/workflows",
        "Source Code": "https://github.com/cbwinslow/opendiscourse",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.32.0",
        "pydantic>=2.0.0",
        "urllib3>=1.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
            "types-requests>=2.31.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
            "sphinx-autodoc-typehints>=1.24.0",
        ],
    },
    keywords=[
        "congress",
        "govinfo",
        "openstates",
        "legislation",
        "bills",
        "government",
        "api",
        "politics",
        "legislative",
        "federal",
        "state",
    ],
    license="MIT",
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "opendiscourse-sdk-examples=opendiscourse_sdk.examples:main",
        ],
    },
)
