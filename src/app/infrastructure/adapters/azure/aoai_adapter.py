"""Azure OpenAI Adapter for interfacing with Azure's OpenAI services."""

import logging
from typing import Any, Dict, Optional
from langchain_core.callbacks import AsyncCallbackHandler
from pydantic import SecretStr
from openai import RateLimitError
from langchain_openai import AzureChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import (  # pylint: disable=ungrouped-imports
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import LLMResult, Generation

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)
from app.domain.ports.azure import AzureOpenAIPort


_logger = logging.getLogger(__name__)


def _log_retry(retry_state: RetryCallState) -> None:
    """Logs a warning when a retry attempt is made."""
    _logger.warning(
        "Azure OpenAI retry %s after %ss",
        retry_state.attempt_number,
        retry_state.seconds_since_start,
    )


def _to_lc_message(
    msg: Dict[str, str],
) -> HumanMessage | AIMessage | SystemMessage | ToolMessage:
    role = msg["role"]
    content = msg["content"]
    if role == "user":
        return HumanMessage(content=content)
    if role == "assistant":
        return AIMessage(content=content)
    if role == "system":
        return SystemMessage(content=content)
    if role == "tool":
        return ToolMessage(content=content)

    return HumanMessage(content=content)


class AzureOpenAIAdapter(AzureOpenAIPort):
    """Adapter for Azure OpenAI services."""

    def __init__(
        self,
        *,
        azure_endpoint: str,
        azure_deployment: str,
        api_key: str,
        api_version: str,
        default_temperature: float,
        default_max_tokens: int,
        default_timeout: Optional[float] = None,
    ):
        self._endpoint = azure_endpoint
        self._deployment = azure_deployment
        self._api_key = api_key
        self._api_version = api_version
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        self._default_timeout = default_timeout

        self._llm_cache: Dict[tuple, AzureChatOpenAI] = {}

    def chat_completion(
        self, messages: list[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        """Create a chat agent completion using Azure OpenAI."""
        tools = kwargs.pop("tools", [])
        system_prompt = kwargs.pop("system_prompt", None)

        model = self._get_or_create_llm(
            temperature=self._resolve(
                kwargs.get("temperature"), self._default_temperature
            ),
            max_tokens=self._resolve(
                kwargs.get("max_tokens"), self._default_max_tokens
            ),
            extra=kwargs,
        )

        agent = create_agent(
            model,
            tools=tools,
            system_prompt=system_prompt,
        )
        response = agent.invoke({"messages": messages})

        if isinstance(response, dict):
            if "output" in response:
                text = response["output"]
            elif "messages" in response and isinstance(response["messages"], list):
                last = response["messages"][-1]
                text = getattr(last, "content", str(last))
            else:
                text = str(response)
            meta = {}
        else:
            text = getattr(response, "content", str(response))
            meta = getattr(response, "response_metadata", {}) or {}
        return {"text": text, "metadata": meta}

    async def chat_completion_stream(
        self,
        messages: list[Dict[str, Any]],
        callback: AsyncCallbackHandler,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a streaming chat completion using Azure OpenAI."""
        tools = kwargs.pop("tools", [])
        system_prompt = kwargs.pop("system_prompt", None)
        temperature = kwargs.pop("temperature", self._default_temperature)
        max_tokens = kwargs.pop("max_tokens", self._default_max_tokens)

        llm = self._get_or_create_llm(
            temperature=self._resolve(
                kwargs.get("temperature"), self._default_temperature
            ),
            max_tokens=self._resolve(
                kwargs.get("max_tokens"), self._default_max_tokens
            ),
            extra=kwargs,
        )

        full_response = ""

        try:
            if tools:
                agent = create_agent(
                    llm,
                    tools=tools,
                    system_prompt=system_prompt,
                )

                agent_messages = [
                    {"role": msg["role"], "content": msg["content"]} for msg in messages
                ]

                async for event in agent.astream_events(
                    {"messages": agent_messages},
                    version="v2",
                ):
                    kind = event["event"]

                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            full_response += content
                            await callback.on_llm_new_token(content)

                    elif kind == "on_tool_start":
                        tool_name = event.get("name", "unknown")
                        _logger.debug("Tool started: %s", tool_name)

                    elif kind == "on_tool_end":
                        tool_name = event.get("name", "unknown")
                        _logger.debug("Tool completed: %s", tool_name)

                metadata = {
                    "model": self._deployment,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "streaming": True,
                    "tools_used": len(tools),
                }

            else:
                lc_messages = []
                if system_prompt:
                    lc_messages.append(SystemMessage(content=system_prompt))
                lc_messages.extend([_to_lc_message(msg) for msg in messages])

                async for chunk in llm.astream(
                    lc_messages, config={"callbacks": [callback]}
                ):
                    if hasattr(chunk, "content") and chunk.content:
                        full_response += chunk.content

                metadata = {
                    "model": self._deployment,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "streaming": True,
                }

            if not getattr(callback, "finished", False):
                llm_result = LLMResult(
                    generations=[[Generation(text=full_response)]],
                    llm_output={"model_name": self._deployment},
                )
                await callback.on_llm_end(llm_result)

            return {
                "text": full_response,
                "metadata": metadata,
            }

        except Exception as e:
            _logger.error("Streaming error: %s", e, exc_info=True)
            await callback.on_llm_error(e)
            raise

    def _get_or_create_llm(
        self,
        temperature: float,
        max_tokens: int,
        extra: Dict[str, Any],
    ) -> AzureChatOpenAI:
        """Get or create an LLM instance with caching."""
        tools = extra.get("tools", [])

        cache_key = (
            temperature,
            max_tokens,
            len(tools),
            extra.get("top_p"),
            extra.get("frequency_penalty"),
            extra.get("presence_penalty"),
        )

        if cache_key in self._llm_cache:
            _logger.debug("Reusing cached LLM instance for config: %s", cache_key)
            return self._llm_cache[cache_key]

        _logger.debug("Creating new LLM instance for config: %s", cache_key)
        llm = self._build_llm(
            temperature=temperature,
            max_tokens=max_tokens,
            extra=extra,
        )

        if tools:
            _logger.info("Binding %d tools to LLM", len(tools))
            llm = llm.bind_tools(tools)

        if len(self._llm_cache) >= 10:
            oldest_key = next(iter(self._llm_cache))
            del self._llm_cache[oldest_key]
            _logger.debug("LLM cache full, removed oldest config: %s", oldest_key)

        self._llm_cache[cache_key] = llm
        return llm

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential_jitter(initial=1, max=20),
        stop=stop_after_attempt(5),
        after=_log_retry,
        reraise=True,
    )
    def _build_llm(
        self,
        temperature: float,
        max_tokens: int,
        extra: Dict[str, Any],
    ) -> AzureChatOpenAI:
        model_kwargs = {}
        if "top_p" in extra:
            model_kwargs["top_p"] = float(extra["top_p"])
        if "frequency_penalty" in extra:
            model_kwargs["frequency_penalty"] = float(extra["frequency_penalty"])
        if "presence_penalty" in extra:
            model_kwargs["presence_penalty"] = float(extra["presence_penalty"])

        return AzureChatOpenAI(
            azure_endpoint=self._endpoint,
            deployment_name=self._deployment,
            openai_api_key=SecretStr(self._api_key),
            openai_api_version=self._api_version,
            temperature=float(temperature),
            max_tokens=int(max_tokens),
            model_kwargs=model_kwargs,
            timeout=self._default_timeout,
            streaming=True,
        )

    @staticmethod
    def _resolve(value, default):
        return default if value is None else value
