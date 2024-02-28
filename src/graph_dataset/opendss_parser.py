""" This module contains an opendss parser utility functions. """

# standard imports
from typing import Optional
from pathlib import Path
import logging

# third-party imports
import opendssdirect as dss
import networkx as nx

# internal imports
from graph_dataset.exceptions import OpenDSSCommandError
from graph_dataset.interfaces import (
    DistEdgeAttrs,
    DistNodeAttrs,
    DistEdgeType,
    PhaseType,
    NodeType,
)
from graph_dataset.util import timeit

logger = logging.getLogger(__name__)

UNIT_MAPPER = {
    0: 0,
    1: 1.60934,
    2: 0.3048,
    3: 1,
    4: 0.001,
    5: 0.0003048,
    6: 0.0000254,
    7: 0.00001,
}

PHASE_MAPPER = {1: "A", 2: "B", 3: "C", 0: "N"}


def add_transformer_edges(dss_instance: dss, graph: nx.Graph) -> nx.Graph:
    """Function to add transformer edges in the graph.

    Args:
        dss_instance (dss): OpenDSS instance with models preloaded
        graph (nx.Graph): Instance of networkx graph for adding transformer edges

    Returns:
        nx.Graph: Updated networkx graph instance
    """

    flag = dss_instance.Transformers.First()
    while flag > 0:
        buses = dss_instance.CktElement.BusNames()
        bus1, bus2 = buses[0].split(".")[0], buses[1].split(".")[0]

        edge_attrs = DistEdgeAttrs(
            num_phase=dss_instance.CktElement.NumPhases(),
            capacity_kva=dss_instance.Transformers.kVA(),
            edge_type=DistEdgeType.TRANSFORMER,
            length_miles=0,
            r0=0,
            r1=dss_instance.Transformers.R(),  # Percentage resistance of active winding
            x1=dss_instance.Transformers.Xhl(),  # Percent reactance between winding 1 and 2
            x0=0,
        )
        graph.add_edge(bus1, bus2, attr=edge_attrs)
        flag = dss_instance.Transformers.Next()
    return graph


def add_line_edges(dss_instance: dss, graph: nx.Graph) -> nx.Graph:
    """Function to add line segment edges in the graph.

    Args:
        dss_instance (dss): OpenDSS instance with models preloaded
        graph (nx.Graph): Instance of networkx graph for adding buses

    Returns:
        nx.Graph: Updated networkx graph instance
    """

    flag = dss_instance.Lines.First()
    while flag > 0:
        buses = dss_instance.CktElement.BusNames()
        bus1, bus2 = buses[0].split(".")[0], buses[1].split(".")[0]

        bus1_attr: DistNodeAttrs = graph.nodes[bus1].get("attr")

        edge_attrs = DistEdgeAttrs(
            num_phase=dss_instance.CktElement.NumPhases(),
            capacity_kva=(dss_instance.Lines.NormAmps() * bus1_attr.kv_level)
            * (1.713 if dss_instance.CktElement.NumPhases() > 1 else 1),
            edge_type=DistEdgeType.CONDUCTOR,
            length_miles=UNIT_MAPPER[dss_instance.Lines.Units()]
            * dss_instance.Lines.Length()
            * 0.621,
            r0=dss_instance.Lines.R0() * dss_instance.Lines.Length(),
            r1=dss_instance.Lines.R1() * dss_instance.Lines.Length(),
            x1=dss_instance.Lines.X1() * dss_instance.Lines.Length(),
            x0=dss_instance.Lines.X0() * dss_instance.Lines.Length(),
        )

        graph.add_edge(bus1, bus2, attr=edge_attrs)

        flag = dss_instance.Lines.Next()
    return graph


def add_buses_as_nodes(dss_instance: dss, graph: nx.Graph) -> nx.Graph:
    """Function to add buses in the graph.

    Args:
        dss_instance (dss): OpenDSS instance with models preloaded
        graph (nx.Graph): Instance of networkx graph for adding buses

    Returns:
        nx.Graph: Updated networkx graph instance
    """

    for bus in dss_instance.Circuit.AllBusNames():
        dss_instance.Circuit.SetActiveBus(bus)

        phase_type = "".join(
            [PHASE_MAPPER[item] for item in dss_instance.Bus.Nodes()]
        )

        node_attr = DistNodeAttrs(
            num_nodes=dss_instance.Bus.NumNodes(),
            kv_level=dss_instance.Bus.kVBase(),
            phase_type=getattr(PhaseType, phase_type),
        )
        graph.add_node(bus, attr=node_attr)
    return graph


