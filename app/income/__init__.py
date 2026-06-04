"""Pure, deterministic qualifying-income calc engine (income-engine-spec.md).

Everything that does income math lives in this package. No file, DB, or network
access here — extraction populates the input models and calls these functions.
"""
