# Prolec GE Transformer (LLM) POC

This project classifies transformer data using a Large Language Model (LLM) via the Gemini API. It reads transformer specifications from a CSV file, generates a prompt for the LLM, and parses the AI's JSON response to classify each transformer. Then, it will print the cycle, labor, and test schedule hours using the data given from the Gemini API and the SAP Master File (`SAP.json`).

## Features

- Classifies transformer type (Medium, Large, EHV), winding type (Two-Winding, Three-Winding), and after test requirement.
- Batch testing: Loops through all transformers in `data/updated_data.csv` and compares AI output to expected values.
- Handles Gemini API rate limits automatically.
- Uses environment variables for API key management.
- Looks up cycle time, labor hours, and test schedule hours from `data/SAP.json` based on the AI's classification results.

## Dependencies

This project uses the following Python packages (see `requirements.txt`):

- `google-generativeai`, `google-ai-generativelanguage`, `google-api-core`, `google-api-python-client`, `google-auth`, `google-auth-httplib2`, `googleapis-common-protos`, `grpcio`, `grpcio-status`, `proto-plus`, `protobuf`: For interacting with the Gemini LLM API.
- `requests`, `tqdm`, `certifi`, `charset-normalizer`, `idna`, `pyasn1`, `pyasn1_modules`, `pydantic`, `pydantic_core`, `pyparsing`, `typing-inspection`, `typing_extensions`, `uritemplate`, `urllib3`: General dependencies for HTTP, parsing, and type support.
- `python-dotenv`: For loading environment variables (API keys) from a `.env` file.
- `csv`, `json`, `time`: Standard Python libraries for data handling and timing.

## APIs Used

- **Gemini API (Google Generative AI):** Used for LLM-based classification. Requires an API key, which should be stored in a `.env` file as `GOOGLE_API_KEY`.

## Files

- `main.py`: Classifies a single transformer based on user input. Prompts for a transformer ID, fetches its data from the CSV, sends a prompt to the Gemini API, and prints the classification result. Then, it uses the classification to look up and print cycle, labor, and test schedule hours from `data/SAP.json`.
- `tests/test_main.py`: Batch tests all transformers in the CSV. For each row, sends a prompt to the Gemini API, parses the response, and compares the AI's output to the expected values in the CSV for transformer type, winding type, and after test required. Handles API rate limits automatically.
- `data/updated_data.csv`: Source data for transformers, including all fields used for classification and expected results for validation.
- `data/SAP.json`: SAP Master File containing cycle time, labor hours, and test schedule hours for different transformer types and test scenarios. Used by `main.py` to provide additional operational data based on AI classification.
- `requirements.txt`: Python dependencies for the project.
- `.env`: (Not included in repo) Should contain your `GOOGLE_API_KEY` for the Gemini API.

## Usage

### 0. (Recommended) Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up your API key

#### Create a `.env` file in the project root with the following content:

```
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

### 3. Run single transformer classification

```bash
python3 main.py
```

Follow the prompt to enter a transformer ID. The script will print the classification result and the corresponding cycle, labor, and test schedule hours from `SAP.json`.

### 4. Run batch test

```bash
python3 tests/test_main.py
```

The script will process all transformers in the CSV, compare AI results to expected values, and handle API rate limits automatically.

## Notes

- Requires a valid Gemini API key.
- The test script checks for transformer type, winding type, and after test requirement.
- Update `data/updated_data.csv` to add or modify transformer records.
- Make sure your `.env` file is present and correct before running the scripts.
- The SAP Master File (`SAP.json`) must be present in the `data/` directory for `main.py` to provide cycle, labor, and test schedule hours.
