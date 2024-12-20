import re

def extract_references(text):
    ref_match = re.search(r'(?:References:|References)\s*(.*)', text, re.DOTALL)
    if ref_match:
        references_text = ref_match.group(1)
        body_text = text[:ref_match.start()]
    else:
        lines = text.splitlines()
        references_text = ""
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if re.match(r'^(?:\[\d+\]|\(\d+\)|\d+\.|[-•])\s*.+', line):
                references_text = '\n'.join(lines[i:])
                body_text = lines[:i]
                break
        body_text = text 
        references_text = ""
    
    references = {}
    matches = re.findall(
        r'^\s*(?:\[(\d+)\]|\((\d+)\)|(\d+)\.|[-•]?)\s*(.+)',
        references_text,
        re.MULTILINE
    )

    if matches:
        for match in matches:

            number = match[0] or match[1] or match[2] 
            content = match[3].strip()              
            if content:                               
                key = int(number) if number else len(references) + 1  
                references[key] = extract_url(content)
    else:
        lines = [line.strip() for line in references_text.splitlines() if line.strip()]
        references = {i + 1: line for i, line in enumerate(lines[:5])}
    
    sentences = re.split(r'(\.|\?|!)', body_text.strip())
    
    complete_sentences = [
        sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else '')
        for i in range(0, len(sentences), 2)
    ]
    # Vancouver-style references pattern
    reference_pattern = re.compile(r'\[(\d+(?:,\s?\d+)*)\]')
    
    in_text_citations = {}
    for sentence in complete_sentences[:-1]:
        matches = reference_pattern.findall(sentence)

        if matches:
            citations = [int(ref) for group in matches for ref in group.split(',')]
            in_text_citations[remove_brackets_and_numbers(sentence).strip()] = citations
        else:
            in_text_citations[sentence.strip()] = []

    print(in_text_citations)

    return references, in_text_citations

def extract_url(text):
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, text)
    if match:
        return match.group(0)
    else:
        return None
    
def remove_brackets_and_numbers(sentence):
    # Use regex to remove squared brackets and numbers inside them
    return re.sub(r'\[\d*\]', '', sentence)