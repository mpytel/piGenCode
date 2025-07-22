import sys, traceback
from argparse import Namespace
from pigencode.defs.logIt import printIt, lable
from .commands import Commands
from .cmdOptSwitchbord import cmdOptSwitchbord
from pigencode.classes.argParse import ArgParse
from pigencode.classes.piSeedRegistry import command_registry

cmdObj = Commands()
commands = cmdObj.commands
switchFlags = cmdObj.switchFlags["switcheFlags"]

def cmdSwitchbord(argParse: ArgParse):
    global commands
    theCmd = 'notSet'
    try:
        if len(sys.argv) > 1:
            if len(sys.argv) > 2:
                switchFlagChk = sys.argv[2]
                if len(sys.argv) == 3 and switchFlagChk[0] in '-+?' and not switchFlagChk.startswith('--'):
                    if switchFlagChk[1:] in switchFlags.keys():
                        print(f'00001: {switchFlagChk}')
                        cmdOptSwitchbord(switchFlagChk, switchFlags)
                    else:
                        if switchFlagChk not in ["-h", "--help"]:
                            printIt(f'{switchFlagChk} not defined',lable.WARN)
                        else:
                            argParse.parser.print_help()
                    exit()
            args: Namespace = argParse.args
            theCmd = args.commands[0]
            if theCmd in commands.keys():
                # Use registry pattern instead of exec()
                try:
                    command_registry.execute_command(theCmd, argParse)
                except ValueError:
                    # Fallback to old exec() method if command not in registry
                    exec(f'from pigencode.commands.{theCmd} import {theCmd}')
                    exec(f'{theCmd}(argParse)')
            else:
                print(args)
                printIt(f'Command "{theCmd}" not present.\n',lable.ERROR)
                argParse.parser.print_help()
        else:
            argParse.parser.print_help()
    except Exception as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'{theCmd}\n{tb_str}', lable.ERROR)
        exit()


# Register all commands with the command registry for lazy loading
# This replaces the exec() pattern with a cleaner registry approach
def _register_commands():
    """Register all available commands with the command registry"""
    # Register commands for lazy loading
    command_registry.register_lazy("newCmd", "newCmd")
    command_registry.register_lazy("modCmd", "modCmd")
    command_registry.register_lazy("rmCmd", "rmCmd")
    command_registry.register_lazy("germSeed", "germSeed")
    command_registry.register_lazy("genCode", "genCode")
    command_registry.register_lazy("syncCode", "syncCode")
    command_registry.register_lazy("reorderSeeds", "reorderSeeds")

# Initialize command registration
_register_commands()
