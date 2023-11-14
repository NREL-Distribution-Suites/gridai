""" Test module for checking utilities in OpenDSS parsers. """
# standard imports
from pathlib import Path

# third-party imports
import networkx as nx

# internal imports
from graph_dataset.opendss_parser import get_networkx_model


def test_generate_networkx_graph():
    """Test function to generate networkx representation of opendss model."""

    master_file = (
        Path(__file__).parent / "data" / "P1U" / "p1uhs0_1247" / "Master.dss"
    )
    graph = get_networkx_model(master_file)
    assert isinstance(graph, nx.Graph)
