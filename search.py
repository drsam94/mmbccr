#!/usr/bin/python

import sys
import argparse
from typing import List, Any, Dict
from megadata import DataType


def search(pattern: List[int], data: bytearray, args: Any) -> List[int]:
    stride: int = args.stride
    rooted: bool = args.rooted
    ind = 0
    patInd = 0
    dataLen = len(data)
    patLen = len(pattern)
    ret: List[int] = []
    varMap: Dict[int, int] = {}
    while ind < dataLen:
        isMatch = False
        if not args.delta and not args.variable:
            isMatch = data[ind] == pattern[patInd]
        elif args.delta:
            prev = data[ind - patInd * stride] if rooted else data[ind - stride]
            if patInd == 0:
                isMatch = not args.middleStart or (data[ind] != 0 and data[ind] != 255)
            elif pattern[patInd - 1] == 300:
                isMatch = True
            elif pattern[patInd - 1] == 400:
                isMatch = prev != data[ind]
            else:
                isMatch = data[ind] == prev + pattern[patInd - 1]
        elif args.variable:
            if patInd == 0:
                varMap = {}
            if data[ind] in varMap:
                isMatch = varMap[data[ind]] == pattern[patInd]
            elif pattern[patInd] == 0:
                isMatch = True
            elif pattern[patInd] in varMap.values():
                isMatch = False
            else:
                isMatch = True
                varMap[data[ind]] = pattern[patInd]
        if isMatch:
            if patInd == patLen - (0 if args.delta else 1):
                ret.append(ind - patInd * args.stride)
                patInd = 0
            else:
                patInd += 1
            ind += stride
            continue
        elif patInd > 0:
            ind -= patInd
            patInd = 0
        ind += 1
    return ret


def isBN2Mapped(loc: int):
    """
    Returns true if the data is already known in BN2 mapping
    TODO: incorporate variable size regions
    """
    for type in [
        DataType.Chip_BN2,
        DataType.Virus_BN2,
        DataType.EncounterEVT_BN2,
        DataType.EncounterRegion_BN2,
        DataType.ShopInventory_BN2,
        DataType.ChipFolder_BN2,
    ]:
        base = type.getOffset()
        end = base + type.getArrayLength() * type.getSize()
        if loc >= base and loc <= end:
            return True
    return False


def printRes(res: List[int], args: Any):
    prev = 0
    for loc in res:
        delta = loc - prev
        if args.maxDelta == 0 or delta < args.maxDelta:
            if args.skipMapped and isBN2Mapped(loc):
                continue
            print(hex(loc))
            if args.printDelta:
                print(loc - prev)
        prev = loc


def main():
    parser = argparse.ArgumentParser(
        "search", description="A utility to find patterns in the source ROM"
    )
    parser.add_argument("--stride", metavar="stride", type=int, default=1)
    parser.add_argument("--delta", action="store_true")
    parser.add_argument("--rooted", action="store_true")
    parser.add_argument("--middleStart", action="store_true")
    parser.add_argument("--variable", action="store_true")
    parser.add_argument("--hex", action="store_true")
    parser.add_argument("--printDelta", action="store_true")
    parser.add_argument("--maxDelta", metavar="maxDelta", type=int, default=0)
    parser.add_argument("--skipMapped", action="store_true")
    parser.add_argument("file", metavar="file", type=str)
    parser.add_argument("pattern", metavar="code", type=str, nargs="+")
    args = parser.parse_args()

    input = open(args.file, "rb")

    byteData = input.read()

    base = 16 if args.hex else 10
    args.pattern = [int(x, base) for x in args.pattern]
    if args.stride == -1:
        args.stride = 1
        while args.stride < 64:
            print(args.stride)
            res = search(args.pattern, byteData, args)
            if len(res) > 0:
                printRes(res, args)
            args.stride += 1
    else:
        res = search(args.pattern, byteData, args)
    printRes(res, args)


if __name__ == "__main__":
    main()
