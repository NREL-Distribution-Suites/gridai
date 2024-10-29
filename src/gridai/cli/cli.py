"""Command line utilities for generating dataset."""

from pathlib import Path

import click
from gridai.analyze_dataset import analyze_dataset
from gridai.constants import DATA_TABLE_NAME

from gridai.create_dataset import create_dataset


@click.command()
@click.option(
    "-j",
    "--json-file",
    help="Path to system JSON file.",
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
    "-se",
    "--is-secondary",
    default=True,
    show_default=True,
    help="Generate secondary graphs",
)
@click.option(
    "-lt",
    "--min-transformers",
    default=3,
    show_default=True,
    help="Minimum number of transformers to include in the graph.",
)
@click.option(
    "-gt",
    "--max-transformers",
    default=10,
    show_default=True,
    help="Maximum number of transformers to include in the graph.",
)
def generate_dataset(
    json_file,
    sqlite_file,
    table_name,
    is_secondary,
    min_transformers,
    max_transformers,
):
    """Command line function to generate geojsons from opendss model"""

    create_dataset(
        Path(json_file),
        sqlite_file,
        table_name,
        dist_xmfr_graphs=bool(is_secondary),
        min_num_transformers=int(min_transformers),
        max_num_transformers=int(max_transformers),
    )


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
    """Function to dump stats around the dataset."""
    df_ = analyze_dataset(file_path, table_name)
    df_.write_csv(out_path)


@click.group()
def cli():
    """Entry point"""


cli.add_command(generate_dataset)
cli.add_command(generate_stats)
