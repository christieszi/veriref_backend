from .mistral_tokeniser import MistralTokeniser
import aiohttp
from dotenv import load_dotenv
import os
from huggingface_hub import login

load_dotenv()
mistral_endpoint = os.getenv('MISTRAL_ENDPOINT')
huggingface_token = os.getenv('HUGGINGFACE_TOKEN')

login(token = huggingface_token)

# Load variables from .env file

tokenizer = MistralTokeniser.from_pretrained("mistralai/Mistral-Small-Instruct-2409")

def TokensPrompt(tokens):
    return {"prompt_token_ids":tokens}


async def mistral(prompt, stream=False, sampling_params=None, url=mistral_endpoint):
    
    payload = {
        "prompt": prompt,
        "stream": stream,
    }
    if sampling_params:
        payload["sampling_params"] = sampling_params

    headers = {
        "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Error: {response.status}, {response}")

async def mistral_stream(prompt, stream=False, sampling_params=None, url=mistral_endpoint):
    
    payload = {
        "prompt": prompt,
        "stream": stream,
    }
    if sampling_params:
        payload["sampling_params"] = sampling_params

    headers = {
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                async for line in response.content:
                    yield line
            else:
                raise Exception(f"Error: {response.status}, {await response.text()}")

tokenizer = MistralTokeniser.from_pretrained("mistralai/Mistral-Small-Instruct-2409")
def ask_question(question):
    
    messages= [
{"role": "user", "content": question}
        ]
    return  TokensPrompt(tokenizer.apply_chat_template(
    messages=messages
))