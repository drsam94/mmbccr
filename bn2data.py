from typing import Tuple, Dict
import struct

class BN2Char:
    """
    Strings in MMBN2 are sequences of 1-byte characters, using a special terminator 
    character. Strings are not padded in any way so they are in memory one after another,
    which would make replacing strings with longer strings require a fair amount of tweaking
    """

    A = 0x25
    a = 0x0B

    specialMap = {0: " ",
                 0x3f: "@", # V2
                 0x40: "#", # V3
                 0x41: "-",
                 0x45: "?",
                 0x46: "+",
                 0x4d: '&',
                 0x53: "'",
                 0xe8: "\n",
            }

    inverseMap = {v: k for k,v in specialMap.items()}

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
        return 0xe7

    @classmethod
    def isTerminator(cls, char: int) -> bool:
        return char == 0xe7


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
        ChipT_BN2.myStruct.pack_into(data, offset,
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
            f"unk1: {self.unk1}, mb: {self.mb}, flags: {self.flags}, ap: {self.ap}, "
            f"idx: {self.idx} "
            f"effect: {hex(self.effect)} descBytes: {hex(self.descBytes)} "
            f"img: {hex(self.imgPtr)} col: {hex(self.colorPtr)} thumb: {hex(self.thumbnailPtr)}"
        )

class VirusT_BN2:
    myStruct = struct.Struct("<HBIB")

    def __init__(self, data: bytearray, offset: int):
        (
            self.hp,
            self.unk,
            self.descBytes,
            self.level
        ) = self.myStruct.unpack_from(data, offset)

    def serialize(self, data: bytearray, offset: int):
        self.myStruct.pack_into(data, offset,
            self.hp,
            self.unk,
            self.descBytes,
            self.level
        )

    def __str__(self):
        return (
            f"hp: {self.hp}, descBytes: {hex(self.descBytes)}, lvl: {self.level}, unk: {self.unk}"
        )

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
    myStruct = struct.Struct("<4B")


    @classmethod
    def toString(cls, data: bytearray, offset: int) -> Tuple[str, int]:
        out = ""
        isNotEncounter = False
        isFieldPtr = True
        while True:
            idx, *pdata = cls.myStruct.unpack_from(data, offset)
            offset += 4
            if idx == 0xFF:
                break

            isValidStart = idx == 0 and pdata[2] == 0 and pdata[0] < 4 and pdata[1] < 4
            if (len(out) == 0 or isNotEncounter) and not isValidStart:
                # Encounter always starts with Megaman's position
                isNotEncounter = True
                out += f"{'Field:' if isFieldPtr else 'Enc:'} {hex( idx + (pdata[0] << 8) + (pdata[1] << 16)  + (pdata[2] << 24))} "
                isFieldPtr = not isFieldPtr
                continue
            if isNotEncounter:
                offset -= 4
                break
            out += f"{cls.virusNameMap.get(idx, idx)} @ {pdata[0]},{pdata[1]} {pdata[2]}; "
        return out, offset

    virusNameMap : Dict[int, str] = {}
    @classmethod
    def setVirusNameMap(cls, m: Dict[int, str]):
        cls.virusNameMap = m

"""
Interface based on fixed-size API; BN2 has a lot more variable size structs so will require slightly different
handling
    def __init__(self, data: bytearray, offset: int):
        self.viruses = [0] * 3
        self.data = [0] * 9
        (
            self.viruses[0],
            self.data[0],
            self.data[1],
            self.data[2],
            self.viruses[1],
            self.data[3],
            self.data[4],
            self.data[5],
            self.viruses[2],
            self.data[6],
            self.data[7],
            self.data[8]
        ) = self.myStruct.unpack_from(data, offset)

    def serialize(self, data: bytearray, offset: int):
        self.myStruct.pack_into(data, offset,
            self.viruses[0],
            self.data[0],
            self.data[1],
            self.data[2],
            self.viruses[1],
            self.data[3],
            self.data[4],
            self.data[5],
            self.viruses[2],
            self.data[6],
            self.data[7],
            self.data[8]
        )



    def __str__(self):
        virusNames = [self.virusNameMap.get(v, v) for v in self.viruses]
        return (
            f"viruses: {virusNames}, data: {[hex(d) for d in self.data]}"
        )
"""

"""
0x0104E7 -- start of chip #262 of size 32
0x00E477 -- start of cannon
class ChipT_BN2 {
    uint8_t unknown1;
    uint8_t unknown2;
    uint8_t 00 if no dmg 01 if normal;
    uint8_t MB; // CONFIRM
    unit16_t attack; // CONFIRM
    uint16_t index; // 231 for FireGspl, 229 for GateSP
    uint8_t unknown[8];
    uint32_t imgPtr;
    uint32_t colorPtr;
    uint8_t other[8];
}

0x73328c -- first virus name pointer
0x733294 -- Text Pointer for 'Mettaur'
0x728792 -- Text Pointer for 'Shotgun'
0x728779 -- Test Pointer for 'Cannon'
31 0F 1E 1E 0B 1F 1C E7
M  e  t  t  a  u  r  <>
0x7355a1 -- start of captions
0x729679 -- Chip descriptions
0x1515c -- Mettaur Virus Status

8 Byte Virus Struct
28 00 (HP)
1E (idk)
01 (Sprite and behavior)
04
01 
18
00 (Level, 00/01/02)
Mettaur: 28 00 1E 01 04 01 18 00
Bunny:   28 10 30 05 04 08 18 00 (15 Damage...?)
"""