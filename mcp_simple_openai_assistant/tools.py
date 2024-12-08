"""Tool definitions for the OpenAI Assistant MCP server."""

from mcp.types import Tool

def get_tool_definitions() -> list[Tool]:
    """Get all tool definitions for the server."""
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
                        "description": "Instructions for the assistant that will shape its behavior and responses"
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
            description="Creates a new conversation thread. Threads have large capacity and the context window is moving so that it always covers a certain number of tokens (depending on the model).",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="send_message",
            description="""Send a message to assistant and start processing.
                         The response will not be immediately available - use check_response with the same thread_id to get it when ready.""",
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
                        "description": "Message to send"
                    }
                },
                "required": ["thread_id", "assistant_id", "message"]
            }
        ),
        Tool(
            name="check_response",
            description="""Check if assistant's response is ready in the thread.
                         Returns either 'in_progress' status or the actual response if ready.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "string",
                        "description": "Thread ID to check"
                    }
                },
                "required": ["thread_id"]
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
                        "description": "Optional: New model to use (e.g. gpt-4o)"
                    }
                },
                "required": ["assistant_id"]
            }
        )
    ]