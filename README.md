# mmbccr
A Randomizer for Megaman Battlechip Challenge. Only has a CLI

For inquiries, either post issues/pull requests to github or contact
root@melancholytree.com

# How to use
 Requires a modern version of python (>= 3.6), and a ROM of Megaman Battlechip challenge
```
    python rando.py inFile outFile
```
# tools
* rando.py: The randomizer itself
* inspection.py: A tool that prints out the contents of a ROM of various datatypes
* search.py: A tool for finding patterns in a ROM to detect what we are looking for
* strconv.py: Encode/Decode a string to bcc format
* distribution.py: A tool to play with the random distribtions used in the randomizer
# Process
Some documentation of how I went through finding out how the game stores data
* Play with memory, see where stuff changes
* Look in library, look for places in memory 23 <-> 16 swapping chips
* Identify folder layout order
* search ROM for folders of NAVIs
* Look at tile data, identify sprite information, search for that in ROM
* Search for literal use of pointers in the ROM, find a reference to chip folder, inspect nearby pointers
* See one of these pointers is to an array of pointers, play with it and deduce it is the pointers to chip names
* Check other pointers around there, find chip descriptions
* Play with strings, eventually learn how chip effect descriptions are rendered, then search for such strings

# Features
This randomizer can randomizer the following aspects of the game:

* The statistics of battle chips (and/or navi chips)
* The chips in the decks of encounters with other navis
* Which encounters occur at which points
* The operators of battles
* The names of battle chips

# Logic
To make a randomizer fun to play, it shouldn't just randomize arbitrarily. To this end, I have added the following options to customize how the randomizing works to tailor the experience. The style of randomization is determined by a conffile, the default one being rando.conf

* ChipRange - specify values for the range to randomize over for chip mb/hp/ap. These values are percentages, so a value of 100 means a value will be picked uniformly between 10 and twice the original value
* NaviRange - live ChipRange, but to pick separate values for Navi chips
* ChipGlobal - options for how to randomize chips
    * preserveOrdering: Ensure that chips in a series maintain their relationships of "strictly more powerly", e.g ensure that M-Cannon always has more ap,mb,and hp than Hi-Cannon.
* Encounters - options for how to randomize encounters
    * randomizeChips - randomize the chips in the Navi's deck; by default they will be randomized to other chips with the same MB values
    * randomizeNavi - If specified, the navi chip for the deck will also be randomized
    * smartAtkPlus - If specified, no enemy decks will have Attack+/Elem+/Navi+ chips in locations that could never accomplish anything
    * fillChips - If specified, empty slots in a deck will be filled with 10 MB chips
    * shuffle - shuffle encounters themselves, rather than  the content of encounters (i.e the first fight in the GP could be against the final boss Bass GS deck)
    * randomizeOperators - Randomize the operator of encounters (purely aesthetic)
    * upgradeChipParam - Rather than always exchange chips of equal MB, replace chips with MB of original + X, where X is a random variable following a Poisson distribution of the provided parameter.
* Names - Whether names should be randomized (purely asthetic)
    * randomizeNames - if set, randomize chip names
    * chipNames - path to a file to be used for chip names. One name per line, names must be at most 8 chars. Some names may be truncated if randomized onto chips with shorter names
