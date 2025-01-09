import re
import requests
from bs4 import BeautifulSoup

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
    
    sentences = re.split(r'(?<=[.!?])\s+', body_text.strip())

    in_text_citations = {}

    for sentence in sentences:
        if not sentence.strip():
            continue

        matches = re.finditer(r'(.*?)[\[\()]([0-9,\s]+)[\]\)]', sentence)

        current_sentence = sentence.strip()
        sentence_processed = False

        for match in matches:
            part = (match.group(1) or "").strip() or (match.group(3) or "").strip()
            numbers = (match.group(2) or "").strip() or (match.group(3) or "").strip()

            number_list = [int(num.strip()) for num in numbers.split(',') if num.strip().isdigit()]

            if part:
                in_text_citations[part] = number_list
                sentence_processed = True

        if not sentence_processed:
            clean_sentence = re.sub(r'\s*[\[(][0-9,\s]+[\])]\s*$', '', current_sentence)
            in_text_citations[clean_sentence] = []

    return references, in_text_citations

def extract_url(text):
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, text)
    if match:
        return match.group(0)
    else:
        return None
    
def remove_brackets_and_numbers(sentence):
    return re.sub(r'\[\d*\]', '', sentence)

def get_source_text_from_link(source):
    response = requests.get(source)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser").get_text()