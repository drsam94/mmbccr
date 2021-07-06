#!/usr/bin/python

import sys
import argparse
from megadata import *
import configparser
import random
import itertools


def getValWithVar(num: int, var: float, floorVal: int) -> int:
    if num == 0:
        return 0
    var = num * (var / 100)
    low = round(max(10 + floorVal, num - var))
    high = round(min(2 ** 16, num + var))
    return round(random.randint(low, high), -1)


def randomizeChips(data: bytearray, config: configparser.ConfigParser):
    type = DataType.Chip
    for variance, R in (
        (config["ChipRange"], Library.standardChipRange()),
        (config["NaviRange"], Library.naviChipRange()),
    ):
        for i in R:
            obj = type.parse(data, i)
            weakerInd = 0
            if config["ChipGlobal"]["preserveOrdering"]:
                # Preserve the relative power of chips
                weakerInd = Library.getWeakerChip(i + 1)
            for key, _val in variance.items():
                val = int(_val)
                if val == 0:
                    # variance of 0, continue
                    continue
                floorVal = (
                    getattr(type.parse(data, weakerInd - 1), key)
                    if weakerInd != 0
                    else 0
                )
                newVal = getValWithVar(getattr(obj, key), val, floorVal)
                setattr(obj, key, newVal)
                type.rewrite(data, i, obj)

                if key == "ap" and newVal != 0:
                    # Update the descriptions to agree with the new values
                    # we have set

                    for desc in [DataType.EffectDesc, DataType.ChipDesc]:
                        ind = i + (1 if desc == DataType.ChipDesc else 0)
                        descObj = desc.parse(data, ind)
                        assert isinstance(descObj, StringT)
                        descObj.changeAttackPower(newVal)
                        desc.rewrite(data, ind, descObj)


def randomizeNames(data: bytearray, config: configparser.ConfigParser):
    nameConf = config["Names"]
    if not nameConf.getboolean("randomizeNames"):
        return

    nameFile = open(nameConf["chipNames"])
    randoNames = [name.strip() for name in nameFile.readlines()]
    type = DataType.ChipName
    for i in Library.standardChipRange():
        obj = type.parse(data, i)
        assert isinstance(obj, StringT)
        obj.assign(random.choice(randoNames))
        type.rewrite(data, i, obj)


def isBoostable(booster: ChipT, boosted: ChipT) -> bool:
    if boosted.ap == 0:
        return False
    elif booster.getElement() == Element.Normal:
        return True
    else:
        return booster.getElement() == boosted.getElement()


def hasBadAtkBooster(chipMap, enc: EncounterT, j: int) -> bool:
    """
    Returns True iff index j in this encounter contains a chp that enhances
    a next attack which has no followup attack to run after it
    """
    chipDetails = chipMap[enc.chips[j] - 1]
    chipPlusRange = range(0, 5)
    naviPlusRange = range(5, 10)

    if chipDetails.isChipPlus() and not j in chipPlusRange:
        return True
    elif chipDetails.isNaviPlus() and not j in naviPlusRange:
        return True
    elif chipDetails.isChipPlus() and j in chipPlusRange:
        colLen = 2 if j < 2 else 3
        nextChips = (j + colLen, j + colLen + 1)
        boostedChips = []
        for idx in nextChips:
            if enc.chips[idx] != 0:
                boostedChips.append(chipMap[enc.chips[idx] - 1])
        return not any(isBoostable(chipDetails, tgtChip) for tgtChip in boostedChips)

    return False


def randomizeEncounters(data: bytearray, config: configparser.ConfigParser):
    choices = config["Encounters"]
    if not choices.getboolean("randomizeChips"):
        return
    doAtkFilter = choices.getboolean("smartAtkPlus")
    mbMap = Library.getMBMap(data)
    chipMap = Library.getChipMap(data)
    type = DataType.Encounter
    shuffledEncs = list(range(type.getArrayLength()))
    if choices.getboolean("shuffle"):
        random.shuffle(shuffledEncs)
    writeEncs = []
    for i in range(type.getArrayLength()):
        i = shuffledEncs[i]
        enc = type.parse(data, i)
        assert isinstance(enc, EncounterT)
        if choices.getboolean("randomizeOperators"):
            enc.op = random.randint(0, 125)
        for j, chip in enumerate(enc.chips):
            sourceMb = 0
            if chip == 0:
                if choices.getboolean("fillChips"):
                    sourceMb = 10
                else:
                    continue
            else:
                sourceMb = chipMap[chip - 1].mb
            while True:
                enc.chips[j] = 1 + random.choice(mbMap[sourceMb])
                if not (doAtkFilter and hasBadAtkBooster(chipMap, enc, j)):
                    break
        if choices.getboolean("randomizeNavi"):
            enc.navi = random.choice(list(Library.naviChipRange()))
        writeEncs.append(enc)
    for i, enc in enumerate(writeEncs):
        type.rewrite(data, i, enc)


def main():
    parser = argparse.ArgumentParser(
        "rando", description="A randomizer for Megaman Battlechip Challenge"
    )
    parser.add_argument(
        "--conf", "-f", metavar="conffile", type=str, default="rando.conf"
    )
    parser.add_argument("--seed", "-s", metavar="seed", type=int, default=None)
    parser.add_argument("infile", metavar="infile", type=str)
    parser.add_argument("outfile", metavar="outfile", type=str)
    args = parser.parse_args()

    config = configparser.ConfigParser()
    if args.conf:
        config.read(args.conf)
    if not args.seed:
        args.seed = random.randint(0, 2 ** 64)
    random.seed(args.seed)
    print(f"Randomizing with seed {args.seed}")
    input = open(args.infile, "rb")

    byteData = bytearray(input.read())

    if byteData[0xA0:0xB0] != b"BATTLECHIPGPA89E":
        raise Exception(
            "It appears you are trying to run on a non-Battle Chip Challenge ROM"
        )
    randomizeChips(byteData, config)
    randomizeEncounters(byteData, config)
    randomizeNames(byteData, config)
    outFile = open(args.outfile, "wb+")
    outFile.write(byteData)


if __name__ == "__main__":
    main()
