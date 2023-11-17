""" This module contains data model for node and edge
attributes.
"""

# standard imports
from enum import IntEnum
import enum
from typing import Optional, Any
from typing_extensions import Annotated
import typing

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


class NumPhase(IntEnum):
    """Interface for node type enumerator."""

    single_phase = 1
    two_phase = 2
    three_phase = 3


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


def get_embeddings(enum_type: IntEnum, value: Any):
    """Returns embedding."""
    return [1 if item == value else 0 for item in list(enum_type)]


class EmbeddedModel(BaseModel):
    """Implements get attributes for data models."""

    def get_attr_list(self):
        """Returns embeddings."""

        enum_fields = [
            field
            for field, info in self.model_fields.items()
            if isinstance(info.annotation, enum.EnumType)
        ]
        float_fields = [
            field
            for field, info in self.model_fields.items()
            if info.annotation in [float, typing.Optional[float]]
        ]

        return [
            el
            for field in enum_fields
            for el in get_embeddings(
                self.model_fields[field].annotation, getattr(self, field)
            )
        ] + [getattr(self, field) for field in float_fields]


class DistNodeAttrs(EmbeddedModel):
    """Interface for distribution node attributes."""

    node_type: Annotated[NodeType, serializer] = None
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


class DistEdgeAttrs(EmbeddedModel):
    """Interface for distribution edge attributes."""

    num_phase: Annotated[NumPhase, serializer]
    capacity_kva: confloat(ge=0)
    edge_type: Annotated[DistEdgeType, serializer]
    length_miles: confloat(ge=0)
    r0: float
    r1: float
    x0: float
    x1: float
