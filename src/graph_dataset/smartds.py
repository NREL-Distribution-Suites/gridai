""" This module implements a class for loading 
training graphs from smartds datasets."""


# standard imports
from pathlib import Path

# third-party imports
import networkx as nx
from torch_geometric.data import Data, SQLiteDatabase
import torch

# internal imports
from graph_dataset.opendss_parser import get_networkx_model
from graph_dataset import interfaces
from graph_dataset.util import timeit


@timeit
def get_data_object(graph: nx.Graph):
    """Function to create pytorch data object from networkx graph."""

    # Building node feature matrix
    node_attrs = []
    node_index_mapper = {}

    for id_, (node, node_data) in enumerate(graph.nodes(data=True)):
        node_attr: interfaces.DistNodeAttrs = node_data["attr"]
        node_attrs.append(list(node_attr.model_dump().values()))
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
        edge_attrs.append(list(edge_attr.model_dump().values()))

    edge_attrs = torch.tensor(edge_attrs, dtype=torch.float)
    return Data(x=node_attrs, edge_index=edge_list, edge_attr=edge_attrs)


def create_dataset(
    folder_path: Path,
    sqlite_file: str = "dataset.sqlite",
    table_name: str = "data_table",
    master_file_name: str = "Master.dss",
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
    for id_, file_path in enumerate(folder_path.rglob(master_file_name)):
        db[id_] = get_data_object(get_networkx_model(str(file_path)))
    db.close()