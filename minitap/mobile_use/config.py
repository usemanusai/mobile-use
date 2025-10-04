import json
import os
from pathlib import Path
from typing import Annotated, Any, Literal

import google.auth
from dotenv import load_dotenv
from google.auth.exceptions import DefaultCredentialsError
from pydantic import BaseModel, Field, SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings

from minitap.mobile_use.utils.file import load_jsonc
from minitap.mobile_use.utils.logger import get_logger

### Environment Variables

load_dotenv(verbose=True)
logger = get_logger(__name__)


class Settings(BaseSettings):
    OPENAI_API_KEY: SecretStr | None = None
    GOOGLE_API_KEY: SecretStr | None = None
    XAI_API_KEY: SecretStr | None = None
    OPEN_ROUTER_API_KEY: SecretStr | None = None

    OPENAI_BASE_URL: str | None = None

    DEVICE_SCREEN_API_BASE_URL: str | None = None
    DEVICE_HARDWARE_BRIDGE_BASE_URL: str | None = None
    ADB_HOST: str | None = None
    ADB_PORT: int | None = None

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


def prepare_output_files() -> tuple[str | None, str | None]:
    events_output_path = os.getenv("EVENTS_OUTPUT_PATH") or None
    results_output_path = os.getenv("RESULTS_OUTPUT_PATH") or None

    def validate_and_prepare_file(file_path: str) -> str | None:
        if not file_path:
            return None

        path_obj = Path(file_path)

        if path_obj.exists() and path_obj.is_dir():
            logger.error(f"Error: Path '{file_path}' points to an existing directory, not a file.")
            return None

        if not path_obj.suffix or file_path.endswith(("/", "\\")):
            logger.error(f"Error: Path '{file_path}' appears to be a directory path, not a file.")
            return None

        try:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            path_obj.touch(exist_ok=True)
            return file_path
        except OSError as e:
            logger.error(f"Error creating file '{file_path}': {e}")
            return None

    validated_events_path = (
        validate_and_prepare_file(events_output_path) if events_output_path else None
    )
    validated_results_path = (
        validate_and_prepare_file(results_output_path) if results_output_path else None
    )

    return validated_events_path, validated_results_path


def record_events(output_path: Path | None, events: list[str] | BaseModel | Any):
    if not output_path:
        return

    if isinstance(events, str):
        events_content = events
    elif isinstance(events, BaseModel):
        events_content = events.model_dump_json(indent=2)
    else:
        events_content = json.dumps(events, indent=2)

    with open(output_path, "w") as f:
        f.write(events_content)


### LLM Configuration

LLMProvider = Literal["openai", "google", "openrouter", "xai", "vertexai"]
LLMUtilsNode = Literal["outputter", "hopper"]
AgentNode = Literal["planner", "orchestrator", "cortex", "executor"]
AgentNodeWithFallback = Literal["cortex"]

ROOT_DIR = Path(__file__).parent.parent.parent
DEFAULT_LLM_CONFIG_FILENAME = "llm-config.defaults.jsonc"
OVERRIDE_LLM_CONFIG_FILENAME = "llm-config.override.jsonc"


def validate_vertex_ai_credentials():
    try:
        _, project = google.auth.default()
        if not project:
            raise Exception("VertexAI requires a Google Cloud project to be set.")
    except DefaultCredentialsError as e:
        raise Exception(
            f"VertexAI requires valid Google Application Default Credentials (ADC): {e}"
        )


class LLM(BaseModel):
    provider: LLMProvider
    model: str

    def validate_provider(self, name: str):
        match self.provider:
            case "openai":
                if not settings.OPENAI_API_KEY:
                    raise Exception(f"{name} requires OPENAI_API_KEY in .env")
            case "google":
                if not settings.GOOGLE_API_KEY:
                    raise Exception(f"{name} requires GOOGLE_API_KEY in .env")
            case "vertexai":
                validate_vertex_ai_credentials()
            case "openrouter":
                if not settings.OPEN_ROUTER_API_KEY:
                    raise Exception(f"{name} requires OPEN_ROUTER_API_KEY in .env")
            case "xai":
                if not settings.XAI_API_KEY:
                    raise Exception(f"{name} requires XAI_API_KEY in .env")

    def __str__(self):
        return f"{self.provider}/{self.model}"


class LLMWithFallback(LLM):
    fallback: LLM

    def __str__(self):
        return f"{self.provider}/{self.model} (fallback: {self.fallback})"


class LLMConfigUtils(BaseModel):
    outputter: LLM
    hopper: LLM


