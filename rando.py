#!/usr/bin/python

import sys
import argparse
import configparser
import random
from typing import Optional, Callable
from enum import Enum


class Game(Enum):
    BCC = 1
    BN2 = 2


def identifyGame(byteData: bytearray) -> Game:
    header = byteData[0xA0:0xB0]
    if header == b"BATTLECHIPGPA89E":
        return Game.BCC
    elif header == b"MEGAMAN_EXE2AE2E":
        return Game.BN2
    raise Exception(f"Detected no valid game, found header {header}")


def randomize(
    byteData: bytearray, config: configparser.ConfigParser, seed: Optional[int]
) -> int:
    if not seed:
        seed = random.randint(0, 2 ** 64)
    random.seed(seed)
    print(f"Randomizing with seed {seed}")
    game = identifyGame(byteData)
    print(f"Randomizing {game}")
    if game == Game.BCC:
        import rando_bcc

        rando_bcc.randomizeChips(byteData, config)
        rando_bcc.randomizeEncounters(byteData, config)
        rando_bcc.randomizeNames(byteData, config)
    elif game == Game.BN2:
        import rando_bn2
        import megadata

        megadata.populateBN2Meta(byteData)
        rando_bn2.randomizeChips(byteData, config)
        # Regenerate meta based on the updated chip data
        megadata.populateBN2Meta(byteData)
        rando_bn2.randomizeEncounters(byteData, config)
        rando_bn2.randomizeShops(byteData, config)
        rando_bn2.randomizeFolders(byteData, config)
        rando_bn2.randomizeDropTables(byteData, config)
        rando_bn2.randomizeGMD(byteData, config)
    return seed


def main():
    parser = argparse.ArgumentParser(
        "rando", description="A randomizer for Megaman Battlechip Challenge"
    )
    parser.add_argument("--conf", "-f", metavar="conffile", type=str, default="")
    parser.add_argument("--seed", "-s", metavar="seed", type=int, default=None)
    parser.add_argument("infile", metavar="infile", type=str)
    parser.add_argument("outfile", metavar="outfile", type=str)
    args = parser.parse_args()
    input = open(args.infile, "rb")

    byteData = bytearray(input.read())
    game = identifyGame(byteData)
    if not args.conf:
        args.conf = "rando_bcc.conf" if game == Game.BCC else "rando_bn2.conf"

    config = configparser.ConfigParser()
    config.read(args.conf)

    randomize(byteData, config, args.seed)
    outFile = open(args.outfile, "wb+")
    outFile.write(byteData)


if __name__ == "__main__":
    main()
