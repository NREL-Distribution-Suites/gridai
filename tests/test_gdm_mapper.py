"""Test module for checking utilities in OpenDSS parsers."""

from pathlib import Path

import networkx as nx
from gdm import DistributionSystem

from gridai.gdm_mapper import get_networkx_model


def test_generating_networkx_graph():
    """Test function to generate networkx representation from system json fule"""

    json_file = Path(__file__).parent / "data" / "p10_gdm.json"
    graph = get_networkx_model(DistributionSystem.from_json(json_file))
    assert isinstance(graph, nx.Graph)
