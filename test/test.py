import csv
import os
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils import mistral_ask, roberta_ask, qwen_ask, gemma_ask


def test_model(input_filename, output_filename, model_func, with_assumption):
    # Open the input CSV file to read
    with open(input_filename, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        
        # Open the output CSV file to write
        with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            
            # Write the header to the new CSV
            writer.writerow(['Number', 'Answer', 'Model Answer'])
            writer.writerow([])
            
            for row in reader:
                print(row)
                # Skip empty rows or section headers
                if not row or row[0].startswith("#"):
                    # Handle section headers (which begin with '#')
                    if row and row[0].startswith("#"):
                        current_section = row[0][1:].strip()  # Remove '#' from section name
                        writer.writerow([current_section])
                    writer.writerow([])
                    continue
                
                # Skip the header row (Number, Source, Statement, Answer)
                if row[0] == "Number":
                    continue
                
                # Process each row with enumeration
                number, source, statement, model_answer = row
                
                if with_assumption:
                    answer = model_func(source, statement)
                else:
                    answer = model_func("Given " + str(source) + ". Explain why the statement  " + str(statement) + " is true or false")

                # Write the processed data to the new CSV
                writer.writerow([number, answer, model_answer])

    print(f"Data has been successfully written to {output_filename}.")

# Specify the CSV file
input_filename = 'test/test_dataset.csv'
output_filename = 'test/gemma_test_results.csv'

# Call the function
test_model(input_filename, output_filename, model_func=gemma_ask, with_assumption=False)
