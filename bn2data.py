from typing import Tuple, Dict, List
import struct
from enum import Enum


class BN2Char:
    """
    Strings in MMBN2 are sequences of 1-byte characters, using a special terminator
    character. Strings are not padded in any way so they are in memory one after another,
    which would make replacing strings with longer strings require a fair amount of tweaking
    """

    A = 0x25
    a = 0x0B

    specialMap = {
        0: " ",
        0x3F: "@",  # V2
        0x40: "#",  # V3
        0x41: "-",
        0x45: "?",
        0x46: "+",
        0x4D: "&",
        0x53: "'",
        0xE8: "\n",
    }

    inverseMap = {v: k for k, v in specialMap.items()}

    @classmethod
    def isEncodedDigit(cls, char: int) -> bool:
        return char > 0 and char <= 10

    @classmethod
    def convFrom(cls, char: int) -> str:
        if char in cls.specialMap:
            return cls.specialMap[char]
        elif cls.isEncodedDigit(char):
            return chr(ord("0") + char - 1)
        elif char >= cls.A and char < cls.A + 26:
            return chr(ord("A") + char - cls.A)
        elif char >= cls.a and char < cls.a + 26:
            return chr(ord("a") + char - cls.a)
        else:
            return f"<{hex(char)}>"

    @classmethod
    def convTo(cls, charInput: str) -> int:
        char = ord(charInput)
        if char >= ord("0") and char <= ord("9"):
            return char - ord("0") + 1
        if char >= ord("A") and char < ord("A") + 26:
            return cls.A + char - ord("A")
        elif char >= ord("a") and char < ord("a") + 26:
            return cls.a + char - ord("a")
        elif charInput in cls.inverseMap:
            return cls.inverseMap[charInput]
        else:
            return 0x5D

    @classmethod
    def toString(cls, data: bytearray, offset: int) -> Tuple[str, int]:
        out = ""
        while not cls.isTerminator(data[offset]):
            out += cls.convFrom(data[offset])
            offset += 1
        return out, offset + 1

    @classmethod
    def terminator(cls, len: int) -> int:
        return 0xE7

    @classmethod
    def isTerminator(cls, char: int) -> bool:
        return char == 0xE7


class ChipT_BN2:
    myStruct = struct.Struct("<2I4B2H4B3I")

    def __init__(self, data: bytearray, offset: int):
        self.unk1 = [0] * 2
        self.unk2 = [0] * 4
        (
            self.descBytes,
            self.effect,
            self.unk1[0],
            self.unk1[1],
            self.mb,
            self.flags,
            self.ap,
            self.idx,
            self.unk2[0],
            self.unk2[1],
            self.unk2[2],
            self.unk2[3],
            self.thumbnailPtr,
            self.imgPtr,
            self.colorPtr,
        ) = ChipT_BN2.myStruct.unpack_from(data, offset)

    def serialize(self, data: bytearray, offset: int):
        ChipT_BN2.myStruct.pack_into(
            data,
            offset,
            self.descBytes,
            self.effect,
            self.unk1[0],
            self.unk1[1],
            self.mb,
            self.flags,
            self.ap,
            self.idx,
            *self.unk2,
            self.thumbnailPtr,
            self.imgPtr,
            self.colorPtr,
        )

    def __str__(self):
        return (
            f"unk1: {self.unk1}, unk2: {self.unk2}, mb: {self.mb}, flags: {self.flags}, ap: {self.ap}, "
            f"idx: {self.idx} "
            f"effect: {hex(self.effect)} descBytes: {hex(self.descBytes)} "
            f"img: {hex(self.imgPtr)} col: {hex(self.colorPtr)} thumb: {hex(self.thumbnailPtr)}"
        )


class VirusT_BN2:
    myStruct = struct.Struct("<HBIB")

    def __init__(self, data: bytearray, offset: int):
        (self.hp, self.unk, self.descBytes, self.level) = self.myStruct.unpack_from(
            data, offset
        )

    def serialize(self, data: bytearray, offset: int):
        self.myStruct.pack_into(
            data, offset, self.hp, self.unk, self.descBytes, self.level
        )

    def __str__(self):
        return f"hp: {self.hp}, descBytes: {hex(self.descBytes)}, lvl: {self.level}, unk: {self.unk}"


