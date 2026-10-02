"""Binary hidden Markov environment. Truth is reserved for evaluation."""
import numpy as np


def generate(q, r, steps, seed):
    if not 0 <= q <= 0.5 or not 0 <= r <= 0.5 or steps < 2:
        raise ValueError("Require q,r in [0,0.5] and steps >= 2")
    # Separate streams and common random numbers across grid cells/methods.
    state_rng, noise_rng = [np.random.default_rng(s) for s in
                            np.random.SeedSequence(seed).spawn(2)]
    changes = state_rng.random(steps) < q
    changes[0] = False
    initial = int(state_rng.integers(2))
    truth = np.bitwise_xor(np.cumsum(changes) % 2, initial).astype(int)
    noisy = noise_rng.random(steps) < r
    return truth, np.bitwise_xor(truth, noisy).astype(int)
