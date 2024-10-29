"""This module contains an opendss parser utility functions."""

from collections import defaultdict
import logging
import copy
from typing import NamedTuple, Any, Type

import networkx as nx
from gdm import (
    DistributionSystem,
    DistributionBus,
    DistributionLoad,
    DistributionSolar,
    DistributionCapacitor,
    DistributionBranchBase,
    MatrixImpedanceBranch,
    SequenceImpedanceBranch,
    GeometryBranch,
    DistributionTransformer,
    DistributionVoltageSource,
    MatrixImpedanceSwitch,
    MatrixImpedanceFuse,
)
from infrasys.component import Component

from gridai.interfaces import (
    DistEdgeAttrs,
    DistNodeAttrs,
    DistEdgeType,
    PhaseType,
    NodeType,
)
from gridai.util import timeit


logger = logging.getLogger(__name__)


@timeit
def add_transformer_edges(system: DistributionSystem, graph: nx.Graph) -> nx.Graph:
    """Function to add transformer edges in the graph."""

    trs: list[DistributionTransformer] = list(system.get_components(DistributionTransformer))
    for tr in trs:
        edge_attrs = DistEdgeAttrs(
            num_phase=tr.equipment.windings[0].num_phases,
            capacity_kva=tr.equipment.windings[0].rated_power.to("kilova").magnitude,
            edge_type=DistEdgeType.TRANSFORMER,
            length_miles=0,
        )
        graph.add_edge(tr.buses[0].name, tr.buses[1].name, attr=edge_attrs)

    return graph


def _get_ampacity_from_branch(branch: Any):
    """Internal method to get ampacity from branch."""
    if (
        isinstance(branch, MatrixImpedanceBranch)
        or isinstance(branch, SequenceImpedanceBranch)
        or isinstance(branch, MatrixImpedanceSwitch)
        or isinstance(branch, MatrixImpedanceFuse)
    ):
        return branch.equipment.ampacity.to("ampere").magnitude
    elif isinstance(branch, GeometryBranch):
        return max(c.ampacity for c in branch.equipment.conductors).to("ampere").magnitude
    else:
        msg = f"Invalid {branch=} type passed to compute ampacity."
        raise ValueError(msg)


@timeit
def add_line_edges(system: DistributionSystem, graph: nx.Graph) -> nx.Graph:
    """Function to add line segment edges in the graph."""

    branches: list[DistributionBranchBase] = list(system.get_components(DistributionBranchBase))
    for branch in branches:
        edge_attrs = DistEdgeAttrs(
            num_phase=len(branch.phases),
            capacity_kva=(
                _get_ampacity_from_branch(branch)
                * branch.buses[0].nominal_voltage.to("kilovolt").magnitude
            )
            * (1.713 if len(branch.phases) > 1 else 1),
            edge_type=DistEdgeType.CONDUCTOR,
            length_miles=branch.length.to("mile").magnitude,
        )
        graph.add_edge(branch.buses[0].name, branch.buses[1].name, attr=edge_attrs)
    return graph


class PowerPair(NamedTuple):
    """Named tuple for collecting power."""

    active: float
    reactive: float


def _get_total_load_kw_kvar(loads: list[DistributionLoad]) -> PowerPair:
    """Internal method to get total load power."""

    if not loads:
        return PowerPair(active=0, reactive=0)

    load_p, load_q = 0, 0
    for load in loads:
        load_p += (
            sum(ph_load.real_power for ph_load in load.equipment.phase_loads)
            .to("kilowatt")
            .magnitude
        )
        load_q += (
            sum(ph_load.reactive_power for ph_load in load.equipment.phase_loads)
            .to("kilovar")
            .magnitude
        )
    return PowerPair(active=load_p, reactive=load_q)


def _get_total_solar_kw_kvar(solars: list[DistributionSolar]) -> PowerPair:
    """Internal method to get total solar power."""

    if not solars:
        return PowerPair(active=0, reactive=0)

    solar_power = 0
    for solar in solars:
        solar_power += solar.equipment.rated_capacity.to("kilowatt").magnitude

    return PowerPair(active=solar_power, reactive=0)


def _get_total_capacitor_kw_kvar(
    caps: list[DistributionCapacitor],
) -> PowerPair:
    """Internal method to get total capacitor power."""

    if not caps:
        return PowerPair(active=0, reactive=0)

    reactive_power = 0
    for cap in caps:
        reactive_power += sum(
            ph_cap.rated_capacity.to("kilovar").magnitude
            for ph_cap in cap.equipment.phase_capacitors
        )
    return PowerPair(active=0, reactive=reactive_power)


