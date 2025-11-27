from re import compile
from getpass import getpass
from pi.defs.logIt import printIt, label, cStr, color
from pi.defs.piFileIO import piAPIURL
from fastapi import status
import requests as req
from re import findall, escape, compile as reCompile, match as reMatch
from pathlib import Path
from ..piApi.piAPIModel import UserLoginSchema
import string

def getValidPassword() -> bool:

    validUserName = "A valid username:\n"
    validUserName += "  1) is 4-20 characters long"
    validUserName += "  2) start with a number or letter"
    validUserName += "  3) containes at least one digit"
    validUserName += "  4) containes an uppercase letter"
    validUserName += "  5) containes a lowercase letter"
    validUserName += "  6) containes a special character (!@#$%^&*)"
    matchStr = "Not Match"
    while matchStr == "Not Match":
        password = input("Enter string to test: ")
        # Add any special characters as your wish I used only #@$
        if reMatch(r"^(?=.*[\d])(?=.*[A-Z])(?=.*[a-z])(?=.*[@#$])[\w\d@#$]{6,12}$", password):
            print ("match")
            matchStr = "match"
        else:
            print ("Not Match")
    return True


def logedIn(piCurrentIndexer) -> dict[str, str]:
    theURL = f'{piAPIURL}/pi/chkLogin'
    piAuthHeader = {"Authorization": f"Bearer {piCurrentIndexer.getUserToken}"}
    res = req.get(theURL,headers=piAuthHeader)
    if res.status_code == status.HTTP_200_OK:
        printIt(f'user {cStr(piCurrentIndexer.User.piBase.piTitle,color.UNDERLINE)} loged in', label.INFO,label.ABORTPRT)
        return piAuthHeader
    elif res.status_code == status.HTTP_403_FORBIDDEN:
        tryTimes = 0
        maxTrys = 3
        while tryTimes < maxTrys:
            userName = input('π-user: ')
            if len(userName) == 0: return {}
            password = getpass('π-pass: ')
            user: UserLoginSchema = {"username": userName, "password": password} # type: ignore
            chgUser = piCurrentIndexer.setUser(userName,False)
            if chgUser:
                theURL = f'{piAPIURL}/pi/login'
                res = req.post(theURL,json=user)
                if res.status_code == status.HTTP_200_OK:
                    try:
                        tempStr =  res.json()["Authorization"]
                        piCurrentIndexer.User.piBody.piUserProfile.userToken = tempStr
                        piCurrentIndexer.User.piSave()
                        return {"Authorization": f"Bearer {tempStr}"}
                    except: pass
                tryTimes += 1
                printIt(f'{res.status_code} ({tryTimes} of {maxTrys})', label.WARN)
            else:
                tryTimes += 1
                printIt(f'{userName} not found ({tryTimes} of {maxTrys})', label.WARN)
    else:
        printIt(res.status_code, label.ERROR)
    return {}

def piDupPiTitleZfill(piType: str, piTitle: str, piCurrentIndexer):
    # printIt(f'piTitle: {piTitle}',label.DEBUG)
    chkZfill = reCompile(r"([a-zA-Z]+)\s*([0-9]+)")
    fileMatch = chkZfill.findall(piTitle)
    rtnStr = ''
    piTopics: dict = {}
    if fileMatch: # is a stemed zfill title
        # print('fileMatch',fileMatch)
        if piType in piCurrentIndexer.piPiClasses.piSpcTypeNames.keys():
            piContainerNames = piCurrentIndexer.piPiClasses.piSpcTypeNames[piType]
            typePiFile = eval(f'piCurrentIndexer.Subject.piBody.{piContainerNames}[{piType}]')
            typePiPiID = Path(typePiFile).stem
            typePiPs, source = piCurrentIndexer.piFromLink(typePiPiID)
            piTopics = getattr(typePiPs.piBody, piContainerNames)
        else:
            piContainerNames = 'topics'
            # get the last topic
            if 'topic' in piCurrentIndexer.Subject.piBody.topics.keys():
                typePiFile = Path(piCurrentIndexer.Subject.piBody.topics['topic'])
            else: return rtnStr
            # print('typePiFile:',typePiFile)
            typePiPiID = Path(typePiFile).stem
            typePiPs, source = piCurrentIndexer.piFromLink(typePiFile)
            piTopics = getattr(typePiPs.piBody, piContainerNames)
        #print(cStr('piContainerNames:',color.CYAN),piContainerNames)
        #print(cStr('piType:',color.CYAN),piType,list(piTopics.keys()))
        if piType in piTopics.keys():
            fileParts = fileMatch[0]
            stemStr: str = fileParts[0]
            zWidth = len(fileParts[1])
            #print(cStr('piTopics[piType]:',color.CYAN),piTopics[piType])
            typePiPiIDPath = Path(piTopics[piType])
            typePiPs, source = piCurrentIndexer.piFromLink(typePiPiIDPath)
            if not typePiPs: return rtnStr
            piTopicTitles = getattr(typePiPs.piBody, piContainerNames)
            maxIndex = 0
            for title in piTopicTitles.keys():
                fileMatch = chkZfill.findall(title)
                if fileMatch:
                    fileParts = fileMatch[0]
                    if fileParts[0] == stemStr:
                        if  len(str(fileParts[1])) == zWidth:
                            fileIndex = int(fileParts[1])
                            if fileIndex > maxIndex:
                                maxIndex = fileIndex
            if maxIndex < int((str(9)*zWidth)):
                rtnStr =  stemStr + str(maxIndex+1).zfill(zWidth)
            else: printIt(f'Maximum zFill reached: {maxIndex}',label.INFO)
    return rtnStr

