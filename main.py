import asyncio
from utils import model_utils

async def main(prompt,stream=False):

    sampling_params = {
        "max_tokens": 200,
        "temperature":1,
    }
    if stream:
        
        async for line in model_utils.mistral_stream(prompt=prompt,sampling_params=sampling_params,stream=True):
            text=line.decode('utf-8')
            print(text,end='',flush=True)
    else:
        result = await model_utils.mistral(prompt,sampling_params=sampling_params)
        return result['text']

if __name__ == "__main__":
    text= asyncio.run(main(model_utils.ask_question("Given the fact that Monica likes dogs. Is it correct that Monica likes cats? Reply with 'yes' or 'no'"),stream=True))