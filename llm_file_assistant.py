"""
LLM File Assistant
Integrates file system tools with LLM (OpenAI/Anthropic) for intelligent file operations.
"""

import json
import os
from typing import Optional

from fs_tools import TOOL_DEFINITIONS, execute_tool


class LLMFileAssistant:
    """
    File assistant that uses LLM to understand queries and execute file operations.
    Supports both OpenAI and Anthropic APIs.
    """
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the LLM File Assistant.
        
        Args:
            provider: LLM provider ('openai' or 'anthropic')
            api_key: API key (if not provided, reads from environment)
            model: Model name to use
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.conversation_history = []
        
        if self.provider == "openai":
            self._init_openai(model)
        elif self.provider == "anthropic":
            self._init_anthropic(model)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'anthropic'")
    
    def _init_openai(self, model: Optional[str]):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI package required. Install with: pip install openai")
        
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model or "gpt-4o-mini"
        
        # Convert tool definitions to OpenAI format
        self.tools = [
            {
                "type": "function",
                "function": tool_def
            }
            for tool_def in TOOL_DEFINITIONS
        ]
    
    def _init_anthropic(self, model: Optional[str]):
        """Initialize Anthropic client."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Anthropic package required. Install with: pip install anthropic")
        
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model or "claude-3-5-sonnet-20241022"
        
        # Convert tool definitions to Anthropic format
        self.tools = [
            {
                "name": tool_def["name"],
                "description": tool_def["description"],
                "input_schema": tool_def["parameters"]
            }
            for tool_def in TOOL_DEFINITIONS
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the assistant."""
        return """You are a helpful file assistant that can read, write, list, and search files.
You have access to tools for file operations on the user's system.

When a user asks about files or file operations:
1. Use the appropriate tool to accomplish the task
2. Provide clear, helpful responses about the results
3. If reading resumes, summarize key information like skills, experience, and education

Available operations:
- Read files (PDF, TXT, DOCX)
- List files in directories with optional filtering
- Write content to files
- Search for keywords in files

Always be helpful and provide actionable information based on file contents."""
    
    def query(self, user_message: str) -> str:
        """
        Process a user query and return the response.
        
        Args:
            user_message: The user's query/request
            
        Returns:
            str: The assistant's response
        """
        if self.provider == "openai":
            return self._query_openai(user_message)
        else:
            return self._query_anthropic(user_message)
    
    def _query_openai(self, user_message: str) -> str:
        """Process query using OpenAI API."""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            *self.conversation_history
        ]
        
        # Initial API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        # Process tool calls if any
        while assistant_message.tool_calls:
            # Add assistant message with tool calls
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
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"  [Executing: {tool_name}({arguments})]")
                result = execute_tool(tool_name, arguments)
                
                # Add tool result to conversation
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, indent=2)
                })
            
            # Get next response
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                *self.conversation_history
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            assistant_message = response.choices[0].message
        
        # Add final assistant message
        final_response = assistant_message.content or ""
        self.conversation_history.append({
            "role": "assistant",
            "content": final_response
        })
        
        return final_response
    
    def _query_anthropic(self, user_message: str) -> str:
        """Process query using Anthropic API."""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Initial API call
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self._get_system_prompt(),
            tools=self.tools,
            messages=self.conversation_history
        )
        
        # Process response and tool calls
        while response.stop_reason == "tool_use":
            # Collect all content blocks
            assistant_content = response.content
            
            # Add assistant message
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_content
            })
            
            # Process tool use blocks
            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    tool_name = block.name
                    arguments = block.input
                    
                    print(f"  [Executing: {tool_name}({arguments})]")
                    result = execute_tool(tool_name, arguments)
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, indent=2)
                    })
            
            # Add tool results
            self.conversation_history.append({
                "role": "user",
                "content": tool_results
            })
            
            # Get next response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self._get_system_prompt(),
                tools=self.tools,
                messages=self.conversation_history
            )
        
        # Extract final text response
        final_response = ""
        for block in response.content:
            if hasattr(block, 'text'):
                final_response += block.text
        
        # Add final assistant message
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        
        return final_response
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        print("Conversation history cleared.")


def interactive_mode(assistant: LLMFileAssistant):
    """Run the assistant in interactive mode."""
    print("\n" + "=" * 60)
    print("LLM File Assistant - Interactive Mode")
    print("=" * 60)
    print("Commands:")
    print("  - Type your query to interact with files")
    print("  - 'clear' to clear conversation history")
    print("  - 'quit' or 'exit' to exit")
    print("=" * 60 + "\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            if user_input.lower() == 'clear':
                assistant.clear_history()
                continue
            
            print("\nAssistant: ", end="")
            response = assistant.query(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def demo_mode():
    """Run demo without API (shows what would be sent to LLM)."""
    print("\n" + "=" * 60)
    print("LLM File Assistant - Demo Mode (No API Required)")
    print("=" * 60)
    
    from fs_tools import list_files, read_file, search_in_file, write_file
    
    # Demo queries
    demo_queries = [
        ("List all files in the current directory", 
         lambda: list_files(".")),
        ("List only PDF files in resumes folder",
         lambda: list_files("resumes", ".pdf")),
        ("Read a resume file",
         lambda: read_file("resumes/sample_resume.txt")),
        ("Search for Python skills",
         lambda: search_in_file("resumes/sample_resume.txt", "python")),
    ]
    
    print("\nDemo queries and their results:\n")
    
    for query, func in demo_queries:
        print(f"Query: '{query}'")
        print("-" * 40)
        try:
            result = func()
            print(f"Result: {json.dumps(result, indent=2)[:500]}...")
        except Exception as e:
            print(f"Result: {e}")
        print()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM File Assistant")
    parser.add_argument(
        "--provider", 
        choices=["openai", "anthropic"], 
        default="openai",
        help="LLM provider to use (default: openai)"
    )
    parser.add_argument(
        "--model",
        help="Model name to use (optional)"
    )
    parser.add_argument(
        "--api-key",
        help="API key (optional, can also use environment variables)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode without API"
    )
    parser.add_argument(
        "--query", "-q",
        help="Single query to process (non-interactive mode)"
    )
    
    args = parser.parse_args()
    
    if args.demo:
        demo_mode()
        return
    
    try:
        assistant = LLMFileAssistant(
            provider=args.provider,
            api_key=args.api_key,
            model=args.model
        )
        
        if args.query:
            # Single query mode
            print("Processing query...")
            response = assistant.query(args.query)
            print(f"\nResponse:\n{response}")
        else:
            # Interactive mode
            interactive_mode(assistant)
            
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nTip: Set environment variables:")
        print("  - For OpenAI: export OPENAI_API_KEY='your-key'")
        print("  - For Anthropic: export ANTHROPIC_API_KEY='your-key'")
        print("\nOr run with --demo flag to see demo mode.")
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("\nInstall required packages:")
        print("  pip install openai anthropic PyPDF2 python-docx")


if __name__ == "__main__":
    main()
