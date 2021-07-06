#!/usr/bin/python

import sys
import argparse
from megadata import *


def main():
    parser = argparse.ArgumentParser(
        "inspect", description="A tool to dump out parsed information from a ROM"
    )
    parser.add_argument("file", metavar="file", type=str)
    parser.add_argument("type", metavar="type", type=str)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    input = open(args.file, "rb")

    byteData = input.read()

    type = DataType[args.type]

    if args.verbose:
        PrintOpts.verbose = True
        PrintOpts.refdata = byteData

    for i in range(type.getArrayLength()):
        obj = type.parse(byteData, i)
        print(f"{i}: {obj}")


if __name__ == "__main__":
    main()