"""
Info to deduce relative levels of viruses; these are mostly highly 
straightforward but some viruses are listed in weird orders
(see Fishy for example)
"""
levelTuples = [
    (1, 2, 3),  # Mettaur
    (4, 5, 6),  # Canodumb
    (7, 8, 9),  # Beetank
    (10, 11, 44),  # Fishy
    (12, 13, 14),  # Cloudy
    (15, 16, 17),  # Spooky
    (18, 19, 20),  # Handy
    (21, 22, 23),  # Bunny
    (24, 25, 26),  # Meteor/Fire
    (27, 28, 43),  # Puffy
    (29, 30, 31),  # HardHead
    (32, 33, 34),  # CanDevil
    (35, 36, 37),  # Mushy
    (38, 39, 40),  # Swordy
    (45, 46, 47),  # Flappy
    (48, 49, 50),  # Ratty
    (51, 52, 53),  # Twisty
    (54, 55, 56),  # Popper
    (57, 58, 59),  # Spikey
    (60, 61, 62),  # Flamey
    (63, 64, 65),  # Shrimpy
    (66, 67, 68),  # Puffball
    (69, 70, 71),  # Sparky
    (72, 73, 74),  # Octo
    (75, 76, 77),  # Yoyo
    (78, 79, 80),  # Shell
    (81, 82, 83),  # KillPlant
    (84, 85, 86),  # Dominerd
    (87, 88, 89),  # Protecto
    (90, 91, 92),  # Null/Void
    (93, 94, 95),  # Mag
    (96, 97, 98),  # Shadow
    (99, 100, 101),  # Fan
    (102, 103, 104),  # UFO
    (105, 106, 107),  # Snapper
    (108, 109, 110),  # Brushman
    (111, 112, 113),  # Dragon
    (123, 124, 125),  # AirMan
    (126, 127, 128),  # QuickMan
    (129, 130, 131),  # CutMan
    (132, 133, 134),  # ShadowMan
    (135, 136, 137),  # KnightMan
    (138, 139, 140),  # MagnetMan
    (141, 142, 143),  # FreezeMan
    (145, 146, 147),  # HeatMan
    (148, 149, 150),  # ToadMan
    (151, 152, 153),  # ThunMan
    (154, 155, 156),  # SnakeMan
    (157, 158, 159),  # GutsMan
    (160, 161, 162),  # ProtoMan
    (163, 164, 165),  # GateMan
    (166, 167, 168),  # PlanetMan
    (169, 170, 171),  # NapalmMan
    (172, 173, 174),  # PharaohMan
    (175, 176, 177),  # Bass
]


class VirusCategory(Enum):
    Level1 = 1
    Level2 = 2
    Level3 = 3
    Shadow = 4
    Protecto = 5
    Face = 6
    Aura = 7
    Dragon = 8
    Mole = 9
    Navi = 10

    @classmethod
    def _getLevelList(cls, ind: int) -> List[int]:
        return [tup[ind] for tup in levelTuples]

    @classmethod
    def getLevel(cls, ind: int) -> int:
        for tup in levelTuples:
            for i, elem in enumerate(tup):
                if elem == ind:
                    return i + 1
        return 0

    def getRange(self) -> List[int]:
        if self == VirusCategory.Shadow:
            """
            Shadows can only be damaged by swords and thus are
            dangerous to randomize in some locations
            96: Shadow
            97: RedDevil
            98: BlueDemon
            """
            return [96, 97, 98]
        elif self == VirusCategory.Protecto:
            """
            Protecto fights are very particular and generally
            not safe for randomization
            87: Protecto
            88: Protecto2
            89: Protecto3
            """
            return [87, 88, 89]
        elif self == VirusCategory.Face:
            """
            Face viruses require some degree of specialized
            chips so are not universally safe for randomization
            66: Puffball
            67: Poofball
            68: Goofball
            """
            return [66, 67, 68]
        elif self == VirusCategory.Aura:
            """
            Viruses with auras require certain chips to beat
            (Though technically Megalians can be beaten when their heads
            leave)
            114: Scutz
            115: Scuttle
            116: Scuttler
            117: Scuttzer
            118: Scuttlest
            119: MegalianA
            120: MegalianH
            121: MegalianW
            122: MegalianE
            """
            return list(range(114, 123))
        elif self == VirusCategory.Dragon:
            """
            Dragon viruses require holes on a field to exist so cannot
            be added to all encounters
            111: Lavagon
            112: Bluegon
            113: Yellowgon
            """
            return [111, 112, 113]
        elif self == VirusCategory.Navi:
            """
            Generally you don't want to randomize navis into virus
            encounters
            """
            return list(range(123, 178))
        elif self == VirusCategory.Level1:
            return self._getLevelList(0)
        elif self == VirusCategory.Level2:
            return self._getLevelList(1)
        elif self == VirusCategory.Level3:
            return self._getLevelList(2)
        else:
            raise KeyError(f"Unsupported category {self}")

    def isInCategory(self, ind: int):
        return ind in self.getRange()


class NameMaps(object):
    virusNameMap: Dict[int, str] = {}
    chipNameMap: Dict[int, str] = {}
    # Unclear to me what this ordering is / how to directly derive
    # this from the ROM
    itemNameMap: Dict[int, str] = {
        0x60: "HPMemory",
        0x61: "PowerUp",
        0x70: "MiniEnrg",
        0x71: "FullEnrg",
        0x72: "SneakRun",
        0x73: "Untrap",
        0x74: "LocEnemy",
        0x75: "Unlocker",
    }

    @classmethod
    def setVirusNameMap(cls, m: Dict[int, str]):
        cls.virusNameMap = m

    @classmethod
    def setChipNameMap(cls, m: Dict[int, str]):
        cls.chipNameMap = m


