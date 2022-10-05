import json
import logging
import os

import click
import nbformat
import papermill as pm

from .analyzer import analyze_notebook, tag_pragma_cell
from .build import build as build_image
from .deploy import deploy as deploy_func
from .deploy import undeploy as undeploy_func
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
@click.option("--force", "-f", is_flag=True, default=False)
def init(notebook_path, force):
    """Analyze a notebook and output a report."""

    result = analyze_notebook(notebook_path, force=force)
    # pretty print the result
    click.echo(result)

    # modify the notebook metadata
    nb = nbformat.read(notebook_path, as_version=4)
    # add the metadata
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
        LOG.info("Running init...")
        ctx.invoke(init, notebook_path=notebook_path)

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
        LOG.info("Running init...")
        ctx.invoke(init, notebook_path=notebook_path)
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
        LOG.info("Running init...")
        ctx.invoke(init, notebook_path=notebook_path)
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


@main.command()
@click.argument("notebook-path", type=click.Path(exists=True))
@click.option("--name", "-n", type=str, default=None)
@click.option("--description", "-d", type=str, default=None)
@click.option("--endpoint", "-e", type=str, default="http://localhost:9000")
@click.pass_context
def deploy(ctx, notebook_path, name, description, endpoint):
    """
    Deploy a notebook as a trac app
    """
    # check if the notebook contains convect metadata
    # if not, run init
    nb = nbformat.read(notebook_path, as_version=4)
    if "convect" not in nb.metadata:
        LOG.info("No convect metadata found in the notebook.")
        LOG.info("Running init...")
        ctx.invoke(init, notebook_path=notebook_path)
        # reload the notebook
        nb = nbformat.read(notebook_path, as_version=4)

    # build the image
    LOG.info("Building image...")
    image_name, image_tag = build_image(
        notebook_path,
    )

    if name is None:
        name = "notebook" + "-" + os.path.basename(notebook_path).split(".")[0]

    LOG.info(f"Using name: {name}")

    if description is None:
        description = "Notebook deployed with track adk"

    LOG.info(f"Using description: {description}")

    # deploy the notebook
    LOG.info("Deploying notebook...")
    dashboard_url = deploy_func(
        endpoint=endpoint,
        app_def_name=name,
        app_def_description=description,
        app_def_image_name=image_name,
        app_def_image_tag=image_tag,
        app_inst_description=description,
        app_inst_name=name,
    )

    click.echo(f"Use the following url to access the dashboard: {dashboard_url}")


def cli():
    main.add_command(launcher)
    main()


if __name__ == "__main__":
    cli()