class LLMConfig(BaseModel):
    planner: LLM
    orchestrator: LLM
    cortex: LLMWithFallback
    executor: LLM
    utils: LLMConfigUtils

    def validate_providers(self):
        self.planner.validate_provider("Planner")
        self.orchestrator.validate_provider("Orchestrator")
        self.cortex.validate_provider("Cortex")
        self.executor.validate_provider("Executor")
        self.utils.outputter.validate_provider("Outputter")
        self.utils.hopper.validate_provider("Hopper")

    def __str__(self):
        return f"""
📃 Planner: {self.planner}
🎯 Orchestrator: {self.orchestrator}
🧠 Cortex: {self.cortex}
🛠️ Executor: {self.executor}
🧩 Utils:
    🔽 Hopper: {self.utils.hopper}
    📝 Outputter: {self.utils.outputter}
"""

    def get_agent(self, item: AgentNode) -> LLM:
        return getattr(self, item)

    def get_utils(self, item: LLMUtilsNode) -> LLM:
        return getattr(self.utils, item)


def get_default_llm_config() -> LLMConfig:
    try:
        if not os.path.exists(ROOT_DIR / DEFAULT_LLM_CONFIG_FILENAME):
            raise Exception("Default llm config not found")
        with open(ROOT_DIR / DEFAULT_LLM_CONFIG_FILENAME) as f:
            default_config_dict = load_jsonc(f)
        return LLMConfig.model_validate(default_config_dict["default"])
    except Exception as e:
        logger.error(f"Failed to load default llm config: {e}. Falling back to hardcoded config")
        return LLMConfig(
            planner=LLM(provider="openai", model="gpt-4.1"),
            orchestrator=LLM(provider="openai", model="gpt-4.1"),
            cortex=LLMWithFallback(
                provider="openai",
                model="o3",
                fallback=LLM(provider="openai", model="gpt-5"),
            ),
            executor=LLM(provider="openai", model="gpt-4.1"),
            utils=LLMConfigUtils(
                outputter=LLM(provider="openai", model="gpt-5-nano"),
                hopper=LLM(provider="openai", model="gpt-4.1"),
            ),
        )


def deep_merge_llm_config(default: LLMConfig, override: dict) -> LLMConfig:
    def _deep_merge_dict(base: dict, extra: dict):
        for key, value in extra.items():
            if isinstance(value, dict):
                _deep_merge_dict(base[key], value)
            else:
                base[key] = value

    merged_dict = default.model_dump()
    _deep_merge_dict(merged_dict, override)
    return LLMConfig.model_validate(merged_dict)


def parse_llm_config() -> LLMConfig:
    if not os.path.exists(ROOT_DIR / DEFAULT_LLM_CONFIG_FILENAME):
        return get_default_llm_config()

    override_config_dict = {}
    if os.path.exists(ROOT_DIR / OVERRIDE_LLM_CONFIG_FILENAME):
        logger.info("Loading custom llm config...")
        with open(ROOT_DIR / OVERRIDE_LLM_CONFIG_FILENAME) as f:
            override_config_dict = load_jsonc(f)
    else:
        logger.warning("Custom llm config not found, loading default config")

    try:
        default_config = get_default_llm_config()
        return deep_merge_llm_config(default_config, override_config_dict)

    except ValidationError as e:
        logger.error(f"Invalid llm config: {e}. Falling back to default config")
        return get_default_llm_config()


def initialize_llm_config() -> LLMConfig:
    llm_config = parse_llm_config()
    llm_config.validate_providers()
    logger.success("LLM config initialized")
    return llm_config


### Output config


class OutputConfig(BaseModel):
    structured_output: Annotated[
        type[BaseModel] | dict | None,
        Field(
            default=None,
            description=(
                "Optional structured schema (as a BaseModel or dict) to shape the output. "
                "If provided, it takes precedence over 'output_description'."
            ),
        ),
    ]
    output_description: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Optional natural language description of the expected output format. "
                "Used only if 'structured_output' is not provided. "
                "Example: 'Output a JSON with 3 keys: color, price, websiteUrl'."
            ),
        ),
    ]

    def __str__(self):
        s_builder = ""
        if self.structured_output:
            s_builder += f"Structured Output: {self.structured_output}\n"
        if self.output_description:
            s_builder += f"Output Description: {self.output_description}\n"
        if self.output_description and self.structured_output:
            s_builder += (
                "Both 'structured_output' and 'output_description' are provided. "
                "'structured_output' will take precedence.\n"
            )
        return s_builder

    @model_validator(mode="after")
    def warn_if_both_outputs_provided(self):
        if self.structured_output and self.output_description:
            import warnings

            warnings.warn(
                "Both 'structured_output' and 'output_description' are provided. "
                "'structured_output' will take precedence.",
                stacklevel=2,
            )
        return self

    def needs_structured_format(self):
        return self.structured_output or self.output_description
