"""Test module for testing utility in smartds module."""

from pathlib import Path

from gridai.interfaces import DistNodeAttrs
from torch_geometric.data import SQLiteDatabase

from gridai.create_dataset import create_dataset


def test_creating_dataset(tmp_path):
    """Test creating dataset."""

    sqlite_file, table_name = tmp_path / "dataset.sqlite", "data_table"
    dataset_file = Path(sqlite_file)
    create_dataset(
        Path(__file__).parent / "data" / "p10_gdm.json",
        sqlite_file=sqlite_file,
        table_name=table_name,
    )
    assert dataset_file.exists()
    db = SQLiteDatabase(path=sqlite_file, name=table_name)
    assert len(db)
    _ = DistNodeAttrs.from_array(db[0].x[0])
    db.close()