def piJoinStr(strList: list) -> str:
    rtnStr: str = ''
    for aStr in strList:
        if aStr in string.punctuation:
            if rtnStr[-1] == ' ':
                rtnStr = rtnStr[:-1]
            rtnStr += aStr + ' '
        elif aStr in string.whitespace:
            rtnStr += aStr
        else:
            if piMatchFileNamePattern(aStr):
                if len(rtnStr) == 0:
                    rtnStr += aStr + ' '
                elif rtnStr[-1] == '/ ':
                    rtnStr = rtnStr[:-1] + aStr + ' '
                else:
                    rtnStr += aStr + ' '
            else:
                rtnStr += aStr + ' '
    if rtnStr[-1] == ' ': rtnStr = rtnStr[:-1]
    return rtnStr

def piSplitStr(text):
    # piSplitStr('Work to import pis of different formats\n*.pi as txt and json files.')
    prtDebug = False
    chkLen1 = len(text)
    unescaped_text = text.encode('utf-8').decode('unicode_escape')
    chkLen2 = len(unescaped_text)
    if chkLen1 > chkLen2: text = unescaped_text
    if prtDebug: print('text:', text)
    escape_pattern = r'(\n|\r|\t|\f)'
    filename_pattern = r'[a-zA-Z0-9_-]+\.[a-zA-Z0-9_]+'
    split_pattern = reCompile(r'(' + filename_pattern + r')|(' + escape_pattern + r')|([\[\]\{\}\(\)<>])|\s+')
    result = split_pattern.split(text)
    cleaned_result = [item for item in result if item is not None and item != '']
    if prtDebug: print('cleaned_result1:',cleaned_result)
    # Handle the first two words split only if the first element contains a space
    if cleaned_result and ' ' in cleaned_result[0]:
        first2 = cleaned_result[0].split()
        if len(first2) > 1:
            # Remove the original combined element
            cleaned_result.pop(0)
            # Insert the split words at the beginning
            for i, aWord in enumerate(first2):
                cleaned_result.insert(i, aWord)
    if prtDebug: print('cleaned_result2:',cleaned_result)
    normalized_result = []
    i = 0
    while i < len(cleaned_result):
        token = cleaned_result[i]
        if token in ['\n', '\r', '\t', '\f']:
            normalized_result.append(token)
            i += 1
            while i < len(cleaned_result) and cleaned_result[i] == token:
                i += 1
        else:
            normalized_result.append(token)
            i += 1
    if prtDebug: print('normalized_result:',normalized_result)
    processed_list = []
    special_chars_to_split = r'\[\]\{\}\(\)<>'
    punctuation_chars = escape(string.punctuation) + special_chars_to_split
    for token in normalized_result:
        if prtDebug: print('match(token):',token)
        match = reCompile(r'^(.*?)([' + escape(string.punctuation) + r']+)$').match(token)
        if match:
            word_part = match.group(1)
            punctuation_part = match.group(2)
            if word_part:
                processed_list.append(word_part)
            for char_punc in punctuation_part:
                 processed_list.append(char_punc)
        else:
            processed_list.append(token)
    if prtDebug: print('processed_list:',processed_list)
    return processed_list

def parse_padded_string(s: str) -> tuple[str, int, int]:
    """
    Parses a string that may have padded spaces before and after a set of non-space characters.
    Args:
        s: The input string.
    Returns:
        A tuple containing:
            - The set of non-space characters.
            - The number of spaces before this set.
            - The number of spaces after this set.
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string.")
    s_stripped = s.strip()
    if not s_stripped:
        return "", len(s), 0
    num_leading_spaces = s.find(s_stripped[0])
    num_trailing_spaces = len(s) - (s.rfind(s_stripped[-1]) + 1)
    return s_stripped, num_leading_spaces, num_trailing_spaces

def split_camel_case(text):
    if not isinstance(text, str) or not text:
        return []
    pattern = r'[a-z]+|[A-Z][a-z]*|[A-Z]+(?=[A-Z]|$)'
    return findall(pattern, text)

def piMatchFileNamePattern(path_string):

    if not isinstance(path_string, str) or not path_string:
        return False
    segment_char_or_wildcard = r'(?:\*\*|\*|[a-zA-Z0-9_.-])'
    path_segment = f'{segment_char_or_wildcard}+'
    flexible_path_pattern = reCompile(f'^/?{path_segment}(?:/{path_segment})*$')
    return bool(flexible_path_pattern.fullmatch(path_string))