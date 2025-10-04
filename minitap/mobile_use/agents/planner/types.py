from enum import Enum

from pydantic import BaseModel
from typing import Annotated


class PlannerSubgoalOutput(BaseModel):
    id: Annotated[str | None, "If not provided, it will be generated"] = None
    description: str


class PlannerOutput(BaseModel):
    subgoals: list[PlannerSubgoalOutput]


class SubgoalStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class Subgoal(BaseModel):
    id: Annotated[str, "Unique identifier of the subgoal"]
    description: Annotated[str, "Description of the subgoal"]
    completion_reason: Annotated[
        str | None, "Reason why the subgoal was completed (failure or success)"
    ] = None
    status: SubgoalStatus

    def __str__(self):
        status_emoji = "❓"
        match self.status:
            case SubgoalStatus.SUCCESS:
                status_emoji = "✅"
            case SubgoalStatus.FAILURE:
                status_emoji = "❌"
            case SubgoalStatus.PENDING:
                status_emoji = "⏳"
            case SubgoalStatus.NOT_STARTED:
                status_emoji = "(not started yet)"

        output = f"- [ID:{self.id}]: {self.description} : {status_emoji}."
        if self.completion_reason:
            output += f" Completion reason: {self.completion_reason}"
        return output

    def __repr__(self):
        return str(self)
