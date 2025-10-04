import asyncio
import uuid
from pathlib import Path

from jinja2 import Template
from langchain_core.messages import HumanMessage, SystemMessage

from minitap.mobile_use.agents.planner.types import PlannerOutput, Subgoal, SubgoalStatus
from minitap.mobile_use.agents.planner.utils import one_of_them_is_failure
from minitap.mobile_use.context import MobileUseContext
from minitap.mobile_use.graph.state import State
from minitap.mobile_use.services.llm import get_llm_with_structured_output
from minitap.mobile_use.tools.index import EXECUTOR_WRAPPERS_TOOLS, format_tools_list
from minitap.mobile_use.utils.decorators import wrap_with_callbacks
from minitap.mobile_use.utils.logger import get_logger

logger = get_logger(__name__)


class PlannerNode:
    def __init__(self, ctx: MobileUseContext):
        self.ctx = ctx

    @wrap_with_callbacks(
        before=lambda: logger.info("Starting Planner Agent..."),
        on_success=lambda _: logger.success("Planner Agent"),
        on_failure=lambda _: logger.error("Planner Agent"),
    )
    async def __call__(self, state: State):
        needs_replan = one_of_them_is_failure(state.subgoal_plan)

        system_message = Template(
            Path(__file__).parent.joinpath("planner.md").read_text(encoding="utf-8")
        ).render(
            platform=self.ctx.device.mobile_platform.value,
            executor_tools_list=format_tools_list(ctx=self.ctx, wrappers=EXECUTOR_WRAPPERS_TOOLS),
        )
        human_message = Template(
            Path(__file__).parent.joinpath("human.md").read_text(encoding="utf-8")
        ).render(
            action="replan" if needs_replan else "plan",
            initial_goal=state.initial_goal,
            previous_plan="\n".join(str(s) for s in state.subgoal_plan),
            agent_thoughts="\n".join(state.agents_thoughts),
        )
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=human_message),
        ]

        llm = get_llm_with_structured_output(ctx=self.ctx, name="planner", schema=PlannerOutput)

        # Retry logic for LLM errors (especially for free OpenRouter models)
        max_retries = 3
        retry_delay = 2
        last_error = None

        for attempt in range(max_retries):
            try:
                response: PlannerOutput = await llm.ainvoke(messages)  # type: ignore
                break
            except Exception as e:
                last_error = e
                error_msg = str(e)
                logger.warning(f"Planner LLM call failed (attempt {attempt + 1}/{max_retries}): {error_msg}")

                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Planner failed after {max_retries} attempts")
                    raise last_error

        subgoals_plan = [
            Subgoal(
                id=subgoal.id or str(uuid.uuid4()),
                description=subgoal.description,
                status=SubgoalStatus.NOT_STARTED,
                completion_reason=None,
            )
            for subgoal in response.subgoals
        ]
        logger.info("📜 Generated plan:")
        logger.info("\n".join(str(s) for s in subgoals_plan))

        return state.sanitize_update(
            ctx=self.ctx,
            update={
                "subgoal_plan": subgoals_plan,
            },
            agent="planner",
        )
