from typing import List, Union, Tuple, Iterable, Dict
import struct
from enum import Enum
import itertools


class Element(Enum):
    Normal = 0
    Fire = 1
    Aqua = 2
    Wood = 3
    Elec = 4


class ChipT:
    """
    A descripton of a chip; this includes description of the art and pallette and the
    in-battle effect, but not the description of the effect or the name.
    fields: effectIndex -- I gave it this name but I don't know what it does
    flags: I documented some of these, but some of them do not seem to be fully consistent
    """

    myStruct = struct.Struct("<5H6B")

    def __init__(self, data: bytearray, offset: int):
        (
            self.hp,
            self.effectIndex,
            self.ap,
            self.mb,
            self.flags,
            self.rarity,
            self.chipCategory,
            self.hitChance,
            self.dodgeChance,
            self.artIndex,
            self.palleteIndex,
        ) = ChipT.myStruct.unpack_from(data, offset)

    def serialize(self, data: bytearray, offset: int):
        ChipT.myStruct.pack_into(
            data,
            offset,
            self.hp,
            self.effectIndex,
            self.ap,
            self.mb,
            self.flags,
            self.rarity,
            self.chipCategory,
            self.hitChance,
            self.dodgeChance,
            self.artIndex,
            self.palleteIndex,
        )

    def getHitChance(self) -> int:
        return self.hitChance

    def getDodgeChance(self) -> int:
        return self.dodgeChance

    ElemMask = 0x1000
    Add = 0x10
    AllAdd = 0x20
    RandomAdd = 0x30
    Pierce = 0x40
    Break = 0x800
    RandomDesc = (
        0x07  # 1 -> sword, 6 -> RandomT, 2 -> RandomCust, 3 -> Muramasa, 4 -> VarSwrd
    )
    # Slasher = 0x3c0 RCnt100
    # FireRate = 0x13a0 Cnt120
    # GutPunch 0x805

    def getElement(self) -> Element:
        return Element((self.flags // 0x1000) & 0x7)

    def isChipPlus(self):
        return self.flags == 0xD1 or (self.flags & 0xFF) == 0xD0

    def isNaviPlus(self):
        return self.flags == 0xD2

    def __str__(self):
        return (
            f"hp: {self.hp} ei: {self.effectIndex} ap: {self.ap} "
            f"mb: {self.mb} rarity: {self.rarity} cat: {self.chipCategory} "
            f"hit: {self.getHitChance()} dodge: {self.getDodgeChance()} art: {self.artIndex} "
            f"pallette: {self.palleteIndex} elem: {self.getElement()} flags: {hex(self.flags)}"
        )


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


class EncounterT:
    """
    Representation of an encounter;
    fields: u1,u2,u3: always 0
    self.chips: selected chips, going from inner to outer, bottom to top
    thresh: thresholds at which the AI will slot in
    """

    myStruct = struct.Struct("<20B")

    def __init__(self, data: bytearray, offset: int):
        self.chips = [0] * 11
        (
            self.idx,
            self.u1,
            self.u2,
            self.u3,
            self.op,
            self.navi,
            self.altNavi,
            *self.chips,
            self.slotBotThresh,
            self.slotTopThresh,
        ) = EncounterT.myStruct.unpack_from(data, offset)

    def serialize(self, data: bytearray, offset: int):
        EncounterT.myStruct.pack_into(
            data,
            offset,
            self.idx,
            self.u1,
            self.u2,
            self.u3,
            self.op,
            self.navi,
            self.altNavi,
            *self.chips,
            self.slotBotThresh,
            self.slotTopThresh,
        )

    def __str__(self):
        return (
            f"idx: {self.idx} navi: {self.navi} chips: {self.chips} "
            f"bTh: {self.slotBotThresh} tTh: {self.slotTopThresh} op: {self.op} altNavi: {self.altNavi}"
        )


def invertMap(m):
    return {v: k for k, v in m.items()}


class MMChar:
    """
    Strings in MMBCC are stores using 16-bit wide characters, and using
    a terminator of the form 0x80LL where LL is the length of the string
    This class has helper method to convert a 16-bit char to/fromm ASCII
    Part of the high byte can be used as a format, in particular 0x06XX
    will render the text bold with a background, as is done in effect
    descriptions
    """

    A = 0x5E
    a = 0xEB

    specialMap = {
        0: " ",
        0x79: "\u00d7",
        0x7C: "?",
        0x7D: "+",
        0x81: "!",
        0x8C: "\u2200",
        0x87: ".",
        0x99: "_",
        0x109: "-",
    }
    inverseMap = invertMap(specialMap)

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
        elif char in cls.inverseMap:
            return cls.inverseMap[char]
        else:
            return 0x5D

    @classmethod
    def terminator(cls, len: int) -> int:
        return 0x8000 | len

    @classmethod
    def isTerminator(cls, char: int) -> bool:
        return (char >> 8) == 0x80


def parsePtr(data: bytearray, offset: int) -> int:
    romLoadOffset = 0x08000000
    (namePtr,) = struct.unpack_from("<I", data, offset)
    namePtr -= romLoadOffset
    return namePtr


class StringT:
    """
    A representation of a String, which is a pointer to a string as
    described in MMChar, normally of length at most 8
    Also stores a format, which we assume everything we parse has, and will emit it
    out
    """

    def __init__(
        self,
        data: bytearray,
        offset: int,
        *,
        strCount: int = 1,
        format: int = 0,
        indirect: bool = False,
    ):
        self.chars = []
        self.lengths = []
        self.format = format
        self.indirect = indirect
        namePtr = self.getNamePtr(data, offset)
        while strCount > 0:
            (c,) = struct.unpack_from("<H", data, namePtr)
            self.chars.append(c & ~format)
            if MMChar.isTerminator(c):
                self.lengths.append(len(self.chars) - 1)
                strCount -= 1
            namePtr += 2

    def getNamePtr(self, data: bytearray, offset: int):
        basePtr = parsePtr(data, offset) if self.indirect else offset
        return parsePtr(data, basePtr)

    def assign(self, val: str):
        if len(val) > self.lengths[0]:
            val = val[: self.lengths[0]]
        for i, c in enumerate(val):
            self.chars[i] = MMChar.convTo(c)
        self.chars[len(val)] = 0x8000 | len(val)

    def changeAttackPower(self, val: int):
        valStr = str(val)
        for lenI, sLen in enumerate(self.lengths):
            i = sLen - 1
            existingNumSize = 0
            while MMChar.isEncodedDigit(self.chars[i]) and i >= 0:
                i -= 1
                existingNumSize += 1
            if existingNumSize == 0:
                continue
            valLen = len(valStr)
            if existingNumSize > valLen:
                # The existing number is larger than the number we
                # are about to write (e.g) 100 -> 80 so let's update
                # the len encoded
                self.lengths[lenI] = sLen - (existingNumSize - valLen)
                sLen = self.lengths[lenI]
                self.chars[sLen] = MMChar.terminator(valLen)

            for i in range(valLen):
                self.chars[sLen - valLen + i] = MMChar.convTo(valStr[i])

    def serialize(self, data: bytearray, offset: int):
        namePtr = self.getNamePtr(data, offset)
        chars = [
            c | (self.format if not MMChar.isTerminator(c) else 0) for c in self.chars
        ]
        totLen = sum(len + 1 for len in self.lengths)
        struct.pack_into(f"<{len(chars)}H", data, namePtr, *chars)

    def __str__(self):
        parts = []
        lastLen = 0
        for len in self.lengths:
            parts.append("".join(MMChar.convFrom(c) for c in self.chars[lastLen:len]))
            lastLen = len + 1
        return "\n".join(parts)


class DataType(Enum):
    """
    DataType represents the various data types, which are generally stored in
    large arrays; DataType has accessors to parse and serialize the data, as well
    as knowledge as to how large each object is and where the home array lives
    """

    Encounter = 1
    Chip = 2
    Sprite = 3
    ChipName = 4
    OpName = 5
    ChipDesc = 6
    EffectDesc = 7

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
        raise KeyError("bad value")

    def getSize(self) -> int:
        if self == DataType.Encounter:
            return 20
        elif self == DataType.Chip:
            return 16
        elif self == DataType.Sprite:
            return 256
        elif (
            self == DataType.ChipName
            or self == DataType.OpName
            or self == DataType.EffectDesc
            or self == DataType.ChipDesc
        ):
            return 4  # Pointer
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
        raise KeyError("bad value")

    def parse(self, data: bytearray, index: int) -> Union[EncounterT, ChipT, StringT]:
        offset = self.getOffset() + index * self.getSize()
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
        raise KeyError("bad value")

    def rewrite(
        self, data: bytearray, index: int, objT: Union[EncounterT, ChipT, StringT]
    ):
        objT.serialize(data, self.getOffset() + index * self.getSize())
