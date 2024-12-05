"""MCP server implementation for OpenAI Assistant integration."""

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
                model=arguments.get("model", "gpt-4-turbo-preview")
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