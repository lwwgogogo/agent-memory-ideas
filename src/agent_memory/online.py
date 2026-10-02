"""Exact Bayesian averaging over a fixed, discrete stationary Q/R prior."""
import numpy as np


def model_average(observations, q_grid, r_grid, prior_weights=None, forgetting=1.0):
    y = np.asarray(observations)
    if y.ndim != 1 or not np.isin(y, [0, 1]).all():
        raise ValueError("Expected binary observations")
    for grid in (q_grid, r_grid):
        if not len(grid) or len(set(grid)) != len(grid) or any(not 0 <= v <= .5 for v in grid):
            raise ValueError("Require nonempty unique grids in [0, .5]")
    q, r = np.array([(q, r) for q in q_grid for r in r_grid]).T
    p = np.full(len(q), .5)
    if not 0 < forgetting <= 1:
        raise ValueError("Forgetting must be in (0,1]")
    if prior_weights is None:
        log_w = np.full(len(q), -np.log(len(q)))
    else:
        weights = np.asarray(prior_weights, dtype=float)
        if weights.shape != q.shape or not np.isfinite(weights).all() or (weights <= 0).any():
            raise ValueError("Require positive finite prior per model")
        log_w = np.log(weights / weights.sum())
    log_prior = log_w.copy()
    result = np.empty(len(y))
    diagnostics = []
    for t, obs in enumerate(y):
        if forgetting != 1:
            # Heuristic discounting of model weights, not exact nonstationary Bayes.
            log_w = forgetting*log_w + (1-forgetting)*log_prior
            m = np.max(log_w)
            log_w -= m + np.log(np.exp(log_w-m).sum())
        prior = q + (1 - 2*q)*p
        l1, l0 = (1-r, r) if obs else (r, 1-r)
        likelihood = prior*l1 + (1-prior)*l0
        # Score each model BEFORE assimilating this observation into its state.
        with np.errstate(divide="ignore"):
            updated = log_w + np.log(likelihood)
        maximum = np.max(updated)
        if not np.isfinite(maximum):
            raise ValueError("Observation impossible under every supported model")
        normalizer = maximum + np.log(np.exp(updated-maximum).sum())
        log_w = updated-normalizer
        w = np.exp(log_w)
        p = np.divide(prior*l1, likelihood, out=np.full_like(p,.5), where=likelihood > 0)
        result[t] = w @ p
        diagnostics.append(dict(t=t, q_mean=float(w@q), r_mean=float(w@r),
                                effective_models=float(1/(w@w)),
                                predictive_nll=float(-normalizer)))
    return result, diagnostics
