import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

st.set_page_config(
    page_title="DS-Agents",
    page_icon="🔬",
    layout="wide",
)

# Log styling
st.markdown("""
<style>
    .log-entry {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 6px;
        font-size: 0.85rem;
        border-left: 3px solid transparent;
    }
    .log-analyzer  { background: #dbeafe22; border-left-color: #3b82f6; }
    .log-planner   { background: #e0e7ff22; border-left-color: #6366f1; }
    .log-coder     { background: #fae8ff22; border-left-color: #c026d3; }
    .log-executor  { background: #fef3c722; border-left-color: #f59e0b; }
    .log-verifier  { background: #d1fae522; border-left-color: #10b981; }
    .log-router    { background: #ffedd522; border-left-color: #f97316; }
    .log-debugger  { background: #fee2e222; border-left-color: #ef4444; }
    .log-finalyzer { background: #cffafe22; border-left-color: #06b6d4; }
    .log-agent-name { font-weight: 700; min-width: 80px; }
    .log-details { color: #9ca3af; }
</style>
""", unsafe_allow_html=True)


AGENT_META = {
    "analyzer":  {"desc": "Profile data files"},
    "planner":   {"desc": "Plan analysis steps"},
    "coder":     {"desc": "Generate Python code"},
    "executor":  {"desc": "Run code in sandbox"},
    "verifier":  {"desc": "Check if answer is sufficient"},
    "router":    {"desc": "Refine or add steps"},
    "debugger":  {"desc": "Fix execution errors"},
    "finalyzer": {"desc": "Produce final answer"},
}

AGENT_COLORS = {
    "analyzer":  ("#dbeafe", "#1e40af", "#3b82f6"),
    "planner":   ("#e0e7ff", "#3730a3", "#6366f1"),
    "coder":     ("#fae8ff", "#86198f", "#c026d3"),
    "executor":  ("#fef3c7", "#92400e", "#f59e0b"),
    "verifier":  ("#d1fae5", "#065f46", "#10b981"),
    "router":    ("#ffedd5", "#9a3412", "#f97316"),
    "debugger":  ("#fee2e2", "#991b1b", "#ef4444"),
    "finalyzer": ("#cffafe", "#155e75", "#06b6d4"),
}


