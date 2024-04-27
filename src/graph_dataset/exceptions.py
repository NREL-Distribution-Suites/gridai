"""This module manages all the exceptions."""


class OpenDSSCommandError(Exception):
    """This error will be raised when executing opendss command fails."""


class NotSupportedFieldExists(Exception):
    """This error will be raised if fields other than enum or
    float exists on attributes of node and/or edge"""


class GraphNotFoundError(Exception):
    """Raise this error if graph is not found."""
