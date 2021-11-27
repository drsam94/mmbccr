#!/usr/bin/python

from megadata import *
from bccdata import Element
from distribution import getValWithVar, getPoissonRandom
import configparser
import random
from typing import Callable


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
                newVal = getValWithVar(getattr(obj, key), float(val), floorVal)
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
    mbMap = Library.getMBMap(data)
    chipMap = Library.getChipMap(data)
    type = DataType.Encounter
    shuffledEncs = list(range(type.getArrayLength()))
    doAtkFilter = choices.getboolean("smartAtkPlus")
    randomOp = choices.getboolean("randomizeOperators")
    fillChips = choices.getboolean("fillChips")
    randomizeNavi = choices.getboolean("randomizeNavi")
    poissonParam = choices.getfloat("upgradeChipParam", 0)
    if choices.getboolean("shuffle"):
        random.shuffle(shuffledEncs)
    writeEncs = []

    def randomizeChipList(chipArr: List[int], rejectCB: Callable[[int], bool]):
        for j, chip in enumerate(chipArr):
            if chip == 0:
                if not fillChips:
                    continue
                sourceMb = 0
            else:
                sourceMb = chipMap[chip - 1].mb

            sourceMb = max(10, sourceMb + 10 * getPoissonRandom(poissonParam))
            origSouceMb = sourceMb
            myMap: List[int] = []
            while len(myMap) == 0 and sourceMb > 0:
                if sourceMb in mbMap:
                    myMap = mbMap[sourceMb]
                sourceMb -= 10
            if len(myMap) == 0:
                chipArr[j] = 0
            else:
                while True:
                    chipArr[j] = 1 + random.choice(myMap)
                    if not rejectCB(j):
                        break

    if config["ChipGlobal"].getboolean("randomizeStartingChips", fallback=True):
        startingChips = DataType.StartingChips.parse(data, 0)
        assert isinstance(startingChips, StartingChipsT)
        randomizeChipList(startingChips.chips, lambda x: False)
        DataType.StartingChips.rewrite(data, 0, startingChips)

    for i in range(type.getArrayLength()):
        i = shuffledEncs[i]
        enc = type.parse(data, i)
        assert isinstance(enc, EncounterT)
        if randomOp:
            enc.op = random.randint(0, 125)
        filterCB = lambda ind: doAtkFilter and hasBadAtkBooster(chipMap, enc, ind)
        randomizeChipList(enc.chips, filterCB)
        if randomizeNavi:
            enc.navi = random.choice(list(Library.naviChipRange()))

        if choices.getboolean("randomizeChips"):
            writeEncs.append(enc)
    for i, enc in enumerate(writeEncs):
        type.rewrite(data, i, enc)
