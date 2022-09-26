import pandas as pd

from .analyzer import scan_pragma_cells


def get_output_dataframe(cell):
    """
    Given a nbformat NotebookNode cell, extract the output dataframe.
    """
    if cell.cell_type != "code":
        raise ValueError("Cell is not a code cell")

    if "outputs" not in cell:
        raise ValueError("Cell has no outputs")

    for output in cell.outputs:
        if output.output_type == "execute_result":
            if "data" in output:
                if "text/html" not in output.data:
                    raise ValueError("Cell does not contain a dataframe in html format")
                html = output.data["text/html"]
                tables = pd.read_html(html)
                table = tables[0]
                # ignore the index column, and all columns starting with 'Unnamed:'
                table = table.loc[:, ~table.columns.str.startswith("Unnamed")]
                return table

    return None


def extract_output(nb):
    """
    Given a nbformat NotebookNode, extract the output from the notebook.
    The output cells are ones starting with '# PRAGMA OUTPUT'.
    """

    output_cells = scan_pragma_cells(nb, "OUTPUT")
    results = []
    for cell in output_cells:
        df = get_output_dataframe(cell)
        results.append(df)
    return results
