# LLM-Powered File System Assistant

An intelligent file-system assistant that uses **GitHub Models** (via the OpenAI-compatible API) to interpret natural-language queries and automatically interact with local files. Built for resume management but works with any text-based documents.

## Features

- **Read** PDF, DOCX, and plain-text files with automatic text extraction
- **List** directory contents with optional extension filtering
- **Write** files with automatic directory creation
- **Search** for keywords across any supported file type (case-insensitive, with context)
- **Natural language** interface — ask questions in plain English and the LLM decides which tools to call

## Project Structure

```
├── fs_tools.py              # File-system tool functions
├── llm_file_assistant.py    # LLM integration (GitHub Models)
├── requirements.txt         # Python dependencies
├── README.md
└── resumes/                 # Sample resume data (10 files)
    ├── resume_john_doe.txt
    ├── resume_jane_smith.txt
    ├── resume_alex_johnson.txt
    ├── resume_maria_garcia.txt
    ├── resume_david_kim.txt
    ├── resume_sarah_chen.docx
    ├── resume_omar_hassan.docx
    ├── resume_emily_taylor.docx
    ├── resume_michael_brown.pdf
    └── resume_lisa_wang.pdf
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/pranav22kurup/LLM-Powered-File-System-Assistant.git
cd LLM-Powered-File-System-Assistant
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your GitHub Token

Create a `.env` file in the project root (recommended):

```
GITHUB_TOKEN=ghp_...
```

Or export it directly:

```bash
# Windows PowerShell
$env:GITHUB_TOKEN = "ghp_..."

# macOS / Linux
export GITHUB_TOKEN="ghp_..."
```

> **Note:** You need a GitHub personal access token with access to GitHub Models.
> Generate one at https://github.com/settings/tokens.

### 5. (Optional) Choose a model

By default the assistant uses `gpt-4o-mini`. Override with the `GITHUB_MODEL` env var:

```bash
# .env
GITHUB_MODEL=gpt-4o-mini
```

See the full catalog at https://github.com/marketplace/models.

> **Free-tier note:** GitHub Models limits requests to **8 000 tokens**.
> The assistant automatically truncates large tool results and trims
> conversation history to stay within this budget.

## Usage

### Interactive mode

```bash
python llm_file_assistant.py
```

This opens a REPL where you can type queries in plain English. Type `exit` to quit.

### Single-query mode

```bash
python llm_file_assistant.py "Read all resumes in the resumes folder"
```

### Example queries

| Query | What happens |
|---|---|
| `Read all resumes in the resumes folder` | Lists the directory, then reads every file and summarises contents |
| `Find resumes mentioning Python experience` | Searches each resume for "Python" and reports matches with context |
| `Create a summary file for resume_john_doe.txt` | Reads the resume, generates a summary, and writes it to a new file |
| `List all PDF files in the resumes folder` | Calls `list_files` with extension `.pdf` |
| `Search for Kubernetes in resume_maria_garcia.txt` | Searches the file and returns matching snippets |

### Using the tools directly (no LLM)

You can also import `fs_tools` in your own scripts:

```python
from fs_tools import read_file, list_files, write_file, search_in_file

# Read a resume
result = read_file("resumes/resume_john_doe.txt")
print(result["content"])

# List all PDFs
files = list_files("resumes", extension=".pdf")
for f in files:
    print(f["name"], f["size_bytes"], "bytes")

# Search for a keyword
matches = search_in_file("resumes/resume_jane_smith.txt", "machine learning")
print(f"Found {matches['match_count']} matches")

# Write a file
write_file("output/summary.txt", "This is a summary.")
```

## Tool Reference

### `read_file(filepath: str) -> dict`

Reads and extracts text from PDF (via PyPDF2), DOCX (via python-docx), or plain-text files. Returns:

```json
{
  "status": "success",
  "filepath": "resumes/resume_john_doe.txt",
  "content": "John Doe\nEmail: ...",
  "metadata": {
    "filename": "resume_john_doe.txt",
    "extension": ".txt",
    "size_bytes": 1383,
    "modified": "2026-03-01T07:56:03"
  },
  "error": null
}
```

### `list_files(directory: str, extension: str = None) -> list`

Lists files in a directory with optional extension filter. Returns a list of:

```json
{
  "name": "resume_john_doe.txt",
  "path": "/full/path/to/resume_john_doe.txt",
  "size_bytes": 1383,
  "modified": "2026-03-01T07:56:03"
}
```

### `write_file(filepath: str, content: str) -> dict`

Writes text content to a file, creating parent directories as needed. Returns:

```json
{
  "status": "success",
  "filepath": "/full/path/to/output.txt",
  "bytes_written": 42,
  "error": null
}
```

### `search_in_file(filepath: str, keyword: str) -> dict`

Case-insensitive keyword search with surrounding context. Returns:

```json
{
  "status": "success",
  "keyword": "python",
  "match_count": 3,
  "matches": [
    {
      "position": 245,
      "context": "...Languages: [Python], JavaScript, TypeScript...",
      "matched_text": "Python"
    }
  ],
  "error": null
}
```

## How it works

1. The user types a natural-language query
2. The query is sent to **GitHub Models** along with tool definitions
3. The model decides which tools to call and with what arguments
4. `llm_file_assistant.py` executes the tools via `fs_tools.py` and returns the JSON results
5. Large tool results are **truncated** to stay within the token budget
6. The model interprets the results and generates a human-readable response
7. Steps 3-6 repeat if the model needs to call more tools (agentic loop)
8. Older conversation history is **trimmed** automatically when the context grows too large

## Dependencies

| Package | Purpose |
|---|---|
| `openai` | OpenAI-compatible client for GitHub Models |
| `PyPDF2` | PDF text extraction |
| `python-docx` | DOCX text extraction |
| `python-dotenv` | Load API key from `.env` file (optional) |

## License

MIT
