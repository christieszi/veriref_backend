from .model_utils import ask_question, mistral_stream, mistral
import asyncio
from .prompts import *
import json
from .text_analysis_utils import extract_claims_and_word_combinations
from .sources_utils import get_source_text_from_link

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

def process_sentence(source_numbers, doc_references, sentence, sentence_index):
    source_text = ""
    sources = [] 

    for source_number in source_numbers:
        if source_number and doc_references.get(source_number, None):
            try:
                source = doc_references[source_number]
                source_text += get_source_text_from_link(source)
                source_text += "\n"
                sources.append(source)
            except:
                source_text = source_text

    if len(source_text) == 0: 
        claim_dict = {
            "claim": sentence,
            "answer": "Could not check",
            "type": 4,
            "explanation": "Could not access source",
            "references": None,
            "sentenceParts": sentence
        }
        yield ("data: " + json.dumps({
            "messageType": "claimNoResource",
            "claim": claim_dict,
            "sentenceIndex": sentence_index
        }) + "\n\n")

    else:
        claims_response = asyncio.run(ask(ask_question(split_claims_prompt(sentence))))
        print(claims_response)
        claims_and_parts = extract_claims_and_word_combinations(claims_response, sentence) 
        claims = [claim for (claim, _) in claims_and_parts]
        yield ("data: " + json.dumps({
            "messageType": "claims",
            "claims": ([{
            "claim": claim,
            "answer": None,
            "type": 5,
            "explanation": None,
            "references": None} for claim in claims]),
            "sentenceIndex": sentence_index
        }) + "\n\n")

        claim_dicts = [{
                "claim": claim,
                "answer": None,
                "type": None,
                "explanation": None,
                "references": None,
                "sentenceParts": parts
            } for (claim, parts) in claims_and_parts]
        
        enumerted_claim_dicts = list(enumerate(claim_dicts))

        # provide short answers and classifications for all claims
        for i in range(len(enumerted_claim_dicts)):
            claim_index, claim_dict = enumerted_claim_dicts[i]
            updated_claim_dict = get_claim_classification(source_text, claim_dict)
            enumerted_claim_dicts[i] = (claim_index, updated_claim_dict)
            yield from yield_claim_data("claimAnswer", claim_dict, sentence_index, claim_index)

        # provide explanations for all claims
        for i in range(len(enumerted_claim_dicts)):
            claim_index, claim_dict = enumerted_claim_dicts[i]
            updated_claim_dict = get_claim_explanation(source_text, claim_dict)
            enumerted_claim_dicts[i] = updated_claim_dict
            enumerted_claim_dicts[i] = (claim_index, updated_claim_dict)
            yield from yield_claim_data("claimExplanation", claim_dict, sentence_index, claim_index)

        # provide references for all claims
        for i in range(len(enumerted_claim_dicts)):
            claim_index, claim_dict = enumerted_claim_dicts[i]
            updated_claim_dict = get_claim_references(source_text, claim_dict)
            enumerted_claim_dicts[i] = updated_claim_dict
            enumerted_claim_dicts[i] = (claim_index, updated_claim_dict)
            yield from yield_claim_data("claimReferences", claim_dict, sentence_index, claim_index)