from typing import List, Union, Dict, Any, cast, Iterable
import struct
from enum import Enum
import itertools
from bn2data import (
    ChipT_BN2,
    VirusT_BN2,
    EncounterT_BN2,
    ShopInventory,
    NameMaps,
    BN2Char,
    ChipFolder,
    DropTable,
)

from bccdata import EncounterT, ChipT, StringT, StartingChipsT, PrintOpts

DataTypeVar = Union[
    EncounterT,
    ChipT,
    StringT,
    StartingChipsT,
    ChipT_BN2,
    VirusT_BN2,
    EncounterT_BN2,
    ShopInventory,
    ChipFolder,
    DropTable,
]


class DataType(Enum):
    """
    DataType represents the various data types, which are generally stored in
    large arrays; DataType has accessors to parse and serialize the data, as well
    as knowledge as to how large each object is and where the home array lives
    """

    # mmbcc
    Encounter = 1
    Chip = 2
    Sprite = 3
    ChipName = 4
    OpName = 5
    ChipDesc = 6
    EffectDesc = 7
    StartingChips = 8
    # bn2
    Chip_BN2 = 9
    ChipName_BN2 = 10
    VirusName_BN2 = 11
    ItemName_BN2 = 12
    Virus_BN2 = 13
    EncounterEVT_BN2 = 14
    EncounterRegion_BN2 = 15
    ShopInventory_BN2 = 16
    ChipFolder_BN2 = 17
    DropTable_BN2 = 18
    GMD_BN2 = 19

    def isVarLengthString(self):
        return self in [
            DataType.ChipName_BN2,
            DataType.VirusName_BN2,
            DataType.ItemName_BN2,
            DataType.GMD_BN2,
        ]

    def getOffset(self) -> int:
        """
        Offset of array start; notably computations in the code are often 1-indexed,
        so the pointers in the code are to memory regions that start one object
        earlier
        """
        if self == DataType.Encounter:
            return 0x229900
        elif self == DataType.Chip:
            return 0x22741C
        elif self == DataType.Sprite:
            return 0x32CB78
        elif self == DataType.ChipName:
            return 0x22BB90
        elif self == DataType.OpName:
            return 0x22D69C
        elif self == DataType.ChipDesc:
            return 0x22C35C
        elif self == DataType.EffectDesc:
            return 0x22BF78
        elif self == DataType.StartingChips:
            return 0x2273C1
        elif self == DataType.Chip_BN2:
            return 0x00E470
        elif self == DataType.ChipName_BN2:
            return 0x728779
        elif self == DataType.VirusName_BN2:
            return 0x73328C
        elif self == DataType.ItemName_BN2:
            return 0x7339B4
        elif self == DataType.Virus_BN2:
            return 0x01515C
        elif self == DataType.EncounterEVT_BN2:
            return 0x01571C
        elif self == DataType.EncounterRegion_BN2:
            # 0x0a1000 is around Den 1 ; the first region
            # starts right after the event encounters though, with the different event pointer structure
            return 0x0168C0
        elif self == DataType.ShopInventory_BN2:
            return 0x030184
        elif self == DataType.ChipFolder_BN2:
            return 0x009974
        elif self == DataType.DropTable_BN2:
            return 0x012624
        elif self == DataType.GMD_BN2:
            # GMDs are handled very specially, see the GMD class for
            # more details
            return 0
        raise KeyError("bad value")

    def getSize(self, obj: Any = None) -> int:
        if self == DataType.Encounter:
            return 20
        elif self == DataType.Chip:
            return 16
        elif self == DataType.Sprite:
            return 256
        elif self in [
            DataType.ChipName,
            DataType.OpName,
            DataType.EffectDesc,
            DataType.ChipDesc,
        ]:
            return 4  # Pointer
        elif self == DataType.StartingChips:
            return 7
        elif self == DataType.Chip_BN2:
            return 32
        elif self == DataType.Virus_BN2:
            return 8
        elif self == DataType.ShopInventory_BN2:
            return 96
        elif self in [
            DataType.EncounterEVT_BN2,
            DataType.EncounterRegion_BN2,
        ]:
            return 0 if obj is None else obj.getSize()
        elif self == DataType.ChipFolder_BN2:
            return 120
        elif self == DataType.DropTable_BN2:
            return 60
        raise KeyError("bad value")

    def getArrayLength(self) -> int:
        if self == DataType.Encounter:
            return 419
        elif (
            self == DataType.Chip
            or self == DataType.ChipName
            or self == DataType.ChipDesc
            or self == DataType.EffectDesc
        ):
            return 248
        elif self == DataType.Sprite:
            return 174
        elif self == DataType.OpName:
            return 143
        elif self == DataType.StartingChips:
            return 1
        elif self == DataType.Chip_BN2:
            return 265
        elif self == DataType.ChipName_BN2:
            # Special Values:
            # Weird data at 255/256  (between BlkBomb and FtrSword)
            # 265: GateSP
            # 270: Scntuary (empty before) empty strs, Snctuary (270)
            # 272-303: PAs
            # 304-315: Enemy 'chips' (e.g RemoGate) and empty strs
            # 315: '????'
            return 316
        elif self == DataType.VirusName_BN2:
            return 178
        elif self == DataType.ItemName_BN2:
            return 113
        elif self == DataType.Virus_BN2:
            return 178
        elif self == DataType.EncounterEVT_BN2:
            return 243
        elif self == DataType.EncounterRegion_BN2:
            return 849
        elif self == DataType.ShopInventory_BN2:
            return 25
        elif self == DataType.ChipFolder_BN2:
            return 6
        elif self == DataType.DropTable_BN2:
            return 184
        elif self == DataType.GMD_BN2:
            return 0
        raise KeyError("bad value")

    def parseAtOffset(self, data: bytearray, offset: int) -> DataTypeVar:
        if self == DataType.Encounter:
            return EncounterT(data, offset)
        elif self == DataType.Chip:
            return ChipT(data, offset)
        elif self == DataType.ChipName or self == DataType.OpName:
            return StringT(data, offset)
        elif self == DataType.ChipDesc:
            return StringT(data, offset, strCount=3, indirect=True)
        elif self == DataType.EffectDesc:
            return StringT(data, offset, format=0x600)
        elif self == DataType.StartingChips:
            return StartingChipsT(data, offset)
        elif self == DataType.Chip_BN2:
            return ChipT_BN2(data, offset)
        elif self == DataType.Virus_BN2:
            return VirusT_BN2(data, offset)
        elif self in [DataType.EncounterEVT_BN2, DataType.EncounterRegion_BN2]:
            return EncounterT_BN2(data, offset)
        elif self == DataType.ShopInventory_BN2:
            return ShopInventory(data, offset)
        elif self == DataType.ChipFolder_BN2:
            return ChipFolder(data, offset)
        elif self == DataType.DropTable_BN2:
            return DropTable(data, offset)
        raise KeyError("bad value")

    def parse(self, data: bytearray, index: int) -> DataTypeVar:
        objSize = self.getSize()
        if objSize == 0:
            raise KeyError(f"Parse not supported on type {self}")
        offset = self.getOffset() + index * objSize
        return self.parseAtOffset(data, offset)

    def rewrite(self, data: bytearray, index: int, objT: DataTypeVar):
        objT.serialize(data, self.getOffset() + index * self.getSize())


