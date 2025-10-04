import asyncio
import os

import typer
from adbutils import AdbClient
from langchain.callbacks.base import Callbacks
from rich.console import Console
from typing import Annotated

from minitap.mobile_use.config import (
    initialize_llm_config,
    settings,
)
from minitap.mobile_use.sdk import Agent
from minitap.mobile_use.sdk.builders import Builders
from minitap.mobile_use.sdk.types.task import AgentProfile
from minitap.mobile_use.utils.cli_helpers import display_device_status
from minitap.mobile_use.utils.logger import get_logger

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)
logger = get_logger(__name__)


async def run_automation(
    goal: str,
    test_name: str | None = None,
    traces_output_path_str: str = "traces",
    output_description: str | None = None,
    graph_config_callbacks: Callbacks = [],
):
    llm_config = initialize_llm_config()
    agent_profile = AgentProfile(name="default", llm_config=llm_config)
    config = Builders.AgentConfig.with_default_profile(profile=agent_profile)

    if settings.ADB_HOST:
        config.with_adb_server(host=settings.ADB_HOST, port=settings.ADB_PORT)
    if settings.DEVICE_HARDWARE_BRIDGE_BASE_URL:
        config.with_hw_bridge(url=settings.DEVICE_HARDWARE_BRIDGE_BASE_URL)
    if settings.DEVICE_SCREEN_API_BASE_URL:
        config.with_screen_api(url=settings.DEVICE_SCREEN_API_BASE_URL)
    if graph_config_callbacks:
        config.with_graph_config_callbacks(graph_config_callbacks)

    agent = Agent(config=config.build())
    agent.init(
        retry_count=int(os.getenv("MOBILE_USE_HEALTH_RETRIES", 5)),
        retry_wait_seconds=int(os.getenv("MOBILE_USE_HEALTH_DELAY", 2)),
    )

    task = agent.new_task(goal)
    if test_name:
        task.with_name(test_name).with_trace_recording(path=traces_output_path_str)
    if output_description:
        task.with_output_description(output_description)

    agent_thoughts_path = os.getenv("EVENTS_OUTPUT_PATH", None)
    llm_result_path = os.getenv("RESULTS_OUTPUT_PATH", None)
    if agent_thoughts_path:
        task.with_thoughts_output_saving(path=agent_thoughts_path)
    if llm_result_path:
        task.with_llm_output_saving(path=llm_result_path)

    await agent.run_task(request=task.build())

    agent.clean()


@app.command()
def main(
    goal: Annotated[str, typer.Argument(help="The main goal for the agent to achieve.")],
    test_name: Annotated[
        str | None,
        typer.Option(
            "--test-name",
            "-n",
            help="A name for the test recording. If provided, a trace will be saved.",
        ),
    ] = None,
    traces_path: Annotated[
        str,
        typer.Option(
            "--traces-path",
            "-p",
            help="The path to save the traces.",
        ),
    ] = "traces",
    output_description: Annotated[
        str | None,
        typer.Option(
            "--output-description",
            "-o",
            help=(
                """
                A dict output description for the agent.
                Ex: a JSON schema with 2 keys: type, price
                """
            ),
        ),
    ] = None,
):
    """
    Run the Mobile-use agent to automate tasks on a mobile device.
    """
    console = Console()
    adb_client = AdbClient(
        host=settings.ADB_HOST or "localhost",
        port=settings.ADB_PORT or 5037,
    )
    display_device_status(console, adb_client=adb_client)
    asyncio.run(
        run_automation(
            goal=goal,
            test_name=test_name,
            traces_output_path_str=traces_path,
            output_description=output_description,
        )
    )


@app.command()
def serve(
    port: Annotated[
        int,
        typer.Option("--port", "-P", help="Port to run the Web GUI on (inside container)")
    ] = int(os.getenv("WEB_GUI_PORT", "8086")),
):
    """Start the Web GUI server (FastAPI) and wait indefinitely."""
    # Do not initialize the Agent here; the server will do it on-demand after it is ready.
    from minitap.mobile_use.web_gui.server import run as run_server

    console = Console()
    console.print(f"Starting Web GUI on http://0.0.0.0:{port} (mapped to host port via Docker)")
    os.environ["WEB_GUI_PORT"] = str(port)
    run_server()


def cli():
    app()


if __name__ == "__main__":
    cli()
