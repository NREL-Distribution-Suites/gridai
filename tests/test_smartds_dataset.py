""" Test module for testing utility in smartds module."""
# standard imports
from pathlib import Path

# third-party imports
from torch_geometric.data import SQLiteDatabase

# internal imports
from graph_dataset.smartds import create_dataset


def test_creating_smartds_dataset():
    """Test creating smartds dataset."""

    try:
        sqlite_file, table_name = "dataset.sqlite", "data_table"
        dataset_file = Path(sqlite_file)
        create_dataset(
            Path(__file__).parent / "data",
            sqlite_file=sqlite_file,
            table_name=table_name,
        )
        assert dataset_file.exists()
        db = SQLiteDatabase(path=sqlite_file, name=table_name)
        assert len(db)
        db.close()
    finally:
        dataset_file.unlink(missing_ok=True)
