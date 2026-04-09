import re

from src.graph.state import AgentState
from src.providers.azure import call_llm
from src.utils.code_executor import execute_code
from src.utils.prompts import get_prompts


def _extract_code(response: str) -> str:
    blocks = re.findall(r"```(?:python)?\n(.*?)\n```", response, re.DOTALL)
    return blocks[0] if blocks else response.strip()


def run_finalyzer(state: AgentState) -> dict:
    """Produce the final answer code and execute it."""
    prompts = get_prompts()
    code = state["code"]
    result = state.get("execution_result", "")
    query = state["query"]
    data_desc = "\n".join(
        f"File: {k}\n{v}" for k, v in state["data_summaries"].items()
    )
    log_entries: list[dict] = list(state.get("agent_log") or [])

    prompt = prompts["finalyzer"].format(
        summaries=data_desc,
        code=code,
        result=result,
        question=query,
        guidelines="Print the final answer clearly. If numeric, print just the number.",
    )

    response = call_llm(prompt)
    final_code = _extract_code(response)

    stdout, error = execute_code(final_code)
    if error:
        # one debug attempt
        debug_prompt = prompts["debugger"].format(
            summaries=data_desc,
            code=final_code,
            bug=error,
            filenames=", ".join(state["data_files"]),
        )
        fixed = call_llm(debug_prompt)
        final_code = _extract_code(fixed)
        stdout, error = execute_code(final_code)

    log_entries.append({
        "agent": "finalyzer",
        "status": "ok" if not error else "error",
    })

    return {
        "final_code": final_code,
        "final_result": stdout.strip() if stdout else f"[error: {error}]",
        "agent_log": log_entries,
    }
