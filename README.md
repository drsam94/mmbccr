# mmbccr
Randomizer for Magaman Battle Network games. Currently the following games are supported:
 * Megaman Battlechip Challenge (US)
 * Megaman Battle Network 2 (US)

This program only has a command line interface, though at some times may have a web interface also

For inquiries, either post issues/pull requests to github or contact
sam@samdonow.com

# How to use
 Requires a modern version of python (>= 3.6), and a US ROM of Megaman Battlechip challenge, or of Megaman Battle Network 2
```
    # Easiest invocation Usage
    python rando.py inFile outFile
    # With optional flags, or --help to see these options
    # By default either rando_bn2.conf or rando_bcc.conf will be used
    python rando.py inFile outFile [--conf rando.conf] [--seed seed]
```
# tools
* rando.py: The randomizer itself
* inspection.py: A tool that prints out the contents of a ROM of various datatypes
* search.py: A tool for finding patterns in a ROM to detect what we are looking for
* strconv.py: Encode/Decode a string to bcc format
* distribution.py: A tool to play with the random distribtions used in the randomizer


# Features (BN2)
This randomizer can randomize the following aspects of the game:
 * The contents of obtained folders
 * The codes of battlechips available
 * The drop tables of random encounters 
   * Somewhat reasonable drop tables can be added for viruses normally not found in encounters
 * The enemies faced in randomized and static encounters
 * The chips available from NetDealers
 * Chips and Zenny dropped from GMD

# Logic (BN2)
See documentation of supported configuration options in rando_bn2.conf (which will be loaded by the randomizer by default)

# Known Deficiencies (BN2)
 * FtrSword and KnghtSwrd are not supported in NetDealers due to crashes observed in testing (apparently due to the details of how the text data for these chips are stored)
 * Certain GMDs do not have independent their chip or code set independently from other GMDs. In these cases, the code displayed in text may be different from what ends up in the folder. An example of this are the chips that are normally WideSwrd Y and LongSwrd Y in Den 3; if WideSwrd is unchanged and LongSwrd is randomized to a chip that doesn't support the code Y, then the message will say an e.g Cannon Y is received, but that will be converted to a valid code of Cannon in the pack
 * I am still investigating how BMDs and PMDs are stored in order to randomize those
 * Randomizing Navis into battles seems to work, but I have not yet supported it due to not having thought through the best way to apply it
 * Virus battles are currently not randomized with regards for the field:
   * CanDevil viruses can be spawned without candles
   * Mushy viruses can be spawned on non-grass
   * The Lavagon family of viruses are not ranzomized due to this restriction
 * If the available codes of chips are randomized, then code-based Program Advances won't work (e.g Z-Cannon) though other P.As (e.g Gater) will work. This can be worked around but I have not done so yet.

# Features (BCC)
This randomizer can randomizer the following aspects of the game:

* The statistics of battle chips (and/or navi chips)
* The chips in the decks of encounters with other navis
* Which encounters occur at which points
* The operators of battles
* The names of battle chips

# Logic (BCC)
To make a randomizer fun to play, it shouldn't just randomize arbitrarily. To this end, I have added the following options to customize how the randomizing works to tailor the experience. The style of randomization is determined by a conffile, the default one being rando.conf

* ChipRange - specify values for the range to randomize over for chip mb/hp/ap. These values are percentages, so a value of 100 means a value will be picked uniformly between 10 and twice the original value
* NaviRange - live ChipRange, but to pick separate values for Navi chips
* ChipGlobal - options for how to randomize chips
    * preserveOrdering: Ensure that chips in a series maintain their relationships of "strictly more powerly", e.g ensure that M-Cannon always has more ap,mb,and hp than Hi-Cannon.
    * randomizeStartingChips: Randomize the starting chips in the player's folder, like chips in an encounter (defaults to true)
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
