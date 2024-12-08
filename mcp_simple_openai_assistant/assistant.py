"""OpenAI Assistant implementation with quick return and separate status checking."""

import os
from typing import Optional, Literal
import openai
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Run

RunStatus = Literal["completed", "in_progress", "failed", "cancelled", "expired"]

class OpenAIAssistant:
    """Handles interactions with OpenAI's Assistant API."""
    
    def __init__(self):
        """Initialize the OpenAI client with API key from environment."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = openai.OpenAI(api_key=self.api_key)

    async def create_assistant(
        self,
        name: str,
        instructions: str,
        model: str = "gpt-4o"
    ) -> Assistant:
        """Create a new OpenAI assistant.
        
        Args:
            name: Name for the assistant
            instructions: Instructions defining assistant's behavior
            model: Model to use (default: gpt-4o)
            
        Returns:
            Assistant object containing the assistant's details
        """
        return self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=model
        )

    async def new_thread(self) -> Thread:
        """Create a new conversation thread.
        
        Returns:
            Thread object containing the thread details
        """
        return self.client.beta.threads.create()

    async def list_assistants(self, limit: int = 20) -> list[Assistant]:
        """List available OpenAI assistants.
        
        Args:
            limit: Maximum number of assistants to return
            
        Returns:
            List of Assistant objects containing details like ID, name, and instructions
        """
        response = self.client.beta.assistants.list(limit=limit)
        return response.data

    async def retrieve_assistant(self, assistant_id: str) -> Assistant:
        """Get details about a specific assistant.
        
        Args:
            assistant_id: ID of the assistant to retrieve
            
        Returns:
            Assistant object with full configuration details
            
        Raises:
            ValueError: If assistant not found
        """
        return self.client.beta.assistants.retrieve(assistant_id)

    async def update_assistant(
        self,
        assistant_id: str,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        model: Optional[str] = None
    ) -> Assistant:
        """Update an existing assistant's configuration.
        
        Args:
            assistant_id: ID of the assistant to modify
            name: Optional new name
            instructions: Optional new instructions
            model: Optional new model
            
        Returns:
            Updated Assistant object
            
        Raises:
            ValueError: If assistant not found
        """
        update_params = {}
        if name is not None:
            update_params["name"] = name
        if instructions is not None:
            update_params["instructions"] = instructions
        if model is not None:
            update_params["model"] = model
            
        return self.client.beta.assistants.update(
            assistant_id=assistant_id,
            **update_params
        )

    async def send_message(
        self,
        thread_id: str,
        assistant_id: str,
        message: str
    ) -> str:
        """Send a message to an assistant and start processing.
        
        This method returns immediately after the message is sent and run is created.
        Use check_response() to get the actual response once it's ready.
        
        Args:
            thread_id: ID of the thread to use
            assistant_id: ID of the assistant to use
            message: Message content to send
            
        Returns:
            Status message confirming the message was sent
        """
        # Send the message
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            content=message,
            role="user"
        )

        # Create the run and return immediately
        self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        return "Message sent and processing started. Use check_response with this thread_id to get the response when ready."

    async def check_response(self, thread_id: str) -> tuple[RunStatus, Optional[str]]:
        """Check if response is ready in the thread.
        
        Args:
            thread_id: Thread ID to check
            
        Returns:
            Tuple of (status, response_text)
            - status is one of: "completed", "in_progress", "failed", "cancelled", "expired"
            - response_text is the assistant's response if status is "completed", None otherwise
        """
        # Get the latest run in the thread
        runs = self.client.beta.threads.runs.list(thread_id=thread_id, limit=1)
        if not runs.data:
            raise ValueError(f"No runs found in thread {thread_id}")
        
        latest_run = runs.data[0]
        
        # If run is completed, get the response
        if latest_run.status == "completed":
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=1
            )
            if not messages.data:
                raise ValueError("No response message found")
            
            message = messages.data[0]
            if not message.content or not message.content[0].text:
                raise ValueError("Response message has no text content")
                
            return "completed", message.content[0].text.value
        else:
            return latest_run.status, None
