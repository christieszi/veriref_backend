from .model_utils import ask_question, mistral_stream, mistral
import asyncio
from .prompts import *
import json

async def ask(prompt,stream=False):

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
    

def get_claim_classification(source_text, claim_dict):
    claim = claim_dict['claim']
    answer = asyncio.run(ask(ask_question(short_response(claim, source_text))))
    answer = answer.lstrip()
    claim_dict['answer'] = answer

    if answer == "Cannot Say" or "cannot say" in answer.lower(): 
        claim_dict['type'] = 3
    elif answer == "Incorrect" or "incorrect" in answer.lower():
        claim_dict['type'] = 2
    elif answer == "Correct" or "correct" in answer.lower(): 
        claim_dict['type'] = 1  
    else:
        claim_dict['type'] = 3

    return claim_dict

def get_claim_explanation(source_text, claim_dict):
    claim = claim_dict['claim']
    claim_type = claim_dict['type'] 
    if claim_type == 1: 
        explanation = asyncio.run(ask(ask_question(explain_correct(claim, source_text))))
    elif claim_type == 2:
        explanation = asyncio.run(ask(ask_question(explain_incorrect(claim, source_text))))
    else:
        explanation = asyncio.run(ask(ask_question(explain_not_given(claim, source_text))))
    
    claim_dict['explanation'] = explanation
    claim_dict['references'] = None

    return claim_dict

def get_claim_references(source_text, claim_dict):
    claim = claim_dict['claim']
    claim_type = claim_dict['type'] 
    if claim_type == 1: 
        references = asyncio.run(ask(ask_question(reference_sentences_correct(claim, source_text))))
    elif claim_type == 2:
        references = asyncio.run(ask(ask_question(reference_sentences_incorrect(claim, source_text))))  
    else:
        references = None
    
    claim_dict['references'] = references

    return claim_dict

def yield_claim_data(message_type, claim_dict, sentence_index, claim_index): 
    yield ("data: " + json.dumps({
        "messageType": message_type,
        "claim": claim_dict,
        "sentenceIndex": sentence_index,
        "claimIndex": claim_index
    }) + "\n\n")  