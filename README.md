# LLM-Powered File System Assistant

An AI-powered assistant that uses Large Language Models (LLM) to perform intelligent file operations on resume files. The assistant can read, search, analyze, and summarize resumes through natural language queries.

## Features

- **Read Files**: Extract text from PDF, TXT, and DOCX files
- **List Files**: Browse directories with optional extension filtering
- **Search Files**: Case-insensitive keyword search with context
- **Write Files**: Create summaries and reports
- **Natural Language Interface**: Interact using plain English queries
- **Tool Calling**: LLM automatically selects appropriate tools

## Project Structure

```
LLM Assignment/
├── fs_tools.py              # Core file system tools
├── llm_file_assistant.py    # LLM integration and chat interface
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── resumes/                 # Sample resume files
    ├── resume_john_doe.txt
    ├── resume_jane_smith.txt
    ├── resume_michael_chen.txt
    ├── resume_sarah_johnson.txt
    ├── resume_david_wilson.txt
    ├── resume_emily_brown.txt
    ├── resume_alex_martinez.txt
    ├── resume_lisa_taylor.txt
    ├── resume_james_anderson.txt
    └── resume_rachel_kim.txt
```

## Prerequisites

- Python 3.8 or higher
- Groq API key (free tier available)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/pranav22kurup/LLM-Powered-File-System-Assistant.git
   cd LLM-Powered-File-System-Assistant
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up API key**
   
   Get a free API key from [Groq Console](https://console.groq.com/keys)
   
   ```bash
   # Windows (Command Prompt)
   set GROQ_API_KEY=your-api-key-here
   
   # Windows (PowerShell)
   $env:GROQ_API_KEY="your-api-key-here"
   
   # Linux/Mac
   export GROQ_API_KEY=your-api-key-here
   ```

## Usage

### Running the Assistant

```bash
python llm_file_assistant.py
```

### Example Queries

Once the assistant is running, you can ask questions like:

| Query | Description |
|-------|-------------|
| `List all resumes in the resumes folder` | Shows all resume files |
| `Read the resume for John Doe` | Displays resume content |
| `Find resumes mentioning Python experience` | Searches for Python skills |
| `Which candidates have AWS certifications?` | Searches for AWS |
| `Create a summary of Jane Smith's resume` | Generates and saves summary |
| `Find all backend engineers` | Searches job titles |
| `Who has machine learning experience?` | Searches for ML skills |

### Using Individual Tools

You can also import and use the tools directly:

```python
from fs_tools import read_file, list_files, search_in_file, write_file

# List all text files in resumes folder
files = list_files("./resumes", extension=".txt")
print(files)

# Read a specific resume
content = read_file("./resumes/resume_john_doe.txt")
print(content)

# Search for a keyword
results = search_in_file("./resumes/resume_john_doe.txt", "Python")
print(results)

# Write content to a file
result = write_file("./output/summary.txt", "Resume summary content here")
print(result)
```

## API Reference

### fs_tools.py

#### `read_file(filepath: str) -> dict`
Reads content from PDF, TXT, or DOCX files.

**Returns:**
```python
{
    "success": True,
    "filepath": "path/to/file",
    "content": "extracted text content",
    "metadata": {
        "size": 1234,
        "modified": "2024-01-15T10:30:00",
        "extension": ".txt"
    }
}
```

#### `list_files(directory: str, extension: str = None) -> list`
Lists files in a directory with optional extension filter.

**Returns:**
```python
[
    {
        "name": "resume.txt",
        "path": "resumes/resume.txt",
        "size": 2048,
        "modified": "2024-01-15T10:30:00"
    }
]
```

#### `search_in_file(filepath: str, keyword: str) -> dict`
Searches for keywords in file content (case-insensitive).

**Returns:**
```python
{
    "success": True,
    "filepath": "path/to/file",
    "keyword": "Python",
    "matches": [
        {
            "line_number": 15,
            "line": "Programming Languages: Python, JavaScript",
            "context": "surrounding text..."
        }
    ],
    "total_matches": 3
}
```

#### `write_file(filepath: str, content: str) -> dict`
Writes content to a file, creating directories if needed.

**Returns:**
```python
{
    "success": True,
    "filepath": "path/to/file",
    "bytes_written": 1234,
    "message": "File written successfully"
}
```

## Configuration

### Changing the LLM Model

Edit `llm_file_assistant.py` to use a different Groq model:

```python
assistant = LLMFileAssistant(model="llama-3.1-8b-instant")  # Faster, smaller
assistant = LLMFileAssistant(model="mixtral-8x7b-32768")    # Alternative model
```

### Using a Different LLM Provider

To use OpenAI instead of Groq, modify the `LLMFileAssistant` class to use the OpenAI client and set `OPENAI_API_KEY` environment variable.

## Troubleshooting

### Common Issues

**"API key is required" error**
- Ensure you've set the `GROQ_API_KEY` environment variable
- Check that the API key is valid at [Groq Console](https://console.groq.com)

**"Module not found" error**
- Run `pip install -r requirements.txt`
- Ensure your virtual environment is activated

**"File not found" error**
- Check that the file path is correct
- Use relative paths from the project directory

**PDF reading issues**
- Ensure `pypdf` is installed: `pip install pypdf`
- Some PDFs with complex formatting may not extract text properly

## Dependencies

| Package | Purpose |
|---------|---------|
| `groq` | LLM API client |
| `pypdf` | PDF text extraction |
| `python-docx` | DOCX file reading |

## License

MIT License - feel free to use and modify as needed.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Author

Pranav Kurup

---

*Built as part of an LLM Assignment project demonstrating tool-calling capabilities with Large Language Models.*
