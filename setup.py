from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()


dev_requirements = [
    "pre-commit",
    "pytest",
    "wheel",
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="jupyter-compiler",
    version="0.1.0",
    description="A tool to compile Jupyter notebooks into runnable Docker images",
    author="Yuhui Shi",
    packages=find_packages(),
    exclude=["tests", "tests.*"],
    install_requires=requirements,
    extras_require={"dev": dev_requirements},
    # script entrypoint
    entry_points={
        "console_scripts": [
            "jupyter-compiler = jupyter_compiler.cli:cli",
        ],
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
)
