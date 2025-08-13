from typing import Any
import logging
from os import remove
from pathlib import Path
from .piFileIO import getKeyItem, resetPiRC
from pi.piClasses.piBase import PiBase

NEWPI = 1
CHGPI = 1
EDSD = 1
RMSD = 1

loglevel = NEWPI
pisDir = getKeyItem('pisDir')
if pisDir: pisPath = Path(pisDir)
else:
    resetPiRC()
    pisPath = Path(getKeyItem('pisDir'))
piWaveDir = pisPath.joinpath('piWave')
if not piWaveDir.is_dir():
    piWaveDir.mkdir(mode=511, parents=True, exist_ok=False)
filename = str(piWaveDir.joinpath('piWave000.pi'))
log_handler = logging.FileHandler(filename)

# Define custom logging levels.
# Choose integer values that don't conflict with standard levels:
# CRITICAL=50, ERROR=40, WARNING=30, INFO=20, DEBUG=10, NOTSET=0
logging.addLevelName(NEWPI, "NEWPI")
logging.addLevelName(CHGPI, "CHGPI")
logging.addLevelName(EDSD, "EDSD")
logging.addLevelName(RMSD, "RMSD")

# Create a custom logger class that inherits from logging.Logger
class PiLogger(logging.Logger):
    """A custom logger with methods for PI ID events."""

    def newpi(self, msg: str, *args: Any, **kws: Any) -> None:
        """Log a message with the NEWPI level."""
        self.log(NEWPI, msg, *args, **kws)

    def chgpi(self, msg: str, *args: Any, **kws: Any) -> None:
        """Log a message with the CHGPI level."""
        self.log(CHGPI, msg, *args, **kws)

    def editsd(self, msg: str, *args: Any, **kws: Any) -> None:
        """Log a message with the EDSD level."""
        self.log(EDSD, msg, *args, **kws)

    def removepi(self, msg: str, *args: Any, **kws: Any) -> None:
        """Log a message with the RMSD level."""
        self.log(RMSD, msg, *args, **kws)


# Register our custom logger class so that all new loggers use it.
logging.setLoggerClass(PiLogger)


def setup_log(name) -> PiLogger:
    logger = logging.getLogger(name)
    logger.setLevel(loglevel)
    log_format = logging.Formatter('pi %(message)s')
    log_handler.setLevel(loglevel)
    log_handler.setFormatter(log_format)
    logger.addHandler(log_handler)
    return logger  # type: ignore

piLogger = setup_log('PiLogger')

def piPiLogStr(piBase: PiBase) -> str:
    outStr = ''
    splitCount = len(piBase.piType.split())
    if splitCount > 1:  outStr = f'\'{piBase.piType}\''
    else: outStr = piBase.piType
    splitCount = len(piBase.piTitle.split())
    if splitCount > 1: outStr += f' \'{piBase.piTitle}\''
    else: outStr += ' ' + piBase.piTitle
    if piBase.piSD:
        splitCount = len(piBase.piSD.split())
        if splitCount > 1: outStr += f' \'{piBase.piSD}\''
        else: outStr += ' ' + piBase.piSD
    # print('piLogStr:',outStr)
    return outStr

def rmPiWaveFile():
    testName = Path(filename)
    if testName.is_file():
        remove(Path(filename))
