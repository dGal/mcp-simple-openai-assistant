"""OpenAI Assistant implementation."""

import os
import asyncio
from typing import Optional
import openai
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Run


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
            model: Model to use (default: gpt-4-turbo-preview)
            
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
        message: str,
        timeout: Optional[int] = 120
    ) -> str:
        """Send a message to an assistant and wait for response.
        
        Args:
            thread_id: ID of the thread to use
            assistant_id: ID of the assistant to use
            message: Message content to send
            timeout: Maximum seconds to wait for response (default: 120)
            
        Returns:
            Assistant's response text
            
        Raises:
            TimeoutError: If response not received within timeout
            ValueError: If run fails or is cancelled
        """
        # Send the message
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            content=message,
            role="user"
        )

        # Create and monitor the run
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        # Poll for completion
        timeout_time = asyncio.get_event_loop().time() + timeout if timeout else None
        while True:
            # Check timeout
            if timeout_time and asyncio.get_event_loop().time() > timeout_time:
                await self._cancel_run(thread_id, run.id)
                raise TimeoutError("Assistant response timed out")

            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

            if run_status.status == "completed":
                # Get the latest message (the assistant's response)
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )
                if not messages.data:
                    raise ValueError("No response message found")
                
                # Extract text content from the message
                message = messages.data[0]
                if not message.content or not message.content[0].text:
                    raise ValueError("Response message has no text content")
                
                return message.content[0].text.value
            
            elif run_status.status in ["failed", "cancelled", "expired"]:
                raise ValueError(f"Run failed with status: {run_status.status}")
            
            # Wait before checking again
            await asyncio.sleep(1)

    async def _cancel_run(self, thread_id: str, run_id: str) -> None:
        """Cancel a running assistant run.
        
        Args:
            thread_id: ID of the thread
            run_id: ID of the run to cancel
        """
        try:
            self.client.beta.threads.runs.cancel(
                thread_id=thread_id,
                run_id=run_id
            )
        except Exception as e:
            # Log but don't raise - this is cleanup code
            print(f"Error cancelling run: {e}")
