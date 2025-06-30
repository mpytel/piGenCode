from classes.piSeeds import PiSeeds
from classes.piGermSeeds import PiGermSeeds

def germinateSeeds(fileName) -> PiGermSeeds:
    piSeeds = PiSeeds(fileName)
    seedPis = PiGermSeeds(piSeeds)
    return seedPis

