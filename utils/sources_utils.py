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
                references[key] = content
    else:
        lines = [line.strip() for line in references_text.splitlines() if line.strip()]
        references = {i + 1: line for i, line in enumerate(lines[:5])}
    
    in_text_citations = {}
    pattern = r'([^.]*?)(\[\d+(?:,\s*\d+)*\]|\(\d+(?:,\s*\d+)*\))'
    matches = re.findall(pattern, body_text)

    for sentence, numbers in matches:
        individual_numbers = re.findall(r'\d+', numbers)
        in_text_citations[sentence.strip()] = list(map(int, individual_numbers))

    return references, in_text_citations