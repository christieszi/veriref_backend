def get_keywords(text):
    res = '''
    Your task is summarise what the text is about and extract the main keywords from it.
        Text: "{text}"
    Instructions:
        Analyse the meaning of the text, provide a short summary of what the text is about. 
        Additionally, extract main keywords such as names, terms, events, places, and concepts from the text, capturing its meaning. 
    Output Format:
        Return a JSON entry, containing:
        "summary": The short summary of the text in maximum 2-4 sentences.
        "keywors": List of strings which a keywords capturing the meaning of the text.

        Return only the json without any extra information. 
    Example output: 
        {{
            "summary": "The text describes Albert Einstaein's biography, specifically the creation of the theory of relativity.",
            "word_combinations": ["Albert Einstein", "The theory of relativity"]
        }}
    '''.format(text=text)
    return res

def is_a_sentence_to_check(sentence):
    res = '''
    Your task is to classify the given string '{sentence}' into one of the following categories based on its meaning and content:

    Information Sentence - The string is a sentence with a complete predicate. And the sentence contains meaningful, non-trivial information or factual statements. 
    Title - The string is most likely the title of an article, chapter, section, etc.
    General Information about the text - The string provides general metadata about the text, such as the date and place of publishing, authors of the text, or similar text details.
    Text descitption - The string is a sentence describes what will be further done in the text or what the author(s) or speaker(s) will do, or do, or did (e.g., "we will examine..." "this study will explore...", "in this article...", "we propose...", "we introduce...").
    Not a Sentence - If the string is not a sentence, i.e. it does not have a subject and a verb. 

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
    Example input: 
        Sentence: "He invented the theory."
        Source Text: "The theory of relativity is one of the most famous theories in physics. Albert Enstein is its inventor."
    Example output for the example input: 
        "Albert Enstein invented the theory of relativity".
    Output:
        Return only the modified sentence without any additional information or formatting.
    '''.format(sentence=sentence, source_text=source_text)
    return res


    # Ensure each extracted claim is fully self-contained and can be understood on its own without other claims.
    #     Use explicit names and complete concepts from the contextualized sentence.
    #     Make sure that each claim comes with an explicit context.
    #     Do not use pronouns, 'this', 'that', 'these', 'those', or 'the' instead of full description. Use full names and complete concrete descriptions instead.

