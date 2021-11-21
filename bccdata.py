from typing import List, Iterable, Dict
from enum import Enum
import itertools
import struct


class PrintOpts:
    verbose: bool = False
    refdata: bytes = b""


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
            self.pri,
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
            self.pri,
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
    # 0x25 -> 'Fire type all add navi attack

    def getElement(self) -> Element:
        return Element((self.flags // 0x1000) & 0x7)

    def isChipPlus(self):
        return self.flags == 0xD1 or (self.flags & 0xFF) == 0xD0

    def isNaviPlus(self):
        return self.flags == 0xD2

    def __str__(self):
        return (
            f"hp: {self.hp} pri: {self.pri} ap: {self.ap} "
            f"mb: {self.mb} rarity: {self.rarity} cat: {self.chipCategory} "
            f"hit: {self.getHitChance()} dodge: {self.getDodgeChance()} art: {self.artIndex} "
            f"pallette: {self.palleteIndex} elem: {self.getElement()} flags: {hex(self.flags)}"
        )


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
        """
        TODO: factor out dependence with NameMaps to allow this
        if PrintOpts.verbose:
            getChipName = lambda idx: str(
                DataType.ChipName.parse(PrintOpts.refdata, idx - 1)
            )
        else:
        """
        getChipName = lambda idx: str(idx)
        return (
            f"idx: {self.idx} navi: {getChipName(self.navi)} chips: [{', '.join(getChipName(c) for c in self.chips)}] "
            f"bTh: {self.slotBotThresh} tTh: {self.slotTopThresh} op: {self.op} altNavi: {self.altNavi}"
        )


class StartingChipsT:
    """
    The list of chips in your starting folder
    """

    myStruct = struct.Struct("<7B")

    def __init__(self, data: bytearray, offset: int):
        self.chips = [0] * 7
        (*self.chips,) = StartingChipsT.myStruct.unpack_from(data, offset)

    def serialize(self, data: bytearray, offset: int):
        StartingChipsT.myStruct.pack_into(
            data,
            offset,
            *self.chips,
        )

    def __str__(self):
        """
        TODO: refactor dependencies for this to be possible
        (NameMaps)
        if PrintOpts.verbose:
            getChipName = lambda idx: str(
                DataType.ChipName.parse(PrintOpts.refdata, idx - 1)
            )
        else:
        """
        getChipName = lambda idx: str(idx)
        return f" chips: [{', '.join(getChipName(c) for c in self.chips)}] "


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
            if MMChar.convFrom(self.chars[i]) == "+":
                # For chips with a '+' attack value, we need to modify
                # the serialization around this, it isn't at the end
                i -= 1
                valStr += "+"
                existingNumSize += 1
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
