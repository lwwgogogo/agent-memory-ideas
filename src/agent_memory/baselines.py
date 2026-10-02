"""Causal filters: every output at t uses observations through t only."""
import numpy as np


def candidates():
    specs = [{"name": "last", "kind": "last"},
             {"name": "majority", "kind": "majority"}]
    for alpha in [0.05, 0.15, 0.35, 0.65]:
        specs.append(dict(name=f"ema_{alpha}", kind="ema", alpha=alpha))
    for decay in [0.5, 0.8, 0.95, 0.99]:
        specs.append(dict(name=f"recency_{decay}", kind="recency", decay=decay))
    for window in [5, 15, 51]:
        specs.append(dict(name=f"window_{window}", kind="window", window=window))
    specs.append(dict(name="raw_conflict", kind="conflict", low=0.05, high=0.65))
    for q, r in [(0.01, 0.1), (0.05, 0.2), (0.2, 0.35)]:
        specs.append(dict(name=f"bayes_{q}_{r}", kind="bayes", q=q, r=r))
    return specs


def predict(observations, spec):
    ys = np.asarray(observations)
    if ys.ndim != 1 or not np.isin(ys, [0, 1]).all():
        raise ValueError("Observations must be a binary vector")
    result = np.empty(len(ys), dtype=float)
    p, numerator, denominator = 0.5, 0.0, 0.0
    for t, y in enumerate(ys):
        kind = spec["kind"]
        if kind == "last":
            p = float(y)
        elif kind == "majority":
            numerator += y
            p = numerator / (t + 1)
        elif kind == "window":
            numerator += y
            if t >= spec["window"]:
                numerator -= ys[t - spec["window"]]
            p = numerator / min(t + 1, spec["window"])
        elif kind == "recency":
            numerator = spec["decay"] * numerator + y
            denominator = spec["decay"] * denominator + 1
            p = numerator / denominator
        elif kind in ("ema", "conflict"):
            alpha = spec.get("alpha", spec.get("low"))
            if kind == "conflict" and y != int(p >= 0.5):
                alpha = spec["high"]
            p = (1 - alpha) * p + alpha * y
        elif kind == "bayes":
            q, r = spec["q"], spec["r"]
            prior = q + (1 - 2 * q) * p
            l1, l0 = ((1 - r, r) if y else (r, 1 - r))
            evidence = prior * l1 + (1 - prior) * l0
            if evidence <= 0:
                raise ValueError("Observation has zero probability under filter")
            p = prior * l1 / evidence
        else:
            raise ValueError(f"Unknown baseline: {kind}")
        result[t] = p
    return result
