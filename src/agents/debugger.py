import re

from src.graph.state import AgentState
from src.providers.azure import call_llm
from src.utils.prompts import get_prompts


def _extract_code(response: str) -> str:
    blocks = re.findall(r"```(?:python)?\n(.*?)\n```", response, re.DOTALL)
    return blocks[0] if blocks else response.strip()


def run_debugger(state: AgentState) -> dict:
    """Fix code that failed execution."""
    prompts = get_prompts()
    code = state["code"]
    error = state.get("execution_error", "")
    data_desc = "\n".join(
        f"File: {k}\n{v}" for k, v in state["data_summaries"].items()
    )
    filenames = ", ".join(state["data_files"])
    log_entries: list[dict] = list(state.get("agent_log") or [])

    prompt = prompts["debugger"].format(
        summaries=data_desc,
        code=code,
        bug=error,
        filenames=filenames,
    )

    response = call_llm(prompt)
    fixed_code = _extract_code(response)

    log_entries.append({
        "agent": "debugger",
        "error_type": error.split(":")[0] if error else "unknown",
    })

    return {"code": fixed_code, "execution_error": "", "agent_log": log_entries}
