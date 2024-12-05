"""MCP server implementation for OpenAI Assistant integration.

This server provides tools for creating and interacting with OpenAI assistants.
Available tools:
- list_assistants: Get a list of all available assistants
- create_assistant: Create a new assistant with specific instructions
- retrieve_assistant: Get details about an existing assistant
- update_assistant: Modify an existing assistant's configuration
- new_thread: Create a new conversation thread
- send_message: Send a message to an assistant and get their response

Usage examples:
1. Create an assistant for data analysis:
   create_assistant(
       name="Data Analyst",
       instructions="You help analyze data and create visualizations",
       model="gpt-3.5-turbo-0125"
   )

2. Start a conversation:
   thread_id = new_thread()
   send_message(
       thread_id=thread_id,
       assistant_id=assistant_id,
       message="Can you help me analyze this dataset?"
   )

Notes:
- Assistant IDs and Thread IDs should be stored for reuse
- Model names should be current OpenAI model versions
- Messages are processed asynchronously with appropriate timeouts
"""

import sys
import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .assistant import OpenAIAssistant

# Initialize the MCP server
app = Server("mcp-openai-assistant")

# Create a global assistant instance that will be initialized in main()
assistant: OpenAIAssistant | None = None

@app.list_tools()
async def list_tools() -> list[Tool]:
    """ List available tools for interacting with OpenAI assistants """
    return [
        Tool(
            name="create_assistant",
            description="Create a new OpenAI assistant to help you with your tasks, you can provide instructions that this assistant will follow when working with your prompts",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name for the assistant, use a descriptive name to be able to re-use it in the future"
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Instructions for the assistant"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (default: gpt-4o)",
                        "default": "gpt-4o"
                    }
                },
                "required": ["name", "instructions"]
            }
        ),
        Tool(
            name="new_thread",
            description="Creates a new conversation thread. Threads have large capacity and the context window is moving so that it always covers last X tokens.",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="send_message",
            description="Send a message to the assistant and wait for response",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "string",
                        "description": "Thread ID to use"
                    },
                    "assistant_id": {
                        "type": "string",
                        "description": "Assistant ID to use"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message (prompt) to send"
                    }
                },
                "required": ["thread_id", "assistant_id", "message"]
            }
        ),
        Tool(
    name="list_assistants",
    description="""List all available OpenAI assistants.
        Returns a list of assistants with their IDs, names, and configurations.
        Use this to find existing assistants you can work with.
        The results can be used with other tools like send_message or update_assistant.""",
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "number",
                "description": "Optional: Maximum number of assistants to return (default: 20)",
                "default": 20
            }
        },
        "additionalProperties": False
        }
        ),
        Tool(
            name="retrieve_assistant",
            description="Get details of a specific assistant",
            inputSchema={
                "type": "object",
                "properties": {
                    "assistant_id": {
                        "type": "string",
                        "description": "ID of the assistant to retrieve"
                    }
                },
                "required": ["assistant_id"]
            }
        ),
        Tool(
            name="update_assistant",
            description="Modify an existing assistant",
            inputSchema={
                "type": "object",
                "properties": {
                    "assistant_id": {
                        "type": "string",
                        "description": "ID of the assistant to modify"
                    },
                    "name": {
                        "type": "string",
                        "description": "Optional: New name for the assistant"
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Optional: New instructions for the assistant"
                    },
                    "model": {
                        "type": "string",
                        "description": "Optional: New model to use (e.g. gpt-3.5-turbo-0125)"
                    }
                },
                "required": ["assistant_id"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """ Handle tool calls. """
    global assistant
    if not assistant:
        return [TextContent(
            type="text",
            text="Error: Assistant not initialized. Missing OPENAI_API_KEY?"
        )]

    try:
        if name == "create_assistant":
            result = await assistant.create_assistant(
                name=arguments["name"],
                instructions=arguments["instructions"],
                model=arguments.get("model", "gpt-4o")
            )
            return [TextContent(
                type="text",
                text=f"Created assistant '{result.name}' with ID: {result.id}"
            )]

        elif name == "new_thread":
            result = await assistant.new_thread()
            return [TextContent(
                type="text",
                text=f"Created new thread with ID: {result.id}"
            )]

        elif name == "send_message":
            response = await assistant.send_message(
                thread_id=arguments["thread_id"],
                assistant_id=arguments["assistant_id"],
                message=arguments["message"]
            )
            return [TextContent(
                type="text",
                text=response
            )]
        elif name == "list_assistants":
            limit = arguments.get("limit", 20)
            assistants = await assistant.list_assistants(limit=limit)
            # Format the response to be readable
            assistant_list = [f"ID: {a.id}\nName: {a.name}\nModel: {a.model}\n" for a in assistants]
            return [TextContent(
                type="text",
                text="Available Assistants:\n\n" + "\n".join(assistant_list)
            )]

        elif name == "retrieve_assistant":
            result = await assistant.retrieve_assistant(arguments["assistant_id"])
            return [TextContent(
                type="text",
                text=f"Assistant Details:\nID: {result.id}\nName: {result.name}\n"
                     f"Model: {result.model}\nInstructions: {result.instructions}"
            )]

        elif name == "update_assistant":
            result = await assistant.update_assistant(
                assistant_id=arguments["assistant_id"],
                name=arguments.get("name"),
                instructions=arguments.get("instructions"),
                model=arguments.get("model")
            )
            return [TextContent(
                type="text",
                text=f"Updated assistant '{result.name}' (ID: {result.id})"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def main():
    """Main entry point for the server."""
    global assistant

    # Initialize the assistant
    try:
        assistant = OpenAIAssistant()
    except ValueError as e:
        print(f"Error initializing assistant: {e}", file=sys.stderr)
        return

    # Start the server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())