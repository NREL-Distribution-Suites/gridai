"""This module implements a class for loading
training graphs from smartds datasets."""

from pathlib import Path

import networkx as nx
from torch_geometric.data import Data, SQLiteDatabase
import torch
from gdm import DistributionSystem

from gridai.gdm_mapper import (
    get_networkx_model,
    get_node_graphs,
    get_transformer_sub_graphs,
)
from gridai import interfaces
from gridai.util import timeit
from gridai.exceptions import GraphNotFoundError


def get_data_object(graph: nx.Graph):
    """Function to create pytorch data object from networkx graph."""

    # Building node feature matrix
    node_attrs = []
    node_index_mapper = {}

    for id_, (node, node_data) in enumerate(graph.nodes(data=True)):
        node_attr: interfaces.DistNodeAttrs = node_data["attr"]
        node_attrs.append(node_attr.get_attr_list())
        node_index_mapper[node] = id_

    node_attrs = torch.tensor(node_attrs, dtype=torch.float)

    # Edge list
    edges = list(graph.edges())
    source_nodes, target_nodes = zip(*edges)

    edge_list = torch.tensor(
        [
            [node_index_mapper[item] for item in source_nodes],
            [node_index_mapper[item] for item in target_nodes],
        ],
        dtype=torch.long,
    )

    # Build edge attribute matrix
    edge_attrs = []

    for _, _, edge_data in graph.edges(data=True):
        edge_attr: interfaces.DistEdgeAttrs = edge_data["attr"]
        edge_attrs.append(edge_attr.get_attr_list())

    edge_attrs = torch.tensor(edge_attrs, dtype=torch.float)
    return Data(x=node_attrs, edge_index=edge_list, edge_attr=edge_attrs)


@timeit
def _read_system_json(file_path: Path) -> DistributionSystem:
    """Internal method to read system json file."""
    return DistributionSystem.from_json(file_path)


@timeit
def create_dataset(
    json_file_path: Path,
    sqlite_file: str = "dataset.sqlite",
    table_name: str = "data_table",
    dist_xmfr_graphs: bool = True,
    min_num_transformers: int | None = None,
    max_num_transformers: int | None = None,
) -> None:
    """Function to create a dataset. Explores all master.dss file recursively
    in the specified folder path and creates a sqlite database.

    Parameters
    ----------

    json_file_path :Path
        Path to system JSON file.
    sqlite_file :str
        Sqlite database table file.
    table_name :str
        Table name storing the data.
    dist_xmfr_graphs: bool
        Generates one dataset for one
        distribution transformers.
    min_num_transformers: int
        Minimum number of transformers
        to include in the dataset.
    max_num_transformers: int
        Maximum number of transformers to include
        in the dataset.
    """

    db = SQLiteDatabase(path=sqlite_file, name=table_name)
    try:
        counter = 0
        json_files = (
            [json_file_path]
            if not json_file_path.is_dir()
            else [
                item
                for item in json_file_path.glob("**/*")
                if item.is_file() and item.suffix.lower() == ".json"
            ]
        )
        for json_file in json_files:
            sys = _read_system_json(json_file)
            networks = get_transformer_sub_graphs(get_networkx_model(sys))
            if dist_xmfr_graphs:
                networks = get_transformer_sub_graphs(get_networkx_model(sys))
            else:
                networks = get_node_graphs(
                    get_networkx_model(sys),
                    lt=min_num_transformers,
                    gt=max_num_transformers,
                )
            if networks is None:
                raise GraphNotFoundError("No networks found.")
            for network_ in networks:
                db[counter] = get_data_object(network_)
                counter += 1
    finally:
        db.close()
