# Welcome to Graph Dataset Repo

## Installation

Use following commands to install
```cmd title="Installation Steps"
git clone https://github.nrel.gov/GATES-TLDRD/graph-dataset.git
cd graph-dataset
pip install -e.
```

## Available commands

Use following command to see available commands.

```cmd
graphd --help
```

You will see something like this.
```
Usage: graphd [OPTIONS] COMMAND [ARGS]...

  Entry point

Options:
  --help  Show this message and exit.    

Commands:
  generate-dataset  Command line function to...
```

## How to create a dataset ?

The command `generate-dataset` can convert all opendss models available in the parent folder by recursively searching for all valid opendss models.

```
graphd generate-dataset -f <parent-path>
```

This will create a sqlite db file stroing all training data in `pytorch.data.Data` format.

## How to use the dataset ?

```python
>>> from torch_geometric.data import SQLiteDatabase
>>> db = SQLiteDatabase(path="dataset.sqlite",name="data_table")
>>> len(db)
51
>>> db[0]
Data(x=[104750, 8], edge_index=[2, 104742], edge_attr=[104742, 8])
```