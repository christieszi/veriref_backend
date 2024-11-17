import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import asyncio
from utils import mistral_stream, mistral, ask_question

statements = [
    "A is true",
    "B is true",
    "(A and B) is true"
]

questions = [
    "is A true",
    "is not B true", 
    "is A true"
]

model_answers = [
    "yes",
    "no",
    "yes"
]

async def main(prompt,stream=False):

    sampling_params = {
        "max_tokens": 200,
        "temperature":1,
    }
    if stream:
        
        async for line in mistral_stream(prompt=prompt,sampling_params=sampling_params,stream=True):
            text=line.decode('utf-8')
            print(text,end='',flush=True)
    else:
        result = await mistral(prompt,sampling_params=sampling_params)
        return result['text']

if __name__ == "__main__":
    for i in range(len(statements)):
        text= asyncio.run(main(ask_question("Given the fact that " + statements[i] + ". " + questions[i] + "? Reply with 'yes' or 'no'"),stream=True))
        print(text)
