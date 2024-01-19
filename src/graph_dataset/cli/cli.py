""" Command line utilities for generating dataset."""
# standard imports
from pathlib import Path

# third party imports
import click
from graph_dataset.analyze_dataset import analyze_dataset
from graph_dataset.constants import DATA_TABLE_NAME

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


@click.command()
@click.option(
    "-f",
    "--file_path",
    help="File path to dataset.sqlite file",
)
@click.option(
    "-o",
    "--out_path",
    default="dataset_stats.csv",
    help="CSV file path for dumping stats.",
)
@click.option(
    "-t",
    "--table_name",
    default=DATA_TABLE_NAME,
    help="CSV file path for dumping stats.",
)
def generate_stats(file_path: str, out_path: str, table_name: str):
    """ Function to dump stats around the dataset."""
    df_ = analyze_dataset(file_path, table_name)
    df_.write_csv(out_path)



@click.group()
def cli():
    """Entry point"""


cli.add_command(generate_dataset)
cli.add_command(generate_stats)