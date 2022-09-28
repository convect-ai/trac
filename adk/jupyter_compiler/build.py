import logging
import os
import shutil
import subprocess
from tempfile import TemporaryDirectory

import nbformat

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


PKG_WHEEL = "dist/jupyter_compiler-0.1.0-py3-none-any.whl"
PKG_SDIST = "dist/jupyter-compiler-0.1.0.tar.gz"


def build(notebook_path, clear_cache=False):
    """
    Given path to a notebook, build a docker image to run it
    using paketo python buildpacks
    """

    # check if the notebook contains convect metadata
    nb = nbformat.read(notebook_path, as_version=4)
    if "convect" not in nb.metadata:
        LOG.error("No convect metadata found in the notebook.")
        LOG.info("Please run `jupyter-compiler analyze` first.")
        raise Exception("No convect metadata found in the notebook.")

    metadata = nb.metadata["convect"]

    # create a temporary directory to store the build context
    with TemporaryDirectory() as tmpdir:
        LOG.info(f"Created temporary directory {tmpdir}")
        # copy the notebook to the temporary directory
        nbformat.write(nb, f"{tmpdir}/notebook.ipynb")
        # TODO: copy the jupyter-compiler wheel to the temporary directory
        # if the package is published to pypi, we do not need this step
        dest_path = shutil.copy(PKG_WHEEL, tmpdir)

        # create a requirements.txt file
        with open(f"{tmpdir}/requirements.txt", "w") as f:
            packages = metadata["packages"]
            # add common packages, papermill, jupyter-complier to the packages
            packages.append("papermill")
            packages.append("ipykernel")
            # add a local reference to jupyter-compiler wheel
            packages.append(f"./jupyter_compiler-0.1.0-py3-none-any.whl")

            f.write("\n".join(metadata["packages"]))
            LOG.info(f"Created requirements.txt file {tmpdir}/requirements.txt")
            LOG.info(f"Requirements: {packages}")

        # create an entrypoint.sh file, which is a thin wrapper around jupyter-compiler launcher notebook.ipynb
        with open(f"{tmpdir}/entrypoint.sh", "w") as f:
            # shebang
            f.write("#!/usr/bin/env bash\n")
            # echo the command
            # pass all the arguments (except first) to jupyter-compiler launcher
            f.write("jupyter-compiler launcher notebook.ipynb ${@:2}\n")
            # make the file executable
            os.chmod(f"{tmpdir}/entrypoint.sh", 0o755)

        # create a Procfile
        with open(f"{tmpdir}/Procfile", "w") as f:
            f.write("web: ./entrypoint.sh")
            LOG.info(f"Created Procfile {tmpdir}/Procfile")
            LOG.info("Procfile: web: jupyter-compiler launcher notebook.ipynb")

        # list the files in the temporary directory
        LOG.info(f"Files in the temporary directory {tmpdir}")
        res = subprocess.run(["ls", "-l", tmpdir], check=True)

        # call the buildpacks to build the image
        # check if "pack" command is installed, if not, install it
        res = shutil.which("pack")
        if res is None:
            # install buildpacks
            LOG.warn("Buildpacks is not installed, installing it now...")
            res = subprocess.run(
                [
                    "curl",
                    "-sSL",
                    "https://raw.githubusercontent.com/buildpacks/pack/main/install.sh",
                    "|",
                    "sudo",
                    "bash",
                ]
            )
            # check if the installation is successful
            if res.returncode != 0:
                LOG.error("Buildpacks installation failed.")
                raise Exception("Buildpacks installation failed.")
            else:
                LOG.info("Buildpacks installation successful.")

        # create a dummy python file to satisfy the buildpacks
        with open(f"{tmpdir}/main.py", "w") as f:
            f.write("print('hello world')")

        # call paketo python buildpacks to build the image
        # image name is the name of the notebook
        image_name = os.path.basename(notebook_path).split(".")[0]
        image_name = image_name.lower() + "-runner"

        # TODO: we are not utilizing the cache. This should change after we publish the package to
        # pypi and adopt the versioning
        command = [
            "pack",
            "build",
            image_name,
            "--buildpack",
            "gcr.io/paketo-buildpacks/python",
            "--builder",
            "docker.io/paketobuildpacks/builder:full",
            "--path",
            tmpdir,
        ]

        if clear_cache:
            command.append("--clear-cache")
        res = subprocess.run(command, capture_output=True)

        if res.returncode != 0:
            LOG.error("Buildpacks build failed.")
            LOG.info(res.stdout)
            LOG.error(res.stderr)
            raise Exception("Buildpacks build failed.")
        else:
            LOG.info("Buildpacks build successful.")
            LOG.info(f"Image {image_name} built successfully.")
            LOG.info(
                f"You can run the image using `docker run --rm {image_name} -- --help`"
            )