def update_pvsystem_nodes(dss_instance: dss, graph: nx.Graph) -> nx.Graph:
    """Function to update nodes with pv systems.

    Args:
        dss_instance (dss): OpenDSS instance with models preloaded
        graph (nx.Graph): Instance of networkx graph for updating nodes with pvsystems.

    Returns:
        nx.Graph: Updated networkx graph instance
    """

    flag = dss_instance.PVsystems.First()
    while flag:
        buses = dss_instance.CktElement.BusNames()
        bus1 = buses[0].split(".")[0]

        if graph.has_node(bus1):
            node_attr: DistNodeAttrs = graph.nodes[bus1].get("attr")
            node_attr.active_generation_kw += dss_instance.PVSystems.Pmpp()
            graph.nodes[bus1]["attr"] = node_attr

        flag = dss_instance.PVsystems.Next()
    return graph


def update_load_nodes(dss_instance: dss, graph: nx.Graph) -> nx.Graph:
    """Function to update nodes with loads.

    Args:
        dss_instance (dss): OpenDSS instance with models preloaded
        graph (nx.Graph): Instance of networkx graph for adding buses

    Returns:
        nx.Graph: Updated networkx graph instance
    """

    flag = dss_instance.Loads.First()
    while flag:
        buses = dss_instance.CktElement.BusNames()
        bus1 = buses[0].split(".")[0]

        if graph.has_node(bus1):
            node_attr: DistNodeAttrs = graph.nodes[bus1].get("attr")
            node_attr.active_demand_kw += dss_instance.Loads.kW()
            node_attr.reactive_demand_kw += dss_instance.Loads.kvar()
            graph.nodes[bus1]["attr"] = node_attr

        flag = dss_instance.Loads.Next()
    return graph


def execute_dss_command(dss_instance: dss, dss_command: str) -> None:
    """Pass the valid dss command to be executed.

    Args:
        dss_instance (dss): OpenDSS instance with models preloaded
        dss_command (str): DSS command sring to be executed

    Raises:
        OpenDSSCommandError: Raises this because opendss command execution
            ran into error

    """
    error = dss_instance.run_command(dss_command)
    if error:
        logger.error("Error executing command %s >> %s", dss_command, error)
        raise OpenDSSCommandError(
            f"Error executing command {dss_command} >> {error}"
        )
    logger.info("Sucessfully executed the command, %s", dss_command)


def get_source_node(dss_instance: dss) -> str:
    """Function to return source node for dss model.

    Args:
        dss_instance (dss): Instance of OpenDSSDirect

    Returns:
        str: Name of the source node
    """

    df = dss_instance.utils.class_to_dataframe("vsource")
    source_node = df["bus1"].tolist()[0].split(".")[0]
    return source_node


def add_source_node(source_node: str, graph: nx.Graph) -> nx.Graph:
    """Function to update source node in graph.

    Args:
        source_node (str): Name of source node
        graph (nx.Graph): Graph instance

    Returns:
        nx.Graph: Updated graph instance
    """

    if graph.has_node(source_node):
        node_attr: DistNodeAttrs = graph.nodes[source_node]["attr"]
        node_attr.node_type = NodeType.SOURCE
        graph.nodes[source_node]["attr"] = node_attr
    return graph


def get_transformers_from_graph(graph: nx.Graph) -> list[tuple[str, str]]:
    """Function to return number of transformers.

    Args:
        graph (nx.Graph): Instance of networkx graph.

    Return:
        list[tuple[str, str]]: List of transformers in a graph.
    """

    return [
        edge_
        for edge_ in graph.edges
        if graph.get_edge_data(*edge_)["attr"].edge_type
        == DistEdgeType.TRANSFORMER
    ]


