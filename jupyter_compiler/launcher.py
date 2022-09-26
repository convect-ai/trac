# given a notebook path, parameterize it and launch it

import click
import papermill as pm

# @click.command()
# @click.argument('notebook_path')
# @click.option('--parameter-path', type=click.Path(exists=True), default=None)
# def launch(notebook_path, parameter_path):
#     # mark the cell with comment '# PRAGMA PARAMETER' with tag 'parameters'