def populateBN2Meta(byteData: bytearray):
    offset = DataType.VirusName_BN2.getOffset()
    vn: Dict[int, str] = {}
    for i in range(DataType.VirusName_BN2.getArrayLength()):
        out, offset = BN2Char.toString(byteData, offset)
        vn[i] = out
    vn[255] = "<255>"
    vn[0] = "<0>"
    NameMaps.setVirusNameMap(vn)

    offset = DataType.ChipName_BN2.getOffset()
    cn: Dict[int, str] = {}
    for i in range(DataType.ChipName_BN2.getArrayLength()):
        out, offset = BN2Char.toString(byteData, offset)
        cn[i] = out
    NameMaps.setChipNameMap(cn)

    offset = DataType.Chip_BN2.getOffset()

    cim: Dict[int, ChipT_BN2] = {}
    for i in range(DataType.Chip_BN2.getArrayLength()):
        chip = cast(ChipT_BN2, DataType.Chip_BN2.parse(byteData, i))
        cim[i] = chip
    NameMaps.setChipInfoMap(cim)


# BCC Library, still haven't factored out dependencies cleanly
class Library:
    """
    Helper methods for metadata on the library layout
    One interesting note is that in addition to the 4 data chips, there are
    5 additional chips in the storage which aren't in the library, these are
    'Zenny', 'Empty', 'No Chip', 'Chip OK', and 'Deleted' in order
    (indixes 194-198)
    """

    @staticmethod
    def standardChipRange() -> Iterable[int]:
        return range(190)

    @staticmethod
    def naviChipRange() -> Iterable[int]:
        return range(199, 247)

    @classmethod
    def getChipMap(cls, data: bytearray) -> Dict[int, ChipT]:
        type = DataType.Chip
        ret: Dict[int, ChipT] = {}
        for i in itertools.chain(cls.standardChipRange(), cls.naviChipRange()):
            obj = type.parse(data, i)
            assert isinstance(obj, ChipT)
            ret[i] = obj
        return ret

    @classmethod
    def getMBMap(cls, data: bytearray) -> Dict[int, List[int]]:
        type = DataType.Chip
        ret: Dict[int, List[int]] = {}
        for i in cls.standardChipRange():
            obj = type.parse(data, i)
            assert isinstance(obj, ChipT)
            if obj.mb not in ret:
                ret[obj.mb] = []
            ret[obj.mb].append(i)
        return ret

    @classmethod
    def getWeakerChip(cls, ind: int) -> int:
        """
        Given a chip index (library index, i.e starting with 1),
        Returns a chip index of the next chip below in ability
        (e.g HiCannon for M-Cannon)
        returns 0 if there is no known weaker chip.
        Note that not all v1/v2/v3 relationships in chips are strict
        relationships, e.g ZapRings which go up in power and down in
        HP; those relationships we don't keep strictly
        """
        # Chips which are exactly 1 unit stronger than the chip
        # below
        oneStronger = {
            2,
            3,
            5,
            6,
            7,
            9,
            10,
            11,
            13,
            14,
            15,
            17,
            18,
            19,
            21,
            22,
            24,
            34,
            35,
            44,
            45,
            56,
            57,
            67,
            68,
            70,
            71,
            73,
            74,
            76,
            77,
            79,
            80,
            105,
            106,
            136,
            137,
            138,
            139,
        }
        directMap = {
            25: 23,  # LongSwrd > Sword
            29: 26,  # Blades > Swords
            30: 27,
            31: 28,
            54: 52,  # Trident > TripNdl
        }
        if ind in oneStronger:
            return ind - 1
        elif ind in directMap:
            return directMap[ind]
        else:
            return 0
