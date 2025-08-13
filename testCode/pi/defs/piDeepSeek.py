import requests
import json

# Replace with your actual API key and endpoint
API_KEY = 'Bearer ' + 'sk-43b53ee281074cc485877e2433332a7f'
API_URL = 'https://api.deepseek.com/chat/completions'

def getWordDef(theWord: str) -> str:
    '''Get a one sentance definition of theWord from deepseek'''
    message = f'define the word "{theWord}"'
    payload = json.dumps({
        "messages": [
            {
                "content": "You are a helpful assistant. Always provide concise and accurate information. When asked to define a word, respond in one sentance. If the word can not be defined, return the 'TBD' token.",
                "role": "system"
            },
            {
                "content": message,
                "role": "user"
            }
        ],
        "model": "deepseek-chat",
        "frequency_penalty": 0,
        "max_tokens": 2048,
        "presence_penalty": 0,
        "stop": None,
        "stream": False,
        "temperature": 1,
        "top_p": 1,
        "logprobs": False,
        "top_logprobs": None
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization':  API_KEY
    }

    response = requests.request("POST", API_URL, headers=headers, data=payload)

    if response.status_code == 200:
        chkJson = json.loads(response.text)
        rtnStr = chkJson['choices'][0]['message']['content']
        chkList = rtnStr.split()
        goodDef = False
        for i in chkList:
            chkWord: str = i.lower().replace('"','')
            if theWord.lower() == chkWord:
                goodDef = True
                break
        if not goodDef: rtnStr = f'TBD: {rtnStr}'
        return rtnStr
    else:
        return f"TBD: {response.status_code}, {response.text}"