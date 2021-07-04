/**
(1) Play with memory, see where stuff changes
(2) Look in library, look for places in memory 23 <-> 16 swapping chips
(3) Identify folder layout order
(4) search ROM for folders of NAVIs
(5) Look at tile data, identify sprite information, search for that in ROM
(6) Search for literal use of pointers in the ROM, find a reference to chip folder,
    inspect nearby pointers
(7) See one of these pointers is to an array of pointers, play with it and deduce it
    is the pointers to chip names
(8) Check other pointers around there, find chip descriptions
(9) Play with strings, eventually learn how chip effect descriptions are rendered, then
    search for such strings
*/
// Encounter array: 0x229900
struct Encounter {
    uint8_t enounterIdx; // ?
    uint8_t unknown;
    uint8_t unknown;
    uint8_t unknown;
    uint8_t unknown; // Nonzero, 55, 3F
    uint8_t navi; // Library Code + 5
    uint8_t unknown
    uint8_t chipBottomFirst;
    uint8_t chipTopFirst;
    uint8_t chipBottomMiddle;
    uint8_t chipMiddleMiddle;
    uint8_t chipTopMiddle;
    uint8_t chipBottomEnd;
    uint8_t chip2End;
    uint8_t chip3End;
    uint8_t chip4End;
    uint8_t chipSlotBot;
    uint8_t chipSlotDown;
    uint8_t slotBotThresh;
    uint8_t slotTopThresh;
};
static_assert(sizeof(Encounter) == 20)

// Chip array: 0x22741c
struct Chip {
    uint16_t hp;
    uint16_t effect_index; // 5A 00
    uint16_t AP; // 5A 00 break?
    uint16_t MB; // 96
    //uint8_t j; // flags?
    //uint8_t type/flags; // 0 -> Normal, 10 -> Fire, 20 -> Aqua, 30 -> Wood, 40 -> Elec
    uint16_t flags;
    uint8_t rarity; // 05
    uint8_t a; // 01 (0 or 1 for navis, 6 for unlisted)
    uint8_t b; // 52 hit chance / 255
    uint8_t c; // 49 (navi only) dodge chance / 255
    uint8_t index // art index;
    uint8_t e; // pallette index
}

/**
chipBase 0822740c
chipNameTextPtrArray 0822bb8c
chipDescArray (Select Desc) 0822c35c
OperatorName 0822d69c

HrtFlash

0xe9c20
0xefdc2

*/