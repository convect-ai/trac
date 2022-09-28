# App Development Kit (ADK)

## Introduction

This development kit takes in a jupyter notebook, parses its information and write metadata to it.
Metadata including
- What types of input the notebook takes in and their schemas
- What types of output the notebook spits out and their schemas
- What types of 3rd party libraries the notebook depends on

After the metadata are generated, it can automatically build a docker image that wraps the notebook and make it runnable.

## Installation

```sh
pip install .
```

## Usage

Run analysis (metadata generation on a notebook)
```bash
cd examples
jupyter-compiler analyze simple.ipynb --attach
```

Pack the notebook in a runnable docker image
```bash
jupyter-compiler build simple.ipynb
```

Run the docker image
```bash
docker run --rm simple-runner -- --help
```

## For notebook author

In order to let the ADK pick up the correct information, we need the following labels in the notebook:
- When reading an input, mark the cell with `# PRAGMA INPUT`
- When defining parameters, mark the cell with `# PRAGMA PARAMETER`
- When outputing a dataframe, mark the cell with `# PRAGMA OUTPUT`
