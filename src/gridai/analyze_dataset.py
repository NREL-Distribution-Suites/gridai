import polars as pl
from torch_geometric.data import SQLiteDatabase

from gridai.constants import DATA_TABLE_NAME


def analyze_dataset(db_file: str, table_name: str = DATA_TABLE_NAME):
    """Function to provide stats around the dataset"""

    db_instance = SQLiteDatabase(path=db_file, name=table_name)

    return pl.DataFrame(
        {
            "data_index": list(range(len(db_instance))),
            "number_of_nodes": [len(db_instance[index_].x) for index_ in range(len(db_instance))],
            "number_of_edges": [
                len(db_instance[index_].edge_attr) for index_ in range(len(db_instance))
            ],
            "no_loops_or_island": [
                len(db_instance[index_].edge_attr) + 1 == len(db_instance[index_].x)
                for index_ in range(len(db_instance))
            ],
        }
    )