def split_claims_prompt(sentence, sentence_with_context):
    res =   '''
    Your task is to extract all key claims, encapsulating the meaning of the given original sentence:

    Original sentence: "{sentence}"
    Contextualized sentence: "{sentence_with_context}"
    Instructions:

    Extract only the most important and fundamental claims that do not overlap in meaning.
    
    Replace all ambigious details of each claim (like using 'the' to refer to previous description or pronouns or this, that, these, those) with complete concepts and descriptions from the contextualized sentence so that the claim can be understood in full without any context.

    Map each claim to the exact reference word combinations in the original sentence.
        Each claim must be linked to specific word combinations as they appear in the original sentence.
        Ensure that word combinations for different claims do not have overlapping words.

    Output Format:

        Return a JSON list where each entry contains:

        "claim": The extracted claim in full, written with explicit references.
        "word_combinations": The exact text spans from the original sentence that support the claim.

    Example input:

    Original sentence: "He developed the theory, which revolutionized physics. 
    Contextualized sentence: "Albert Einstein developed the theory of relativity, which revolutionized physics."

    Example output for the example input:

    [
        {{
            "claim": "Albert Einstein developed the theory of relativity.",
            "word_combinations": "He developed the theory."
        }},
        {{
            "claim": "The theory of relativity revolutionized physics.",
            "word_combinations": "revolutionized physics."
        }}
    ]
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

def disambiguate_based_on_keywords(keywords, sentence, prev_sentence_with_context, summary, paragraph_summary):
    return '''
    Given the context for the sentence charcterised as in terms of keywords: '{keywords}'
    and the previous sentence: '{prev_sentence_with_context}'.
    Replace all ambigious details of the sentence (like using 'the' to refer to previous description or pronouns or this, that, these, those) with complete concepts and descriptions so that the sentence can be understood in full without any context.
    The sentence is: '{sentence}'. 
    It is taken from a text with summary: '{paragraph_summary}'.
    Return only the disambiguated sentence without any extra information. 
    '''.format(keywords=keywords, sentence=sentence, prev_sentence_with_context=prev_sentence_with_context, paragraph_summary=paragraph_summary) 

def disambiguate_based_on_keywords_no_prev(keywords, sentence, summary, paragraph_summary):
    return '''
    Given the context for the sentence charcterised as in terms of keywords: '{keywords}.
    Replace all ambigious details of the sentence (like using 'the' to refer to previous description or pronouns or this, that, these, those) with complete concepts and descriptions so that the sentence can be understood in full without any context.
    The sentence is: '{sentence}'. 
    It is taken from a text with summary: '{paragraph_summary}'.
    Return only the disambiguated sentence without any extra information. 
    '''.format(keywords=keywords, sentence=sentence, paragraph_summary=paragraph_summary) 

def split_by_ides(text):
    return '''
    Given text: '{text}'. 
    extract parts of the text bound by the same idea, containing minimum 5 sentences. For each extracted part output the first sentence, the last sentence, and the keywords describing main concepts, names, places, and/or events encapsulating the meaning of the part. 
    Output format as json:
    [
        {{
            "first sentence": "some sentence", 
            "last sentence": "some sentence", 
            "keywords": ["concept_1","place_2", "event_3"]
        }}
    ]
    '''.format(text=text)

def get_keywords_paragraph(paragraph, summary, paragraph_summary):
    res = '''
    Your task is summarise what the paragraph is about and extract the main keywords from it.
        paragraph: "{paragraph}"
    The text is a paragraph taken from a text described as: "{summary}". 
    And the summary for the previous paragraph: "{paragraph_summary}".
    Instructions:
        Analyse the meaning of the paragraph, provide a short summary of what the text is about. 
        Additionally, extract main keywords such as names, terms, events, places, and concepts from the paragraph, capturing its meaning. 
    Output Format:
        Return a JSON entry, containing:
        "summary": The short summary of the text in maximum 2-4 sentences.
        "keywors": List of strings which a keywords capturing the meaning of the text.

        Return only the json without any extra information. 
    Example output: 
        {{
            "summary": "The text describes Albert Einstaein's biography, specifically the creation of the theory of relativity.",
            "word_combinations": ["Albert Einstein", "The theory of relativity"]
        }}
    '''.format(paragraph=paragraph, summary=summary, paragraph_summary=paragraph_summary)
    return res

def get_keywords_paragraph_no_prev(paragraph, summary):
    res = '''
    Your task is summarise what the paragraph is about and extract the main keywords from it.
        paragraph: "{paragraph}"
    The text is a paragraph taken from a text described as: "{summary}". 
    Instructions:
        Analyse the meaning of the paragraph, provide a short summary of what the text is about. 
        Additionally, extract main keywords such as names, terms, events, places, and concepts from the paragraph, capturing its meaning. 
    Output Format:
        Return a JSON entry, containing:
        "summary": The short summary of the text in maximum 2-4 sentences.
        "keywors": List of strings which a keywords capturing the meaning of the text.

        Return only the json without any extra information. 
    Example output: 
        {{
            "summary": "The text describes Albert Einstaein's biography, specifically the creation of the theory of relativity.",
            "word_combinations": ["Albert Einstein", "The theory of relativity"]
        }}
    '''.format(paragraph=paragraph, summary=summary)
    return res

def get_google_prompt(claim):
    return '''
    Given the following claim:

    '{claim}'

    Generate one Google search query:
    A keyword-based search that captures the main idea but allows for variations in wording.

    Return only the query without any extra information.
    '''.format(claim=claim)