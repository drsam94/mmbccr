from typing import List, cast
import configparser
import random
from megadata import DataType
from bn2data import ShopInventory, EncounterT_BN2, VirusCategory
from distribution import getValWithVar, getPoissonRandom


def randomizeEncounter(encounter: EncounterT_BN2, config: configparser.SectionProxy):
    if encounter.isNaviBattle() and not config.getboolean("RandomizeNavis"):
        return

    # We should look into changing positions, but that does require knowledge
    # of the field
    for entity in encounter.entities:
        if entity.idx == 0:
            # Megaman or obstacle, do not change
            continue
        dontTouchCategories = [VirusCategory.Protecto, VirusCategory.Dragon]
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
            randomizeEncounter(encounter, choices)
            encounter.serialize(data, writeOffset)


def randomizeShop(shop: ShopInventory, config: configparser.SectionProxy):
    if shop.isSubChipShop():
        return

    minShopElements = min(8, config.getint("MinElements", 8))
    cheapPowerUps = config.getboolean("CheapPowerUps")
    forceStoryChips = config.getboolean("ForceStoryChips")
    isFirstShop = False
    for i, elem in enumerate(shop.elems):
        if elem.type == 0x01:
            if cheapPowerUps:
                elem.cost = 100
            continue
        fixedInd = False
        if elem.ind == 0x04:
            isFirstShop = True
        elif isFirstShop and forceStoryChips:
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
        # Can put any code but will be converted
        elem.code = random.randint(0, 27)
        elem.cost = random.randint(elem.cost // 2, 2 * elem.cost)
        while not fixedInd:
            elem.ind = random.randint(1, 266)
            fixedInd = elem.ind != 256  # Broken index


def randomizeShops(data: bytearray, config: configparser.ConfigParser):
    choices = config["Shops"]

    if not choices.getboolean("RandomizeChipShops"):
        return
    type = DataType.ShopInventory_BN2
    offset = type.getOffset()
    for i in range(type.getArrayLength()):
        shop = cast(ShopInventory, type.parseAtOffset(data, offset))
        writeOffset = offset
        offset += type.getSize()
        randomizeShop(shop, choices)
        shop.serialize(data, writeOffset)
