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

def extract_claims_and_word_combinations(data, sentence):
    print(data)
    data = data.strip()
    if data[0] == "[" and data[-1] == "]":
        match = data
    else:
        match = re.search(r'\[.*\]', data, re.DOTALL).group(0)

    parsed_data = json.loads(match)

    pairs = [(entry['claim'], check_substring(entry['word_combinations'], sentence)) for entry in parsed_data]

    print(pairs)
    return pairs


def process_unifinished_output(text):
    lines = text.splitlines()
    result_lines = []
    
    for line in lines:
        if re.match(r"^\s*(\d+\.|-|\*)\s+", line): 
            if not re.search(r"[.!?]$", line.strip()):
                continue
        elif not re.search(r"[.!?]$", line.strip()) and line.strip():
            continue
        
        result_lines.append(line)

    return " ".join(result_lines)

def check_substring(parts, sentence):
    if isinstance(parts, str):
        if parts in sentence:
            return parts
        else: 
            return longest_common_substring(parts, sentence)
    else: 
        processed_parts = []
        for part in parts: 
            if part in sentence:
                processed_parts.append(part)
            else: 
                processed_parts.append(longest_common_substring(parts, sentence))     
        return processed_parts    

def find_overlap(s1, s2):
    """
    Finds the largest overlap string between two strings, s1 and s2.
    Returns the overlapping portion or an empty string if no overlap exists.
    """
    for i in range(len(s1)):
        if s2.startswith(s1[i:]):
            return s1[i:]

    for i in range(len(s2)):
        if s1.startswith(s2[i:]):
            return s2[i:]
    
    return ""

def longest_common_substring(s1, s2):
    """
    Finds the longest common substring between two strings, s1 and s2.
    Returns the common substring or an empty string if no common substring exists.
    """
    # Initialize the DP table
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    max_length = 0
    end_index_s1 = 0

    # Fill the DP table
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > max_length:
                    max_length = dp[i][j]
                    end_index_s1 = i

    # Extract the longest common substring
    longest_substring = s1[end_index_s1 - max_length:end_index_s1]
    return longest_substring