import ast
import re
import json

def process_sentence_parts(sentence_parts):
    sentence_parts_clean = re.search(r'\[([^\[\]]*)\]', sentence_parts).group(1)
    res = ast.literal_eval("[" + str(sentence_parts_clean) + "]")
    sorted_strings = sorted(res, key=len, reverse=True)
    return sorted_strings

def classify_and_find_majority(sentences):
    def classify_sentence(sentence):
        sentence_lower = sentence.lower()
        if "not given" in sentence_lower or "not provided" in sentence_lower or "does not mention" in sentence_lower:
            return 3
        elif "correct" in sentence_lower or "true" in sentence_lower:
            return 1
        elif "incorrect" in sentence_lower or "false" in sentence_lower:
            return 2
        else:
            return 3
    
    classifications = [classify_sentence(sentence) for sentence in sentences]
    classifications = [(sentence, classify_sentence(sentence)) for sentence in sentences]
    
    type_counts = {1: 0, 2: 0, 3: 0}
    for _, classification in classifications:
        type_counts[classification] += 1
    
    max_count = max(type_counts.values())
    majority_types = [type_ for type_, count in type_counts.items() if count == max_count]
    
    if len(majority_types) > 1:
        return 3, None
    
    majority_type = majority_types[0]
    example_sentence = next(sentence for sentence, classification in classifications if classification == majority_type)
    return majority_type, example_sentence

def map_colours_to_sentence(sentence, mappings):
    used_indices = set()
    coloured_parts = []

    for claim, claim_type, explanation, substrings in mappings:
        for substring in substrings:
            start = 0
            while (index := sentence.find(substring, start)) != -1:
                end = index + len(substring)
                if not any(i in used_indices for i in range(index, end)):
                    print("yay")
                    coloured_parts.append((index, end, claim, claim_type, explanation))
                    used_indices.update(range(index, end))
                start = index + 1

    return coloured_parts

def extract_claims_and_word_combinations(data):
    print(data)
    match = re.search(r'\[.*?\]', data, re.DOTALL)
    print(match)
    parsed_data = json.loads(match.group(0))

    # Extract the list of pairs (claim, word_combinations)
    pairs = [(entry['claim'], entry['word_combinations']) for entry in parsed_data]

    print(pairs)
    return pairs


def process_unifinished_output(text):
    lines = text.splitlines()
    result_lines = []
    
    for line in lines:
        # Check if the line is part of an enumerated list
        if re.match(r"^\s*(\d+\.|-|\*)\s+", line):  # Matches "1.", "-", or "*"
            # If the line doesn't end with punctuation, skip it
            if not re.search(r"[.!?]$", line.strip()):
                continue
        # Check if the line is an unfinished sentence
        elif not re.search(r"[.!?]$", line.strip()) and line.strip():
            # Skip the unfinished line
            continue
        
        # Add valid lines to the result
        result_lines.append(line)

    return " ".join(result_lines)