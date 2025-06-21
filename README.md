# Prolec GE Transformer (LLM) POC

This project classifies transformer data using a Large Language Model (LLM) via the Gemini API. It reads transformer specifications from a CSV file, generates a prompt for the LLM, and parses the AI's JSON response to classify each transformer.

## Features

- Classifies transformer type (Medium, Large, EHV), winding type (Two-Winding, Three-Winding), and after test requirement.
- Batch testing: Loops through all transformers in `data/updated_data.csv` and compares AI output to expected values.
- Handles Gemini API rate limits automatically.

## Files

- `main.py`: Classifies a single transformer based on user input.
- `test_main.py`: Batch tests all transformers in the CSV and compares AI output to expected results.
- `data/updated_data.csv`: Source data for transformers, including expected classification fields.
- `requirements.txt`: Python dependencies.

## Usage

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run single transformer classification

```bash
python3 main.py
```

Follow the prompt to enter a transformer ID.

### 3. Run batch test

```bash
python3 test_main.py
```

The script will process all transformers in the CSV, compare AI results to expected values, and handle API rate limits automatically.

## Notes

- Requires a valid Gemini API key.
- The test script checks for transformer type, winding type, and after test requirement.
- Update `data/updated_data.csv` to add or modify transformer records.
