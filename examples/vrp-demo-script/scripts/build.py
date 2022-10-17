# build a runnable app image from a folder
# ideally we should make it as a buildpack

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import click

MY_PATH = Path(__file__).parent.resolve()


@click.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
def build(folder):
    print(folder)

    # get the absolute path of the folder
    folder = Path(folder).resolve()

    # copy the folder to a temp folder
    with tempfile.TemporaryDirectory() as tmpdir:
        # copy the contents of the folder to the temp folder
        shutil.copytree(folder, tmpdir, dirs_exist_ok=True)

        # copy the launcher.py to the temp folder
        shutil.copy(MY_PATH / "launcher.py", tmpdir)

        # write a Procfile to the temp folder
        with open(f"{tmpdir}/Procfile", "w") as f:
            f.write("web: python launcher.py")

        # read the trac.json file
        app_spec = json.load(open(Path(folder) / "trac.json"))
        app_name = app_spec["name"]

        # slugify the app name
        app_name = app_name.replace(" ", "_").lower()  # this will be the image name

        # call the buildpacks to build the image
        # check if "pack" command is installed, if not, throw an error
        res = shutil.which("pack")
        if res is None:
            raise Exception("Buildpacks is not installed")

        # call paketo python buildpacks to build the image
        command = [
            "pack",
            "build",
            app_name,
            "--buildpack",
            "gcr.io/paketo-buildpacks/python",
            "--builder",
            "docker.io/paketobuildpacks/builder:base",
            "--path",
            tmpdir,
        ]

        # call the command and display the output
        res = subprocess.run(command, capture_output=True)
        print(res.stdout.decode("utf-8"))

        if res.returncode != 0:
            print(res.stderr)
            raise Exception("Buildpacks build failed.")
        else:
            print(f"Image {app_name} built successfully.")
            print(f"Run the app with docker run {app_name} -- --help")


if __name__ == "__main__":
    build()
