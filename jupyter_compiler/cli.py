# import pretty print
from pprint import pprint

import click
import nbformat

from analyzer import analyze_notebook


@click.group()
def main():
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

        # write the notebook
        nbformat.write(nb, notebook_path)


if __name__ == "__main__":
    # register as a subcommand
    main.add_command(analyze)
    main()
