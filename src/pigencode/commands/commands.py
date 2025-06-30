import json, os
from copy import copy
import inspect

cmdDescriptionTagStr = "_description"

class Commands(object):
    def __init__(self) -> None:
        self.cmdFileDir = os.path.dirname(inspect.getfile(self.__class__))
        self.cmdFileName = os.path.join(self.cmdFileDir, "commands.json" )
        with open(self.cmdFileName, "r") as fr:
            rawJson = json.load(fr)
            self._switchFlags = {}
            try:
                self._switchFlags["switcheFlags"] = copy(rawJson["switcheFlags"])
                del rawJson["switcheFlags"]
            except: self._switchFlags["switcheFlags"] = {}
            self._commands = rawJson
        self.checkForUpdates()

    @property
    def commands(self):
        return self._commands

    @commands.setter
    def commands(self, aDict: dict):
        self._commands = aDict
        self._writeCmdJsonFile()

    @property
    def switchFlags(self):
        return self._switchFlags

    @switchFlags.setter
    def switchFlags(self, aDict: dict):
        self._switchFlags = aDict
        self._writeCmdJsonFile()

    def _writeCmdJsonFile(self):
        # outJson = copy(self._switchFlags)
        # outJson.update(self._commands)
        outJson = self._switchFlags | self._commands
        with open(self.cmdFileName, "w") as fw:
            json.dump(outJson, fw, indent=2)

    def checkForUpdates(self):
        dirList = os.listdir(self.cmdFileDir)
        for aFile in dirList:
            if aFile[:-2] == "py":
                chkName = aFile[:-3]
                if chkName not in self.commands and chkName != "commands":
                    self.commands[chkName] = [" - No argument"]
