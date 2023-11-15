""" This module contains data model for node and edge
attributes.
"""

# standard imports
from enum import IntEnum
from typing import Optional
from typing_extensions import Annotated

# third-party imports
# pylint:disable=import-error
from pydantic import (
    BaseModel,
    conint,
    confloat,
    model_validator,
    PlainSerializer,
)


class NodeType(IntEnum):
    """Interface for node type enumerator."""

    source_node = 1
    load_node = 2
    generation_node = 3
    load_and_generation_node = 4
    other = 5


NODE_TYPE_MAPPING = {
    (True, True): NodeType.load_and_generation_node,
    (True, False): NodeType.generation_node,
    (False, True): NodeType.load_node,
    (False, False): NodeType.other,
}


class DistEdgeType(IntEnum):
    """Interface for dist edge type."""

    transformer = 1
    conductor = 2


class PhaseType(IntEnum):
    """Interface for dist edge type."""

    ABC = 1
    A = 2
    B = 3
    C = 4
    AB = 5
    BC = 6
    CA = 7
    ABCN = 1
    AN = 2
    BN = 3
    CN = 4
    BA = 5
    CB = 6
    AC = 7
    # TODO Need to fix split phase transformer connection


serializer = PlainSerializer(lambda x: x.value, when_used="always")


class DistNodeAttrs(BaseModel):
    """Interface for distribution node attributes."""

    node_type: Annotated[Optional[NodeType], serializer] = None
    active_demand_kw: Optional[float] = 0.0
    reactive_demand_kw: Optional[float] = 0.0
    active_generation_kw: Optional[float] = 0.0
    reactive_generation_kw: Optional[float] = 0.0
    phase_type: Annotated[PhaseType, serializer]
    num_nodes: conint(ge=1)
    kv_level: confloat(ge=0, le=700)

    @model_validator(mode="after")
    def compute_node_type(self) -> 'DistNodeAttrs':
        """Compute node type if not passed."""
        if self.node_type != NodeType.source_node:
            self.node_type = NODE_TYPE_MAPPING[
                (
                    bool(self.active_generation_kw),
                    bool(self.active_demand_kw),
                )
            ]
        return self


class DistEdgeAttrs(BaseModel):
    """Interface for distribution edge attributes."""

    num_phase: conint(ge=1, le=3)
    capacity_kva: confloat(ge=0)
    edge_type: Annotated[DistEdgeType, serializer]
    length_miles: confloat(ge=0)
    r0: float
    r1: float
    x0: float
    x1: float
