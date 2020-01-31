---
layout: default
title: Installation
nav_order: 1
---

# Installation
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Python Version

Flipy suports Python 3.6 and newer.

## Dependencies

Flipy does not require any third party packages. However, to solve a linear programming problem, a linear solver is required.

Flipy currently supports [Gurobi](https://www.gurobi.com/) and [CBC](https://github.com/coin-or/Cbc) as the backend solver.

1. CBC:
   Flipy comes with a CBC solver so you don't have to do anything. However, if you want to user a different version of CBC, please set the environment variable `CBC_SOLVER_BIN` to the designated CBC solver executable.
2. Gurobi:
    To use Gurobi, make sure you have a valid Gurobi license file, and `gurobipy` is installed in your Python environment. You can find details from [Gurobi's documentation](https://www.gurobi.com/documentation/8.1/quickstart_mac/the_gurobi_python_interfac.html).

## Installation

The latest offical version of Flipy can be installed with pip:

```bash
pip install flipy
```

The latest development version can be get with Git.

```bash
git clone https://github.com/freewheel/flipy.git
cd flipy
python setup.py install
```