from .new_model_utils import ask
import asyncio
from .new_prompts import *
import json
from .text_analysis_utils import extract_claims_and_word_combinations, extract_summary_and_keywords
from .sources_utils import get_external_source_text, get_text_from_paragraphs

# Old ask
# async def ask(prompt,stream=False, max_tokens=200):

#     sampling_params = {
#         "max_tokens": max_tokens,
#         "temperature":1,
#     }
#     if stream:
        
#         async for line in mistral_stream(prompt=prompt,sampling_params=sampling_params,stream=True):
#             text=line.decode('utf-8')
#             print(text,end='',flush=True)
#     else:
#         result = await mistral(prompt,sampling_params=sampling_params)
#         return result['text']

def get_claim_classification(source_text, claim_dict):
    claim = claim_dict['claim']
    answer = asyncio.run(ask(short_response(claim, source_text[:600])))
    answer = answer.lstrip()
    claim_dict['answer'] = answer

    if answer == "Cannot Say" or "cannot say" in answer.lower() or "not provide" in answer.lower(): 
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
        explanation = asyncio.run(ask(explain_correct(claim, source_text[:600])))
    elif claim_type == 2:
        explanation = asyncio.run(ask(explain_incorrect(claim, source_text[:600])))
    else:
        explanation = asyncio.run(ask(explain_not_given(claim, source_text[:600])))
    
    claim_dict['explanation'] = explanation
    claim_dict['references'] = None

    return claim_dict

def get_claim_references(source_text, claim_dict, link):
    claim = claim_dict['claim']
    claim_type = claim_dict['type'] 
    references = "" if link is None else "See source: " + link + "\n"
    if claim_type == 1: 
        references += asyncio.run(ask(reference_sentences_correct(claim, source_text[:600])))
    elif claim_type == 2:
        references += asyncio.run(ask(reference_sentences_incorrect(claim, source_text[:600])))
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

