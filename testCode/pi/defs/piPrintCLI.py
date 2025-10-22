# piPrintCLI functions - synced from existing code
import os
import math
from .logIt import color

def getPiIndexerStr(thePiIndexerTitels: dict, thePiIndexerHash: dict | None = None, padding=6) -> str:
    spPaddingStr = f'{" "* padding}'
    if thePiIndexerHash:
        userStr = f'{color.GREEN}u:{color.RESET} {thePiIndexerTitels["piUser"],thePiIndexerHash["piUser"]}'
        realmStr = f'{color.GREEN}r:{color.RESET} {thePiIndexerTitels["piUser"],thePiIndexerHash["piRealm"]}'
        domainStr = f'{color.GREEN}d:{color.RESET} {thePiIndexerTitels["piUser"],thePiIndexerHash["piDomain"]}'
        subjectStr = f'{color.GREEN}s:{color.RESET} {thePiIndexerTitels["piUser"],thePiIndexerHash["piSubject"]}'
    else:
        userStr = f'{color.GREEN}u:{color.RESET} {thePiIndexerTitels["piUser"]}'
        realmStr = f'{color.GREEN}r:{color.RESET} {thePiIndexerTitels["piRealm"]}'
        domainStr = f'{color.GREEN}d:{color.RESET} {thePiIndexerTitels["piDomain"]}'
        subjectStr = f'{color.GREEN}s:{color.RESET} {thePiIndexerTitels["piSubject"]}'
    # get current consol size
    # rows, columns = os.popen('stty size', 'r').read().split()
    prtStr = f'{userStr} {realmStr} {domainStr} {subjectStr}'
    return f'{spPaddingStr}{prtStr}'
# wordListLen = lambda l: sum(list(map(len, l))) + len(l)
def getFormattedSD(spPaddingStr, sdLines, leadingPad = True) -> str:
    tRows, tCols = os.popen('stty size', 'r').read().split()
    tCols = int(tCols)
    rtnStr = ''
    for sdLine in sdLines:
        outLine = spPaddingStr
        thewords = sdLine.split()
        for word in thewords: #finditer(pattern, sdLine):  # break out and cycle though words
            chkStr = outLine + word + ' '        # check the lengh of the line
            if len(chkStr) <= tCols:
                outLine = chkStr                    # less the the colums of copy over to outline
            else:
                if len(word) > tCols:
                    # print(f'here with long match.group():\n{match.group()}')
                    # exit()
                    chkStr = word
                    while len(chkStr) > tCols:  # a single word may be larger the tCols
                        outLine += chkStr[:tCols]
                        chkStr = f'\n{chkStr[tCols:]}'
                    outLine += chkStr
                else:
                    rtnStr += outLine
                    outLine = f'\n{spPaddingStr}{word.strip()} '

        rtnStr += f'{outLine}\n'
    rtnStr = rtnStr[:-1]
    if not leadingPad: rtnStr = rtnStr.strip()
    return f'{color.CYAN}{rtnStr}{color.RESET}'
def currPiStr(thePi: dict) -> str:
    tRows, tCols = os.popen('stty size', 'r').read().split()
    tCols = int(tCols)
    emDash = '—'*tCols
    spPaddingStr = f'{" "*6}'
    rtnStr = f'{emDash}\n'
    rtnStr += f'{color.YELLOW}{thePi["piBase"]["piType"]}: {color.GREEN}{thePi["piBase"]["piTitle"]}{color.RESET}\n'
    sdLines = thePi["piBase"]["piSD"].split('\n')
    sdStr = getFormattedSD(spPaddingStr, sdLines)
    rtnStr += f'{sdStr}'
    return rtnStr
def currIndexerStr(indexerTitels) -> str:
    tRows, tCols = os.popen('stty size', 'r').read().split()
    tCols = int(tCols)
    emDash = '—'*tCols
    currIndexerStr = getPiIndexerStr(indexerTitels, None, False)
    currIndexerStr = f'{color.YELLOW}PI: {color.RESET}{currIndexerStr}'
    return f'{emDash}\n{currIndexerStr}\n{emDash}'
def dependentPiStr(thePi: dict) -> str:
    '''Return formated pi string'''
    spPaddingStr = f'{" "*6}'
    rtnStr = f'{color.YELLOW}{thePi["piBase"]["piType"]}: '
    rtnStr += f'{color.GREEN}{thePi["piBase"]["piTitle"]}{color.RESET}\n'
    sdLines = thePi["piBase"]["piSD"].split('\n')
    sdStr = getFormattedSD(spPaddingStr, sdLines)
    rtnStr += f'{sdStr}'
    return rtnStr
def getPiListStr(thePi: dict, piList=False) -> str:
    spPaddingStr = f'{" "*6}'
    typeStr = f'{color.RED}{thePi["piBase"]["piType"]}{color.RESET}'
    if piList:
        titleStr = f'{thePi["piBase"]["piTitle"]}'# ({thePi["piID"]})'
    else:
        titleStr = f'{thePi["piBase"]["piTitle"]} ({thePi["piID"]})'
    sdLines = thePi["piBase"]["piSD"].split('\n')
    sdStr = getFormattedSD(spPaddingStr, sdLines)
    prtStr = f'{typeStr}: {titleStr}\n'
    prtStr += f'{sdStr}\n'
    return prtStr
def getIndexedStr(strList: list, numOfCol: int = 1, nextLinePadding: int = 0) -> str:
    """
    Formats a list of strings into indexed, multi-column output, with optional
    left padding for lines after the first.

    Args:
        strList: A list of strings to be formatted.
        numOfCol: The number of columns to arrange the strings into.
                  Defaults to 1. Must be a positive integer.
        nextLinePadding: The number of spaces to pad on the left for every
                         line except the first. Defaults to 0. Must be a
                         non-negative integer.

    Returns:
        A single formatted string representing the indexed, multi-column output.
        Returns an empty string if strList is empty.
    """
    if not strList:
        return ""

    if numOfCol <= 0:
        raise ValueError("numOfCol must be a positive integer.")
    if nextLinePadding < 0:
        raise ValueError("nextLinePadding must be a non-negative integer.")

    indexed_items = [f"{i+1}. {item}" for i, item in enumerate(strList)]
    max_item_len = 0
    if indexed_items: # Ensure there's at least one item to check its length
        max_item_len = max(len(item) for item in indexed_items)

    # Calculate column width: max item length + some buffer (e.g., 2 spaces)
    # This buffer ensures items in adjacent columns don't touch even if they're
    # exactly the same length.
    column_width = max_item_len + 2

    num_rows = math.ceil(len(indexed_items) / numOfCol)
    output_lines = []

    for row_idx in range(num_rows):
        current_line_items = []
        for col_idx in range(numOfCol):
            # item_index = row_idx + col_idx * num_rows # vertical numbering
            item_index = row_idx * numOfCol + col_idx # horizontal numbering
            if item_index < len(indexed_items):
                item = indexed_items[item_index]
                # Pad individual items to align columns
                current_line_items.append(item.ljust(column_width))
            else:
                # Add empty padding for incomplete rows/columns
                current_line_items.append(" " * column_width)

        line = "".join(current_line_items).rstrip() # Remove trailing spaces from the last column
        if row_idx > 0:
            output_lines.append(" " * nextLinePadding + line)
        else:
            output_lines.append(line)

    return "\n".join(output_lines)


