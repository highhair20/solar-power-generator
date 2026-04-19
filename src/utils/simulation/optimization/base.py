"""
Shared NSGA-II optimization infrastructure.

Provides run_nsga2() and decode_design_vector() used by all subsystem
optimizers (Stirling, collector, thermal storage).

Each subsystem defines its own:
  - Physics model (analysis.py) with evaluate(params) -> dict
  - DESIGN_VARS list of (key, lo, hi, description) tuples
  - pymoo Problem subclass wrapping evaluate()
  - extract_designs() and print_designs() with subsystem-specific columns

This module provides only the shared algorithm configuration and the
design-vector decode utility. No physics here.
"""

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.lhs import LHS
from pymoo.optimize import minimize as pymoo_minimize
from pymoo.termination import get_termination


def run_nsga2(problem, pop_size=120, n_gen=100, seed=42, verbose=True):
    """Configure and run NSGA-II on a pymoo Problem.

    Uses Latin Hypercube Sampling for the initial population, SBX crossover,
    and polynomial mutation — the same configuration across all subsystem
    optimizers for consistent comparison.

    Args:
        problem: pymoo Problem subclass with _evaluate() defined
        pop_size: individuals per generation [int]
        n_gen: number of generations [int]
        seed: random seed for reproducibility [int]
        verbose: print per-generation progress [bool]

    Returns:
        pymoo Result with .X (design variables), .F (objectives),
        .G (constraint violations). result.F is None if no feasible
        solutions were found.
    """
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=LHS(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True,
    )
    termination = get_termination("n_gen", n_gen)

    if verbose:
        print(f"Running NSGA-II: {pop_size} pop × {n_gen} gen "
              f"({pop_size * n_gen:,} evaluations)")
        print(f"  {problem.n_var} design variables, "
              f"{problem.n_obj} objectives, "
              f"{problem.n_ieq_constr} constraints")
        print()

    return pymoo_minimize(
        problem,
        algorithm,
        termination,
        seed=seed,
        verbose=verbose,
    )


def decode_design_vector(X_row, design_vars, int_keys=None):
    """Decode a raw design vector (numpy row) into a named parameter dict.

    Args:
        X_row: 1-D numpy array — one individual's design variable values
        design_vars: list of (key, lo, hi, description) tuples, same order as X
        int_keys: collection of keys that must be rounded to integers

    Returns:
        dict mapping each parameter key to its decoded value
    """
    int_keys = set(int_keys or [])
    params = {}
    for j, (key, _lo, _hi, _desc) in enumerate(design_vars):
        val = float(X_row[j])
        if key in int_keys:
            val = round(val)
        params[key] = val
    return params
