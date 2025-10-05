import asyncio
import json
from pathlib import Path

from jinja2 import Template
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    RemoveMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from minitap.mobile_use.agents.cortex.types import CortexOutput
from minitap.mobile_use.agents.planner.utils import get_current_subgoal
from minitap.mobile_use.constants import EXECUTOR_MESSAGES_KEY
from minitap.mobile_use.context import MobileUseContext
from minitap.mobile_use.graph.state import State
from minitap.mobile_use.services.llm import (
    get_llm_with_structured_output,
    with_fallback,
)
from minitap.mobile_use.tools.index import EXECUTOR_WRAPPERS_TOOLS, format_tools_list
from minitap.mobile_use.utils.conversations import get_screenshot_message_for_llm
from minitap.mobile_use.utils.decorators import wrap_with_callbacks
from minitap.mobile_use.utils.logger import get_logger

logger = get_logger(__name__)


class CortexNode:
    def __init__(self, ctx: MobileUseContext):
        self.ctx = ctx

    @wrap_with_callbacks(
        before=lambda: logger.info("Starting Cortex Agent..."),
        on_success=lambda _: logger.success("Cortex Agent"),
        on_failure=lambda _: logger.error("Cortex Agent"),
    )
    async def __call__(self, state: State):
        executor_feedback = get_executor_agent_feedback(state)

        system_message = Template(
            Path(__file__).parent.joinpath("cortex.md").read_text(encoding="utf-8")
        ).render(
            platform=self.ctx.device.mobile_platform.value,
            initial_goal=state.initial_goal,
            subgoal_plan=state.subgoal_plan,
            current_subgoal=get_current_subgoal(state.subgoal_plan),
            executor_feedback=executor_feedback,
            executor_tools_list=format_tools_list(ctx=self.ctx, wrappers=EXECUTOR_WRAPPERS_TOOLS),
        )
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(
                content=(
                    "Here are my device info:\n"
                    + self.ctx.device.to_str()
                    + f"Device date: {state.device_date}\n"
                    if state.device_date
                    else (
                        "" + f"Focused app info: {state.focused_app_info}\n"
                        if state.focused_app_info
                        else ""
                    )
                )
            ),
        ]
        for thought in state.agents_thoughts:
            messages.append(AIMessage(content=thought))

        if state.latest_screenshot_base64:
            messages.append(get_screenshot_message_for_llm(state.latest_screenshot_base64))
            logger.info("Added screenshot to context")

        if state.latest_ui_hierarchy:
            ui_hierarchy_dict: list[dict] = state.latest_ui_hierarchy
            ui_hierarchy_str = json.dumps(ui_hierarchy_dict, indent=2, ensure_ascii=False)
            messages.append(HumanMessage(content="Here is the UI hierarchy:\n" + ui_hierarchy_str))

        llm = get_llm_with_structured_output(
            ctx=self.ctx, name="cortex", schema=CortexOutput, temperature=1
        )
        llm_fallback = get_llm_with_structured_output(
            ctx=self.ctx,
            name="cortex",
            schema=CortexOutput,
            use_fallback=True,
            temperature=1,
        )

        # Retry logic with fallback for LLM errors
        max_retries = 3
        retry_delay = 2
        last_error = None

        for attempt in range(max_retries):
            try:
                response: CortexOutput = await with_fallback(
                    main_call=lambda: llm.ainvoke(messages),
                    fallback_call=lambda: llm_fallback.ainvoke(messages),
                )  # type: ignore
                break
            except Exception as e:
                last_error = e
                error_msg = str(e)
                logger.warning(
                    f"Cortex LLM call failed (attempt {attempt + 1}/{max_retries}): {error_msg}"
                )

                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2**attempt)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Cortex failed after {max_retries} attempts")
                    raise last_error from None

        is_subgoal_completed = (
            response.complete_subgoals_by_ids is not None
            and len(response.complete_subgoals_by_ids) > 0
            and (len(response.decisions) == 0 or response.decisions in ["{}", "[]", "null", ""])
        )
        if not is_subgoal_completed:
            response.complete_subgoals_by_ids = []

        return state.sanitize_update(
            ctx=self.ctx,
            update={
                "agents_thoughts": [response.agent_thought],
                "structured_decisions": (response.decisions if not is_subgoal_completed else None),
                "complete_subgoals_by_ids": response.complete_subgoals_by_ids or [],
                "latest_screenshot_base64": None,
                "latest_ui_hierarchy": None,
                "focused_app_info": None,
                "device_date": None,
                # Executor related fields
                EXECUTOR_MESSAGES_KEY: [RemoveMessage(id=REMOVE_ALL_MESSAGES)],
                "cortex_last_thought": response.agent_thought,
            },
            agent="cortex",
        )


def get_executor_agent_feedback(state: State) -> str:
    if state.structured_decisions is None:
        return "None."
    executor_tool_messages = [m for m in state.executor_messages if isinstance(m, ToolMessage)]
    return (
        f"Latest UI decisions:\n{state.structured_decisions}"
        + "\n\n"
        + f"Executor feedback:\n{executor_tool_messages}"
    )
