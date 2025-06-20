"""MCP server implementation for OpenAI Assistant integration.

This server provides tools for creating and interacting with OpenAI assistants.
Available tools:
- list_assistants: Get a list of all available assistants
- create_assistant: Create a new assistant with specific instructions
- retrieve_assistant: Get details about an existing assistant
- update_assistant: Modify an existing assistant's configuration
- new_thread: Create a new conversation thread
- send_message_get_response: Start processing a message and wait for response and return it

Usage examples:
1. Create an assistant for data analysis:
   create_assistant(
       name="Data Analyst",
       instructions="You help analyze data and create visualizations",
       model="gpt-4o"
   )

2. Start a conversation:
   thread_id = new_thread()
   send_message_get_response(
       thread_id=thread_id,
       assistant_id=assistant_id,
       message="Can you help me analyze this dataset?"
   )

Notes:
- Assistant IDs and Thread IDs should be stored for reuse
- Messages may take some time to process
"""

import sys
import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .assistant import OpenAIAssistant
from .tools import get_tool_definitions

# Initialize the MCP server
app = Server("mcp-openai-assistant")

# Create a global assistant instance that will be initialized in main()
assistant: OpenAIAssistant | None = None

@app.list_tools()
async def list_tools():
    """List available tools for interacting with OpenAI assistants."""
    return get_tool_definitions()

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
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

        elif name == "send_message_get_response":
            thread_id = arguments.get("thread_id")
            # create new thread if no thread id is provided
            # and return the id as part of the response
            if not thread_id:
                thread = await assistant.new_thread()
                thread_id = thread.id
            status, response = await assistant.send_message_get_response(
                thread_id=thread_id,
                assistant_id=arguments["assistant_id"],
                message=arguments["message"]
            )
            thread_msg = ""
            if not arguments.get("thread_id") and thread_id:
                thread_msg = f"Created new thread with ID: {thread_id}\n\n"
            if status == "completed" and response:
                return [TextContent(type="text", text=thread_msg + response)]
            else:
                return [TextContent(
                    type="text",
                    text=thread_msg + f"Error: Run {status}. Please try sending your message again."
                )]

        elif name == "list_assistants":
            limit = 20
            if arguments:
                try:
                    limit = int(arguments.get("limit", 20))
                except ValueError:
                    pass
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

async def serve():
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
