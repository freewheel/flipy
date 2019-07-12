---
layout: default
title: Home
nav_order: 1
description: "Flippy is a linear programming interface for Python built by FreeWheel."
permalink: /
---

# Flippy
{: .fs-9 }

<img src="{{site.baseurl}}/assets/images/flippy.png">

FreeWheel Linear Programming Interface for Python
{: .fs-5 .fw-300 }

[Get started now](#getting-started){: .btn .btn-blue .fs-5 .mb-4 .mb-md-0 .mr-2 } [View it on GitHub](https://github.freewheel.tv/linear/flippy/){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## Getting started

### Dependencies

Flippy is an integer and linear programming interface. It currently supports [Gurobi](https://www.gurobi.com/) and [CBC](https://github.com/coin-or/Cbc) as the backend solver.

To use CBC, follow the CBC documentation [here](https://github.com/coin-or/Cbc#building-from-source) and make sure the command `cbc` is available on your machine.

To use Gurobi, make sure you have a Gurobi license file, and `gurobipy` is installed in your Python environment. You can find details from [Gurobi's documentation](https://www.gurobi.com/documentation/8.1/quickstart_mac/the_gurobi_python_interfac.html).

Flippy requires Python 3.6 or newer.

## Installation

Flippy can be installed with `setuptools`

```bash
$ git clone https://github.freewheel.tv/linear/flippy
$ cd flippy
$ python setup.py install
```

## About the project

Flippy is &copy; 2019 by [FreeWheel](http://freewheel.com) Algo team.
