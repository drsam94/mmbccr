#!/usr/bin/python

import math
import random
import argparse
from typing import Dict

"""
This file exports library functions for drawing random numbers,
and also allows running manual trials to validate how the draws go
"""


def getValWithVar(num: int, var: float, floorVal: int) -> int:
    """
    Returns a uniform number in a range bounded by var% of the base num
    """
    if num == 0:
        return 0
    var = num * (var / 100)
    low = round(max(10 + floorVal, num - var))
    high = round(min(2 ** 16, num + var))
    if low > high:
        return round(low, -1)

    return round(random.randint(low, high), -1)


def getPoissonRandom(param: float) -> int:
    """
    Returns an integer value from a poisson distribution of the
    given param
    """
    prob = random.random()
    # Use the CDF to determine what int to draw from the distribution
    i = 0
    cdf: float = 0.0
    while cdf < prob:
        cdf += (math.e ** -param) * (param ** i) / math.factorial(i)
        i += 1
    return i - 1


def main():
    parser = argparse.ArgumentParser(
        "distribution", description="print a histogram of draws from a distribution"
    )
    parser.add_argument("type", metavar="type", type=str)
    parser.add_argument("-n", "--numtrials", type=int)
    parser.add_argument("-p", "--param", type=float)
    args = parser.parse_args()

    histogram: Dict[int, int] = {}

    if args.type == "poisson":
        randFn = lambda: getPoissonRandom(args.param)
    elif args.type == "uniform":
        randFn = lambda: getValWithVar(100, args.param, 0)
    else:
        raise Exception("No function type provided")

    for _ in range(args.numtrials):
        val = randFn()
        if val not in histogram:
            histogram[val] = 0
        histogram[val] += 1

    for key in sorted(histogram.keys()):
        print(f"{key}: {histogram[key]}")


if __name__ == "__main__":
    main()
