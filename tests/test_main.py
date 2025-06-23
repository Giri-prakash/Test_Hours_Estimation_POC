import dotenv
import google.generativeai as genai  # pylint: disable=import-error
import csv
import json
import time
from google.api_core.exceptions import ResourceExhausted

# Load environment variables from .env file
dotenv.load_dotenv()
# Ensure the .env file is in the same directory as this script

# Define Google API Key
GOOGLE_API_KEY = dotenv.get_key('.env', 'GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def build_prompt(row):
    rubric = f"""
You are a classification assistant for transformer data. Based on the rubric provided, classify the transformer type, winding type, and whether an After Test is required.

## Rubric:
Step 1: Transformer Type (Check if EHV first, then Large, then Medium)
- EHV: (MVA > 90 and any BIL and **Conservator Unit = False is required for a transformer to be an EHV**) or (BIL = 1150/1300 and **Conservator Unit = False is required for a transformer to be an EHV**)
- Large: **A Large transformer needs to have a conservator unit** MVA ≥ 60 (Other) or ≥ 36 (Auto), and BIL ≥ 750
- Medium: MVA < 60 and BIL < 650 (Conservator Unit does not matter)


Step 2: Winding Type
- Three-Winding: Type should not be "Auto" to be classified as Three-Winding and "TV" or "YV" present in Winding Config
- Two-Winding: all other cases

Step 3: After Test Requirement
- If the test code contains "ALL TESTS", then After Test Required = True

## Input:
MVA: {row['MVA']}  
BIL: {row['BIL']}  
Type: {'Auto' if row['Auto(Yes/No)'] == 'Yes' else 'Other'}  
Conservator Unit: {'True' if row['Conservator'] == 'Yes' else 'False'}  
Winding Config: {'TV' if row['YV/TV Present (Connection_YV or Connection_TV key exists in DB)'] == 'Yes' else 'Other'}  
Test Codes: {'ALL TESTS' if row['After Test Required (keyword After All Tests exists in DB)'] == 'Yes' else 'None'}  

## Output Format:
The output should be a JSON object with the following keys:
- "transformer_type": The type of transformer (Medium, Large, EHV)
- "winding_type": The type of winding (Three-Winding, Two-Winding)
- "after_test_required": Boolean indicating if an After Test is required
- 'reason_for_transformer_type': A brief explanation of the classification
## Example Output:
"""
    prompt = rubric + """
{
  "transformer_type": "EHV",
  "winding_type": "Two-Winding",
  "after_test_required": false,
  "reason_for_winding_type": "The winding type is classified as Two-Winding because the transformer does not have 'TV' or 'YV' in its winding configuration and is not an Auto type."
}

## Output:
"""

    return prompt

def normalize_bool(val):
    return val.strip().lower() in ['yes', 'true']

def normalize_winding(val):
    return 'Three-Winding' if '3' in val else 'Two-Winding'

def normalize_transformer_type(val):
    return val.strip().capitalize() if val else 'Unknown'

def test_transformers():
    with open('data/updated_data.csv', 'r') as file:
        reader = csv.DictReader(file)
        total = 0
        correct = 0
        for row in reader:
            prompt = build_prompt(row)
            while True:
                try:
                    response = model.generate_content(prompt)
                    break
                except ResourceExhausted as e:
                    print('Rate limit hit. Waiting 60 seconds before retrying...')
                    time.sleep(60)
                except Exception as e:
                    print(f"{row['OrderCode']}: Unexpected error: {e}")
                    return
            try:
                json_start = response.text.find('{')
                json_end = response.text.rfind('}') + 1
                json_str = response.text[json_start:json_end]
                ai_result = json.loads(json_str)
            except Exception as e:
                print(f"{row['OrderCode']}: Failed to parse JSON: {e}")
                print('Raw response:', response.text)
                continue
            expected_winding = normalize_winding(row['Winding Type'])
            expected_after_test = normalize_bool(row['After Test Required (keyword After All Tests exists in DB)'])
            expected_transformer_type = normalize_transformer_type(row['Transformer Type'])
            winding_match = ai_result['winding_type'].replace('-', ' ') == expected_winding.replace('-', ' ')
            after_test_match = ai_result['after_test_required'] == expected_after_test
            transformer_type_match = ai_result['transformer_type'].capitalize() == expected_transformer_type
            print(f"{row['OrderCode']}: Transformer Type: AI={ai_result['transformer_type']} | CSV={expected_transformer_type} | Match={transformer_type_match}")
            print(f"{row['OrderCode']}: Winding Type: AI={ai_result['winding_type']} | CSV={expected_winding} | Match={winding_match}")
            print(f"{row['OrderCode']}: After Test Required: AI={ai_result['after_test_required']} | CSV={expected_after_test} | Match={after_test_match}")
            print('-' * 60)

            total += 1
            if winding_match and after_test_match and transformer_type_match:
                correct += 1
        
        print(f"Total: {total}, Correct: {correct}, Accuracy: {correct / total * 100:.2f}%")

if __name__ == "__main__":
    test_transformers()
