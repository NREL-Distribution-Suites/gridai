# Welcome to Graph Dataset Repo

[View full docs here](https://pages.github.nrel.gov/GATES-TLDRD/graph-dataset/)

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

## How to create a dataset ?

The command `generate-dataset` can convert all opendss models available in the parent folder by recursively searching for all valid opendss models.

```
graphd generate-dataset -f <parent-path>
```

This will create a sqlite db file stroing all training data in `pytorch.data.Data` format.

## How to create stats for dataset ?

The command `generate-stats` can be used to generate stats for dataset.
```
graphd generate-stats -f "dataset.sqlite" -o "dataset_stat.csv"
```


## How to use the dataset ?

```python
>>> from torch_geometric.data import SQLiteDatabase
>>> db = SQLiteDatabase(path="dataset.sqlite",name="data_table")
>>> len(db)
51
>>> db[0]
Data(x=[104750, 8], edge_index=[2, 104742], edge_attr=[104742, 8])
```

## Getting NodeObject and EdgeObject

You can use following snippet to convert node attributes back to an instance of 
`DistNodeAttrs` and edge attributes back to an `DistEdgeAttrs`.

```python
>>> from torch_geometric.data import SQLiteDatabase
>>> from graph_dataset.interfaces import DistNodeAttrs, DistEdgeAttrs
>>> from rich import print
>>> db = SQLiteDatabase(path="dataset.sqlite",name="data_table")
>>> print(DistNodeAttrs.from_array(db.x[0]))
>>> print(DistEdgeAttrs.from_array(db.edge_attr[0]))
DistNodeAttrs(
    node_type=<NodeType.SOURCE: 1>,
    active_demand_kw=0.0,
    reactive_demand_kw=0.0,
    active_generation_kw=0.0,
    reactive_generation_kw=0.0,
    phase_type=<PhaseType.A: 2>,
    kv_level=7.199557781219482
)
DistEdgeAttrs(
    num_phase=<NumPhase.ONE: 1>,
    capacity_kva=10.0,
    edge_type=<DistEdgeType.TRANSFORMER: 1>,
    length_miles=0.0,
    r0=0.0,
    r1=0.8321009874343872,
    x0=0.0,
    x1=1.0800000429153442
)
```


## Plotting the dataset

You can use following command to plot the dataset.

```python
>>> from graph_dataset.plot_dataset import plot_dataset
>>> from torch_geometric.data import SQLiteDatabase
>>> db = SQLiteDatabase(path="dataset.sqlite",name="data_table")
>>> plot_dataset(db[0])
```