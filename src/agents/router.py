import re

from src.graph.state import AgentState
from src.providers.azure import call_llm
from src.utils.prompts import get_prompts


def _summaries_str(summaries: dict[str, str]) -> str:
    return "\n".join(f"File: {k}\n{v}" for k, v in summaries.items())


def run_router(state: AgentState) -> dict:
    """Decide whether to revise an existing step or add a new one."""
    prompts = get_prompts()
    plan = state["plan"]
    query = state["query"]
    result = state.get("execution_result", "")
    data_desc = _summaries_str(state["data_summaries"])
    log_entries: list[dict] = list(state.get("agent_log") or [])

    plan_str = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan))
    prompt = prompts["router"].format(
        question=query,
        summaries=data_desc,
        plan=plan_str,
        current_step=plan[-1],
        result=result,
    )

    decision = call_llm(prompt).strip()
    log_entries.append({"agent": "router", "decision": decision})

    # If a step is identified as wrong, truncate the plan
    step_match = re.search(r"Step\s+(\d+)", decision, re.IGNORECASE)
    if step_match:
        step_idx = int(step_match.group(1)) - 1
        truncated_plan = plan[:step_idx]
        return {
            "plan": truncated_plan,
            "route_decision": decision,
            "base_code": "",
            "agent_log": log_entries,
        }

    return {"route_decision": decision, "agent_log": log_entries}
