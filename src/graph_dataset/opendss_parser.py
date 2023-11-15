""" This module contains an opendss parser utility functions. """


# standard imports
from pathlib import Path
import logging

# third-party imports
import opendssdirect as dss
import networkx as nx

# internal imports
from graph_dataset.exceptions import OpenDSSCommandError
from graph_dataset import interfaces
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

        edge_attrs = interfaces.DistEdgeAttrs(
            num_phase=dss_instance.CktElement.NumPhases(),
            capacity_kva=dss_instance.Transformers.kVA(),
            edge_type=interfaces.DistEdgeType.transformer,
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

        bus1_attr: interfaces.DistNodeAttrs = graph.nodes[bus1].get('attr')

        edge_attrs = interfaces.DistEdgeAttrs(
            num_phase=dss_instance.CktElement.NumPhases(),
            capacity_kva=(dss_instance.Lines.NormAmps() * bus1_attr.kv_level)
            * (1.713 if dss_instance.CktElement.NumPhases() > 1 else 1),
            edge_type=interfaces.DistEdgeType.conductor,
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

        # pylint:disable=eval-used
        node_attr = interfaces.DistNodeAttrs(
            num_nodes=dss_instance.Bus.NumNodes(),
            kv_level=dss_instance.Bus.kVBase(),
            phase_type=eval(
                f'interfaces.PhaseType.{"".join([PHASE_MAPPER[item] for item in dss_instance.Bus.Nodes()])}'
            ),
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
            node_attr: interfaces.DistNodeAttrs = graph.nodes[bus1].get("attr")
            node_attr.active_generation_kw += dss_instance.PVSystems.Pmpp()
            graph.nodes[bus1]['attr'] = node_attr

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
            node_attr: interfaces.DistNodeAttrs = graph.nodes[bus1].get("attr")
            node_attr.active_demand_kw += dss_instance.Loads.kW()
            node_attr.reactive_demand_kw += dss_instance.Loads.kvar()
            graph.nodes[bus1]['attr'] = node_attr

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
        node_attr: interfaces.DistNodeAttrs = graph.nodes[source_node]["attr"]
        node_attr.node_type = interfaces.NodeType.source_node
        graph.nodes[source_node]["attr"] = node_attr
    return graph

@timeit
def get_networkx_model(master_file: str) -> nx.Graph:
    """Extract the opendss models and returns networkx
    representation of the model.

    Args:
        master_file (str): Path to opendss master file

    Returns:
        Networkx undirected graph instance.

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
        node_attr: interfaces.DistNodeAttrs = graph.nodes[node]["attr"]
        node_attr_dict = node_attr.model_dump()
        graph.nodes[node]["attr"] = interfaces.DistNodeAttrs(**node_attr_dict)

    return graph
