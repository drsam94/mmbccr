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
    args = parser.parse_args()

    input = open(args.file, "rb")

    byteData = input.read()

    type = DataType[args.type]

    for i in range(type.getArrayLength()):
        obj = type.parse(byteData, i)
        print(f"{i}: {obj}")


if __name__ == "__main__":
    main()
