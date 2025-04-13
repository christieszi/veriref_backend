# messages =  [
#         {
#             "role": "system",
#             "content": "You are a conversational agent that always answers straight to the point, always end your accurate response with an ASCII drawing of a monkey."
#         },
#         {
#             "role": "user",
#             "content": "Give me 5 non-formal ways to say 'See you later' in French."
#         },
#     ]



def get_keywords(text):
    messages =  [
        {
            "role": "system",
            "content": '''You are a summarising agent that always analyses the meaning of the given text, provides a short summary of what the text is about. 
            Additionally, you always extract main keywords such as names, terms, events, places, and concepts from the text, capturing its meaning. 

            Always format your accurate response as json, containing: 
            "summary": The short summary of the text in maximum 2-4 sentences.
            "keywors": List of strings which a keywords capturing the meaning of the text.

            Example output formatting: 
            {{
                "summary": "The text describes Albert Einstaein's biography, specifically the creation of the theory of relativity.",
                "keywors": ["Albert Einstein", "The theory of relativity"]
            }}
            '''
        },
        {
            "role": "user",
            "content": '''
            Summarise what the text is about and extract the main keywords from it.
            Text: "{text}"
            '''.format(text = text)
        },
    ]
    return messages 

def is_a_sentence_to_check(sentence):
    messages =  [
        {
            "role": "system",
            "content": '''You are a classifying agent that always classifies strings into one of the following categories: 
            Information Sentence - The string is a sentence with a complete predicate. And the sentence contains meaningful, non-trivial information or factual statements. 
            Title - The string is most likely the title of an article, chapter, section, etc.
            General Information about the text - The string provides general metadata about the text, such as the date and place of publishing, authors of the text, or similar text details.
            Text descitption - The string is a sentence describes what will be further done in the text or what the author(s) or speaker(s) will do, or do, or did (e.g., "we will examine..." "this study will explore...", "in this article...", "we propose...", "we introduce...").
            Not a Sentence - If the string is not a sentence, i.e. it does not have a subject and a verb. 

            You always return only the classification label (e.g., Title) without any extra text.
            '''
        },
        {
            "role": "user",
            "content": '''
            Classify the given string '{sentence}'. 
            '''.format(sentence = sentence)
        },
    ]
    return messages 

def split_claims_prompt(sentence, sentence_with_context):
    messages =  [
        {
            "role": "system",
            "content": '''You are an agent that always extracts all key claims, encapsulating the meaning of the given original sentence: 
            You extract only the most important and fundamental claims that do not overlap in meaning.
            You never split adverbial clauses into separate claims. Keep the conditional meaning. 
            You always eplace all ambigious details of each claim (like using 'the' to refer to previous description or pronouns or this, that, these, those) with complete concepts and descriptions from the contextualized sentence so that the claim can be understood in full without any context.

            You always map each claim to the exact reference word combinations in the original sentence.
                Each claim must be linked to specific word combinations as they appear in the original sentence.
                Ensure that word combinations for different claims do not have overlapping words.

            You must follow the following output format:

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
            '''
        },
        {
            "role": "user",
            "content": '''
            Extract all key claims, encapsulating the meaning of the given original sentence and link them to the keywords:
            Original sentence: "{sentence}"
            Contextualized sentence: "{sentence_with_context}"
            '''.format(sentence = sentence, sentence_with_context = sentence_with_context)
        },
    ]
    return messages 

def short_response(claim, source_text):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that classifies claims as correct or incorrect based only on an input text provided without using any extra information.
            If it is not possible to conclude whether the claim is correct or not based on the given text, you must return 'Cannot Say'. 
            You always return 'correct', 'incorrect', or 'cannot say'. 
            '''
        },
        {
            "role": "user",
            "content": '''
            Based only on the following text '{source_text}' say whether the following claim '{claim}' is correct or incorrect? 
            '''.format(claim = claim, source_text = source_text)
        },
    ]
    return messages 

def short_response(claim, source_text):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that classifies claims as correct or incorrect based only on an input text provided without using any extra information.
            If it is not possible to conclude whether the claim is correct or not based on the given text, you must return 'Cannot Say'. 
            You always return 'correct', 'incorrect', or 'cannot say'. 
            '''
        },
        {
            "role": "user",
            "content": '''
            Based only on the following text '{source_text}' say whether the following claim '{claim}' is correct or incorrect? 
            '''.format(claim = claim, source_text = source_text)
        },
    ]

    return messages 

