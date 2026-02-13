"""Azure OpenAI Port Interface"""

from typing import Protocol, runtime_checkable, Any
from langchain_core.callbacks import AsyncCallbackHandler


@runtime_checkable
class AzureOpenAIPort(Protocol):
    """Interface for Azure OpenAI operations."""

    def chat_completions(
        self,
        deployment_name: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] = None,
        tool_choice: str = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict[str, Any]:
        """Create a chat completion using Azure OpenAI.

        Args:
            deployment_name (str): The name of the deployment.
            messages (List[Dict[str, Any]]): The list of messages for the chat completion.
            tools (List[Dict[str, Any]], optional): List of tools to use. Defaults to None.
            tool_choice (str, optional): The chosen tool. Defaults to None.
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            max_tokens (int, optional): Maximum number of tokens to generate. Defaults to 1000.

        Returns:
            Dict[str, Any]: The response from the Azure OpenAI service.
        """

    async def chat_completions_stream(
        self,
        deployment_name: str,
        messages: list[dict[str, Any]],
        callback: AsyncCallbackHandler,
        tools: list[dict[str, Any]] = None,
        tool_choice: str = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Any:
        """Create a streaming chat completion using Azure OpenAI.

        Args:
            deployment_name (str): The name of the deployment.
            messages (List[Dict[str, Any]]): The list of messages for the chat completion.
            callback (AsyncCallbackHandler): The callback handler for streaming responses.
            tools (List[Dict[str, Any]], optional): List of tools to use. Defaults to None.
            tool_choice (str, optional): The chosen tool. Defaults to None.
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            max_tokens (int, optional): Maximum number of tokens to generate. Defaults to 1000.

        Returns:
            Any: An asynchronous generator yielding the streaming response.
        """
