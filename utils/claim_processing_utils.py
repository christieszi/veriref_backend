from .model_utils import ask_question, mistral_stream, mistral
import asyncio
from .prompts import *
import json
from .text_analysis_utils import extract_claims_and_word_combinations
from .sources_utils import get_external_source_text, get_text_from_paragraphs

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

def get_claim_references(source_text, claim_dict, link):
    claim = claim_dict['claim']
    claim_type = claim_dict['type'] 
    references = "" if link is None else "See source: " + link + "\n"
    if claim_type == 1: 
        references += asyncio.run(ask(ask_question(reference_sentences_correct(claim, source_text))))
    elif claim_type == 2:
        references += asyncio.run(ask(ask_question(reference_sentences_incorrect(claim, source_text)))) 
    elif link is None:
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

def process_sentence(claims, source_text, sentence, sentence_index, types_to_analyse=[1, 2, 3, 4, 5]):
    if len(source_text) == 0: 
        external_si, source_text, link = get_external_source_text(sentence, 0)[:500]
    else:
        external_si = None 
        link = None

    print(source_text)
    if len(source_text.strip()) == 0:
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
        if not claims or len(claims) == 0 or claims[0]['type'] == 4: 
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
        else: 
            claims_and_parts = [(claim['claim'], claim['sentenceParts']) for claim in claims]

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

            local_external_si, local_source_text, local_link = external_si, source_text, link

            while local_external_si is not None and updated_claim_dict['type'] == 3 and local_external_si <= 5:
                local_external_si, local_source_text, local_link = get_external_source_text(sentence, local_external_si)[:500]
                updated_claim_dict = get_claim_classification(local_source_text, claim_dict)

            if local_link:
                updated_claim_dict["references"] = local_link

            enumerted_claim_dicts[i] = (claim_index, updated_claim_dict)
            yield from yield_claim_data("claimAnswer", claim_dict, sentence_index, claim_index)

        sorted_enum_dicts = sorted(enumerted_claim_dicts, key=lambda x: [2, 3, 4, 1, 5].index(x[1]["type"]))
        filtered_enum_dicts = [item for item in sorted_enum_dicts if item[1]["type"] in types_to_analyse] 

        # provide explanations for all claims
        for i in range(len(filtered_enum_dicts)):
            claim_index, claim_dict = filtered_enum_dicts[i]

            if claim_dict["references"] is not None:
                local_source_text = get_text_from_paragraphs(claim_dict["references"])
                local_link = claim_dict["references"]
            else: 
                local_source_text = source_text
                local_link = None

            updated_claim_dict = get_claim_explanation(local_source_text, claim_dict)

            if local_link is not None:
                updated_claim_dict["references"] = local_link

            filtered_enum_dicts[i] = updated_claim_dict
            filtered_enum_dicts[i] = (claim_index, updated_claim_dict)
            yield from yield_claim_data("claimExplanation", claim_dict, sentence_index, claim_index)

        # provide references for all claims
        for i in range(len(filtered_enum_dicts)):
            claim_index, claim_dict = filtered_enum_dicts[i]

            if claim_dict["references"] is not None:
                local_source_text = get_text_from_paragraphs(claim_dict["references"])
                local_link = claim_dict["references"]
            else: 
                local_source_text = source_text
                local_link = None

            updated_claim_dict = get_claim_references(local_source_text, claim_dict, local_link)
            filtered_enum_dicts[i] = updated_claim_dict
            filtered_enum_dicts[i] = (claim_index, updated_claim_dict)
            yield from yield_claim_data("claimReferences", claim_dict, sentence_index, claim_index)