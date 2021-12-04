from typing import List, cast, Callable, Any, Tuple
import configparser
import random
from megadata import DataType, DataTypeVar
from bn2data import (
    DropTable,
    ShopInventory,
    EncounterT_BN2,
    VirusCategory,
    NameMaps,
    ChipT_BN2,
    ChipFolder,
    GMD,
)
from distribution import getPoissonRandom


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
    encounter: EncounterT_BN2,
    config: configparser.SectionProxy,
    type: DataType,
    idx: int,
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

        if any(cat.isInCategory(entity.idx) for cat in dontTouchCategories):
            continue
        prohibitCategories = dontTouchCategories + [VirusCategory.Navi]
        if type == DataType.EncounterEVT_BN2:
            # Moles can make many events e.g tutorial virtually impossible
            # as escaping counts as a loss
            prohibitCategories.append(VirusCategory.Mole)
            if idx < 3:
                # Shadows can make the tutorial impossible
                prohibitCategories.append(VirusCategory.Shadow)
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
            randomizeEncounter(encounter, choices, type, i)
            encounter.serialize(data, writeOffset)


def randomizeShop(shop: ShopInventory, config: configparser.SectionProxy, ind: int):
    if shop.isSubChipShop():
        return

    if not config.getboolean("RandomizeChips"):
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
            if i == 5:
                elem.qty = 3
                elem.type = 0x02
                elem.ind = 111  # Guard
                elem.code = 0x1A
                elem.cost = 100
                fixedInd = True
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

        elem.cost = max(
            1, min(2 ** 16 - 1, random.randint(elem.cost // 2, 2 * elem.cost))
        )

        if fixedInd:
            elem.code = getValidCode(elem.ind, elem.code)
        else:
            elem.ind, elem.code = randomizeChipAndCode(elem.ind, elem.code, config)


def randomizeChipInfo(chip: ChipT_BN2, config: configparser.SectionProxy, ind: int):
    randomizeCodes = config.getboolean("RandomizeCodes")

    if randomizeCodes:
        assignedCodes = []
        for i in range(0, 4):
            if ind == 65 and i == 0:
                # ZapRing2 B
                codeToUse = 0x01
            else:
                while True:
                    codeToUse = random.randint(0, 0x19)
                    if codeToUse not in assignedCodes:
                        break
            chip.codes[i] = codeToUse
            assignedCodes.append(codeToUse)


def loadFolderFromFile(folder: ChipFolder, fname: str):
    fldrFile = open(fname, "r")
    invMap = {name: code + 1 for code, name in NameMaps.chipNameMap.items()}
    for i, line in enumerate(fldrFile.readlines()):
        elems = line[:-1].split(" ")
        name, code, *_ = elems
        folder.elems[i].chip = invMap[name]
        folder.elems[i].code = 0x1A if code == "*" else ord(code) - ord("A")


def randomizeFolder(folder: ChipFolder, config: configparser.SectionProxy, ind: int):
    randomizeTutorial = config.getboolean("RandomizeTutorial", False)
    if not randomizeTutorial and ind >= 3:
        return

    key = f"Foldr{ind + 1}File"
    if config.get(key):
        loadFolderFromFile(folder, config.get(key))
        return
    for chip in folder.elems:
        chip.chip, chip.code = randomizeChipAndCode(chip.chip, chip.code, config)


def randomizeChipAndCode(
    chip: int, code: int, config: configparser.SectionProxy
) -> Tuple[int, int]:
    randomizeChips = config.getboolean("RandomizeChips")
    randomizeCodes = config.getboolean("RandomizeCodes")

    if randomizeChips:
        ub = 265
        if config.name in ["GMD", "Shops"]:
            # GMDs only support one byte and many higher code chips
            # break in shops (at least KngtSwrd,FtrSword,Gospel chips)
            ub = 255
        if config.getboolean("OnlyStandardChips"):
            ub = 193
        chip = random.randint(1, ub)

    if randomizeCodes:
        code = getRandomCode(chip, config)
    else:
        code = getValidCode(chip, code)
    return chip, code


def randomizeDropTable(table: DropTable, config: configparser.SectionProxy, ind: int):
    if config.getboolean("PopulateUnused"):

        lowKeys = (0, 1, 2, 3, 4, 10, 11, 12, 13, 14, 20, 21, 22, 23, 24)
        midKeys = (5, 6, 7, 15, 16, 17, 25, 26, 27)
        highKeys = (8, 9, 18, 19, 28, 29)
        if ind == 29 or ind == 30:  # HardHead2 and HardHead3
            for i in lowKeys:
                table.elems[i].writeZenny(10 * ind)
            for i in midKeys:
                # Wrecker *
                table.elems[i].writeChip(51, 0x1A)
            for i in highKeys:
                if ind == 29:
                    # CannBall S
                    table.elems[i].writeChip(52, 17)
                else:
                    # CannBall *
                    table.elems[i].writeChip(52, 0x1A)
        elif ind == 43:  # Poofy
            for i in lowKeys:
                table.elems[i].writeHP(0)
            for i in midKeys:
                # BubSprd L
                table.elems[i].writeChip(11, 11)
            for i in highKeys:
                # HeatSprd L
                table.elems[i].writeChip(15, 11)
        elif ind == 44:  # Fishy 3
            for i in lowKeys:
                table.elems[i].writeZenny(10 * ind)
            for i in midKeys:
                # Dash Atk JG*
                table.elems[i].writeChip(50, (9, 6, 0x1A)[i // 10])
            for i in highKeys:
                # Burner AS*
                table.elems[i].writeChip(64, (0, 18, 0x1A)[i // 10])
        elif ind == 54:  # Popper
            for i in midKeys:
                # LeafShld
                table.elems[i].writeChip(164, (0, 3, 17)[i // 10])
            for i in highKeys:
                # DropDown
                table.elems[i].writeChip(156, (0, 2, 5)[i // 10])
        elif ind == 61 or ind == 62:  # Flamey[23]
            for i in highKeys:
                # LineOut
                code = (5, 7, 9)[i // 10] if ind == 61 else 0x1A
                table.elems[i].writeChip(115, code)
        elif ind == 68:  # Goofball
            for i in midKeys:
                # PoisFace
                table.elems[i].writeChip(108, (19, 20, 0x1A)[i // 10])
            for i in highKeys:
                # Geddon3
                table.elems[i].writeChip(135, 0x1A)
        elif ind == 92:  # Null&Void
            for i in midKeys:
                # Whirlpl
                table.elems[i].writeChip(109, (0, 2, 0x1A)[i // 10])
            for i in highKeys:
                # BlckHole
                table.elems[i].writeChip(110, (1, 3, 0x1A)[1 // 10])
        elif ind == 101:  # StormBox
            for i in midKeys:
                # Wind
                table.elems[i].writeChip(147, 0x1A)
            for i in midKeys:
                # Fan
                table.elems[i].writeChip(148, 0x1A)
        elif ind == 103 or ind == 104:  # {Blue,Green}UFO
            for i in midKeys:
                # AntiDmg
                table.elems[i].writeChip(185, 0x1A)
            for i in highKeys:
                # AntiNavi
                table.elems[i].writeChip(186, 0x1A)
        elif ind == 109 or ind == 110:  # BrushMan[23]
            for i in midKeys:
                # HolyPanel
                table.elems[i].writeChip(179, 0x1A)
            for i in highKeys:
                # TODO: Sanctuary? Make sure it works
                table.elems[i].writeChip(179, 0x1A)
        elif ind == 112 or ind == 113:  # {Blue,Yellow}gon
            for i in highKeys:
                # LavaDrag
                table.elems[i].writeChip(104, 0x1A)

    if ind >= 128 and not config.getboolean("RandomizeNavis"):
        return
    # TODO: options to drop more chips and less zenny?
    randomizeChips = config.getboolean("RandomizeChips")
    randomizeCodes = config.getboolean("RandomizeCodes")
    for elem in table.elems:
        if not elem.isZenny() and not elem.isHP():
            chip = elem.getChipInd()
            code = elem.getChipCode()
            chip, code = randomizeChipAndCode(chip, code, config)
            elem.writeChip(chip, code)


def randomizeGMD(data: bytearray, configuration: configparser.ConfigParser):
    gmd = GMD(data)
    config = configuration["GMD"]
    for info in gmd.info:
        lastChip = -1
        lastCode = 0x1A
        offs = info.offset
        for chipInfo in info.chips:
            chip, code = chipInfo.getChipAndCode(data, offs)
            if chipInfo.noCode:
                code = lastCode
            if chipInfo.noChip:
                chip = lastChip
            assert chip >= 0
            done = False
            while not done:
                chip, code = randomizeChipAndCode(chip, code, config)
                # Only one byte apparently available for GMD chip info
                done = chip <= 0xFF
            chipInfo.serializeChip(data, offs, chip, code)
            offs += chipInfo.getSize()
            lastChip, lastCode = chip, code
        for zenny in info.zennies:
            if not zenny.fullyMutable():
                continue
            zenValue = zenny.getZennyValue(data, offs)
            r = 1 + random.random() * 4
            if random.random() > 0.5:
                zenValue = int(zenValue * 1 / r)
                zenValue = max(zenValue, 100)
            else:
                zenValue = int(zenValue * r)
                zenValue = min(zenValue, 2 ** 16 - 1)
            zenny.serializeZenny(data, offs, zenValue)
            offs += zenny.getSize()


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


def randomizeDropTables(data: bytearray, config: configparser.ConfigParser):
    _randomizeCommon(
        data, config["DropTables"], DataType.DropTable_BN2, randomizeDropTable
    )
