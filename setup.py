from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()


dev_requirements = [
    "pre-commit",
    "pytest",
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="jupyter-compiler",
    version="0.1.0",
    description="A tool to compile Jupyter notebooks into Python scripts",
    author="Yuhui Shi",
    packages=find_packages(),
    exclude=["tests", "tests.*"],
    install_requires=requirements,
    extras_require={"dev": dev_requirements},
    long_description=long_description,
    long_description_content_type="text/markdown",
)
