import re

from src.graph.state import AgentState
from src.providers.azure import call_llm
from src.utils.prompts import get_prompts


def _extract_code(response: str) -> str:
    blocks = re.findall(r"```(?:python)?\n(.*?)\n```", response, re.DOTALL)
    return blocks[0] if blocks else response.strip()


def _summaries_str(summaries: dict[str, str]) -> str:
    return "\n".join(f"File: {k}\n{v}" for k, v in summaries.items())


def run_coder(state: AgentState) -> dict:
    """Generate code for the current plan."""
    prompts = get_prompts()
    plan = state["plan"]
    data_desc = _summaries_str(state["data_summaries"])
    base_code = state.get("base_code") or state.get("code")
    log_entries: list[dict] = list(state.get("agent_log") or [])

    plan_str = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan))

    if not base_code:
        prompt = prompts["coder_init"].format(
            summaries=data_desc, plan=plan_str
        )
    else:
        prompt = prompts["coder_next"].format(
            summaries=data_desc,
            base_code=base_code,
            plan=plan_str,
            current_plan=plan[-1],
        )

    response = call_llm(prompt)
    code = _extract_code(response)

    log_entries.append({
        "agent": "coder",
        "code_length": len(code),
        "has_base": base_code is not None,
    })

    return {"code": code, "agent_log": log_entries}
