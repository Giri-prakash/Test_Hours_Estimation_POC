import time
import google.generativeai as genai  # pylint: disable=import-error
import csv
import json

# Retrieve transformer ID
transformer_id = input("Transformer ID: ")
transformer_row = None

# Loading current transformer data
with open('data/updated_data.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        if transformer_id in row[0]:
            transformer_row = row
            break

# Putting all transformer specs in a global dictionary
transformer_specs = {
    'id': transformer_row[0],
    'mva': transformer_row[1],
    'bil': transformer_row[2],
    'yv/tv': transformer_row[3],
    'auto': transformer_row[4],
    'conservator': transformer_row[5],
    'test_codes': transformer_row[6],
}

# Define Google API Key
GOOGLE_API_KEY = 'AIzaSyDOcEsPOwfMRiYP9KHshZgt-j-ikA1tDXs'

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

# Set up the Gemini 2.0 Flash model
model = genai.GenerativeModel('gemini-2.0-flash')

# Conditional prompt
rubric = f"""
You are a classification assistant for transformer data. Based on the rubric provided, classify the transformer type, winding type, and whether an After Test is required.

## Rubric:
Step 1: Transformer Type
- Medium: MVA < 60 and BIL < 650
- Large: MVA ≥ 60 (Other) or ≥ 36 (Auto), and BIL ≥ 750, and Conservator Unit = True
- EHV: MVA > 90 or BIL = 1150/1300

Step 2: Winding Type
- Three-Winding: "TV" or "YV" present in Winding Config and Type is not "Auto"
- Two-Winding: all other cases

Step 3: After Test Requirement
- If the test code contains "ALL TESTS", then After Test Required = True

## Input:
MVA: {transformer_specs['mva']}  
BIL: {transformer_specs['bil']}  
Type: {'Auto' if transformer_specs['auto'] == 'Yes' else 'Other'}  
Conservator Unit: {'True' if transformer_specs['conservator'] == 'Yes' else 'False'}  
Winding Config: {'TV' if transformer_specs['yv/tv'] == 'Yes' else 'Other'}  
Test Codes: {'ALL TESTS' if transformer_specs['test_codes'] == 'Yes' else 'None'}  

## Output Format:
The output should be a JSON object with the following keys:
- "transformer_type": The type of transformer (Medium, Large, EHV)
- "winding_type": The type of winding (Three-Winding, Two-Winding)
- "after_test_required": Boolean indicating if an After Test is required
## Example Output:
"""

prompt = rubric + """
{
  "transformer_type": "Medium",
  "winding_type": "Two-Winding",
  "after_test_required": false
}

## Output:
"""

# Generate content
while True:
    try:
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
    print(result)
except Exception as e:
    print('Failed to parse JSON:', e)
    print('Raw response:', response.text)