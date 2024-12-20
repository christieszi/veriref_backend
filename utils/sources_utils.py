import re

def extract_references_dict(text):
    ref_match = re.search(r'(?:References:|References)\s*(.*)', text, re.DOTALL)
    
    if ref_match:
        references_text = ref_match.group(1)
    else:
        lines = text.splitlines()
        references_text = ""
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            # Match list formats
            if re.match(r'^(?:\[\d+\]|\(\d+\)|\d+\.|[-•])\s*.+', line):
                references_text = '\n'.join(lines[i:])  # Start of the list found
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

    return references