# LLM File Assistant

A Python-based file system tool suite integrated with LLM (OpenAI/Anthropic) for intelligent file operations, specifically designed for resume processing.

## Project Structure

```
LLM Assignment/
├── fs_tools.py              # Core file system tools module
├── llm_file_assistant.py    # LLM integration module
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── resumes/                # Sample resume files
    ├── resume_john_doe.txt
    ├── resume_jane_smith.txt
    └── resume_michael_chen.txt
```

## Installation

1. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys:**
   ```bash
   # For OpenAI
   export OPENAI_API_KEY="your-openai-api-key"
   
   # For Anthropic
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```

## Part A: Core File System Tools (fs_tools.py)

### Available Functions

#### 1. `read_file(filepath: str) → dict`
Read resume files (PDF, TXT, DOCX) and extract text content.

```python
from fs_tools import read_file

result = read_file("resumes/resume_john_doe.txt")
print(result["content"])
print(result["metadata"])
```

#### 2. `list_files(directory: str, extension: str = None) → dict`
List all files in a directory with optional extension filter.

```python
from fs_tools import list_files

# List all files
result = list_files("resumes")

# Filter by extension
result = list_files("resumes", ".txt")
result = list_files("resumes", ".pdf")
```

#### 3. `write_file(filepath: str, content: str) → dict`
Write content to a file, creating directories if needed.

```python
from fs_tools import write_file

result = write_file("output/summary.txt", "Resume summary content...")
print(result["success"])
```

#### 4. `search_in_file(filepath: str, keyword: str) → dict`
Search for keywords in file content (case-insensitive).

```python
from fs_tools import search_in_file

result = search_in_file("resumes/resume_john_doe.txt", "python")
print(f"Found {result['match_count']} matches")
for match in result["matches"]:
    print(f"Line {match['line_number']}: {match['line']}")
```

## Part B: LLM Integration (llm_file_assistant.py)

### Interactive Mode

```bash
# Using OpenAI (default)
python llm_file_assistant.py

# Using Anthropic
python llm_file_assistant.py --provider anthropic

# Specify model
python llm_file_assistant.py --model gpt-4o
```

### Single Query Mode

```bash
python llm_file_assistant.py -q "Read all resumes in the resumes folder"
python llm_file_assistant.py -q "Find resumes mentioning Python experience"
python llm_file_assistant.py -q "Create a summary file for resume_john_doe.txt"
```

### Demo Mode (No API Required)

```bash
python llm_file_assistant.py --demo
```

### Programmatic Usage

```python
from llm_file_assistant import LLMFileAssistant

# Initialize with OpenAI
assistant = LLMFileAssistant(provider="openai")

# Or with Anthropic
assistant = LLMFileAssistant(provider="anthropic")

# Process queries
response = assistant.query("Read all resumes in the resumes folder")
print(response)

response = assistant.query("Find resumes mentioning Python experience")
print(response)

response = assistant.query("Create a summary file for resume_john_doe.txt")
print(response)
```

## Example Queries

| Query | Action |
|-------|--------|
| "Read all resumes in the resumes folder" | Lists and reads all resume files |
| "Find resumes mentioning Python experience" | Searches for Python keyword in resumes |
| "Create a summary file for resume_john_doe.txt" | Reads resume and writes a summary |
| "List all PDF files in the resumes folder" | Lists files filtered by .pdf extension |
| "What skills does Jane Smith have?" | Reads Jane's resume and extracts skills |

## Supported File Formats

| Format | Extension | Library Used |
|--------|-----------|--------------|
| Plain Text | .txt | Built-in |
| PDF | .pdf | PyPDF2 |
| Word Document | .docx | python-docx |

## Error Handling

All functions return structured responses with:
- `success`: Boolean indicating operation success
- `error`: Error message if failed (None if successful)
- Additional relevant data based on the operation

## Testing

Run the fs_tools module directly to test basic functionality:

```bash
python fs_tools.py
```

## License

This project is created for educational purposes as part of an LLM assignment.
