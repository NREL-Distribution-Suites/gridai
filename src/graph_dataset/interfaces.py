"""This module contains data model for node and edge
attributes.
"""

# standard imports
from enum import IntEnum
import enum
from typing import Optional, Any
import typing
from typing_extensions import Annotated
from graph_dataset.exceptions import NotSupportedFieldExists

from pydantic import BaseModel, model_validator, PlainSerializer, Field


class NodeType(IntEnum):
    """Interface for node type enumerator."""

    SOURCE = 1
    LOAD = 2
    GENERATION = 3
    LOAD_AND_GENERATION = 4
    OTHER = 5


class NumPhase(IntEnum):
    """Interface for node type enumerator."""

    ONE = 1
    TWO = 2
    THREE = 3


NODE_TYPE_MAPPING = {
    (True, True): NodeType.LOAD_AND_GENERATION,
    (True, False): NodeType.GENERATION,
    (False, True): NodeType.LOAD,
    (False, False): NodeType.OTHER,
}


class DistEdgeType(IntEnum):
    """Interface for dist edge type."""

    TRANSFORMER = 1
    CONDUCTOR = 2


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
    S1 = 8
    S2 = 9
    S1S2 = 10
    NS1S2 = 11
    S2S1 = 10


serializer = PlainSerializer(lambda x: x.value, when_used="always")


def get_embeddings(enum_type: IntEnum, value: Any):
    """Returns embedding."""
    return [1 if item == value else 0 for item in list(enum_type)]


def get_enum_fields(model_class: typing.Type[BaseModel]):
    """Returns a list of enumerated fields."""
    return [
        field
        for field, info in model_class.model_fields.items()
        if isinstance(info.annotation, enum.EnumType)
    ]


def get_float_fields(model_class: typing.Type[BaseModel]):
    """Returns a list of float fields."""
    return [
        field
        for field, info in model_class.model_fields.items()
        if info.annotation in [float, typing.Optional[float]]
    ]


class EmbeddedModel(BaseModel):
    """Implements get attributes for data models."""

    @classmethod
    def from_array(cls, values_list: list[float]):
        """Create an instance for values list."""
        values_list = [float(el) for el in values_list]
        enum_fields = get_enum_fields(cls)
        float_fields = get_float_fields(cls)

        enum_dict = {}
        current_index = 0
        for enum_field in enum_fields:
            enum_list = list(cls.model_fields[enum_field].annotation)
            enum_length = len(enum_list)
            sub_array = values_list[current_index : (current_index + enum_length)]
            for enum_value in enum_list:
                if sub_array == get_embeddings(type(enum_value), enum_value):
                    enum_dict[enum_field] = enum_value
                    break
            current_index += enum_length
        float_dict = dict(zip(float_fields, values_list[current_index:]))
        return cls(**enum_dict, **float_dict)

    def get_attr_list(self):
        """Returns embeddings."""

        enum_fields = get_enum_fields(self)
        float_fields = get_float_fields(self)

        if (len(enum_fields) + len(float_fields)) != len(self.model_fields):
            msg = f"Field other than float and enum exists {self=}"
            raise NotSupportedFieldExists(msg)

        return [
            el
            for field in enum_fields
            for el in get_embeddings(self.model_fields[field].annotation, getattr(self, field))
        ] + [getattr(self, field) for field in float_fields]


class DistNodeAttrs(EmbeddedModel):
    """Interface for distribution node attributes.

    Example Tensor:
        ```python
        Data(x=[5, 17], edge_index=[2, 4], edge_attr=[4, 11])

        tensor(
            [
                0.0000,
                0.0000,
                0.0000,
                0.0000,
                1.0000,
                0.0000,
                0.0000,
                0.0000,
                0.0000,
                1.0000,
                0.0000,
                0.0000,
                0.0000,
                0.0000,
                0.0000,
                0.0000,
                0.1201,
            ]
        )
        ```

        Each node will have 17 attributes.

        - First 5 values represent embedding for `Node Type`
        - Next 7 values represent embeddings for `Phase Type`
        - 13th element: `active_demand_kw`
        - 14th element: `reactive_demand_kw`
        - 15th element: `active_generation_kw`
        - 16th element: `reactive_generation_kw`
        - 17th element: `kv_level`

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


class DistEdgeAttrs(EmbeddedModel):
    """Interface for distribution edge attributes.

    Example Tensor:
        ```python
        Data(x=[5, 17], edge_index=[2, 4], edge_attr=[4, 11])

        tensor(
            [
                0.0000e00,
                1.0000e00,
                0.0000e00,
                0.0000e00,
                1.0000e00,
                4.2171e01,
                1.1422e-02,
                3.2814e-03,
                1.0668e-03,
                7.4439e-03,
                2.2183e-03,
            ]
        )
        ```

        Each edge will have 11 attributes.

        - First 3 values represent embedding for `Num Phase`
        - Next 2 values represent embeddings for `DistEdgeType`
        - 6th element: `capacity_kva`
        - 7th element: `length_miles`
    """

    # num_phase: Annotated[NumPhase, serializer]
    capacity_kva: Annotated[float, Field()]
    edge_type: Annotated[DistEdgeType, serializer]
    length_miles: Annotated[float, Field(ge=0)]
