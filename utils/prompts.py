def is_a_sentence_to_check(sentence):
    res = '''
    Your task is to classify the given sentence '{sentence}' into one of the following categories based on its meaning and content:

    Information Sentence - The sentence has a complete predicate. And the sentence contains meaningful, non-trivial information or factual statements. 
    Title - The sentence is most likely the title of an article, chapter, section, etc.
    General Information about the text - The sentence provides general metadata about the text, such as the date and place of publishing, authors of the text, or similar text details.
    Intent Description - The sentence describes what will be done in the text (e.g., "we will examine," "this study will explore").

    Return only the classification label (e.g., Title) without any extra text.
    '''.format(sentence=sentence)
    return res

def replace_pronouns(sentence, source_text):
    res = '''
    Your task is to replace all pronouns, this, that, these, those, and reference nouns in the given sentence so that it can be understood without additional context.
        Sentence: "{sentence}"
        Source text: "{source_text}"
    Instructions:
        Replace all pronouns and nouns that refer to other sentences in the source text with their explicit referents.
        Do not add any extra information beyond what is necessary for clarity.
        Keep the structure and wording of the sentence as close to the original as possible.
    Output:
        Return only the modified sentence without any additional information or formatting.
    '''.format(sentence=sentence, source_text=source_text)
    return res

def split_claims_prompt(sentence, sentence_with_context):
    res =   '''
    Your task is to extract all key claims from the given original sentence:

    Original sentence: "{sentence}"
    Contextualized sentence: "{sentence_with_context}"
    Instructions:

    Extract only the most important and fundamental claims.
        If a claim can be broken down into simpler, meaningful claims, do so.
        Do not include trivial, redundant, or overlapping claims.

    Ensure each extracted claim is fully self-contained.
        Use explicit names and concepts from the contextualized sentence.
        Do not use pronouns, articles, or references to other claims.

    Map each claim to the exact reference word combinations in the original sentence.
        Each claim must be linked to specific word combinations as they appear in the original sentence.
        Ensure that word combinations for different claims do not have overlapping words.

    Output Format:

        Return a JSON list where each entry contains:

        "claim": The extracted claim in full, written with explicit references.
        "word_combinations": The exact text spans from the original sentence that support the claim.

    Example Output:

    [
        {{
            "claim": "Albert Einstein developed the theory of relativity.",
            "word_combinations": "He developed the theory."
        }},
        {{
            "claim": "The theory of relativity revolutionized physics.",
            "word_combinations": "The theory revolutionized physics."
        }}
    ]

    Make sure the claims are independent, precise, and do not assume knowledge of the original sentence structure.
    '''.format(sentence=sentence, sentence_with_context=sentence_with_context)

    return res

def short_response(claim, source_text):
    return '''
    Based only on the following text '{source_text}' say whether the following claim '{claim}' is correct or incorrect? 
    If it is not possible to conclude whether the claim is correct or not based on the given text, return 'Cannot Say'. 
    The response must contain one of the following: Correct, Incorrect, or Cannot Say.
    '''.format(claim=claim, source_text=source_text) 

def explain_correct(claim, source_text):
    return '''
    Based only on the following text '{source_text}' explain why the following claim '{claim}' is correct.
    '''.format(claim=claim, source_text=source_text) 

def explain_incorrect(claim, source_text):
    return '''
    Based only on the following text '{source_text}' explain why the following claim '{claim}' is incorrect.
    '''.format(claim=claim, source_text=source_text) 

def explain_not_given(claim, source_text):
    return '''
    Based only on the following text '{source_text}' explain why it is impoeeible to say whther the following '{claim}' is incorrect or not.
    '''.format(claim=claim, source_text=source_text) 

def reference_sentences_correct(claim,source_text):
    return '''
    Based only on the following text '{source_text}' give specific setences from the text which prove or support the following claim '{claim}'. 
    
    Output only enumerated sentences without any extra information.
    '''.format(claim=claim, source_text=source_text) 

def reference_sentences_incorrect(claim, source_text):
    return '''
    Based only on the following text '{source_text}' give specific setences from the text which contradict the following claim '{claim}'. 
    
    Output only enumerated sentences without any extra information.
    '''.format(claim=claim, source_text=source_text)  

def claim_to_parts_of_sentence_mapping(claim, sentence):
    return '''
    Return only the main word combinations from the sentence '{sentence}' that the claim '{claim}' in the context of the sentence '{sentence_with_context}' corresponds to. 
    Do not return irrelevant word combinations. 
    Output only the word combinations from the sentence without any other information.
    Format the list as a list of strings in python.
    Do not ouput any other information.
    '''.format(claim=claim, sentence=sentence)  