class EncounterEntity(object):
    myStruct = struct.Struct("<4B")

    def __init__(self, data: bytearray, offset: int):
        (self.idx, self.x, self.y, self.role) = self.myStruct.unpack_from(data, offset)

    def serialize(self, data: bytearray, offset: int):
        self.myStruct.pack_into(data, offset, self.idx, self.x, self.y, self.role)

    def isTerminator(self) -> bool:
        return self.idx == 0xFF

    def isValidStart(self) -> bool:
        return self.idx == 0 and self.x < 4 and self.y < 4 and self.role == 0

    def __str__(self):
        return f"{NameMaps.virusNameMap.get(self.idx, self.idx)} @ {self.x},{self.y} {self.role};"


class EncounterDesc(object):
    myStruct = struct.Struct("<2I")

    def __init__(self, data: bytearray, offset: int):
        (self.stage, self.entities) = self.myStruct.unpack_from(data, offset)

    def serialize(self, data: bytearray, offset: int):
        self.myStruct.pack_into(data, offset, self.stage, self.entities)

    def __str__(self):
        return f"Stage: {hex(self.stage)} Entities: {hex(self.entities)}"


class EncounterT_BN2:
    """
    Encounters have a structure where each object in the encounter is represented with 4 bytes
    <id> <xcoord> <ycoord> <team (00 = player, 01 = enemy, 02 = neutral)>
    and ends when we reach a 4 byte chunk with id = 0. Encounters can have as few as 2 actors,
    or as many as 6.

    Encounter lists are structured as a list of (field, encounter) pointers, then a list of encounters; only new encounters
    will be explicitly enumerated, if the same encounter appears elsewhere in the list, a pointer to that same encounter will be
    given
    """

    def __init__(self, data: bytearray, offset: int):
        self.descs: List[EncounterDesc] = []
        self.entities: List[EncounterEntity] = []

        while True:
            entity = EncounterEntity(data, offset)
            isEntities = entity.isValidStart()
            if not entity.isTerminator():
                break
            offset += 4
        while True:
            entity = EncounterEntity(data, offset)
            if isEntities:
                offset += 4
                if entity.isTerminator():
                    break
                self.entities.append(entity)
            else:
                if entity.isValidStart():
                    break
                desc = EncounterDesc(data, offset)
                offset += 8
                self.descs.append(desc)

    def serialize(self, data: bytearray, offset: int):
        for desc in self.descs:
            desc.serialize(data, offset)
            offset += 8
        for ent in self.entities:
            ent.serialize(data, offset)
            offset += 4

    def isEntities(self) -> bool:
        return len(self.entities) > 0

    def isNaviBattle(self) -> bool:
        return any(VirusCategory.Navi.isInCategory(e.idx) for e in self.entities)

    def getSize(self) -> int:
        if self.isEntities() > 0:
            return 4 * (1 + len(self.entities))
        else:
            return 8 * len(self.descs)

    def __str__(self) -> str:
        return " ".join(list(map(str, self.descs)) + list(map(str, self.entities)))


def codeStr(code: int) -> str:
    if code == 0xFF:
        return ""
    elif code == 0x1A:
        return "*"
    else:
        return chr(ord("A") + code)


class ShopElem(object):
    myStruct = struct.Struct("<4B4H")

    def __init__(self, data: bytearray, offset: int):
        (
            self.type,
            self.qty,
            self.ff1,
            self.ff2,
            self.ind,
            self.code,
            self.cost,
            self.zero,
        ) = self.myStruct.unpack_from(data, offset)

    def serialize(self, data: bytearray, offset: int):
        self.myStruct.pack_into(
            data,
            offset,
            self.type,
            self.qty,
            self.ff1,
            self.ff2,
            self.ind,
            self.code,
            self.cost,
            self.zero,
        )

    def isChip(self) -> bool:
        return self.type == 0x02

    def isPowerUp(self) -> bool:
        return self.getName() in ["HPMemory", "PowerUp"]

    def getName(self) -> str:
        if self.isChip():
            return NameMaps.chipNameMap.get(self.ind - 1, self.ind)
        else:
            return NameMaps.itemNameMap.get(self.ind, f"SubChip{hex(self.ind)}")

    def __str__(self):
        if self.ind == 0:
            return ""
        return f"{'inf' if self.qty == 0xFF else self.qty} {self.getName()} {codeStr(self.code)} {self.cost}Z"


class ShopInventory(object):
    def __init__(self, data: bytearray, offset: int):
        self.elems: List[ShopElem] = []
        self.emptyCount = 0
        for _ in range(8):
            elem = ShopElem(data, offset)
            offset += 12
            self.elems.append(elem)

    def serialize(self, data: bytearray, offset: int):
        for elem in self.elems:
            elem.serialize(data, offset)
            offset += 12

    def isSubChipShop(self):
        return all(not elem.isChip() for elem in self.elems)

    def __str__(self) -> str:
        return "\n".join(map(str, self.elems))
