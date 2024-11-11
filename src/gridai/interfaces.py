"""This module contains data model for node and edge
attributes.
"""

from enum import Enum
from typing import Any, Optional, Self
from typing_extensions import Annotated

from pydantic import BaseModel, model_validator, PlainSerializer, Field


class NodeType(str, Enum):
    """Interface for node type enumerator."""

    SOURCE = "SOURCE"
    LOAD = "LOAD"
    GENERATION = "GENERATION"
    LOAD_AND_GENERATION = "LOAD_AND_GENERATION"
    OTHER = "OTHER"


class NumPhase(str, Enum):
    """Interface for node type enumerator."""

    ONE = "ONE"
    TWO = "TWO"
    THREE = "THREE"


NODE_TYPE_MAPPING = {
    (True, True): NodeType.LOAD_AND_GENERATION,
    (True, False): NodeType.GENERATION,
    (False, True): NodeType.LOAD,
    (False, False): NodeType.OTHER,
}


class DistEdgeType(str, Enum):
    """Interface for dist edge type."""

    TRANSFORMER = "TRANSFORMER"
    CONDUCTOR = "CONDUCTOR"


class PhaseType(str, Enum):
    """Interface for dist edge type."""

    ABC = "ABC"
    A = "A"
    B = "B"
    C = "C"
    AB = "AB"
    BC = "BC"
    CA = "CA"
    ABCN = "ABCN"
    AN = "AN"
    BN = "BN"
    CN = "CN"
    BA = "AB"
    CB = "BC"
    AC = "CA"
    S1 = "S1"
    S2 = "S2"
    S1S2 = "S1S2"
    NS1S2 = "S1S2N"
    S2S1 = "S1S2"
    S1N = "S1N"
    S2N = "S2N"


serializer = PlainSerializer(lambda x: x.value, when_used="always")


class GraphBaseModel(BaseModel):
    """Base interface for node and edges."""

    def to_array(self):
        return list(self.model_dump().values())

    @classmethod
    def from_array(cls, values: list[Any]) -> Self:
        return cls.model_validate(dict(zip(cls.model_fields.keys(), values)))


class DistNodeAttrs(GraphBaseModel):
    """Interface for distribution node attributes.

    Example
    =======

    >>> data = Data(x=[3], edge_index=[2, 2], edge_attr=[2])
    >>> data.x[0]
        ['SOURCE', 0.0, 0.0, 0.0, 0.0, 'BC', 7.199557856794634]

    Each node is presented as array with 7 elements in it.

    - 1st element: `node_type`
    - 2nd element: `active_demand_kw`
    - 3rd element: `reactive_demand_kw`
    - 4th element: `active_generation_kw`
    - 5th element: `reactive_generation_kw`
    - 6th element: `phase_type`
    - 7th element: `kv_level`
    """

    node_type: Annotated[NodeType, serializer] = None
    active_demand_kw: Optional[float] = 0.0
    reactive_demand_kw: Optional[float] = 0.0
    active_generation_kw: Optional[float] = 0.0
    reactive_generation_kw: Optional[float] = 0.0
    phase_type: Annotated[PhaseType, serializer]
    kv_level: Annotated[float, Field(ge=0, le=700)]

    @model_validator(mode="after")
    def compute_node_type(self) -> "DistNodeAttrs":
        """Compute node type if not passed."""
        if self.node_type != NodeType.SOURCE:
            self.node_type = NODE_TYPE_MAPPING[
                (
                    bool(self.active_generation_kw),
                    bool(self.active_demand_kw),
                )
            ]
        return self


class DistEdgeAttrs(GraphBaseModel):
    """Interface for distribution edge attributes.

    Example
    =======

    >>> data = Data(x=[3], edge_index=[2, 2], edge_attr=[2])
    >>> data.edge_attr[0]
        [25.0, 'TRANSFORMER', 0.0]


    Each is represented as an array with three values.

    - 1st element: `capacity_kva`
    - 2nd element: `edge_type`
    - 3rd element: `length_miles`
    """

    # num_phase: Annotated[NumPhase, serializer]
    capacity_kva: Annotated[float, Field()]
    edge_type: Annotated[DistEdgeType, serializer]
    length_miles: Annotated[float, Field(ge=0)]