def process_sentence(claims, source_text, sentence, sentence_index, original_text, info_communicator, paragraphs, types_to_analyse=[1, 2, 3, 4, 5]):
    yield ("data: " + json.dumps({
        "messageType": "sentenceProcessingText",
        "sentenceIndex": sentence_index,
        "processingText": "Classifying sentence type",
        "processingTextState": 5
    }) + "\n\n")

    sentence_classification = asyncio.run(ask(is_a_sentence_to_check(sentence)))

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

        keywords = info_communicator["keywords"]
        prev_sentence = info_communicator["prev_sentence_with_context"]
        summary = info_communicator["summary"]
        cur_p_i = info_communicator["cur_p_i"]
        paragraph_summary = info_communicator["paragraph_summary"]

        paragraph = paragraphs[cur_p_i]
        
        while sentence[:-1].strip() not in paragraph:
            info_communicator["cur_p_i"] += 1 
            paragraph = paragraphs[info_communicator["cur_p_i"]] 
            paragraph_summary = None

        # first paragraph
        if not paragraph_summary: 
            extracted_keywords = False
            while not extracted_keywords: 
                try:
                    res = asyncio.run(ask(get_keywords_paragraph_no_prev(paragraph, summary)))
                    paragraph_summary, keywords = extract_summary_and_keywords(res)
                    info_communicator["paragraph_summary"] = paragraph_summary
                    info_communicator["keywords"] = keywords
                    extracted_keywords = True
                except:
                    extracted_keywords = False
        # switched to new paragraph
        elif info_communicator["cur_p_i"] != cur_p_i: 
            extracted_keywords = False
            while not extracted_keywords: 
                try:
                    res = asyncio.run(ask(get_keywords_paragraph(paragraph, summary, paragraph_summary)))
                    paragraph_summary, keywords = extract_summary_and_keywords(res)
                    info_communicator["paragraph_summary"] = paragraph_summary
                    info_communicator["keywords"] = keywords
                    extracted_keywords = True
                except:
                    extracted_keywords = False

        if prev_sentence:
            sentence_with_context = asyncio.run(ask(disambiguate_based_on_keywords(keywords, sentence, prev_sentence, summary, paragraph_summary)))
        else: 
            sentence_with_context = asyncio.run(ask(disambiguate_based_on_keywords_no_prev(keywords, sentence, summary, paragraph_summary)))

        info_communicator["prev_sentence_with_context"] = sentence_with_context

        # EXTRACTING EXTERNAL RESOURCE
        if len(source_text) == 0: 
            yield ("data: " + json.dumps({
            "messageType": "sentenceProcessingText",
            "sentenceIndex": sentence_index,
            "processingText": "No source text provided. Searching the web.", 
            "processingTextState": 5
            }) + "\n\n")
            query = asyncio.run(ask(get_google_prompt(sentence_with_context)))

            yield ("data: " + json.dumps({
            "messageType": "sentenceProcessingText",
            "sentenceIndex": sentence_index,
            "processingText": "No source text provided. Searching the web for " + str(query), 
            "processingTextState": 5
            }) + "\n\n")
            res = get_external_source_text(query, 0, sentence)
            if len(res) != 0: 
                link, source_text = res[0]
                source_text = source_text[:1000]
                external_si = 0
            else: 
                source_text = ""
                link = None
                external_si = None
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
                "processingText": "",
                "otherSourcesConsidered": None
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
                    claims_response = asyncio.run(ask(split_claims_prompt(sentence, sentence_with_context), max_tokens=500))
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
                "textFromLink": None, 
                "otherSourcesConsidered": None,
                "processingText": "Waiting to be processed"
                } for claim in claims]),
                "sentenceIndex": sentence_index,
                "processingText": "",
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
                "processingText": "Waiting to be processed",
                "textFromLink": None, 
                "otherSourcesConsidered": None
            } for (claim, parts) in claims_and_parts]
    
        
        enumerted_claim_dicts = list(enumerate(claim_dicts)) 

        def compare_classifications(a, b, order):
            order_map = {num: idx for idx, num in enumerate(order)}
            return (order_map[a] > order_map[b]) - (order_map[a] < order_map[b])
        order = [2, 1, 3]
        
        # provide short answers and classifications for all claims
        for i in range(len(enumerted_claim_dicts)):
            claim_index, claim_dict = enumerted_claim_dicts[i]
            claim_query = None

            cur_class = None
            cur_link = None
            cur_source_text = None
            cur_answer = None
            cur_considered = []

            claim_dict["processingText"] = "Analysing sentence based on " + (link if link else "source text") + "."
            yield from yield_claim_data("claimProcessingText", claim_dict, sentence_index, claim_index)

            updated_claim_dict = get_claim_classification(source_text, claim_dict)

            local_external_si, local_source_text, local_link = external_si, source_text, link 

            # if local_external_si is not None and updated_claim_dict['type'] == 3 and local_external_si <= 5:
            if local_external_si is not None and local_external_si <= 5:
                claim_dict["processingText"] = "Analysed based on " + link + ". Searching the web for more evidence."
                yield from yield_claim_data("claimProcessingText", claim_dict, sentence_index, claim_index)
                li = 1
                # while li < len(res) and updated_claim_dict['type'] == 3:   
                cur_class = updated_claim_dict['type']
                cur_link = link 
                cur_source_text = source_text
                cur_answer = updated_claim_dict["answer"]
                cur_considered = []
                while li < len(res):
                    local_link, local_source_text = res[li] 
                    local_source_text = local_source_text[:600]
                    claim_dict["processingText"] = "Analysing sentence based on " + local_link + "."
                    yield from yield_claim_data("claimProcessingText", claim_dict, sentence_index, claim_index)
                    updated_claim_dict = get_claim_classification(local_source_text, claim_dict)
                    li += 1
                    if compare_classifications(updated_claim_dict['type'], cur_class, order) < 0: 
                        cur_considered.append(local_link + " - " + cur_answer)
                        cur_class = updated_claim_dict['type'] 
                        cur_link = local_link 
                        cur_source_text = local_source_text 
                        cur_answer = updated_claim_dict["answer"]
                    else: 
                        cur_considered.append(local_link + " - " + claim_dict["answer"])


                if cur_class == 3:
                    li = 0 
                    claim_query = asyncio.run(ask(get_google_prompt(claim_dict["claim"])))
                    local_res = get_external_source_text(claim_query, li, sentence) 
                    while li < len(local_res) and updated_claim_dict['type'] == 3:
                        local_link, local_source_text = local_res[li] 
                        local_source_text = local_source_text[:600]
                        claim_dict["processingText"] = "Analysing sentence based on " + local_link + "."
                        yield from yield_claim_data("claimProcessingText", claim_dict, sentence_index, claim_index)
                        updated_claim_dict = get_claim_classification(local_source_text, claim_dict)
                        li += 1
                        if compare_classifications(updated_claim_dict['type'], cur_class, order) < 0: 
                            cur_considered.append(local_link + " - " + cur_answer)
                            cur_class = updated_claim_dict['type'] 
                            cur_link = local_link 
                            cur_source_text = local_source_text 
                            cur_answer = updated_claim_dict["answer"]
                        else: 
                            cur_considered.append(local_link + " - " + claim_dict["answer"])

                local_link = cur_link
                local_source_text = cur_source_text


            text_from_link = None 

            if local_link:
                updated_claim_dict["references"] = local_link
                text_from_link = local_source_text 
                claim_dict["answer"] = cur_answer 
                claim_dict["type"] = cur_class

            elif link:
                local_link = link
                text_from_link = source_text

            if len(cur_considered) == 0: 
                claim_dict["otherSourcesConsidered"] = None 
            else: 
                claim_dict["otherSourcesConsidered"] = " ".join(f"{i+1}. {item}" for i, item in enumerate(cur_considered))

            claim_dict["textFromLink"] = text_from_link
            claim_dict["processingText"] = "Explaining the claim based on " + local_link if local_link else "source text provided" + "."
            enumerted_claim_dicts[i] = (claim_index, updated_claim_dict)
            yield from yield_claim_data("claimAnswer", claim_dict, sentence_index, claim_index)

        sorted_enum_dicts = sorted(enumerted_claim_dicts, key=lambda x: [2, 3, 4, 1, 5].index(x[1]["type"]))
        filtered_enum_dicts = [item for item in sorted_enum_dicts if item[1]["type"] in types_to_analyse] 

        # provide explanations for all claims
        for i in range(len(filtered_enum_dicts)):
            claim_index, claim_dict = filtered_enum_dicts[i]

            if claim_dict["references"] is not None:
                local_source_text = claim_dict["textFromLink"]
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
                local_source_text = claim_dict["textFromLink"]
                local_link = references
            else: 
                local_source_text = source_text
                local_link = None 
            

            updated_claim_dict = get_claim_references(local_source_text, claim_dict, local_link)
            filtered_enum_dicts[i] = updated_claim_dict
            filtered_enum_dicts[i] = (claim_index, updated_claim_dict)
            yield from yield_claim_data("claimReferences", claim_dict, sentence_index, claim_index)
    else:
        print("")