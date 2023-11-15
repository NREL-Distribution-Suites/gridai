""" Command line utilities for generating dataset."""
# standard imports
from pathlib import Path 

# third party imports
import click

# internal imports
from graph_dataset.smartds import create_dataset


@click.command()
@click.option(
    "-f",
    "--folder-path",
    help="Parent folder to search for Master.dss files.",
)
@click.option(
    "-s",
    "--sqlite-file",
    default="dataset.sqlite",
    show_default=True,
    help="SQlite file for dumping data.",
)
@click.option(
    "-t",
    "--table-name",
    default="data_table",
    show_default=True,
    help="Table name for dumping",
)
@click.option(
    "-m",
    "--master-file",
    default="Master.dss",
    show_default=True,
    help="Name of master dss file to search for.",
)
def generate_dataset(folder_path, sqlite_file, table_name, master_file):
    """Command line function to generate geojsons from opendss model"""

    create_dataset(Path(folder_path), sqlite_file, table_name, master_file)

@click.group()
def cli():
    """Entry point"""

cli.add_command(generate_dataset)