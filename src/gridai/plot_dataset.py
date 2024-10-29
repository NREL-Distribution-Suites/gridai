"""This module contains function to plot database."""

from torch_geometric.data import Data
from torch_geometric.utils import to_networkx
import networkx as nx
import matplotlib.pyplot as plt

from gridai.interfaces import (
    DistEdgeAttrs,
    DistEdgeType,
    DistNodeAttrs,
    NodeType,
    PhaseType,
)

NODE_COLOR_DICT = {
    1: "tab:red",
    2: "tab:gray",
    3: "tab:green",
    4: "tab:cyan",
    5: "tab:blue",
}

EDGE_COLOR_DICT = {1: "tab:red", 2: "tab:blue"}


def plot_dataset(data: Data) -> None:
    """Function to plot database.

    Args:
        data (Data): Instance of torch geometric Data
    """

    node_attrs = {
        id_: DistNodeAttrs.from_array(item).model_dump() for id_, item in enumerate(data.x)
    }
    edge_indexes = [
        (float(el) for el in x) for x in zip(list(data.edge_index[0]), list(data.edge_index[1]))
    ]
    edge_attrs = {
        edge_indexes[id_]: DistEdgeAttrs.from_array(item).model_dump()  # TODO: Remove [3:] later
        for id_, item in enumerate(data.edge_attr)
    }

    g = to_networkx(data)
    nx.set_node_attributes(g, node_attrs)
    nx.set_edge_attributes(g, edge_attrs)
    pos = nx.spring_layout(g)  # positions for all nodes

    node_labels = {}
    for node, node_data in g.nodes.data():
        node_labels[node] = (
            f"""{','.join([item.name for item in list(PhaseType)
                if item.value == node_data['phase_type']])}"""
            + f""" : {','.join([item.name for item in list(NodeType)
                if item.value == node_data['node_type']])}"""
        )

    edge_labels = {}
    for edge in g.edges:
        edge_data = g.get_edge_data(*edge)
        edge_labels[
            edge
        ] = f"""{edge_data['edge_type']} phase, {round(edge_data['length_miles']*1609.34, 1)}m
            """

    for node_type in list(NodeType):
        nx.draw_networkx_nodes(
            g,
            pos,
            nodelist=[x for x in g.nodes if g.nodes[x]["node_type"] == node_type.value],
            node_size=600,
            node_color=NODE_COLOR_DICT[node_type.value],
        )
    for edge_type in list(DistEdgeType):
        nx.draw_networkx_edges(
            g,
            pos,
            edgelist=[
                edge for edge in g.edges if g.get_edge_data(*edge)["edge_type"] == edge_type.value
            ],
            edge_color=EDGE_COLOR_DICT[edge_type.value],
        )
    nx.draw_networkx_labels(g, pos, node_labels, font_size=8, font_color="black")
    nx.draw_networkx_edge_labels(g, pos, edge_labels, font_size=10, font_color="orange")
    plt.tight_layout()
    plt.axis("off")
    plt.show()
