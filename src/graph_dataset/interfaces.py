""" This module contains data model for node and edge
attributes.
"""

# standard imports
from enum import IntEnum
from typing import Optional

# third-party imports
# pylint:disable=import-error
from pydantic import BaseModel, conint, confloat


class NodeType(IntEnum):
    """Interface for node type enumerator."""

    source_node = 1
    load_node = 2
    generation_node = 3
    load_and_generation_node = 4
    bus = 5


class DistEdgeType(IntEnum):
    """ Interface for dist edge type."""
    transformer = 1
    conductor = 2


class DistNodeAttrs(BaseModel):
    """Interface for distribution node attributes."""

    node_type: NodeType
    active_demand_kw: Optional[float] = 0.0
    reactive_demand_kw: Optional[float] = 0.0
    active_generation_kw: Optional[float] = 0.0
    reactive_generation_kw: Optional[float] = 0.0
    num_nodes: conint(ge=1)
    kv_level: confloat(ge=0, le=132)


class DistEdgeAttrs(BaseModel):
    """Interface for distribution edge attributes."""

    num_phase: conint(ge=1, le=3)
    capacity_kva: confloat(ge=0)
    edge_type: DistEdgeType
    length_miles: confloat(ge=0)
    r0: float
    r1: float
    x0: float
    x1: float
