import re
from pathlib import Path

from src.graph.state import AgentState
from src.providers.azure import call_llm
from src.utils.code_executor import execute_code
from src.utils.prompts import get_prompts


def _extract_code(response: str) -> str:
    blocks = re.findall(r"```(?:python)?\n(.*?)\n```", response, re.DOTALL)
    return blocks[0] if blocks else response.strip()


def run_analyzer(state: AgentState) -> dict:
    """Analyze each data file and produce summaries."""
    prompts = get_prompts()
    data_files: list[str] = state["data_files"]
    summaries: dict[str, str] = {}
    log_entries: list[dict] = list(state.get("agent_log") or [])

    for filepath in data_files:
        abs_path = str(Path(filepath).resolve())
        prompt = prompts["analyzer"].format(filename=abs_path)
        response = call_llm(prompt)
        code = _extract_code(response)

        stdout, error = execute_code(code)
        # simple debug retry
        if error:
            debug_prompt = prompts["debugger"].format(
                summaries="", code=code, bug=error, filenames=abs_path
            )
            fixed = call_llm(debug_prompt)
            code = _extract_code(fixed)
            stdout, error = execute_code(code)

        summaries[abs_path] = stdout or f"[analysis failed: {error}]"
        log_entries.append({
            "agent": "analyzer",
            "file": abs_path,
            "status": "ok" if not error else "error",
        })

    return {"data_summaries": summaries, "agent_log": log_entries}
