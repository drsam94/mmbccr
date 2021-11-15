#!/usr/bin/python

import sys
import argparse
from megadata import *
from bn2data import BN2Char, EncounterT_BN2, VirusT_BN2, NameMaps


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

    if type in [
        DataType.EncounterEVT_BN2,
        DataType.EncounterRegion_BN2,
        DataType.ShopInventory_BN2,
        DataType.ChipFolder_BN2,
        DataType.DropTable_BN2,
    ]:
        populateBN2Meta(byteData)

    offset = type.getOffset()
    for i in range(type.getArrayLength()):
        if type.isVarLengthString():
            toStrClass = (
                EncounterT_BN2
                if type in [DataType.EncounterRegion_BN2, DataType.EncounterEVT_BN2]
                else BN2Char
            )
            out, offset = toStrClass.toString(byteData, offset)
        else:
            out = type.parseAtOffset(byteData, offset)
            offset += type.getSize(out)
        print(f"{i}: {out}")
        if PrintOpts.verbose:
            print(hex(offset))


if __name__ == "__main__":
    main()
