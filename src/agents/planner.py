from src.graph.state import AgentState
from src.providers.azure import call_llm
from src.utils.prompts import get_prompts


def _summaries_str(summaries: dict[str, str]) -> str:
    return "\n".join(f"File: {k}\n{v}" for k, v in summaries.items())


def run_planner(state: AgentState) -> dict:
    """Generate the next plan step."""
    prompts = get_prompts()
    plan: list[str] = list(state.get("plan") or [])
    query = state["query"]
    data_desc = _summaries_str(state["data_summaries"])
    last_result = state.get("execution_result", "")
    log_entries: list[dict] = list(state.get("agent_log") or [])

    if not plan:
        prompt = prompts["planner_init"].format(
            question=query, summaries=data_desc
        )
    else:
        plan_str = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan))
        prompt = prompts["planner_next"].format(
            question=query,
            summaries=data_desc,
            plan=plan_str,
            current_step=plan[-1],
            result=last_result,
        )

    next_step = call_llm(prompt)
    plan.append(next_step.strip())

    log_entries.append({
        "agent": "planner",
        "step_added": next_step.strip()[:120],
        "total_steps": len(plan),
    })

    return {
        "plan": plan,
        "current_step_index": len(plan) - 1,
        "agent_log": log_entries,
    }