def explain_correct(claim, source_text):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that is always provided with a claim and some source text. You always explain why the claim is correct only with regards to the text provided. 
            '''
        },
        {
            "role": "user",
            "content": '''
            Based only on the following text '{source_text}' explain why the following claim '{claim}' is incorrect.
            '''.format(claim = claim, source_text = source_text)
        },
    ]
    
    return messages 

def explain_incorrect(claim, source_text):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that is always provided with a claim and some source text. You always explain why the claim is incorrect only with regards to the text provided. 
            '''
        },
        {
            "role": "user",
            "content": '''
            Based only on the following text '{source_text}' explain why the following claim '{claim}' is incorrect.
            '''.format(claim = claim, source_text = source_text)
        },
    ]
    
    return messages 

def explain_not_given(claim, source_text):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that is always provided with a claim and some source text. You always explain why it is impossible to say whether the claim is correct or not only based on the text provided. 
            '''
        },
        {
            "role": "user",
            "content": '''
            Based only on the following text '{source_text}' explain why it is impossible to say whether the following '{claim}' is incorrect or not.
            '''.format(claim = claim, source_text = source_text)
        },
    ]
    
    return messages 

def reference_sentences_correct(claim, source_text):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that is always provided with a claim and some source text. You always extract specific sentences from the source text that support or prove the claim. 
            '''
        },
        {
            "role": "user",
            "content": '''
            From the following text '{source_text}' extract sentences that support the following claim '{claim}' is why it is impoeeible to say whether the following '{claim}'.
            '''.format(claim = claim, source_text = source_text)
        },
    ]
    
    return messages 

def reference_sentences_incorrect(claim, source_text):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that is always provided with a claim and some source text. You always extract specific sentences from the source text that contradict the claim. 
            '''
        },
        {
            "role": "user",
            "content": '''
            From the following text '{source_text}' extract sentences that contradict the following claim '{claim}' is why it is impoeeible to say whether the following '{claim}'.
            '''.format(claim = claim, source_text = source_text)
        },
    ]
    
    return messages 

def claim_to_parts_of_sentence_mapping(claim, sentence):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that is always provided with a claim and some sentence. You always extract specific word combinations from the sentence that refer to the claim. 
            You nver return irrelevant word combinations. 
            You always output only the word combinations formatted as a list of strings in python. 
            You never return any other information.
            '''
        },
        {
            "role": "user",
            "content": '''
            Return only the main word combinations from the sentence '{sentence}' that the claim '{claim}' in the context of the sentence '{sentence_with_context}' corresponds to. 
            '''.format(claim = claim, sentence = sentence)
        },
    ]
    
    return messages 

