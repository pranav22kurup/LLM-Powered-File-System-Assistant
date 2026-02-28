"""
File System Tools Module
Provides utilities for reading, writing, listing, and searching files.
Supports PDF, TXT, and DOCX formats for resume processing.
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
        file_path = Path(filepath)
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {filepath}",
                "content": None,
                "metadata": None
            }
        
        # Get file metadata
        stat = file_path.stat()
        metadata = {
            "filename": file_path.name,
            "filepath": str(file_path.absolute()),
            "extension": file_path.suffix.lower(),
            "size_bytes": stat.st_size,
            "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created_date": datetime.fromtimestamp(stat.st_ctime).isoformat()
        }
        
        extension = file_path.suffix.lower()
        content = ""
        
        if extension == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
        elif extension == ".pdf":
            try:
                import pypdf
                with open(file_path, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    pages_text = []
                    for page in reader.pages:
                        pages_text.append(page.extract_text() or "")
                    content = "\n".join(pages_text)
            except ImportError:
                return {
                    "success": False,
                    "error": "pypdf library not installed. Run: pip install pypdf",
                    "content": None,
                    "metadata": metadata
                }
                
        elif extension == ".docx":
            try:
                import docx
                doc = docx.Document(file_p-ath) # type: ignore
                paragraphs = [para.text for para in doc.paragraphs]
                content = "\n".join(paragraphs)
            except ImportError:
                return {
                    "success": False,
                    "error": "python-docx library not installed. Run: pip install python-docx",
                    "content": None,
                    "metadata": metadata
                }
                
        else:
            # Try to read as plain text for other extensions
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Unsupported file format or read error: {str(e)}",
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


def list_files(directory: str, extension: Optional[str] = None) -> list:
    """
    List all files in a directory with optional extension filtering.
    
    Args:
        directory: Path to the directory to list
        extension: Optional file extension filter (e.g., '.pdf', '.txt')
        
    Returns:
        list: List of dictionaries containing file metadata
    """
    try:
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return [{
                "success": False,
                "error": f"Directory not found: {directory}",
                "files": []
            }]
        
        if not dir_path.is_dir():
            return [{
                "success": False,
                "error": f"Path is not a directory: {directory}",
                "files": []
            }]
        
        files_list = []
        
        # Normalize extension format
        if extension and not extension.startswith("."):
            extension = f".{extension}"
        
        for item in dir_path.iterdir():
            if item.is_file():
                # Filter by extension if specified
                if extension and item.suffix.lower() != extension.lower():
                    continue
                    
                stat = item.stat()
                files_list.append({
                    "name": item.name,
                    "path": str(item.absolute()),
                    "extension": item.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "size_readable": _format_size(stat.st_size),
                    "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "created_date": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        # Sort by name
        files_list.sort(key=lambda x: x["name"].lower())
        
        return files_list
        
    except Exception as e:
        return [{
            "success": False,
            "error": f"Error listing directory: {str(e)}",
            "files": []
        }]


def _format_size(size_bytes: int) -> str:
    """Helper function to format file size in human readable format."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def write_file(filepath: str, content: str) -> dict:
    """
    Write content to a file, creating directories if needed.
    
    Args:
        filepath: Path where the file should be written
        content: Content to write to the file
        
    Returns:
        dict: Success/failure status with details
    """
    try:
        file_path = Path(filepath)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        stat = file_path.stat()
        
        return {
            "success": True,
            "message": f"File written successfully: {filepath}",
            "filepath": str(file_path.absolute()),
            "size_bytes": stat.st_size,
            "error": None
        }
        
    except PermissionError:
        return {
            "success": False,
            "error": f"Permission denied: Cannot write to {filepath}",
            "filepath": str(filepath),
            "size_bytes": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error writing file: {str(e)}",
            "filepath": str(filepath),
            "size_bytes": None
        }


def search_in_file(filepath: str, keyword: str) -> dict:
    """
    Search for keywords in file content with case-insensitive matching.
    
    Args:
        filepath: Path to the file to search
        keyword: Keyword or phrase to search for
        
    Returns:
        dict: Search results with matches and context
    """
    try:
        # First read the file content
        file_result = read_file(filepath)
        
        if not file_result["success"]:
            return {
                "success": False,
                "error": file_result["error"],
                "matches": [],
                "match_count": 0,
                "filepath": filepath
            }
        
        content = file_result["content"]
        if not content:
            return {
                "success": True,
                "matches": [],
                "match_count": 0,
                "filepath": filepath,
                "message": "File is empty"
            }
        
        # Split content into lines for context
        lines = content.split("\n")
        matches = []
        
        # Case-insensitive search using regex
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        
        for line_num, line in enumerate(lines, 1):
            if pattern.search(line):
                # Get surrounding context (2 lines before and after)
                start_idx = max(0, line_num - 3)
                end_idx = min(len(lines), line_num + 2)
                
                context_lines = lines[start_idx:end_idx]
                context = "\n".join(context_lines)
                
                # Highlight the keyword in the match
                highlighted_line = pattern.sub(
                    lambda m: f"**{m.group()}**",
                    line
                )
                
                matches.append({
                    "line_number": line_num,
                    "line_content": line.strip(),
                    "highlighted": highlighted_line.strip(),
                    "context": context
                })
        
        return {
            "success": True,
            "matches": matches,
            "match_count": len(matches),
            "filepath": filepath,
            "keyword": keyword,
            "metadata": file_result["metadata"],
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error searching file: {str(e)}",
            "matches": [],
            "match_count": 0,
            "filepath": filepath
        }


# Tool definitions for LLM integration
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in a directory. Can filter by extension (e.g., .pdf, .txt). Returns file metadata including name, size, and modified date.",
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
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates directories if needed. Returns success/failure status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The path where the file should be written"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": "Search for keywords in file content. Performs case-insensitive search and returns matches with surrounding context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The path to the file to search"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "The keyword or phrase to search for"
                    }
                },
                "required": ["filepath", "keyword"]
            }
        }
    }
]


if __name__ == "__main__":
    # Test examples
    print("Testing fs_tools module...")
    
    # Test list_files
    print("\n1. Testing list_files:")
    files = list_files(".")
    for f in files[:5]:
        if "error" not in f:
            print(f"  - {f['name']} ({f['size_readable']})")
    
    # Test read_file
    print("\n2. Testing read_file:")
    result = read_file("test_resume.txt")
    if result["success"]:
        print(f"  Content preview: {result['content'][:100]}...")
    else:
        print(f"  Error: {result['error']}")
    
    # Test search_in_file
    print("\n3. Testing search_in_file:")
    search_result = search_in_file("test_resume.txt", "Python")
    print(f"  Found {search_result['match_count']} matches for 'Python'")
    
    # Test write_file
    print("\n4. Testing write_file:")
    write_result = write_file("test_output.txt", "Test content written by fs_tools")
    print(f"  Write result: {write_result['success']}")
