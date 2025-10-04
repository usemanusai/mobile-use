import logging
from collections.abc import Awaitable, Callable
from typing import Literal, TypeVar, overload

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI

from minitap.mobile_use.config import (
    AgentNode,
    AgentNodeWithFallback,
    LLMUtilsNode,
    LLMWithFallback,
    settings,
)
from minitap.mobile_use.context import MobileUseContext

logger = logging.getLogger(__name__)


def get_google_llm(
    model_name: str = "gemini-2.5-pro",
    temperature: float = 0.7,
) -> ChatGoogleGenerativeAI:
    assert settings.GOOGLE_API_KEY is not None
    client = ChatGoogleGenerativeAI(
        model=model_name,
        max_tokens=None,
        temperature=temperature,
        api_key=settings.GOOGLE_API_KEY,
        max_retries=2,
    )
    return client


def get_vertex_llm(
    model_name: str = "gemini-2.5-pro",
    temperature: float = 0.7,
) -> ChatVertexAI:
    client = ChatVertexAI(
        model_name=model_name,
        max_tokens=None,
        temperature=temperature,
        max_retries=2,
    )
    return client


def get_openai_llm(
    model_name: str = "o3",
    temperature: float = 1,
) -> ChatOpenAI:
    assert settings.OPENAI_API_KEY is not None
    client = ChatOpenAI(
        model=model_name,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        temperature=temperature,
    )
    return client


def get_openrouter_llm(model_name: str, temperature: float = 1):
    assert settings.OPEN_ROUTER_API_KEY is not None
    # Return a standard ChatOpenAI client for OpenRouter. Structured output handling
    # will be applied by helper functions to avoid modifying Pydantic model fields.
    client = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=settings.OPEN_ROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    return client


def get_grok_llm(model_name: str, temperature: float = 1) -> ChatOpenAI:
    assert settings.XAI_API_KEY is not None
    client = ChatOpenAI(
        model=model_name,
        api_key=settings.XAI_API_KEY,
        temperature=temperature,
        base_url="https://api.x.ai/v1",
    )
    return client


@overload
def get_llm(
    ctx: MobileUseContext,
    name: AgentNodeWithFallback,
    *,
    use_fallback: bool = False,
    temperature: float = 1,
) -> BaseChatModel: ...


@overload
def get_llm(
    ctx: MobileUseContext,
    name: AgentNode,
    *,
    temperature: float = 1,
) -> BaseChatModel: ...


@overload
def get_llm(
    ctx: MobileUseContext,
    name: LLMUtilsNode,
    *,
    is_utils: Literal[True],
    temperature: float = 1,
) -> BaseChatModel: ...


def get_llm(
    ctx: MobileUseContext,
    name: AgentNode | LLMUtilsNode | AgentNodeWithFallback,
    is_utils: bool = False,
    use_fallback: bool = False,
    temperature: float = 1,
) -> BaseChatModel:
    llm = (
        ctx.llm_config.get_utils(name)  # type: ignore
        if is_utils
        else ctx.llm_config.get_agent(name)  # type: ignore
    )
    if use_fallback:
        if isinstance(llm, LLMWithFallback):
            llm = llm.fallback
        else:
            raise ValueError("LLM has no fallback!")
    if llm.provider == "openai":
        return get_openai_llm(llm.model, temperature)
    elif llm.provider == "google":
        return get_google_llm(llm.model, temperature)
    elif llm.provider == "vertexai":
        return get_vertex_llm(llm.model, temperature)
    elif llm.provider == "openrouter":
        return get_openrouter_llm(llm.model, temperature)
    elif llm.provider == "xai":
        return get_grok_llm(llm.model, temperature)
    else:
        raise ValueError(f"Unsupported provider: {llm.provider}")


T = TypeVar("T")


async def with_fallback(
    main_call: Callable[[], Awaitable[T]],
    fallback_call: Callable[[], Awaitable[T]],
    none_should_fallback: bool = True,
) -> T:
    try:
        result = await main_call()
        if result is None and none_should_fallback:
            logger.warning("Main LLM inference returned None. Falling back...")
            return await fallback_call()
        return result
    except Exception as e:
        logger.warning(f"❗ Main LLM inference failed: {e}. Falling back...")
        return await fallback_call()


# Helper that returns a structured-output runnable with provider-aware settings


def get_llm_with_structured_output(
    ctx: MobileUseContext,
    name: AgentNode | LLMUtilsNode | AgentNodeWithFallback,
    schema,
    *,
    is_utils: bool = False,
    use_fallback: bool = False,
    temperature: float = 1,
):
    # Resolve LLM configuration (provider/model), honoring utils and fallback
    llm_cfg = (
        ctx.llm_config.get_utils(name)  # type: ignore
        if is_utils
        else ctx.llm_config.get_agent(name)  # type: ignore
    )

    if use_fallback:
        if isinstance(llm_cfg, LLMWithFallback):
            llm_cfg = llm_cfg.fallback
        else:
            raise ValueError("LLM has no fallback!")

    provider = llm_cfg.provider
    model_name = llm_cfg.model

    # Instantiate the base client as get_llm would
    if provider == "openai":
        client = get_openai_llm(model_name, temperature)
    elif provider == "google":
        client = get_google_llm(model_name, temperature)
    elif provider == "vertexai":
        client = get_vertex_llm(model_name, temperature)
    elif provider == "openrouter":
        client = get_openrouter_llm(model_name, temperature)
    elif provider == "xai":
        client = get_grok_llm(model_name, temperature)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # IMPORTANT: Choose structured output method per provider
    if provider == "openrouter":
        # OpenRouter free models don't support json_schema; force json_mode/json_object
        # include_raw False keeps interface like regular structured output
        try:
            return client.with_structured_output(schema, method="json_mode", include_raw=False)
        except TypeError:
            # Older langchain_openai may not accept include_raw. Fall back gracefully.
            return client.with_structured_output(schema, method="json_mode")
    else:
        # Default behavior for providers that support json_schema/function calling
        return client.with_structured_output(schema)
