# import pretty print
import logging
from pprint import pprint

import click
import nbformat
import papermill as pm

from .analyzer import analyze_notebook, tag_pragma_cell
from .output import extract_output

LOG = logging.getLogger(__name__)


@click.group()
def main():
    pass


@click.group()
def launcher():
    pass


@main.command()
@click.argument("notebook-path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None)
@click.option("--attach", "-a", is_flag=True, default=False)
@click.option("--force", "-f", is_flag=True, default=False)
def analyze(notebook_path, output, attach, force):
    """Analyze a notebook and output a report."""

    result = analyze_notebook(notebook_path, force=force)
    # pretty print the result
    pprint(result, indent=4)

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
@click.argument("notebook-path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None)
@click.option("--parameters-path", "-p", type=click.Path(), default=None)
@click.option("--force", "-f", is_flag=True, default=False)
@click.pass_context
def run(ctx, notebook_path, output, parameters_path, force):
    """Launch a notebook."""

    # check if the notebook contains convect metadata
    nb = nbformat.read(notebook_path, as_version=4)
    if "convect" not in nb.metadata or force:
        LOG.info("No convect metadata found in the notebook.")
        LOG.info("Running analysis...")
        ctx.invoke(analyze, notebook_path=notebook_path, attach=True)

    # run the notebook with papermill
    result = pm.execute_notebook(
        notebook_path,
        output,
        parameters_path=parameters_path,
    )

    # extract output dataframe from the notebook
    output_dfs = extract_output(result)
    pprint(output_dfs, indent=4)


@launcher.command()
@click.argument("notebook-path", type=click.Path(exists=True))
@click.pass_context
def spec(ctx, notebook_path):
    """Generate a spec file for a notebook."""

    # check if the notebook contains convect metadata
    nb = nbformat.read(notebook_path, as_version=4)
    if "convect" not in nb.metadata:
        LOG.info("No convect metadata found in the notebook.")
        LOG.info("Running analysis...")
        ctx.invoke(analyze, notebook_path=notebook_path, attach=True)
        # reload the notebook
        nb = nbformat.read(notebook_path, as_version=4)

    # return the parameters section of the metadata
    pprint(nb.metadata["convect"]["parameter_schema"], indent=4)


@launcher.command()
@click.argument("notebook-path", type=click.Path(exists=True))
@click.pass_context
def schema(ctx, notebook_path):
    """Generate a schema file for a notebook."""

    # check if the notebook contains convect metadata
    nb = nbformat.read(notebook_path, as_version=4)
    if "convect" not in nb.metadata:
        LOG.info("No convect metadata found in the notebook.")
        LOG.info("Running analysis...")
        ctx.invoke(analyze, notebook_path=notebook_path, attach=True)
        # reload the notebook
        nb = nbformat.read(notebook_path, as_version=4)

    # return the input_schema and output_schema sections of the metadata
    pprint(nb.metadata["convect"]["input_schema"], indent=4)
    pprint(nb.metadata["convect"]["output_schema"], indent=4)


def cli():
    main.add_command(launcher)
    main()


if __name__ == "__main__":
    cli()
