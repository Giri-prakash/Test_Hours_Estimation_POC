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
with open('data/core_loss-bushing_data.csv', 'r') as file:
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
Step 1: Winding Type
- Three-Winding: Type should not be "Auto" to be classified as Three-Winding and "TV" or "YV" present in Winding Config
- Two-Winding: all other cases

Step 2: Transformer Type (Check if EHV first, then Large, then Medium)
- EHV (Extra High Voltage Transformer):
    - If MVA > 90: EHV
    - Else if BIL > 900: EHV
    - Conservator presence is irrelevant for EHV.
- Large Transformer (only if not EHV):
    - For Type = 'Other' and Winding Type = 'Two-Winding':
        - If MVA >= 60: Large
        - Else if BIL >= 750: Large
        - Else if Conservator Unit is present: Large
    - For Type = 'Auto'/Winding Type = 'Three-Winding':
        - If MVA >= 36: Large
        - Else if BIL >= 750: Large
        - Else if Conservator Unit is present: Large
- Medium Transformer: If it does not match any of the above conditions: Medium

Step 3: After Test Requirement
- If the test code contains "ALL TESTS", then After Test Required = True

Step 4: Series Parallel
- If Series Parallel is equal to 'Yes', then Series Parallel = True, else False

Step 5: Before Impulse
- If Before Impulse is equal to 'Yes', then Before Impulse = True, else False


## Input:
MVA: {row['MVA']}  
BIL: {row['BIL']}  
Type: {'Auto' if row['Auto(Yes/No)'] == 'Yes' else 'Other'}  
Conservator Unit: {'True' if row['Conservator'] == 'Yes' else 'False'}  
Winding Config: {'TV' if row['YV/TV Present'] == 'Yes' else 'Other'}  
Series Parallel: {row['Series/Parallel']}  
Before Impulse: {row['Before Impulse']}
NamePlate Column: {row['None/nameplate']}
OnCover: {row['Oncover']}
Test Codes: {'ALL TESTS' if row['After Test Required (keyword After All Tests exists in DB)'] == 'Yes' else 'None'}  

## Output Format:
The output should be a JSON object with the following keys:
- "transformer_type": The type of transformer (Medium, Large, EHV)
- "winding_type": The type of winding (Three-Winding, Two-Winding)
- "after_test_required": Boolean indicating if an After Test is required
- "series_parallel": Boolean indicating if Series Parallel is True
- "before_impulse": Boolean indicating if Before Impulse is True
- 'reason_for_transformer_type': A brief explanation of the classification
- 'Nameplate': The value from the NamePlate column
- 'OnCover': The value from the OnCover column
## Example Output:
"""
    prompt = rubric + """
{
  "transformer_type": "EHV",
  "winding_type": "Two-Winding",
  "after_test_required": false,
  "series_parallel": true,
  "before_impulse": false,
  "reason_for_transformer_type": "The transformer is classified as EHV because the MVA is greater than 90.",
  "Nameplate": "Example Nameplate Value",
  "OnCover": "Example OnCover Value"
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

# Cap/DF parameters
winding_type = result.get('winding_type')
after_test_required = result.get('after_test_required')

# Core Loss parameters
before_impulse = result.get('before_impulse')
series_parallel = result.get('series_parallel')

#bushing parameters
nameplate = result.get('Nameplate')
on_cover = result.get('OnCover')

# Cap/DF Hours
cap_df_cycle_time = None
cap_df_labor_hours = None

# Core Loss Hours
core_loss_cycle_time = None
core_loss_labor_hours = None

#bushing Hours
bushing_cycle_time = None
bushing_labor_hours = None

# Determine the cycle time, labor hours, and test schedule hour for the Cap/DF test based on the transformer type and winding type
if winding_type == 'Two-Winding':
    if after_test_required:
        cap_df_cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('44')
        cap_df_labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('44')
    else:
        cap_df_cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('42')
        cap_df_labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('42')
elif winding_type == 'Three-Winding':
    if after_test_required:
        cap_df_cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('45')
        cap_df_labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('45')
    else:
        cap_df_cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('43')
        cap_df_labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('43')

# Determine the cycle time, labor hours, and test schedule hour for the Core Loss test based on the transformer type
if before_impulse:
    if series_parallel:
        core_loss_cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('98')
        core_loss_labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('98')
    else:
        core_loss_cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('96')
        core_loss_labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('96')
else:
    if series_parallel:
        core_loss_cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('97')
        core_loss_labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('97')
    else:
        core_loss_cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('95')
        core_loss_labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('95')

# Determine the cycle time, labor hours, and test schedule hour for the bushing test based on the transformer type
if nameplate == "NP":
    print("Nameplate is NP, using 50 as parameter number")
    bushing_cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('50')
    bushing_labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('50')
else:
    if winding_type == 'Two-Winding':
        bushing_cycle_time += sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('51')
        bushing_labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('51')
    elif winding_type == 'Three-Winding':
        bushing_cycle_time = sap_data.get(f'{result.get('transformer_type')} Power(Cycle Time)', {}).get('52')
        bushing_labor_hours = sap_data.get(f'{result.get('transformer_type')} Power(Labor Hours)', {}).get('52')

print(f"Cap/DF Cycle|Labour|Test Schedule Hours for Transformer ID {transformer_id}:")
print(f"\nCycle Time: {cap_df_cycle_time}")
print(f"Labor Hours: {cap_df_labor_hours}")

print(f"Core Loss Cycle|Labour|Test Schedule Hours for Transformer ID {transformer_id}:")
print(f"\nCycle Time: {core_loss_cycle_time}")
print(f"Labor Hours: {core_loss_labor_hours}")

print(f"bushing Cycle|Labour|Test Schedule Hours for Transformer ID {transformer_id}:")
print(f"\nCycle Time: {bushing_cycle_time}")
print(f"Labor Hours: {bushing_labor_hours}")

# Calculate total estimated hours for all tests
if cap_df_cycle_time and cap_df_labor_hours and core_loss_cycle_time and core_loss_labor_hours and bushing_cycle_time and bushing_labor_hours:
    total_cycle_time = cap_df_cycle_time + core_loss_cycle_time + bushing_cycle_time
    total_labor_hours = cap_df_labor_hours + core_loss_labor_hours + bushing_labor_hours
    print(f'\nTotal Estimated Cycle Time: {total_cycle_time}\n')
    print(f'Total Estimated Labor Hours: {total_labor_hours}\n')
else:
    print('Total Estimated Hours: N/A\n')

# def get_test_index(test_name, sap_json_path='data/SAP.json'):
#     """
#     Returns the index (as int) of the given test_name in the Revision(Classification) object of SAP.json.
#     Returns None if not found.
#     """
#     with open(sap_json_path, 'r') as f:
#         sap_data = json.load(f)
#     classification = sap_data.get('Revision(Classification)', {})
#     for idx, name in classification.items():
#         if name and name.strip() == test_name:
#             try:
#                 return int(idx)
#             except ValueError:
#                 continue
#     return None

# # Example usage:
# # test_index = get_test_index('Cap/DF - 2 windings')
# # print(f"Index: {test_index}")