def build_pipeline_html(active_agents: set[str] | None = None) -> str:
    if active_agents is None:
        active_agents = set()

    def node(name: str) -> str:
        bg, fg, border = AGENT_COLORS[name]
        desc = AGENT_META[name]["desc"]
        label = name.capitalize()
        opacity = "1" if name in active_agents else "0.4"
        glow = ""
        if active_agents and name in active_agents:
            glow = f"box-shadow: 0 0 0 3px {border}44, 0 0 16px {border}33;"
        return (
            f'<div style="padding:14px 24px; border-radius:12px; font-weight:700; '
            f'font-size:0.85rem; text-align:center; min-width:120px; '
            f'background:{bg}; color:{fg}; border:2px solid {border}; '
            f'opacity:{opacity}; {glow}">'
            f'{label}<div style="font-weight:400; font-size:0.7rem; opacity:0.8; margin-top:4px;">{desc}</div>'
            f'</div>'
        )

    arrow = '<div style="font-size:1.4rem; color:#6b7280;">&#8594;</div>'
    arrow_down = '<div style="font-size:1.4rem; color:#6b7280; text-align:center;">&#8595;</div>'
    branch_label = lambda t: f'<div style="width:60px; text-align:center; font-size:0.7rem; color:#9ca3af; font-style:italic;">{t}</div>'
    spacer = lambda w: f'<div style="width:{w}px;"></div>'
    row_style = 'display:flex; align-items:center; justify-content:center; gap:12px; margin:4px 0;'

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0; padding:20px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:transparent;">
        <div style="display:flex; flex-direction:column; align-items:center; gap:0;">

            <div style="{row_style}">
                {node("analyzer")} {arrow} {node("planner")} {arrow} {node("coder")} {arrow} {node("executor")}
            </div>

            {arrow_down}

            <div style="{row_style}">
                {node("debugger")}
                {branch_label("error")}
                {spacer(40)}
                {branch_label("success")}
                {node("verifier")}
            </div>

            <div style="{row_style}">
                {spacer(280)}
                {arrow_down}
            </div>

            <div style="{row_style}">
                {node("router")}
                {branch_label("insufficient")}
                {spacer(40)}
                {branch_label("sufficient")}
                {node("finalyzer")}
            </div>

            <div style="{row_style} margin-top:8px;">
                <div style="font-size:0.7rem; color:#9ca3af; font-style:italic;">&#8593; loops back to Planner</div>
                {spacer(200)}
                <div style="font-size:0.7rem; color:#9ca3af; font-style:italic;">&#8594; Final Answer</div>
            </div>

        </div>
    </body>
    </html>
    """


def render_agent_log(log: list[dict]):
    if not log:
        st.caption("No activity yet. Run an analysis to see agents in action.")
        return

    for entry in log:
        agent = entry.get("agent", "unknown")
        details = {k: v for k, v in entry.items() if k not in ("agent", "status")}
        detail_str = " &middot; ".join(f"{k}={v}" for k, v in details.items())
        css = f"log-{agent}" if agent in AGENT_META else ""

        st.markdown(
            f'<div class="log-entry {css}">'
            f'<span class="log-agent-name">{agent}</span>'
            f'<span class="log-details">{detail_str}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


def check_env():
    required = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        st.error(f"Missing environment variables: {', '.join(missing)}")
        st.info("Create a `.env` file from `.env.example` and fill in your Azure AI Foundry credentials.")
        st.stop()


def main():
    st.title("DS-Agents")
    st.caption("Multi-agent data science system - powered by LangGraph + Azure OpenAI")

    check_env()

    # Sidebar
    with st.sidebar:
        st.header("Settings")
        max_rounds = st.slider("Max refinement rounds", 1, 10, 5)
        st.divider()
        st.markdown("**Agents**")
        for name, meta in AGENT_META.items():
            st.markdown(f"**{name}:** {meta['desc']}")

    # Tabs
    tab_analysis, tab_pipeline, tab_log = st.tabs(["Analysis", "Agent Pipeline", "Agent Log"])

    # Analysis tab
    with tab_analysis:
        col_input, col_result = st.columns([1, 1])

        with col_input:
            st.subheader("Upload Data")
            uploaded_files = st.file_uploader(
                "Upload CSV, Excel, or JSON files",
                type=["csv", "xlsx", "xls", "json"],
                accept_multiple_files=True,
            )

            st.subheader("Ask a Question")
            query = st.text_area(
                "What do you want to know about your data?",
                placeholder="e.g., What is the total revenue by region for Q4 2024?",
                height=100,
            )

            run_btn = st.button("Run Analysis", type="primary", use_container_width=True)

        with col_result:
            st.subheader("Result")
            result_container = st.container()

    # Run pipeline
    if run_btn:
        if not uploaded_files:
            st.warning("Please upload at least one data file.")
            return
        if not query.strip():
            st.warning("Please enter a question.")
            return

        tmp_dir = Path(tempfile.mkdtemp(prefix="ds_agents_"))
        data_paths = []
        for f in uploaded_files:
            path = tmp_dir / f.name
            path.write_bytes(f.getvalue())
            data_paths.append(str(path))

        from src.graph.workflow import compile_graph

        graph = compile_graph()
        initial_state = {
            "query": query.strip(),
            "data_files": data_paths,
            "data_summaries": {},
            "plan": [],
            "current_step_index": 0,
            "code": "",
            "base_code": "",
            "execution_result": "",
            "execution_error": "",
            "is_sufficient": False,
            "route_decision": "",
            "refinement_round": 0,
            "max_refinement_rounds": max_rounds,
            "final_code": "",
            "final_result": "",
            "agent_log": [],
        }

        with st.spinner("Agents are working..."):
            result = graph.invoke(initial_state)

        st.session_state["last_result"] = result
        st.session_state["active_agents"] = {
            e["agent"] for e in result.get("agent_log", [])
        }

        with result_container:
            st.success(result.get("final_result", "No result produced."))

            with st.expander("Plan Steps", expanded=False):
                for i, step in enumerate(result.get("plan", [])):
                    st.markdown(f"**Step {i+1}:** {step}")

            with st.expander("Generated Code", expanded=False):
                st.code(result.get("final_code", ""), language="python")

    # Pipeline tab
    with tab_pipeline:
        st.subheader("Agent Pipeline")
        st.caption(
            "Colored nodes show which agents participated. "
            "Dim nodes were not needed for this query."
        )
        active = st.session_state.get("active_agents", set())
        html = build_pipeline_html(active)
        components.html(html, height=380, scrolling=False)

    # Log tab
    with tab_log:
        st.subheader("Agent Activity Log")
        last = st.session_state.get("last_result")
        if last:
            render_agent_log(last.get("agent_log", []))
        else:
            st.caption("No activity yet. Run an analysis to see agents in action.")


if __name__ == "__main__":
    main()
