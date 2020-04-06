"""The general package information for pipeline."""
from setuptools import find_packages
from setuptools import setup


setup(
    name="pipeline",
    version="0.0.4",
    author="Tobias Raabe",
    author_email="raabe@posteo.de",
    python_requires=">=3.6.0",
    packages=find_packages(),
    package_data={"pipeline": ["templates/*.py", "templates/*.r"]},
    include_package_data=True,
    entry_points={"console_scripts": ["pipeline=pipeline.cli:cli"]},
    zip_safe=False,
)
