from typing import TypedDict, Optional
from dataclasses import dataclass, field


class AgentState(TypedDict, total=False):
    # input
    query: str
    data_files: list[str]

    # data analysis phase
    data_summaries: dict[str, str]

    # planning phase
    plan: list[str]
    current_step_index: int

    # coding phase
    code: str
    base_code: str

    # execution
    execution_result: str
    execution_error: str

    # verification
    is_sufficient: bool

    # routing
    route_decision: str

    # refinement tracking
    refinement_round: int
    max_refinement_rounds: int

    # finalization
    final_code: str
    final_result: str

    # agent activity log for UI
    agent_log: list[dict]


@dataclass
class DSConfig:
    max_refinement_rounds: int = 5
    execution_timeout: int = 120
    runs_dir: str = "runs"
    data_dir: str = "data"