def _get_node_type(
    load_power: PowerPair, solar_power: PowerPair, cap_power: PowerPair
) -> NodeType:
    """Internal function to get node type."""
    if load_power.active > 0 and solar_power.active > 0:
        return NodeType.LOAD_AND_GENERATION
    elif (
        load_power.active == 0
        and load_power.reactive == 0
        and solar_power.active == 0
        and solar_power.reactive == 0
        and cap_power.active == 0
        and cap_power == 0
    ):
        return NodeType.OTHER
    else:
        return NodeType.LOAD


def _get_bus_component_mapping(
    system: DistributionSystem, component_type: Type[Component]
) -> dict[str, list[Component]]:
    """Internal function to get bus component mapping."""

    bus_component_mapper = defaultdict(list)
    for comp in system.get_components(component_type):
        if not isinstance(comp, component_type):
            msg = f"{comp=} must be an instance of {component_type}"
            raise ValueError(msg)
        if "bus" not in comp.model_fields:
            msg = f"{comp=} does not have `bus` field."
            raise ValueError()
        bus_component_mapper[comp.bus.name].append(comp)
    return bus_component_mapper


@timeit
def add_buses_as_nodes(system: DistributionSystem, graph: nx.Graph) -> nx.Graph:
    """Function to add buses in the graph."""

    buses: list[DistributionBus] = list(system.get_components(DistributionBus))
    solar_mapper = _get_bus_component_mapping(system, DistributionSolar)
    capacitor_mapper = _get_bus_component_mapping(system, DistributionCapacitor)
    vsource_mapper = _get_bus_component_mapping(system, DistributionVoltageSource)
    load_mapper = _get_bus_component_mapping(system, DistributionLoad)
    for bus in buses:
        phase = "".join(sorted([el.value for el in bus.phases]))
        load_power = _get_total_load_kw_kvar(load_mapper.get(bus.name, []))
        solar_power = _get_total_solar_kw_kvar(solar_mapper.get(bus.name, []))
        cap_power = _get_total_capacitor_kw_kvar(capacitor_mapper.get(bus.name, []))
        node_attr = DistNodeAttrs(
            num_nodes=len(bus.phases),
            kv_level=bus.nominal_voltage.to("kilovolt").magnitude,
            phase_type=getattr(PhaseType, phase),
            active_demand_kw=load_power.active,
            reactive_demand_kw=load_power.reactive,
            active_generation_kw=solar_power.active,
            reactive_generation_kw=cap_power.reactive,
            node_type=(
                NodeType.SOURCE
                if bus.name in vsource_mapper
                else _get_node_type(load_power, solar_power, cap_power)
            ),
        )
        graph.add_node(bus.name, attr=node_attr)
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
        if graph.get_edge_data(*edge_)["attr"].edge_type == DistEdgeType.TRANSFORMER
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
        dfs_sub_tree[edge[0]][edge[1]]["attr"] = graph.get_edge_data(*edge)["attr"]

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
        node for node in graph.nodes if graph.nodes[node]["attr"].node_type == NodeType.SOURCE
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

    transformer_nodes_set = set()

    for node in graph.nodes:
        dfs_sub_graph = get_sub_dfs_tree(
            dfs_tree=dfs_tree,
            graph=graph,
            start_node=node,
        )
        trs = set(get_transformers_from_graph(dfs_sub_graph))

        if lt <= len(trs) <= gt and not (transformer_nodes_set & trs):
            transformer_nodes_set.update(trs)
            dfs_sub_graph.nodes[node]["attr"].node_type = NodeType.SOURCE
            sub_graphs.append(copy.deepcopy(dfs_sub_graph))

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
            sub_graphs.append(copy.deepcopy(dfs_sub_graph))

    return sub_graphs


@timeit
def get_networkx_model(sys: DistributionSystem) -> nx.Graph:
    """Extract the opendss models and returns networkx
    representation of the model.

    Parameters
    ----------

    sys : DistributionSystem
        Instance of the DistributionSystem

    Returns:
       nx.Graph: Networkx undirected graph instance.

    """

    graph = nx.Graph()

    graph = add_buses_as_nodes(sys, graph)
    graph = add_line_edges(sys, graph)
    graph = add_transformer_edges(sys, graph)

    for node in graph.nodes:
        node_attr: DistNodeAttrs = graph.nodes[node]["attr"]
        node_attr_dict = node_attr.model_dump()
        graph.nodes[node]["attr"] = DistNodeAttrs(**node_attr_dict)

    components = list(nx.connected_components(graph))
    if len(components) > 1:
        graph = graph.subgraph(max(components, key=len))

    loops = list(nx.simple_cycles(graph))
    if loops:
        msg = f"This network has {loops=}"
        raise ValueError(msg)

    return graph
