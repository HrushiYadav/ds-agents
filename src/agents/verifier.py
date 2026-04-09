from src.graph.state import AgentState
from src.providers.azure import call_llm
from src.utils.prompts import get_prompts


def _summaries_str(summaries: dict[str, str]) -> str:
    return "\n".join(f"File: {k}\n{v}" for k, v in summaries.items())


def run_verifier(state: AgentState) -> dict:
    """Check if the current plan + code is sufficient to answer the query."""
    prompts = get_prompts()
    plan = state["plan"]
    code = state["code"]
    result = state.get("execution_result", "")
    query = state["query"]
    data_desc = _summaries_str(state["data_summaries"])
    log_entries: list[dict] = list(state.get("agent_log") or [])

    plan_str = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan))
    prompt = prompts["verifier"].format(
        question=query,
        summaries=data_desc,
        plan=plan_str,
        current_step=plan[-1],
        code=code,
        result=result,
    )

    verdict = call_llm(prompt).strip().lower()
    is_sufficient = verdict.startswith("yes")

    log_entries.append({
        "agent": "verifier",
        "verdict": "sufficient" if is_sufficient else "insufficient",
    })

    return {"is_sufficient": is_sufficient, "agent_log": log_entries}
