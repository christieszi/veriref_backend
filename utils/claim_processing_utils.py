from .model_utils import ask_question, mistral_stream, mistral
import asyncio
from .prompts import *
import json
from .text_analysis_utils import extract_claims_and_word_combinations
from .sources_utils import get_external_source_text, get_text_from_paragraphs

async def ask(prompt,stream=False, max_tokens=200):

    sampling_params = {
        "max_tokens": max_tokens,
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

def yield_claim_data(message_type, claim_dict, sentence_index, claim_index, processing_text="Processing"): 
    yield ("data: " + json.dumps({
        "messageType": message_type,
        "claim": claim_dict,
        "sentenceIndex": sentence_index,
        "claimIndex": claim_index,
    }) + "\n\n")  

def process_sentence(claims, source_text, sentence, sentence_index, original_text, types_to_analyse=[1, 2, 3, 4, 5]):
    yield ("data: " + json.dumps({
        "messageType": "sentenceProcessingText",
        "sentenceIndex": sentence_index,
        "processingText": "Classifying sentence type",
        "processingTextState": 5
    }) + "\n\n")

    sentence_classification = asyncio.run(ask(ask_question(is_a_sentence_to_check(sentence))))
    print(sentence_classification) 


    yield ("data: " + json.dumps({
        "messageType": "sentenceProcessingText",
        "sentenceIndex": sentence_index,
        "processingText": "The sentence contains " + sentence_classification,
        "processingTextState": 0
    }) + "\n\n")

    if sentence_classification.strip().lower() == "information sentence" or "information sentence" in sentence_classification.strip().lower():
        yield ("data: " + json.dumps({
            "messageType": "sentenceProcessingText",
            "sentenceIndex": sentence_index,
            "processingText": "Extracting sentence context from the original text", 
            "processingTextState": 5
            }) + "\n\n")

        sentence_with_context = asyncio.run(ask(ask_question(replace_pronouns(sentence, original_text))))
        print(sentence_with_context)

        # EXTRACTING EXTERNAL RESOURCE
        if len(source_text) == 0: 
            yield ("data: " + json.dumps({
            "messageType": "sentenceProcessingText",
            "sentenceIndex": sentence_index,
            "processingText": "No source text provided. Searching the web.", 
            "processingTextState": 5
            }) + "\n\n")
            external_si, source_text, link = get_external_source_text(sentence_with_context, 0)[:500]
        else:
            external_si = None 
            link = None
        
        if len(source_text.strip()) == 0:
            claim_dict = {
                "claim": sentence,
                "answer": "Could not check",
                "type": 4,
                "explanation": "Could not access source",
                "references": None,
                "sentenceParts": sentence,
                "processingText": ""
            }
            yield ("data: " + json.dumps({
                "messageType": "claimNoResource",
                "claim": claim_dict,
                "sentenceIndex": sentence_index
            }) + "\n\n")

        if not claims or len(claims) == 0 or claims[0]['type'] == 4: 
            yield ("data: " + json.dumps({
            "messageType": "sentenceProcessingText",
            "sentenceIndex": sentence_index,
            "processingText": "Splitting the sentence into claims", 
            "processingTextState": 5
            }) + "\n\n")
            extracted = False 
            while not extracted: 
                try:
                    claims_response = asyncio.run(ask(ask_question(split_claims_prompt(sentence, sentence_with_context)), max_tokens=500))
                    print(claims_response)
                    claims_and_parts = extract_claims_and_word_combinations(claims_response, sentence) 
                    extracted = True 
                except: 
                    extracted = False

            claims = [claim for (claim, _) in claims_and_parts]
            yield ("data: " + json.dumps({
                "messageType": "claims",
                "claims": ([{
                "claim": claim,
                "answer": None,
                "type": 5,
                "explanation": None,
                "references": None,
                "processingText": "Waiting to be processed"
                } for claim in claims]),
                "sentenceIndex": sentence_index,
                "processingText": ""
            }) + "\n\n")
        else: 
            claims_and_parts = [(claim['claim'], claim['sentenceParts']) for claim in claims]

        claim_dicts = [{
                "claim": claim,
                "answer": None,
                "type": 5,
                "explanation": None,
                "references": None,
                "sentenceParts": parts, 
                "processingText": "Waiting to be processed"
            } for (claim, parts) in claims_and_parts]
        
        enumerted_claim_dicts = list(enumerate(claim_dicts)) 

        # provide short answers and classifications for all claims
        for i in range(len(enumerted_claim_dicts)):
            claim_index, claim_dict = enumerted_claim_dicts[i]

            claim_dict["processingText"] = "Analysing sentence based on " + (link if link else "source text") + "."
            yield from yield_claim_data("claimProcessingText", claim_dict, sentence_index, claim_index)

            updated_claim_dict = get_claim_classification(source_text, claim_dict)

            local_external_si, local_source_text, local_link = external_si, source_text, link 

            if local_external_si is not None and updated_claim_dict['type'] == 3 and local_external_si <= 5:
                claim_dict["processingText"] = "Did not find an answer in " + link + ". Searching the web again."
                yield from yield_claim_data("claimProcessingText", claim_dict, sentence_index, claim_index)
                li = 0 
                while li <=5 and updated_claim_dict['type'] == 3:
                    res = get_external_source_text(claim_dict["claim"], li) 
                    if res is not None: 
                        li, local_source_text, local_link =res[:500]
                        claim_dict["processingText"] = "Analysing sentence based on " + local_link + "."
                        updated_claim_dict = get_claim_classification(local_source_text, claim_dict)
                    else: 
                        li = 6

            if local_link:
                updated_claim_dict["references"] = local_link
            elif link:
                local_link = link

            claim_dict["processingText"] = "Explaining the claim based on " + local_link if local_link else "source text provided" + "."
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

            claim_dict["processingText"] = "Looking for reference sentences in " + local_link if local_link else "source text provided" + "."
            filtered_enum_dicts[i] = updated_claim_dict
            filtered_enum_dicts[i] = (claim_index, updated_claim_dict)
            yield from yield_claim_data("claimExplanation", claim_dict, sentence_index, claim_index)

        # provide references for all claims
        for i in range(len(filtered_enum_dicts)):
            claim_index, claim_dict = filtered_enum_dicts[i]



            if claim_dict["references"] is not None:
                references = claim_dict["references"] 
                claim_dict["references"] = None
                yield from yield_claim_data("claimReferences", claim_dict, sentence_index, claim_index)
                local_source_text = get_text_from_paragraphs(references)
                local_link = references
            else: 
                local_source_text = source_text
                local_link = None

            updated_claim_dict = get_claim_references(local_source_text, claim_dict, local_link)
            filtered_enum_dicts[i] = updated_claim_dict
            filtered_enum_dicts[i] = (claim_index, updated_claim_dict)
            yield from yield_claim_data("claimReferences", claim_dict, sentence_index, claim_index)
    else:
        print("AAAAAA")
        print(sentence)
        print(sentence_classification)