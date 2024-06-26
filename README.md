# PolyFLAME

[![](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![tests](https://github.com/globaldothealth/polyflame/actions/workflows/tests.yml/badge.svg)](https://github.com/globaldothealth/polyflame/actions/workflows/tests.yml)
[![docs](https://readthedocs.org/projects/polyflame/badge/)](https://polyflame.readthedocs.io)
[![codecov](https://codecov.io/gh/globaldothealth/polyflame/graph/badge.svg)](https://codecov.io/gh/globaldothealth/polyflame)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Polymorphic FLexible Analytics and Modelling Engine

This package is part of the Global.health-ISARIC pipeline.

## Context and Problem

Data processing and transformation (ETL) is done by the
[FHIRflat](https://fhirflat.readthedocs.io) library. Once input data is brought
into FHIRflat, it is represented as a (optionally zipped) folder of FHIR
resources, with a parquet file corresponding to each resource:
`patient.parquet`, `encounter.parquet` and so on.

Once the data is in FHIRflat, we need a easy to use library that can be used by
itself, and as a building block for visualizations such as
[VERTEX](https://vertex-isaric.replit.app).

**Output**: A easy to use library that can be used in Jupyter notebooks and
other downstream code to allow querying answers to [common research
questions](../1.01_ISARIC3/README.md#research-questions) in
a reproducible analytical pipeline (RAP).

**Non-goals**: Allow answering arbitrary questions. FHIRflat uses open formats
(parquet) that users can query directly using tools such as pandas or the R
[{arrow}](https://arrow.apache.org/docs/1.0/r/) package, and FHIRFLAME allows
flexibility in dataframe type as long as the dataframe schema required patterns
for plot types (e.g. age pyramid plot should have a numeric age column).

## Installing

You can install PolyFLAME from GitHub

```shell
pip install git+https://github.com/globaldothealth/polyflame
```

## Documentation

Detailed documentation and an API reference is at
https://polyflame.readthedocs.io
