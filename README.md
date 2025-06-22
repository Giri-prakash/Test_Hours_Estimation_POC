# Transformer LLM POC

A proof-of-concept project that classifies transformer specifications using Google’s Gemini API (LLM). Based on the classification, the system also retrieves corresponding operational metrics (cycle time, labor hours, test schedule) from SAP master data.

---

## 📌 Key Features

- Classifies:
  - Transformer type: Medium, Large, or EHV
  - Winding type: Two-Winding or Three-Winding
  - After-test requirement: True or False
- Batch testing of multiple transformers from a CSV file
- Handles Gemini API rate limits
- Looks up operational data from SAP master file (`SAP.json`)
- Secure API key handling via `.env`

---

## 🛠️ Dependencies

Install dependencies listed in `requirements.txt`, including:

- **Gemini API Clients**: `google-generativeai`, `google-api-python-client`, etc.
- **Environment & Parsing**: `python-dotenv`, `requests`, `pydantic`, etc.
- **Standard Libraries**: `csv`, `json`, `time`

---

## 🔧 Setup Instructions

### 1. Create a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Required Packages

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

Create a `.env` file in the project root:

```
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

---

## 🚀 Usage

### Classify a Single Transformer

```bash
python3 main.py
```

Follow the prompt to enter a Transformer ID. The script will output the classification and corresponding cycle, labor, and test schedule hours.

### Run Batch Tests

```bash
python3 tests/test_main.py
```

Processes all transformers in `data/updated_data.csv` and compares AI output to expected values.

---

## 📁 Project Structure

| File/Folder             | Description                                       |
| ----------------------- | ------------------------------------------------- |
| `main.py`               | Classifies a single transformer based on ID input |
| `tests/test_main.py`    | Batch tests transformer records                   |
| `data/updated_data.csv` | Source data for transformers                      |
| `data/SAP.json`         | SAP Master File containing operational metrics    |
| `requirements.txt`      | Dependency list                                   |
| `.env`                  | API key file (not included in repo)               |

---

## 🧠 main.py Workflow

1. **User Input**  
   Prompt the user to enter a transformer ID.

2. **Data Lookup**  
   Load transformer data from `data/updated_data.csv`.

3. **Prompt Construction**  
   Build a prompt using transformer specs.

4. **LLM Classification**  
   Send prompt to Gemini API and receive structured JSON.

5. **Result Parsing**  
   Parse classification results:

   - `transformer_type`
   - `winding_type`
   - `after_test_required`

6. **SAP Data Lookup**  
   Use classification to retrieve:

   - Cycle time
   - Labor hours
   - Test schedule hours

7. **Output**  
   Display all retrieved values and total hours.

```
        +---------------------------------+
        |          User Input             |
        |     (Enter Transformer ID)      |
        +---------------------------------+
                        |
                        v
        +---------------------------------+
        |         Data Lookup             |
        |   (Find transformer in CSV)     |
        +---------------------------------+
                        |
                        v
        +---------------------------------+
        |      Prompt Construction        |
        |  (Build prompt for Gemini API)  |
        +---------------------------------+
                        |
                        v
        +---------------------------------+
        |        LLM Classification       |
        |  (Send prompt and receive JSON) |
        +---------------------------------+
                        |
                        v
        +---------------------------------+
        |        Result Parsing           |
        |    (Extract classification)     |
        +---------------------------------+
                        |
                        v
+-----------------------------------------------+
|               SAP Data Lookup                 |
|  (Find cycle, labor, test hours in SAP.json)  |
+-----------------------------------------------+
                        |
                        v
        +---------------------------------+
        |              Output             |
        |         (Print results)         |
        +---------------------------------+
```

---
