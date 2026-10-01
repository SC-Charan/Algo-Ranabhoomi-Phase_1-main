"""Bench config for Relief Loading."""

import _paths  # noqa: F401

import data
import validator
from benchkit import BenchConfig


BENCH = BenchConfig(
    name="relief",
    bench_dir=_paths.BENCH_DIR,
    data=data,
    validate=validator.validate,
    shift_markers=lambda p: "anti-correlated, near-perfect" if p["shifted"] else "",
)
