"""This module manages all the exceptions."""


class OpenDSSCommandError(Exception):
    """This error will be raised when executing opendss command fails."""


class GraphNotFoundError(Exception):
    """Raise this error if graph is not found."""
