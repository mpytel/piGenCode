import sys, traceback
from argparse import Namespace
from ..defs.logIt import printIt, lable
from .commands import Commands
from .cmdOptSwitchbord import cmdOptSwitchbord
from ..classes.argParse import ArgParse

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
                if len(sys.argv) == 3 and switchFlagChk[0] in '-+?':
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
                exec(f'from ..commands.{theCmd} import {theCmd}')
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
