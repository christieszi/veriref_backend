import requests
import json
from vllm.entrypoints.chat_utils import apply_mistral_chat_template
from vllm.transformers_utils.tokenizers import MistralTokenizer
from vllm.inputs import TokensPrompt
import aiohttp
import asyncio
from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()
mistral_endpoint = os.getenv('MISTRAL_ENDPOINT')

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

tokenizer = MistralTokenizer.from_pretrained("mistralai/Mistral-Small-Instruct-2409")
def ask_question(question):
    
    messages= [
{"role": "user", "content": question}
        ]
    return  TokensPrompt(prompt_token_ids=apply_mistral_chat_template(
    tokenizer,
    messages=messages,
    chat_template=None,
    add_generation_prompt=True,
    continue_final_message=False,
    tools=None,
))

