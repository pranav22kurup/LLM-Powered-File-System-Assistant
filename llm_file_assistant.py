"""
LLM File Assistant
Integrates file system tools with Groq LLM for natural language file operations.
"""

import json
import os
from typing import Optional

from groq import Groq

from fs_tools import (
    read_file,
    list_files,
    write_file,
    search_in_file,
    TOOLS_SCHEMA
)


class LLMFileAssistant:
    """
    An LLM-powered assistant that can perform file operations based on natural language queries.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the LLM File Assistant.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY environment variable)
            model: Groq model to use (default: llama-3.3-70b-versatile)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY environment variable or pass api_key parameter.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.model = model
        self.tools = TOOLS_SCHEMA
        self.conversation_history = []
        
        # System prompt for the assistant
        self.system_prompt = """You are a helpful file assistant that helps users manage and analyze resume files.
        
You have access to the following tools:
1. read_file - Read content from PDF, TXT, or DOCX files
2. list_files - List files in a directory, optionally filtered by extension
3. write_file - Write content to a file (creates directories if needed)
4. search_in_file - Search for keywords in a file

When users ask about files or resumes:
- Use list_files to discover available files
- Use read_file to read file contents
- Use search_in_file to find specific keywords or skills
- Use write_file to create summaries or reports

Always provide clear, helpful responses based on the actual file contents.
When creating summaries, extract key information like:
- Name and contact information
- Skills and technologies
- Work experience
- Education

The default resumes folder is './resumes' but users may specify other paths."""

    def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """
        Execute a tool and return the result as a string.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments to pass to the tool
            
        Returns:
            str: JSON string of the tool result
        """
        tool_functions = {
            "read_file": read_file,
            "list_files": list_files,
            "write_file": write_file,
            "search_in_file": search_in_file
        }
        
        if tool_name not in tool_functions:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        
        try:
            result = tool_functions[tool_name](**tool_args)
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Tool execution failed: {str(e)}"})

    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the assistant's response.
        
        Args:
            user_message: The user's natural language query
            
        Returns:
            str: The assistant's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Build messages with system prompt
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history
        
        # Initial API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages, # type: ignore
            tools=self.tools, # type: ignore
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        # Handle tool calls in a loop until no more tools are needed
        while assistant_message.tool_calls:
            # Add assistant message with tool calls to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })
            
            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"  [Calling tool: {tool_name}({tool_args})]")
                
                tool_result = self._execute_tool(tool_name, tool_args)
                
                # Add tool result to history
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            # Get next response
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages, # type: ignore
                tools=self.tools, # type: ignore
                tool_choice="auto"
            )
            
            assistant_message = response.choices[0].message
        
        # Final response (no more tool calls)
        final_response = assistant_message.content or ""
        self.conversation_history.append({
            "role": "assistant",
            "content": final_response
        })
        
        return final_response

    def reset_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []
        print("Conversation history cleared.")


def main():
    """Interactive CLI for the LLM File Assistant."""
    print("=" * 60)
    print("LLM File Assistant")
    print("=" * 60)
    print("An AI-powered assistant for managing resume files.")
    print("Type 'quit' or 'exit' to end the session.")
    print("Type 'reset' to clear conversation history.")
    print("=" * 60)
    print()
    
    try:
        assistant = LLMFileAssistant()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease set your OpenAI API key:")
        print("  Windows: set OPENAI_API_KEY=your-api-key")
        print("  Linux/Mac: export OPENAI_API_KEY=your-api-key")
        return
    
    print("Assistant initialized successfully!")
    print()
    
    # Example queries to show
    example_queries = [
        "Read all resumes in the resumes folder",
        "Find resumes mentioning Python experience",
        "Create a summary file for resume_john_doe.pdf",
        "List all PDF files in the current directory",
        "Search for 'JavaScript' in test_resume.txt"
    ]
    
    print("Example queries you can try:")
    for i, query in enumerate(example_queries, 1):
        print(f"  {i}. {query}")
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
            
            if user_input.lower() == "reset":
                assistant.reset_conversation()
                continue
            
            print()
            response = assistant.chat(user_input)
            print(f"\nAssistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