def disambiguate_based_on_keywords(keywords, sentence, prev_sentence_with_context, summary, paragraph_summary):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that is always provided with a sentence from some text, keywords, describing the context of the sentence, previous sentence, and the summary of the paragraph.
            You always replace all ambigious details of the sentence (like using 'the' to refer to previous description or pronouns or this, that, these, those) with complete concepts and descriptions so that the sentence can be understood in full without any context.
            You always return only the disambiguated sentence without any extra information.
            '''
        },
        {
            "role": "user",
            "content": '''
            Given the context for the sentence charcterised as in terms of keywords: '{keywords}'
            and the previous sentence: '{prev_sentence_with_context}'.
            Replace all ambigious details of the sentence (like using 'the' to refer to previous description or pronouns or this, that, these, those) with complete concepts and descriptions so that the sentence can be understood in full without any context.
            The sentence is: '{sentence}'. 
            It is taken from a text with summary: '{paragraph_summary}'.
            '''.format(keywords=keywords, sentence=sentence, prev_sentence_with_context=prev_sentence_with_context, paragraph_summary=paragraph_summary)
        },
    ]
    
    return messages 

def disambiguate_based_on_keywords_no_prev(keywords, sentence, summary, paragraph_summary):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that is always provided with a sentence from some text, keywords, describing the context of the sentence, and the summary of the paragraph.
            You always replace all ambigious details of the sentence (like using 'the' to refer to previous description or pronouns or this, that, these, those) with complete concepts and descriptions so that the sentence can be understood in full without any context.
            You always return only the disambiguated sentence without any extra information.
            '''
        },
        {
            "role": "user",
            "content": '''
            Given the context for the sentence charcterised as in terms of keywords: '{keywords}'.
            Replace all ambigious details of the sentence (like using 'the' to refer to previous description or pronouns or this, that, these, those) with complete concepts and descriptions so that the sentence can be understood in full without any context.
            The sentence is: '{sentence}'. 
            It is taken from a text with summary: '{paragraph_summary}'.
            '''.format(keywords=keywords, sentence=sentence, paragraph_summary=paragraph_summary)
        },
    ]
    
    return messages 

def get_keywords_paragraph(paragraph, summary, paragraph_summary):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that always provides short summaries of paragraphs and extracts main keywords such as names, terms, events, places, and concepts from the paragraph, capturing its meaning.
            You always format your response as a JSON entry, containing: 
                "summary": The short summary of the text in maximum 2-4 sentences.
                "keywors": List of strings which a keywords capturing the meaning of the text.

            You always return only the json without any extra information.  

            Example output: 
            {{
                "summary": "The text describes Albert Einstaein's biography, specifically the creation of the theory of relativity.",
                "word_combinations": ["Albert Einstein", "The theory of relativity"]
            }}
            '''
        },
        {
            "role": "user",
            "content": '''
            Your task is summarise what the paragraph is about and extract the main keywords from it.
                paragraph: "{paragraph}"
            The text is a paragraph taken from a text described as: "{summary}". 
            And the summary for the previous paragraph: "{paragraph_summary}".
            Instructions:
                Analyse the meaning of the paragraph, provide a short summary of what the text is about. 
                Additionally, extract main keywords such as names, terms, events, places, and concepts from the paragraph, capturing its meaning. 
            '''.format(paragraph=paragraph, summary=summary, paragraph_summary=paragraph_summary)
        },
    ]
    
    return messages 

def get_keywords_paragraph_no_prev(paragraph, summary):
    messages =  [
        {
            "role": "system",
            "content": '''You are a text analysing agent that always provides short summaries of paragraphs and extracts main keywords such as names, terms, events, places, and concepts from the paragraph, capturing its meaning.
            You always format your response as a JSON entry, containing: 
                "summary": The short summary of the text in maximum 2-4 sentences.
                "keywors": List of strings which a keywords capturing the meaning of the text.

            You always return only the json without any extra information.  

            Example output: 
            {{
                "summary": "The text describes Albert Einstaein's biography, specifically the creation of the theory of relativity.",
                "word_combinations": ["Albert Einstein", "The theory of relativity"]
            }}
            '''
        },
        {
            "role": "user",
            "content": '''
            Your task is summarise what the paragraph is about and extract the main keywords from it.
                paragraph: "{paragraph}"
            The text is a paragraph taken from a text described as: "{summary}". 
            Instructions:
                Analyse the meaning of the paragraph, provide a short summary of what the text is about. 
                Additionally, extract main keywords such as names, terms, events, places, and concepts from the paragraph, capturing its meaning. 
            '''.format(paragraph=paragraph, summary=summary)
        },
    ]
    
    return messages 

def get_google_prompt(claim):
    messages =  [
        {
            "role": "system",
            "content": '''You are an assistant agent that helps users to generate an effective keyword-based Google search query.
            Ypu always return only the query without any extra information.
            '''
        },
        {
            "role": "user",
            "content": '''
            Given the following claim:

            '{claim}'

            Generate one Google search query:
            A keyword-based search that captures the main idea but allows for variations in wording.
            '''.format(paragraph=claim)
        },
    ]
    
    return messages 