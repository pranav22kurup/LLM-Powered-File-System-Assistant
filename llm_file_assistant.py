"""
llm_file_assistant.py – LLM-powered file-system assistant.

Uses GitHub Models (via the OpenAI-compatible API) to interpret natural-language
queries and automatically call the file-system tools defined in fs_tools.py
(read_file, list_files, write_file, search_in_file) via function-calling.

Usage
-----
    python llm_file_assistant.py                     # interactive REPL
    python llm_file_assistant.py "Read all resumes"  # single query

Set the GITHUB_TOKEN environment variable (or place it in a .env file).
"""

from __future__ import annotations

import json
import os
import sys

from openai import OpenAI

# -- Import the file-system tools -----------------------------------------
import fs_tools

# -- Try loading .env (optional) ------------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on env var being set already

# =========================================================================
# Tool definitions (OpenAI function-calling schema)
# =========================================================================

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a file and extract its text content. "
                "Supports PDF (.pdf), Word (.docx), and plain-text files "
                "(.txt, .md, .csv, .log, .json). "
                "Returns the full text content together with file metadata "
                "(filename, extension, size, last-modified date)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Absolute or relative path to the file to read.",
                    },
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List all files in a directory. Optionally filter by file extension. "
                "Returns each file's name, full path, size in bytes, and last-modified date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Path to the directory to list.",
                    },
                    "extension": {
                        "type": "string",
                        "description": (
                            "Optional file extension to filter by, e.g. '.pdf' or 'txt'. "
                            "Omit to list all files."
                        ),
                    },
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write text content to a file. Creates any missing parent directories "
                "automatically. Returns success/failure status and number of bytes written."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Destination file path.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content to write to the file.",
                    },
                },
                "required": ["filepath", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": (
                "Search for a keyword inside a file (case-insensitive). "
                "Supports PDF, DOCX, and text files. "
                "Returns the number of matches and each match with its surrounding context."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file to search in.",
                    },
                    "keyword": {
                        "type": "string",
                        "description": "The keyword or phrase to search for (case-insensitive).",
                    },
                },
                "required": ["filepath", "keyword"],
            },
        },
    },
]

# Map tool names → callable functions
TOOL_DISPATCH: dict = {
    "read_file": fs_tools.read_file,
    "list_files": fs_tools.list_files,
    "write_file": fs_tools.write_file,
    "search_in_file": fs_tools.search_in_file,
}

# =========================================================================
# Constants
# =========================================================================

MODEL = os.getenv("GITHUB_MODEL", "gpt-4o-mini")
MAX_TOKENS = 2048
MAX_TOOL_RESULT_CHARS = 800   # aggressive truncation – GitHub Models free tier caps requests at 8 000 tokens
MAX_CONVERSATION_CHARS = 12000  # rough char budget for the whole conversation (≈ 3 000 tokens)
SYSTEM_PROMPT = (
    "You are a helpful file-system assistant. You help users manage, read, "
    "search, and organize files on their local machine.\n\n"
    "You have access to four tools:\n"
    "  • read_file – read/extract content from PDF, DOCX, or text files\n"
    "  • list_files – list files in a directory, optionally filtering by extension\n"
    "  • write_file – write text to a file (creates directories as needed)\n"
    "  • search_in_file – search for keywords inside a file\n\n"
    "Always use these tools to interact with the file system instead of guessing "
    "at file contents. When the user asks about multiple files, call the tools "
    "for each file as needed. Provide clear, concise summaries of the results.\n"
    "NOTE: Tool results may be truncated. Work with whatever data is available."
)

# =========================================================================
# Core assistant logic
# =========================================================================


def _truncate(text: str, max_chars: int = MAX_TOOL_RESULT_CHARS) -> str:
    """Truncate text to *max_chars*, appending an ellipsis note if trimmed."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def _trim_conversation(conversation: list, max_chars: int = MAX_CONVERSATION_CHARS) -> list:
    """Return a trimmed copy of *conversation* that fits within *max_chars*.

    Messages are grouped into logical units (a user msg, an assistant msg
    with its tool-call results, etc.) so that we never orphan ``tool``
    messages from the ``assistant`` message that requested them.  Oldest
    groups are dropped first.
    """
    # -- Build groups: each group is a list of consecutive messages that
    #    must stay together. --
    groups: list[list] = []
    for msg in conversation:
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
        if role == "tool":
            # Attach to the previous group (the assistant + its calls).
            if groups:
                groups[-1].append(msg)
            else:
                groups.append([msg])
        else:
            groups.append([msg])

    # -- Drop oldest groups until we fit. --
    total = sum(len(json.dumps(m, default=str)) for m in conversation)
    while total > max_chars and len(groups) > 1:
        removed_group = groups.pop(0)
        for m in removed_group:
            total -= len(json.dumps(m, default=str))

    # Flatten back.
    return [m for g in groups for m in g]


def execute_tool(name: str, arguments: dict) -> str:
    """Run a tool by name and return the JSON-serialised result."""
    func = TOOL_DISPATCH.get(name)
    if func is None:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        result = func(**arguments)
        raw = json.dumps(result, default=str)
        return _truncate(raw)
    except Exception as exc:
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})


def chat(user_message: str, client: OpenAI, conversation: list) -> str:
    """Send a user message, handle any tool calls in a loop, return the final text."""

    conversation.append({"role": "user", "content": user_message})

    while True:
        trimmed = _trim_conversation(conversation)
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + trimmed,  # type: ignore[list-item]
            tools=TOOLS,  # type: ignore[arg-type]
        )

        # Get the assistant message
        message = response.choices[0].message
        # Append the full assistant message to conversation history
        conversation.append(message.to_dict())  # type: ignore[attr-defined]

        # If the model didn't request any tool calls, we're done
        if not message.tool_calls:
            return message.content or ""

        # Otherwise, execute every tool call and feed results back
        for tool_call in message.tool_calls:
            name = tool_call.function.name  # type: ignore[union-attr]
            arguments = json.loads(tool_call.function.arguments)  # type: ignore[union-attr]

            print(f"  ⚙ Calling {name}({json.dumps(arguments, default=str)}) …")
            result_json = execute_tool(name, arguments)

            conversation.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_json,
                }
            )


# =========================================================================
# Interactive REPL
# =========================================================================


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: Set the GITHUB_TOKEN environment variable.")
        sys.exit(1)

    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=token,
    )
    conversation: list = []

    # If a query was passed as a CLI argument, run it once and exit
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\nYou: {query}\n")
        answer = chat(query, client, conversation)
        print(f"\nAssistant:\n{answer}\n")
        return

    # Otherwise, start an interactive loop
    print("╔══════════════════════════════════════════════════════╗")
    print("║   LLM File-System Assistant  (type 'exit' to quit)  ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() in {"exit", "quit", "q"}:
            print("Goodbye!")
            break

        answer = chat(query, client, conversation)
        print(f"\nAssistant:\n{answer}\n")


if __name__ == "__main__":
    main()
