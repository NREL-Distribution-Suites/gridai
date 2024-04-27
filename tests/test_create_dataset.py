"""Test module for testing utility in smartds module."""

from pathlib import Path

from torch_geometric.data import SQLiteDatabase

from graph_dataset.create_dataset import create_dataset


def test_creating_dataset():
    """Test creating dataset."""

    try:
        sqlite_file, table_name = "dataset.sqlite", "data_table"
        dataset_file = Path(sqlite_file)
        create_dataset(
            Path(__file__).parent / "data" / "p1udt813.json",
            sqlite_file=sqlite_file,
            table_name=table_name,
        )
        assert dataset_file.exists()
        db = SQLiteDatabase(path=sqlite_file, name=table_name)
        assert len(db)
        db.close()
    finally:
        dataset_file.unlink(missing_ok=True)
