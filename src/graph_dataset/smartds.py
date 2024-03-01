""" This module implements a class for loading 
training graphs from smartds datasets."""

# standard imports
from pathlib import Path

# third-party imports
import networkx as nx
from torch_geometric.data import Data, SQLiteDatabase
import torch

# internal imports
from graph_dataset.opendss_parser import (
    get_networkx_model,
    get_node_graphs,
    get_transformer_sub_graphs,
)
from graph_dataset import interfaces

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


def create_dataset(
    folder_path: Path,
    sqlite_file: str = "dataset.sqlite",
    table_name: str = "data_table",
    master_file_name: str = "Master.dss",
    dist_xmfr_graphs: bool = True,
    min_num_transformers: int | None = None,
    max_num_transformers: int | None = None,
) -> None:
    """Function to create a dataset. Explores all master.dss file recursively
    in the specified folder path and creates a sqlite database.

    Args:
        folder_path (Path): Path instance to search for master.dss files.
        sqlite_file (str): Sqlite database table file.
        table_name (str): Table name storing the data.
        master_file_name (str): Master dss file to search.
    """

    db = SQLiteDatabase(path=sqlite_file, name=table_name)
    try:
        counter = 0
        for file_path in folder_path.rglob(master_file_name):
            if len(file_path.parent.name.split("--")) != 2:
                continue

            if dist_xmfr_graphs:
                networks = get_transformer_sub_graphs(
                    get_networkx_model(str(file_path))
                )
            else:
                networks = get_node_graphs(
                    get_networkx_model(str(file_path)),
                    lt=min_num_transformers,
                    gt=max_num_transformers,
                )
            if networks is not None:
                for network_ in networks:
                    db[counter] = get_data_object(network_)
                    counter += 1
    finally:
        db.close()
