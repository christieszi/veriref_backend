import re
import time
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import urllib
import os
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')
local = int(os.getenv('LOCAL'))

def extract_body_part(text): 
    ref_match = re.search(r'(?:References:|References)\s*(.*)', text, re.DOTALL)
    if ref_match:
        body_text = text[:ref_match.start()]
    else:
        body_text = text

    return body_text

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
    
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', body_text.strip())
    
    in_text_citations = {}
    
    for sentence in sentences:
        if not sentence.strip():
            continue

        if len(sentence.strip()) <= 5:
            continue
        
        matches = re.finditer(r'(.*?)(?:\[(\d+(?:,\s*\d+)*)\])+(?:\((\d+)\))?', sentence)
        
        current_sentence = sentence.strip()
        all_numbers = set()
        sentence_processed = False
        cleaned_sentence = re.sub(r'[\[(][0-9,\s]+[\])]', ' ', current_sentence).strip()
        
        for match in matches:
            numbers = (match.group(2) or "").strip() or (match.group(3) or "").strip()
            number_list = [int(num.strip()) for num in numbers.split(',') if num.strip().isdigit()]
            all_numbers.update(number_list)
            sentence_processed = True
        
        if sentence_processed:
            in_text_citations[cleaned_sentence] = sorted(all_numbers)
        else:
            in_text_citations[cleaned_sentence] = []

    return references, in_text_citations, body_text

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

def get_text_from_paragraphs(link):
    response = requests.get(link)
    html = BeautifulSoup(response.text, 'html.parser')

    paragraphs = html.select("p")

    intro = '\n'.join([ para.text for para in paragraphs[0:5]])

    return intro

# def get_external_source_text(query, starting_index):
#     try:
#         for (i, j) in enumerate(search(query, tld="co.in", num=starting_index + 5, stop= starting_index + 5, pause=1)):
#             if i < starting_index: 
#                 continue
            
#             try:
#                 text = get_text_from_paragraphs(j)
#                 if len(text.strip()) == 0:
#                     continue
#                 else:
#                     return i + 1, text, j
#             except Exception: 
#                 continue
#     except urllib.error.HTTPError as e:
#         if e.code == 429:
#             print("Rate limited, waiting...")
#             time.sleep(10)
#     return None

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import time

def get_clean_bing_links(driver, link):
    driver.execute_script("window.open(arguments[0]);", link)  # Open link in new tab
    driver.switch_to.window(driver.window_handles[-1])  # Switch to new tab
    time.sleep(3)  # Allow the redirect to complete
    clean_link = driver.current_url  # Get final resolved URL
    driver.close()  # Close the new tab
    driver.switch_to.window(driver.window_handles[0])  # Switch back to main tab
    return clean_link

def get_external_source_text(query, starting_index, sentence):
    
    if local: 
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        service = Service("/opt/homebrew/bin/geckodriver")  # Replace with the actual path
        driver = webdriver.Firefox(service=service, options=options)
    else: 
        print("YOOOOOO")
        print("FIREFOX PATH:", os.popen("which firefox").read())
        print("GECKODRIVER PATH:", os.popen("which geckodriver").read())

        options = webdriver.FirefoxOptions()
        
        # enable trace level for debugging 
        options.log.level = "trace"

        options.add_argument("-remote-debugging-port=9224")
        options.add_argument("-headless")
        options.add_argument("-disable-gpu")
        options.add_argument("-no-sandbox")

        binary = FirefoxBinary('/app/vendor/firefox/firefox')

        driver = webdriver.Firefox(
            firefox_binary=binary,
            executable_path=os.environ.get('GECKODRIVER_PATH'),
            options=options)

        print("YEEEE")

    links = None
    linky = None 
    text_ret = None
    extracted_data = []

    sentence_cleaned = " ".join(sentence.split())

    try:
        driver.get("https://www.bing.com/")

        time.sleep(2)

        try:
            reject_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Reject')]" or "//button[contains(text(), 'Decline')]")
            reject_button.click()
            time.sleep(2)  # Allow time for changes to take effect
        except:
            pass 

        # Find the search bar and enter the query
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        # Wait for results to load
        time.sleep(2)

        search_results = driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2 a")
        
        links = [result.get_attribute("href") for result in search_results[starting_index:starting_index + 5]]

        for link in links:
            driver.get(link)
            time.sleep(3)  # Allow time for the page to load
            try:
                accept_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept all') or contains(text(), 'Accept')]"))
                )
                accept_button.click()
                time.sleep(2)
            except:
                pass
        
            text_elements = driver.find_elements(By.XPATH, "//p | //li | //blockquote | //div[contains(@class, 'quote') or contains(@class, 'quoteText')]")

            combined_text = "\n".join([el.text for el in text_elements if el.text.strip()])
            text_cleaned = " ".join(combined_text.split())[:4000]
            

            if len(text_cleaned.strip()) != 0 and (not (sentence_cleaned in text_cleaned)):
                clean_link = get_clean_bing_links(driver, link)

                extracted_data.append((clean_link, text_cleaned)) 

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
        return extracted_data

    print("LINKS")
    print(links)
    if links:
        for i, link in enumerate(links):
            try:
                print("LINK")
                print(link)
                text = get_text_from_paragraphs(link)
                if len(text.strip()) == 0:
                    continue
                else:
                    return starting_index + i + 1, text, link
            except Exception: 
                continue

    return None 

# Instructions for running on macOS:
# 1. Install Firefox: `brew install --cask firefox`
# 2. Install geckodriver: `brew install geckodriver`
# 3. Install Selenium and WebDriver Manager: `pip install selenium webdriver-manager`
# 4. Run script using: `python script.py`



def get_data_from_knowledge_graph(query):
    service_url = 'https://kgsearch.googleapis.com/v1/entities:search'
    params = {
        'query': query,
        'limit': 1,
        'indent': True,
        'key': api_key,
    }

    url = service_url + '?' + urllib.parse.urlencode(params)
    response = json.loads(urllib.request.urlopen(url).read())
    for element in response['itemListElement']:
        if element['result'].get("detailedDescription", None): 
            return element['result']["detailedDescription"]["url"]
    
    return None
