import json
import logging

import click
import nbformat
import papermill as pm

from .analyzer import analyze_notebook, tag_pragma_cell
from .build import build as build_image
from .output import extract_output

LOG = logging.getLogger(__name__)


@click.group()
def main():
    pass


@click.group()
@click.argument("notebook-path", type=click.Path(exists=True))
@click.pass_context
def launcher(ctx, notebook_path):
    # bind notebook path to context
    ctx.obj = {"notebook_path": notebook_path}


@main.command()
@click.argument("notebook-path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None)
@click.option("--attach", "-a", is_flag=True, default=False)
@click.option("--force", "-f", is_flag=True, default=False)
def analyze(notebook_path, output, attach, force):
    """Analyze a notebook and output a report."""

    result = analyze_notebook(notebook_path, force=force)
    # pretty print the result
    click.echo(result)

    if output:
        with open(output, "w") as f:
            f.write(result)

    if attach:
        # modify the notebook metadata
        nb = nbformat.read(notebook_path, as_version=4)
        nb.metadata["convect"] = result

        # tag cells with pragma labels with tags
        labels = ["INPUT", "OUTPUT", "PARAMETER"]
        for label in labels:
            tag_pragma_cell(nb, label)

        # write the notebook
        nbformat.write(nb, notebook_path)


@launcher.command()
@click.option("--output", "-o", type=click.Path(), default=None)
@click.option("--parameters-path", "-p", type=click.Path(), default=None)
@click.option("--force", "-f", is_flag=True, default=False)
@click.pass_context
def run(ctx, output, parameters_path, force):
    """Launch a notebook."""
    notebook_path = ctx.obj["notebook_path"]

    # check if the notebook contains convect metadata
    nb = nbformat.read(notebook_path, as_version=4)
    if "convect" not in nb.metadata or force:
        LOG.info("No convect metadata found in the notebook.")
        LOG.info("Running analysis...")
        ctx.invoke(analyze, notebook_path=notebook_path, attach=True)

    # read the parameters
    if parameters_path:
        with open(parameters_path, "r") as f:
            parameters = json.load(f)
    else:
        parameters = None

    # run the notebook with papermill
    result = pm.execute_notebook(
        notebook_path,
        output,
        parameters=parameters,
    )

    # extract output dataframe from the notebook
    output_dfs = extract_output(result)
    click.echo(output_dfs)


@launcher.command()
@click.pass_context
def spec(ctx):
    """Generate a spec file for a notebook."""
    notebook_path = ctx.obj["notebook_path"]

    # check if the notebook contains convect metadata
    nb = nbformat.read(notebook_path, as_version=4)
    if "convect" not in nb.metadata:
        LOG.info("No convect metadata found in the notebook.")
        LOG.info("Running analysis...")
        ctx.invoke(analyze, notebook_path=notebook_path, attach=True)
        # reload the notebook
        nb = nbformat.read(notebook_path, as_version=4)

    # return the parameters section of the metadata
    click.echo(json.dumps(nb.metadata["convect"]["parameter_schema"]))


@launcher.command()
@click.pass_context
def schema(ctx):
    """Generate a schema file for a notebook."""
    notebook_path = ctx.obj["notebook_path"]

    # check if the notebook contains convect metadata
    nb = nbformat.read(notebook_path, as_version=4)
    if "convect" not in nb.metadata:
        LOG.info("No convect metadata found in the notebook.")
        LOG.info("Running analysis...")
        ctx.invoke(analyze, notebook_path=notebook_path, attach=True)
        # reload the notebook
        nb = nbformat.read(notebook_path, as_version=4)

    # return the input_schema and output_schema sections of the metadata
    click.echo(
        json.dumps(
            {
                "input_schema": nb.metadata["convect"]["input_schema"],
                "output_schema": nb.metadata["convect"]["output_schema"],
            }
        )
    )


@main.command()
@click.argument("notebook-path", type=click.Path(exists=True))
@click.option("--clear-cache", is_flag=True, default=False)
def build(notebook_path, clear_cache):
    """
    Build a runnable docker image for a ntoebook.
    """
    build_image(notebook_path, clear_cache=clear_cache)


def cli():
    main.add_command(launcher)
    main()


if __name__ == "__main__":
    cli()
