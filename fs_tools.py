"""
File System Tools Module
Provides tools for reading, listing, writing, and searching files.
Supports PDF, TXT, and DOCX file formats for resume processing.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


def read_file(filepath: str) -> dict:
    """
    Read resume files (PDF, TXT, DOCX) and extract text content.
    
    Args:
        filepath: Path to the file to read
        
    Returns:
        dict: Structured response with content, metadata, and status
    """
    try:
        filepath = Path(filepath)
        
        if not filepath.exists():
            return {
                "success": False,
                "error": f"File not found: {filepath}",
                "content": None,
                "metadata": None
            }
        
        # Get file metadata
        stat = filepath.stat()
        metadata = {
            "filename": filepath.name,
            "filepath": str(filepath.absolute()),
            "size_bytes": stat.st_size,
            "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created_date": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "extension": filepath.suffix.lower()
        }
        
        content = ""
        extension = filepath.suffix.lower()
        
        if extension == ".txt":
            content = _read_txt(filepath)
        elif extension == ".pdf":
            content = _read_pdf(filepath)
        elif extension == ".docx":
            content = _read_docx(filepath)
        else:
            return {
                "success": False,
                "error": f"Unsupported file format: {extension}. Supported formats: .txt, .pdf, .docx",
                "content": None,
                "metadata": metadata
            }
        
        return {
            "success": True,
            "content": content,
            "metadata": metadata,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {str(e)}",
            "content": None,
            "metadata": None
        }


def _read_txt(filepath: Path) -> str:
    """Read text file content."""
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError("Unable to decode file with supported encodings")


def _read_pdf(filepath: Path) -> str:
    """Read PDF file content using PyPDF2."""
    try:
        import PyPDF2
    except ImportError:
        raise ImportError("PyPDF2 is required for PDF support. Install with: pip install PyPDF2")
    
    text_content = []
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
    
    return "\n".join(text_content)


def _read_docx(filepath: Path) -> str:
    """Read DOCX file content using python-docx."""
    try:
        import docx
    except ImportError:
        raise ImportError("python-docx is required for DOCX support. Install with: pip install python-docx")
    
    doc = docx.Document(filepath)
    paragraphs = [para.text for para in doc.paragraphs]
    return "\n".join(paragraphs)


def list_files(directory: str, extension: Optional[str] = None) -> list:
    """
    List all files in a directory with optional extension filter.
    
    Args:
        directory: Path to the directory to list
        extension: Optional file extension filter (e.g., '.pdf', '.txt')
        
    Returns:
        list: List of file metadata dictionaries
    """
    try:
        directory = Path(directory)
        
        if not directory.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}",
                "files": []
            }
        
        if not directory.is_dir():
            return {
                "success": False,
                "error": f"Path is not a directory: {directory}",
                "files": []
            }
        
        files = []
        
        # Normalize extension format
        if extension and not extension.startswith('.'):
            extension = '.' + extension
        
        for item in directory.iterdir():
            if item.is_file():
                # Filter by extension if specified
                if extension and item.suffix.lower() != extension.lower():
                    continue
                
                stat = item.stat()
                files.append({
                    "name": item.name,
                    "path": str(item.absolute()),
                    "size_bytes": stat.st_size,
                    "size_readable": _format_size(stat.st_size),
                    "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "created_date": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "extension": item.suffix.lower()
                })
        
        # Sort by name
        files.sort(key=lambda x: x["name"].lower())
        
        return {
            "success": True,
            "directory": str(directory.absolute()),
            "total_files": len(files),
            "filter_extension": extension,
            "files": files,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error listing directory: {str(e)}",
            "files": []
        }


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def write_file(filepath: str, content: str) -> dict:
    """
    Write content to a file, creating directories if needed.
    
    Args:
        filepath: Path to the file to write
        content: Content to write to the file
        
    Returns:
        dict: Success/failure status with details
    """
    try:
        filepath = Path(filepath)
        
        # Create parent directories if they don't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        stat = filepath.stat()
        
        return {
            "success": True,
            "message": f"File written successfully: {filepath}",
            "filepath": str(filepath.absolute()),
            "size_bytes": stat.st_size,
            "created_directories": not filepath.parent.exists(),
            "error": None
        }
        
    except PermissionError:
        return {
            "success": False,
            "error": f"Permission denied: Cannot write to {filepath}",
            "filepath": str(filepath)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error writing file: {str(e)}",
            "filepath": str(filepath)
        }


def search_in_file(filepath: str, keyword: str) -> dict:
    """
    Search for keywords in file content with context.
    
    Args:
        filepath: Path to the file to search
        keyword: Keyword to search for (case-insensitive)
        
    Returns:
        dict: Matches with surrounding context
    """
    try:
        # First, read the file content
        read_result = read_file(filepath)
        
        if not read_result["success"]:
            return {
                "success": False,
                "error": read_result["error"],
                "matches": [],
                "match_count": 0
            }
        
        content = read_result["content"]
        if not content:
            return {
                "success": True,
                "filepath": filepath,
                "keyword": keyword,
                "matches": [],
                "match_count": 0,
                "message": "File is empty"
            }
        
        # Split content into lines for context
        lines = content.split('\n')
        matches = []
        
        # Case-insensitive search
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        
        for line_num, line in enumerate(lines, 1):
            if pattern.search(line):
                # Get surrounding context (2 lines before and after)
                start_idx = max(0, line_num - 3)
                end_idx = min(len(lines), line_num + 2)
                
                context_lines = lines[start_idx:end_idx]
                context = "\n".join(context_lines)
                
                # Highlight the match in the line
                highlighted_line = pattern.sub(f"**{keyword.upper()}**", line)
                
                matches.append({
                    "line_number": line_num,
                    "line": line.strip(),
                    "highlighted_line": highlighted_line.strip(),
                    "context": context.strip()
                })
        
        return {
            "success": True,
            "filepath": filepath,
            "keyword": keyword,
            "matches": matches,
            "match_count": len(matches),
            "metadata": read_result["metadata"],
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error searching file: {str(e)}",
            "matches": [],
            "match_count": 0
        }


# Tool definitions for LLM integration
TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read resume files (PDF, TXT, DOCX) and extract text content. Returns structured response with content and metadata.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path to the file to read"
                }
            },
            "required": ["filepath"]
        }
    },
    {
        "name": "list_files",
        "description": "List all files in a directory with optional extension filter. Returns file metadata including name, size, and modified date.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "The path to the directory to list"
                },
                "extension": {
                    "type": "string",
                    "description": "Optional file extension filter (e.g., '.pdf', '.txt', '.docx')"
                }
            },
            "required": ["directory"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file, creating directories if needed. Returns success/failure status.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["filepath", "content"]
        }
    },
    {
        "name": "search_in_file",
        "description": "Search for keywords in file content. Returns matches with surrounding context. Case-insensitive search.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path to the file to search"
                },
                "keyword": {
                    "type": "string",
                    "description": "The keyword to search for (case-insensitive)"
                }
            },
            "required": ["filepath", "keyword"]
        }
    }
]


# Function mapping for tool execution
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "list_files": list_files,
    "write_file": write_file,
    "search_in_file": search_in_file
}


def execute_tool(tool_name: str, arguments: dict) -> dict:
    """
    Execute a tool by name with given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool
        
    Returns:
        dict: Result from tool execution
    """
    if tool_name not in TOOL_FUNCTIONS:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
    
    return TOOL_FUNCTIONS[tool_name](**arguments)


if __name__ == "__main__":
    # Example usage
    print("File System Tools Module")
    print("=" * 40)
    
    # Test list_files
    print("\nListing current directory:")
    result = list_files(".", ".py")
    print(f"Found {result.get('total_files', 0)} Python files")
    
    # Test write and read
    test_content = "This is a test resume.\nSkills: Python, JavaScript, SQL"
    print("\nWriting test file...")
    write_result = write_file("test_resume.txt", test_content)
    print(f"Write result: {write_result['success']}")
    
    print("\nReading test file...")
    read_result = read_file("test_resume.txt")
    print(f"Read result: {read_result['success']}")
    
    print("\nSearching for 'python'...")
    search_result = search_in_file("test_resume.txt", "python")
    print(f"Found {search_result['match_count']} matches")
