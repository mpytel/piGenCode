from pigencode.classes.piSeeds import PiSeeds
from pigencode.classes.piGermSeeds import PiGermSeeds

def germinateSeeds(fileName) -> PiGermSeeds:
    piSeeds = PiSeeds(fileName)
    seedPis = PiGermSeeds(piSeeds)
    return seedPis