def get_sub_dfs_tree(
    dfs_tree: nx.DiGraph,
    graph: nx.Graph,
    start_node: str,
) -> nx.DiGraph:
    """Function to return directed sub graph from a given starting node
    with populated attributes.

    Args:
        dfs_tree (nx.DiGraph): Original directed graph
        graph (nx.Graph): Original graph with attributes
        start_node (str): Name of the starting node

    """
    dfs_sub_tree = nx.dfs_tree(dfs_tree, source=start_node).to_undirected()

    for node in dfs_sub_tree.nodes:
        dfs_sub_tree.nodes[node]["attr"] = graph.nodes[node]["attr"]
    for edge in dfs_sub_tree.edges:
        dfs_sub_tree[edge[0]][edge[1]]["attr"] = graph.get_edge_data(*edge)[
            "attr"
        ]

    return dfs_sub_tree


def get_source_dfs(graph: nx.Graph) -> nx.DiGraph:
    """Function to return directed graph from undirected using
    source node as starting node.

    Args:
        graph (nx.Graph): Instance of the undirected graph.

    Returns:
        nx.DiGraph: Instance of directed graph
    """

    source_node = [
        node
        for node in graph.nodes
        if graph.nodes[node]["attr"].node_type == NodeType.SOURCE
    ]
    return nx.dfs_tree(graph, source=source_node[0])


def get_node_graphs(graph: nx.Graph, lt: int, gt: int) -> list[nx.Graph]:
    """Method to get subgraphs for each node with limit on
    number of transformers.

    Args:
        graph (nx.Graph): Instance of networkx graph instance
        lt (int): Least number of transformers to include
        gt (int): Maximum number of transformers to include

    Return:
        list[nx.Graph]: List of subgraphs.
    """

    sub_graphs = []
    dfs_tree = get_source_dfs(graph)

    for node in graph.nodes:
        dfs_sub_graph = get_sub_dfs_tree(
            dfs_tree=dfs_tree,
            graph=graph,
            start_node=node,
        )
        num_trans = len(get_transformers_from_graph(dfs_sub_graph))

        if lt <= num_trans <= gt:
            dfs_sub_graph.nodes[node]["attr"].node_type = NodeType.SOURCE
            sub_graphs.append(dfs_sub_graph)

    return sub_graphs


def get_transformer_sub_graphs(graph: nx.Graph) -> list[nx.Graph]:
    """Method to get subgraphs for each distribution transformers."""
    sub_graphs = []
    tr_edges = get_transformers_from_graph(graph)
    dfs_tree = get_source_dfs(graph)

    tr_node = None
    for tr_edge in tr_edges:
        for tr_node in tr_edge:
            dfs_sub_graph = get_sub_dfs_tree(
                dfs_tree=dfs_tree,
                graph=graph,
                start_node=tr_node,
            )
            num_trans = len(get_transformers_from_graph(dfs_sub_graph))
            if num_trans > 0:
                break

        if num_trans == 1:
            dfs_sub_graph.nodes[tr_node]["attr"].node_type = NodeType.SOURCE
            sub_graphs.append(dfs_sub_graph)

    return sub_graphs


@timeit
def get_networkx_model(master_file: str) -> nx.Graph:
    """Extract the opendss models and returns networkx
    representation of the model.

    Args:
        master_file (str): Path to opendss master file

    Returns:
       nx.Graph: Networkx undirected graph instance.

    """

    # Do a basic check on the path
    master_file = Path(master_file)
    logger.debug("Attempting to read case file >> %s", master_file)

    # Clear memory and compile dss file
    dss.run_command("Clear")
    dss.Basic.ClearAll()
    execute_dss_command(dss, f"Redirect {master_file}")

    graph = nx.Graph()

    # Initial container
    graph = add_buses_as_nodes(dss, graph)
    graph = update_load_nodes(dss, graph)
    graph = update_pvsystem_nodes(dss, graph)
    graph = add_line_edges(dss, graph)
    graph = add_transformer_edges(dss, graph)
    graph = add_source_node(get_source_node(dss), graph)

    for node in graph.nodes:
        node_attr: DistNodeAttrs = graph.nodes[node]["attr"]
        node_attr_dict = node_attr.model_dump()
        graph.nodes[node]["attr"] = DistNodeAttrs(**node_attr_dict)

    components = list(nx.connected_components(graph))
    if len(components) > 1:
        graph = graph.subgraph(max(components, key=len))

    loops = list(nx.simple_cycles(graph))
    if loops:
        print(f"This network has loop {loops=}")
        return None

    return graph
