def is_a_sentence_to_check(sentence):
    res = '''
    Your task is to classify the given sentence {sentence} into one of the following categories based on its meaning and content:

    Title - The sentence is most likely the title of an article, chapter, section, etc.
    Authors - The sentence likely contains information about the authors or publishers of a paper.
    General Information - The sentence provides general metadata about the text, such as the date, place of publishing, or similar contextual details.
    Trivial Claim - The sentence presents obvious or uncontroversial information that does not require verification.
    Intent Description - The sentence describes what will be done in the text (e.g., "we will examine," "this study will explore").
    Information Sentence - The sentence contains meaningful, non-trivial information or factual statements.
    Incomplete Sentence - If sentence is not complete or contains only numbers, and thus, cannot be understood. 

    Return only the classification label (e.g., Title) without any extra text.
    '''.format(sentence=sentence)
    return res

def split_claims_prompt(sentence):
    res =   '''
    Your task is extract all the key claims mentioned in the given sentence {sentence}. 
    Extract only the most important and atomistic claims, if needed break the claims down to the simpler claims.
    Ensure that the claims are autonomous and no context is lost.
    For each claim output the word combinations from the sentence that the claim is based on.
    Make sure that the word combinations returned for different claims do not overlap. 
    Make sure that the word combinations are formatted exactly as they appear in the given sentence. 
    Avoid using pronouns or articles in the extracted claims, referring to other claims or the original sentence. Use complete words, names, or word combonations instead.
    Format your output as a list of json with the following format:
    [
        {{
            "claim": The Claim,
            "word_combinations": The word combinations the claim corresponds to.
        }}, 
    {{ }},
    ]
    '''.format(sentence=sentence)

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

def reference_sentences_correct(claim, source_text):
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
    Return only the main word combinations from the sentence '{sentence}' that the claim '{claim}' corresponds to. 
    Do not return irrelevant word combinations. 
    Output only the word combinations from the sentence without any other information.
    Format the list as a list of strings in python.
    Do not ouput any other information.
    '''.format(claim=claim, sentence=sentence)  