"""Small statistics for evaluations (Chapter 13: how sure is the number?).

No dependencies. Every function works on plain counts, so a lab can report a
range next to every rate without a statistics library.

    wilson(57, 60)              -> (0.863, 0.983)   95% range for 57 right out of 60
    pass_at_k(2, 3, 3)          -> 1.0              right at least once in 3 runs
    pass_hat_k(2, 3, 3)         -> 0.0              right every time in 3 runs
    t_interval([0.9, 0.95, 0.92]) -> (mean, low, high) across repeated runs
    mcnemar(5, 2)               -> 0.453            p-value: new version fixed 5, broke 2
    disagreement([3, 2, 0], 3)  -> 0.222            how often verdicts flip between runs
"""

from __future__ import annotations

from math import comb, sqrt

# Two-sided 95% t values for 1..30 degrees of freedom; above 30 the normal value is close enough.
_T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145, 2.131,
        2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson interval for a rate. Behaves well for small samples and for rates near 0 or 1."""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3))


def pass_at_k(c: int, n: int, k: int) -> float:
    """Chance that at least one of k runs passes, given c passes in n runs of one case."""
    if n - c < k:
        return 1.0
    return 1 - comb(n - c, k) / comb(n, k)


def pass_hat_k(c: int, n: int, k: int) -> float:
    """Chance that all k runs pass, given c passes in n runs of one case (pass^k)."""
    return comb(c, k) / comb(n, k) if c >= k else 0.0


def mean_pass(cases: list[tuple[int, int]], k: int, every_time: bool) -> float:
    """pass@k (every_time=False) or pass^k (every_time=True), averaged over cases given as (passes, runs)."""
    if not cases:
        return 1.0
    f = pass_hat_k if every_time else pass_at_k
    return round(sum(f(c, n, k) for c, n in cases) / len(cases), 4)


def t_interval(values: list[float]) -> tuple[float, float, float]:
    """Mean and 95% Student's t interval across repeated runs (each run is one observation)."""
    k = len(values)
    mean = sum(values) / k if k else 0.0
    if k < 2:
        return (round(mean, 4), round(mean, 4), round(mean, 4))
    sd = sqrt(sum((v - mean) ** 2 for v in values) / (k - 1))
    t = _T95[k - 2] if k - 1 <= len(_T95) else 1.96
    half = t * sd / sqrt(k)
    return (round(mean, 4), round(mean - half, 4), round(mean + half, 4))


def mcnemar(only_new_right: int, only_old_right: int) -> float:
    """Exact two-sided p-value for two versions scored on the same cases.

    Only the cases where they differ count: the new version right and the old wrong, and the reverse.
    A large p-value (say above 0.05) means the difference could easily be chance: call it inconclusive.
    """
    n = only_new_right + only_old_right
    if n == 0:
        return 1.0
    low = min(only_new_right, only_old_right)
    tail = sum(comb(n, i) for i in range(low + 1)) / 2 ** n
    return round(min(1.0, 2 * tail), 4)


def disagreement(passes: list[int], runs: int) -> float:
    """Average chance that two runs of the same case disagree (0 = always the same verdict)."""
    if runs < 2 or not passes:
        return 0.0
    return round(sum(2 * s * (runs - s) / (runs * (runs - 1)) for s in passes) / len(passes), 4)


def flip_rate(verdicts: list[list[str]]) -> float:
    """Share of cases whose verdict was not the same in every run."""
    if not verdicts:
        return 0.0
    return round(sum(len(set(v)) > 1 for v in verdicts) / len(verdicts), 4)
