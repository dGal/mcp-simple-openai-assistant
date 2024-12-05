# MCP Simple OpenAI Assistant

A simple MCP server for interacting with OpenAI assistants. This server allows other tools (like Claude Desktop) to create and interact with OpenAI assistants through the Model Context Protocol.

## Features

- Create new OpenAI assistants
- Start conversation threads
- Send messages and receive responses

## Installation

```bash
pip install mcp-simple-openai-assistant
```

## Configuration

The server requires an OpenAI API key to be set in the environment. For Claude Desktop, add this to your config:

```json
{
  "mcpServers": {
    "openai-assistant": {
      "command": "python",
      "args": ["-m", "mcp-simple-openai-assistant"],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Usage

Once configured, the server provides tools to:
1. Create new assistants with specific instructions
2. Start new conversation threads
3. Send messages and receive responses

The server handles all OpenAI API communication, including managing assistants, threads, and message handling.

## Development

To install for development:

```bash
git clone <repository-url>
cd mcp-simple-openai-assistant
pip install -e .
```