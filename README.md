
# Welcome to Graph Dataset Repo

## Installation

Use following commands to install
```bash title="Installation Steps"
pip install gridai
```

## Available commands

Use following command to see available commands.

```bash
gridai --help
```

You will see something like this.
```bash
Usage: gridai [OPTIONS] COMMAND [ARGS]...

  Entry point

Options:
  --help  Show this message and exit.

Commands:
  generate-dataset  Command line function to generate geojsons from...
  generate-stats    Function to dump stats around the dataset.
```

## How to create a dataset ?

The command `generate-dataset` can convert all opendss models available in the parent folder by recursively searching for all valid opendss models.

```bash
gridai generate-dataset -j <system-json-path>
```

This will create a sqlite db file stroing all training data in `pytorch.data.Data` format.

## How to use the dataset ?

```python
>>> from torch_geometric.data import SQLiteDatabase
>>> db = SQLiteDatabase(path="dataset.sqlite",name="data_table")
>>> len(db)
51
>>> db[0]
Data(x=[22, 21], edge_index=[2, 21], edge_attr=[21, 4])
```

## Getting NodeObject and EdgeObject

You can use following snippet to convert node attributes back to an instance of 
`DistNodeAttrs` and edge attributes back to an `DistEdgeAttrs`.

```python
>>> from torch_geometric.data import SQLiteDatabase
>>> from gridai.interfaces import DistNodeAttrs, DistEdgeAttrs
>>> from rich import print
>>> db = SQLiteDatabase(path="dataset.sqlite",name="data_table")
>>> print(DistNodeAttrs.from_array(db[0].x[0]))
DistNodeAttrs(
   node_type=<NodeType.LOAD: 2>,
   active_demand_kw=5.726587772369385,
   reactive_demand_kw=1.691259503364563,
   active_generation_kw=0.0,
   reactive_generation_kw=0.0,
   phase_type=<PhaseType.NS1S2: 11>,
   kv_level=0.1200888529419899
)
>>> print(DistEdgeAttrs.from_array(db[0].edge_attr[0]))
DistEdgeAttrs(
   capacity_kva=25.0,
   edge_type=<DistEdgeType.TRANSFORMER: 1>,
   length_miles=0.0
)
```

## Plotting the dataset

You can use following command to plot the dataset.

```python
>>> from gridai.plot_dataset import plot_dataset
>>> from torch_geometric.data import SQLiteDatabase
>>> db = SQLiteDatabase(path="dataset.sqlite",name="data_table")
>>> plot_dataset(db[0])
```