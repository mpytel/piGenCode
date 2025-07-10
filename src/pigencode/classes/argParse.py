import os
import sys
import argparse
import shlex
from ..defs.logIt import color, cStr
from ..commands.commands import Commands, cmdDescriptionTagStr


class PiHelpFormatter(argparse.RawTextHelpFormatter):
    # Corrected _max_action_length for the indenting of subactions
    def add_argument(self, action):
        if action.help is not argparse.SUPPRESS:
            # find all invocations
            get_invocation = self._format_action_invocation
            invocations = [get_invocation(action)]
            current_indent = self._current_indent
            for subaction in self._iter_indented_subactions(action):
                # compensate for the indent that will be added
                indent_chg = self._current_indent - current_indent
                added_indent = 'x'*indent_chg
                print('added_indent', added_indent)
                invocations.append(added_indent+get_invocation(subaction))
            # print('inv', invocations)

            # update the maximum item length
            invocation_length = max([len(s) for s in invocations])
            action_length = invocation_length + self._current_indent
            self._action_max_length = max(self._action_max_length,
                                          action_length)

            # add the item to the list
            self._add_item(self._format_action, [action])


def str_or_int(arg):
    try:
        return int(arg)  # try convert to int
    except ValueError:
        pass
    if type(arg) == str:
        return arg
    raise argparse.ArgumentTypeError("arguments must be an integer or string")


class ArgParse():

    def __init__(self):
        # Parse command-specific options (double hyphen) before main parsing
        self.cmd_options = {}
        self.filtered_args = self._extract_cmd_options(sys.argv[1:])
        if not sys.stdin.isatty():
            self.parser = argparse.ArgumentParser(add_help=False)
            self.parser.add_argument('commands', nargs=1)
            self.parser.add_argument('arguments', nargs='*')
            self.args = self.parser.parse_args(self.filtered_args)
        else:
            _, tCols = os.popen('stty size', 'r').read().split()
            tCols = int(tCols)
            indentPad = 8
            def formatter_class(prog): return PiHelpFormatter(
                prog, max_help_position=8, width=tCols)
            commandsHelp = ""
            argumentsHelp = ""
            theCmds = Commands()
            commands = theCmds.commands
            switchFlag = theCmds.switchFlags["switcheFlags"]
            for cmdName in commands:
                needCmdDescription = True
                needArgDescription = True
                arguments = commands[cmdName]
                argumentsHelp += cStr(cmdName, color.YELLOW) + ': \n'
                for argName in arguments:
                    if argName[-len(cmdDescriptionTagStr):] == cmdDescriptionTagStr:
                        cmdHelp = cStr(cmdName, color.YELLOW) + \
                            ': ' + f'{arguments[argName]}'
                        if len(cmdHelp) > tCols:
                            indentPad = len(cmdName) + 2
                            cmdHelp = formatHelpWidth(
                                cmdHelp, tCols, indentPad)
                        else:
                            cmdHelp += '\n'
                        commandsHelp += cmdHelp
                        needCmdDescription = False
                    else:
                        argHelp = cStr(
                            f'  <{argName}> ', color.CYAN) + f'{arguments[argName]}'
                        if len(argHelp) > tCols:
                            indentPad = len(argName) + 5
                            argHelp = ' ' + \
                                formatHelpWidth(argHelp, tCols, indentPad)
                        else:
                            argHelp += '\n'
                        argumentsHelp += argHelp
                        needArgDescription = False
                if needArgDescription:
                    argumentsHelp = argumentsHelp[:-1]
                    argumentsHelp += "no arguments\n"
                if needCmdDescription:
                    commandsHelp += cStr(cmdName, color.WHITE) + '\n'
            #   commandsHelp = commandsHelp[:-1]

            self.parser = argparse.ArgumentParser(
                description="pi pip package pip package pip package",
                epilog="Have Fun!", formatter_class=formatter_class)

            self.parser.add_argument("commands",
                                     type=str,
                                     nargs=1,
                                     metavar=f'{cStr(cStr("Commands", color.YELLOW), color.UNDERLINE)}:',
                                     help=commandsHelp)

            self.parser.add_argument("arguments",
                                     type=str_or_int,
                                     nargs="*",
                                     metavar=f'{cStr(cStr("Arguments", color.CYAN), color.UNDERLINE)}:',
                                     # metavar="arguments:",
                                     help=argumentsHelp)

            for optFlag in switchFlag:
                flagHelp = switchFlag[optFlag]
                self.parser.add_argument(
                    f'-{optFlag}', action='store_true', help=flagHelp)
            self.args = self.parser.parse_args(self.filtered_args)

    def _extract_cmd_options(self, args):
        '''Extract command-specific options(--option) from arguments'''
        
        # Define which options are flags (no value) vs options that take values
        flag_options = {
            'dry-run', 'create-missing', 'validate', 'stats', 'force', 'help'
        }
        value_options = {
            'filter', 'exclude-pattern'
        }
        
        filtered_args = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('--'):
                # Handle command-specific options
                option_name = arg[2:]  # Remove --
                
                if option_name in flag_options:
                    # This is a flag option (no value)
                    self.cmd_options[option_name] = True
                    i += 1
                elif option_name in value_options:
                    # This option takes a value
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        self.cmd_options[option_name] = args[i + 1]
                        i += 2  # Skip both option and value
                    else:
                        # Missing value, treat as flag
                        self.cmd_options[option_name] = True
                        i += 1
                else:
                    # Unknown option - use the old logic as fallback
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        # Option with value
                        self.cmd_options[option_name] = args[i + 1]
                        i += 2  # Skip both option and value
                    else:
                        # Option without value (flag)
                        self.cmd_options[option_name] = True
                        i += 1
            else:
                filtered_args.append(arg)
                i += 1
        return filtered_args


def formatHelpWidth(theText, tCols, indentPad=1) -> str:
    # this uses the screen with to estabhish tCols

    # tCols = int(tCols) - 20
    # print(tCols)
    # tCols = 60
    spPaddingStr = ' '*indentPad
    rtnStr = ''
    outLine = ''
    tokens = shlex.split(theText)
    # print(tokens)
    # exit()
    for token in tokens:  # loop though tokens
        chkStr = outLine + token + ' '
        if len(chkStr) <= tCols:                # check line length after concatinating each word
            outLine = chkStr                    # less the the colums of copy over to outline
        else:
            if len(token) > tCols:
                # when the match word is longer then the terminal character width (tCols),
                # DEBUG how it should be handeled here.
                print(f'here with long match.group():\n{token}')
                exit()
                chkStr = token
                while len(chkStr) > tCols:  # a single word may be larger the tCols
                    outLine += chkStr[:tCols]
                    chkStr = f'\n{chkStr[tCols:]}'
                outLine += chkStr
            else:
                rtnStr += outLine
                outLine = f'\n{spPaddingStr}{token} '
    rtnStr += f'{outLine}\n'
    # rtnStr = rtnStr[:-1]
    return rtnStr
