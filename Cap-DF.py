import time
import google.generativeai as genai  # pylint: disable=import-error
import csv
import json
from google.api_core.exceptions import ResourceExhausted
import dotenv
# Load environment variables from .env file
dotenv.load_dotenv()
# Ensure the .env file is in the same directory as this script

# Retrieve transformer ID
transformer_id = input("\nTransformer ID: ")
transformer_row = None

# Loading current transformer data
with open('data/updated_data.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        if transformer_id in row['OrderCode']:
            transformer_row = row
            break

# Define Google API Key
GOOGLE_API_KEY = dotenv.get_key('.env', 'GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("Google API Key not found in .env file")

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

# Set up the Gemini 2.0 Flash model
model = genai.GenerativeModel('gemini-2.0-flash')

# Conditional prompt
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

# Generate content
while True:
    try:
        prompt = build_prompt(transformer_row)
        response = model.generate_content(prompt)
        break
    except ResourceExhausted as e:
        print("Rate Limit Exceeded. Retrying after 60 seconds")
        time.sleep(60)
    except Exception as e:
        print("Error generating content:", e)

# Parse the response as JSON
try:
    # Extract only the JSON part from the response
    json_start = response.text.find('{')
    json_end = response.text.rfind('}') + 1
    json_str = response.text[json_start:json_end]
    result = json.loads(json_str)
    print("\nResponse from Gemini API:")
    print(f'{result}\n\n')
except Exception as e:
    print('Failed to parse JSON:', e)
    print('Raw response:', response.text)

# Fetch parameter number 42 from the Medium(Cycle Time) in SAP.json file
with open('data/SAP.json', 'r') as sap_file:
    sap_data = json.load(sap_file)

# medium_cycle_time = sap_data.get('Medium Power(Cycle Time)', {})
# parameter_42 = medium_cycle_time.get('42')

# print("Parameter 42 from Medium Power(Cycle Time):", parameter_42)

winding_type = result.get('winding_type')
after_test_required = result.get('after_test_required')

cycle_time = None
labor_hours = None
test_schedule_hour = None

if winding_type == 'Two-Winding':
    if after_test_required:
        cycle_time = sap_data.get('Medium Power(Cycle Time)', {}).get('44')
        labor_hours = sap_data.get('Medium Power(Labor Hours)', {}).get('44')
        test_schedule_hour = sap_data.get('Medium Power(Test Schedule Hour)', {}).get('44')
    else:
        cycle_time = sap_data.get('Medium Power(Cycle Time)', {}).get('42')
        labor_hours = sap_data.get('Medium Power(Labor Hours)', {}).get('42')
        test_schedule_hour = sap_data.get('Medium Power(Test Schedule Hour)', {}).get('42')
elif winding_type == 'Three-Winding':
    if after_test_required:
        cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('45')
        labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('45')
        test_schedule_hour = sap_data.get(f'{result.get('transformer_type')} Power(Test Schedule Hour)', {}).get('45')
    else:
        cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('43')
        labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('43')
        test_schedule_hour = sap_data.get(f'{result.get('transformer_type')} Power(Test Schedule Hour)', {}).get('43')

print(f"Cap/DF Cycle|Labour|Test Schedule Hours for Transformer ID {transformer_id}:")
print(f"\nCycle Time: {cycle_time}")
print(f"Labor Hours: {labor_hours}")
print(f"Test Schedule Hour: {test_schedule_hour}\n")
print(f'Total Estimated Hours: {cycle_time + labor_hours + test_schedule_hour if cycle_time and labor_hours and test_schedule_hour else "N/A"}\n')