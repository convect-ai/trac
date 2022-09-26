from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='jupyter-compiler',
    version='0.1.0',
    description='A tool to compile Jupyter notebooks into Python scripts',
    author='Yuhui Shi',
    packages=find_packages(),
    install_requires=requirements,
    long_description=long_description,
    long_description_content_type="text/markdown",
)
