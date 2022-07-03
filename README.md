# CS 513 Data Cleaning - Team 152

## Setup

### Prerequisites

* [OpenRefine == 3.4.1](https://github.com/OpenRefine/OpenRefine/releases/tag/3.4.1)
* [YesWorkflow](https://github.com/yesworkflow-org/yw-prototypes) (including [GraphViz](https://github.com/yesworkflow-org/yw-prototypes#2--install-graphviz-visualization-software))
* [OR2YWTool](https://github.com/LanLi2017/OR2YWTool) (also included via `requirements.txt`)
* [SQLite >= 3.38](https://www.sqlite.org/index.html) (or `brew install sqlite`)

### Requirements

```sh
python -m venv env
env/bin/pip install -r requirements.txt
```

## Workflow

### Overview

Generate with `dot -Tpng overview.gv > overview.png`.

![Overview](overview.png)

### Partition Dataset
> **TODO:** Sub-workflow documention

### Clean Locations
> **TODO:** Sub-workflow documention

### Clean Inspections
> **TODO:** Sub-workflow documention

### Clean Violations

> **NOTE:** This sub-workflow is from a prototype, and is acting as a placeholder. Naming convention and generation instructions will be updated with the new implementation.

Generate as follows:

```bash
or2yw -i violations.json -o violations.yw
yw graph -c extract.comment='#' -c graph.layout=TB violations.yw > violations.gv
# work around defects in tooling
sed -i "s/{{<f0> \"/{{<f0> \'/g" violations.gv
sed -i "s/\" |<f1>/\' |<f1>/g" violations.gv
dot -Tpng violations.gv > violations.png
```

![Violations](violations.png)

### Repair Locations

> **NOTE:** This sub-workflow is from a prototype, and is acting as a placeholder. Naming convention and generation instructions will be updated with the new implementation.

```bash
yw graph -c extract.comment='#' geocode.py > geocode.gv
dot -Tpng geocode.gv > geocode.png
```

![Geocode](geocode.png)

### Normalize
> **TODO:** Sub-workflow documention

### Visualize
> **TODO:** Documentation of queries specific to use case 1 (U1)
