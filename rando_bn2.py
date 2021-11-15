from typing import List, cast, Callable, Any
import configparser
import random
from megadata import DataType, DataTypeVar
from bn2data import (
    ShopInventory,
    EncounterT_BN2,
    VirusCategory,
    NameMaps,
    ChipT_BN2,
    ChipFolder,
)
from distribution import getValWithVar, getPoissonRandom


def getRandomCode(ind: int, config: configparser.SectionProxy) -> int:
    starChance = config.getint("StarPercent", 20)
    rand = random.randint(0, 99)
    if rand < starChance:
        return 0x1A
    choices = NameMaps.getValidCodes(ind)
    if len(choices) == 1:
        return 0x1A
    else:
        return random.choice(choices[:-1])


def getValidCode(ind: int, code: int) -> int:
    validCodes = NameMaps.getValidCodes(ind)
    if code in validCodes:
        return code
    else:
        return random.choice(validCodes[:-1])


def randomizeEncounter(
    encounter: EncounterT_BN2, config: configparser.SectionProxy, type: DataType
):
    if encounter.isNaviBattle() and not config.getboolean("RandomizeNavis"):
        return

    # We should look into changing positions, but that does require knowledge
    # of the field
    for entity in encounter.entities:
        if entity.idx == 0:
            # Megaman or obstacle, do not change
            continue
        dontTouchCategories = [VirusCategory.Protecto, VirusCategory.Dragon]
        if type == DataType.EncounterEVT_BN2:
            # Moles can make many events e.g tutorial virtually impossible
            # as escaping counts as a loss
            dontTouchCategories.append(VirusCategory.Mole)
        if any(cat.isInCategory(entity.idx) for cat in dontTouchCategories):
            continue
        prohibitCategories = dontTouchCategories + [VirusCategory.Navi]
        oldLevel = VirusCategory.getLevel(entity.idx)
        while True:
            newVal = random.randint(1, 177)
            if any(cat.isInCategory(newVal) for cat in prohibitCategories):
                continue
            newLevel = VirusCategory.getLevel(newVal)
            if oldLevel == 1 and VirusCategory.Aura.isInCategory(newVal):
                # Don't allow aura viruses to replace lv1
                continue
            if oldLevel == 0 or newLevel == 0:
                break
            elif newLevel == oldLevel:
                break
        entity.idx = newVal

    # Randomizing locations would require some knowledge


def randomizeEncounters(data: bytearray, config: configparser.ConfigParser):
    choices = config["Encounters"]
    changeFixed = choices.getboolean("RandomizeFixed")
    changeNet = choices.getboolean("RandomizeNet")
    changePanels = choices.getboolean("RandomizePanels")
    changeTutorial = choices.getboolean("RandomizeTutorial")

    if changePanels:
        raise Exception("Options are unsupported: changeNavis,changePanels")

    randoTypes: List[DataType] = []
    if changeNet:
        randoTypes.append(DataType.EncounterRegion_BN2)
    if changeFixed:
        randoTypes.append(DataType.EncounterEVT_BN2)

    for type in randoTypes:
        offset = type.getOffset()
        for i in range(type.getArrayLength()):
            encounter = cast(EncounterT_BN2, type.parseAtOffset(data, offset))
            writeOffset = offset
            offset += encounter.getSize()
            if type == DataType.EncounterEVT_BN2 and i < 3 and not changeTutorial:
                continue
            if not encounter.isEntities():
                continue
            randomizeEncounter(encounter, choices, type)
            encounter.serialize(data, writeOffset)


def randomizeShop(shop: ShopInventory, config: configparser.SectionProxy, ind: int):
    if shop.isSubChipShop():
        return

    if not config.getboolean("RandomizeChipShops"):
        return
    minShopElements = min(8, config.getint("MinElements", 8))
    cheapPowerUps = config.getboolean("CheapPowerUps")
    forceStoryChips = config.getboolean("ForceStoryChips")
    randomizeCodes = config.getboolean("RandomizeCodes")
    for i, elem in enumerate(shop.elems):
        if elem.type == 0x01:
            if cheapPowerUps:
                elem.cost = 100
            continue
        if elem.qty == 0xFF and not randomizeCodes:
            continue
        fixedInd = False
        if ind == 0 and forceStoryChips:
            if i == 6:
                elem.qty = 3
                elem.type = 0x02
                elem.ind = 66  # ZapRing2
                elem.code = 0x01
                elem.cost = 100
                fixedInd = True
            elif i == 7:
                elem.qty = 3
                elem.type = 0x02
                elem.ind = 19  # BigBomb
                elem.code = 0x1A
                elem.cost = 100
                fixedInd = True
        elif elem.ind == 0 and i == minShopElements:
            return
        elif elem.ind == 0:
            elem.type = 0x02
            elem.qty = 1 + getPoissonRandom(0.5)
            elem.cost = 100

        wasFixedInd = fixedInd
        while not fixedInd:
            elem.ind = random.randint(1, 264)
            fixedInd = elem.ind != 256  # Broken index
            # Fighter sword but crash
            # TODO: check other high values?

        elem.cost = min(2 ** 16 - 1, random.randint(elem.cost // 2, 2 * elem.cost))

        if randomizeCodes and not wasFixedInd:
            elem.code = getRandomCode(elem.ind, config)
        else:
            elem.code = getValidCode(elem.ind, elem.code)


def randomizeChipInfo(chip: ChipT_BN2, config: configparser.SectionProxy, ind: int):
    randomizeCodes = config.getboolean("RandomizeCodes")

    if randomizeCodes:
        assignedCodes = []
        for i in range(0, 4):
            if ind == 63 and i == 0:
                # ZapRing2 B
                codeToUse = 0x01
            else:
                while True:
                    codeToUse = random.randint(0, 0x19)
                    if codeToUse not in assignedCodes:
                        break
            chip.codes[i] = codeToUse
            assignedCodes.append(codeToUse)


def randomizeFolder(folder: ChipFolder, config: configparser.SectionProxy, ind: int):
    randomizeTutorial = config.getboolean("RandomizeTutorial", False)
    if not randomizeTutorial and ind >= 3:
        return

    randomizeFolder = config.getboolean("RandomizeFolder")
    for chip in folder.elems:
        if randomizeFolder:
            # Just use standard chips for now
            chip.chip = random.randint(0, 193)

        if randomizeFolder:
            chip.code = getRandomCode(chip.chip, config)
        else:
            # Adjust the code even if we aren't otherwise randomizing
            # the folders as otherwise folder/pack gets messed up.
            # Note the tutorial folders still work fine even if the codes
            # aren't among the actual possibilities
            chip.code = getValidCode(chip.chip, chip.code)


def _randomizeCommon(
    data: bytearray,
    config: configparser.SectionProxy,
    type: DataType,
    fcn: Callable[[Any, configparser.SectionProxy, int], None],
):

    offset = type.getOffset()
    for i in range(type.getArrayLength()):
        item = type.parseAtOffset(data, offset)
        writeOffset = offset
        offset += type.getSize()
        fcn(item, config, i)
        item.serialize(data, writeOffset)


def randomizeShops(data: bytearray, config: configparser.ConfigParser):
    _randomizeCommon(data, config["Shops"], DataType.ShopInventory_BN2, randomizeShop)


def randomizeChips(data: bytearray, config: configparser.ConfigParser):
    _randomizeCommon(data, config["Chips"], DataType.Chip_BN2, randomizeChipInfo)


def randomizeFolders(data: bytearray, config: configparser.ConfigParser):
    _randomizeCommon(data, config["Folders"], DataType.ChipFolder_BN2, randomizeFolder)
