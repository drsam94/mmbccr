#!/usr/bin/python

import sys
import argparse
from megadata import *
from textwrap import wrap


def main():
    parser = argparse.ArgumentParser(
        "strconv", description="convert a string to/from mm format"
    )
    parser.add_argument("action", metavar="action", type=str)
    parser.add_argument("text", metavar="text", type=str)
    args = parser.parse_args()

    if args.action == "encode":
        print("".join("%04x " % MMChar.convTo(c) for c in args.text))
    else:
        print("".join(MMChar.convFrom(int(c, 16)) for c in wrap(args.text, 4)))


if __name__ == "__main__":
    main()
