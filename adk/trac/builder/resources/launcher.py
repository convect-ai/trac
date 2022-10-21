# this the file to be bundled into the container image
# it reads trac.json and provide the following cli commands:
# run -- run the task with the given name
# spec -- print the task spec

# this file is generic and can be used by any app

import importlib
import json

import click


def slugify(s):
    return s.replace(" ", "_").lower()


@click.group()
def cli():
    pass


@cli.command()
@click.argument("task_name")
def run(task_name):
    # read trac.json
    with open("trac.json") as f:
        spec = json.load(f)

    # find the task with the given name
    task = None
    for t in spec["tasks"]:
        if t["name"].lower() == task_name.lower() or slugify(t["name"]) == task_name:
            task = t
            break

    if task is None:
        raise ValueError(f"Task {task_name} not found")

    # run the task
    # import the handler function as specified by the task
    # handler takes the form of <module>:<function>

    handler = task["handler"]["handler"]
    module_name, func_name = handler.split(":")
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)
    func()


@cli.command()
def readme():
    """
    Return the content of README.md if it exists
    """
    try:
        with open("README.md") as f:
            print(f.read())
    except FileNotFoundError:
        pass


@cli.command()
@click.option("--task-name", "-n", required=False, help="Name of the task")
def spec(task_name):
    # print the task spec
    with open("trac.json") as f:
        spec = json.load(f)

    if task_name:
        # find the task with the given name
        task = None
        for t in spec["tasks"]:
            if (
                t["name"].lower() == task_name.lower()
                or slugify(t["name"]) == task_name
            ):
                task = t
                break

        if task is None:
            available_task_names = [t["name"] for t in spec["tasks"]]
            raise ValueError(
                f"Task {task_name} not found. Available tasks: {available_task_names}"
            )

        print(json.dumps(task, indent=2))

    else:

        print(json.dumps(spec, indent=2))


@cli.command()
def tasks():
    """
    Print the list of tasks
    """
    with open("trac.json") as f:
        spec = json.load(f)

    for task in spec["tasks"]:
        print(task["name"])


if __name__ == "__main__":
    cli()
