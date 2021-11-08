from typing import List, cast
import configparser
import random
from megadata import DataType
from bn2data import EncounterDesc, EncounterT_BN2, EncounterEntity, VirusCategory


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
