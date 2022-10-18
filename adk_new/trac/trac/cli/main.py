import click

from ..builder.build import build_app_image


@click.group()
def cli():
    pass


@cli.command()
@click.argument(
    "folder",
    type=click.Path(exists=True),
)
@click.option("--image-name", help="The name of the image to build")
@click.option("--clear-cache", is_flag=True, help="Clear the cache before building")
def build(folder, image_name, clear_cache):
    build_app_image(folder, image_name, clear_cache)


def main():
    cli()


if __name__ == "__main__":
    main()
