# mmbccr
 A Randomizer for Megaman Battlechip Challenge

# How to use
 Requires a modern version of python, and a ROM of Megaman Battlechip challenge
```
    python rando.py inFile outFile
```
# tools
    * rando.py: The randomizer itself
    * inspection.py: A tool that prints out the contents of a ROM of various datatypes
    * search.py: A tool for finding patterns in a ROM to detect what we are looking for
    * strconv.py: Encode/Decode a string to bcc format
# Process
    Some documentation of how I went through finding out how the game stores data
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