from langgraph.graph import StateGraph, END

from src.graph.state import AgentState
from src.agents.analyzer import run_analyzer
from src.agents.planner import run_planner
from src.agents.coder import run_coder
from src.agents.verifier import run_verifier
from src.agents.router import run_router
from src.agents.debugger import run_debugger
from src.agents.finalyzer import run_finalyzer
from src.utils.code_executor import execute_code


# ---------------------------------------------------------------------------
# Intermediate node: execute the code produced by coder/debugger
# ---------------------------------------------------------------------------
def run_executor(state: AgentState) -> dict:
    """Execute the current code and capture output / errors."""
    code = state.get("code", "")
    stdout, error = execute_code(code)
    log_entries = list(state.get("agent_log") or [])
    log_entries.append({
        "agent": "executor",
        "status": "ok" if not error else "error",
        "output_len": len(stdout),
    })
    return {
        "execution_result": stdout,
        "execution_error": error or "",
        "agent_log": log_entries,
    }


# ---------------------------------------------------------------------------
# Conditional edges
# ---------------------------------------------------------------------------
def after_executor(state: AgentState) -> str:
    """If execution errored, go to debugger; otherwise verify."""
    if state.get("execution_error"):
        return "debugger"
    return "verifier"


def after_verifier(state: AgentState) -> str:
    """If sufficient, finalize; otherwise route for refinement."""
    if state.get("is_sufficient"):
        return "finalyzer"
    # check refinement budget
    current_round = state.get("refinement_round", 0)
    max_rounds = state.get("max_refinement_rounds", 5)
    if current_round >= max_rounds:
        return "finalyzer"
    return "router"


def after_router(state: AgentState) -> str:
    """After routing, always go back to planner for the next step."""
    return "planner"


def after_planner(state: AgentState) -> str:
    """After planning, always go to coder."""
    return "coder"


# ---------------------------------------------------------------------------
# Refinement round counter
# ---------------------------------------------------------------------------
def bump_refinement(state: AgentState) -> dict:
    return {"refinement_round": (state.get("refinement_round", 0)) + 1}


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------
def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # nodes
    graph.add_node("analyzer", run_analyzer)
    graph.add_node("planner", run_planner)
    graph.add_node("coder", run_coder)
    graph.add_node("executor", run_executor)
    graph.add_node("verifier", run_verifier)
    graph.add_node("router", run_router)
    graph.add_node("debugger", run_debugger)
    graph.add_node("finalyzer", run_finalyzer)
    graph.add_node("bump_refinement", bump_refinement)

    # edges: linear start
    graph.set_entry_point("analyzer")
    graph.add_edge("analyzer", "planner")
    graph.add_edge("planner", "coder")
    graph.add_edge("coder", "executor")

    # conditional: executor -> debugger | verifier
    graph.add_conditional_edges("executor", after_executor, {
        "debugger": "debugger",
        "verifier": "verifier",
    })

    # debugger loops back to executor
    graph.add_edge("debugger", "executor")

    # conditional: verifier -> finalyzer | router
    graph.add_conditional_edges("verifier", after_verifier, {
        "finalyzer": "finalyzer",
        "router": "bump_refinement",
    })

    # bump refinement then route
    graph.add_edge("bump_refinement", "router")

    # router -> planner (new plan step or revised plan)
    graph.add_edge("router", "planner")

    # finalyzer -> END
    graph.add_edge("finalyzer", END)

    return graph


def compile_graph():
    return build_graph().compile()
