# not a "real" distribution, the discretization and clamping skew it
def truncated_discrete_distribution(mean, stddev, minimum = None, maximum = None):
    import random

    # rejection sampling: retry until a value lands within the bounds.
    # the attempt cap turns impossible/near-impossible bounds into an error
    # instead of an infinite loop; each attempt consumes exactly one
    # random.gauss call, the same as the previous recursive implementation
    MAX_ATTEMPTS = 10000
    for _ in range(MAX_ATTEMPTS):
        result = round(random.gauss(mean, stddev))
        if minimum and result < minimum:
            continue
        if maximum and result > maximum:
            continue
        return result
    raise ValueError(f"truncated_discrete_distribution: no value within "
                     f"[{minimum}, {maximum}] after {MAX_ATTEMPTS} attempts "
                     f"(mean {mean}, stddev {stddev})")
