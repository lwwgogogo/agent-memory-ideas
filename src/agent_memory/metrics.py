"""Operational state-tracking proxies, not retrieval-level measurements."""
import numpy as np


def evaluate(truth, observations, belief, burn_in):
    x, y, p = map(np.asarray, (truth, observations, belief))
    if not (len(x) == len(y) == len(p)) or not 1 <= burn_in < len(x):
        raise ValueError("Aligned trajectories and 1 <= burn_in < steps required")
    pred = (p >= 0.5).astype(int)  # Same tie rule for all methods.
    t = np.arange(burn_in, len(x))
    stable = x[t] == x[t - 1]
    noise = stable & (y[t] != x[t])
    eligible = noise & (pred[t - 1] == x[t])
    false_update = eligible & (pred[t] != x[t])
    changes = np.flatnonzero(x[1:] != x[:-1]) + 1
    delays, censored, stale_errors, stale_steps = [], 0, 0, 0
    for i, start in enumerate(changes):
        if start < burn_in:
            continue
        end = int(changes[i + 1]) if i + 1 < len(changes) else len(x)
        matches = np.flatnonzero(pred[start:end] == x[start])
        # No recovery before next change/end: capped at segment length, flagged.
        delays.append(int(matches[0]) if len(matches) else end - start)
        censored += int(not len(matches))
        stale_errors += int(np.sum(pred[start:end] == x[start - 1]))
        stale_steps += end - start

    def ratio(n, d):
        return float(n / d) if d else None

    return {
        "accuracy": float(np.mean(pred[t] == x[t])),
        "brier": float(np.mean((p[t] - x[t]) ** 2)),
        "false_update_rate": ratio(int(false_update.sum()), int(eligible.sum())),
        "false_update_events": int(false_update.sum()),
        "false_update_opportunities": int(eligible.sum()),
        "noise_overreaction": float(np.mean(np.abs(p[t][noise] - p[t-1][noise]))) if noise.any() else None,
        "adaptation_delay_capped": float(np.mean(delays)) if delays else None,
        "adaptation_censored_rate": ratio(censored, len(delays)),
        "change_events": len(delays),
        "stale_reuse_proxy": ratio(stale_errors, stale_steps),
        "stale_error_steps": stale_errors,
        "post_change_steps": stale_steps,
    }
