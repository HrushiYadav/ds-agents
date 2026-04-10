import os
import tempfile
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="DS-Agents — Multi-Agent Data Science",
    page_icon="🔬",
    layout="wide",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .agent-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 2px 4px;
    }
    .agent-active { background: #22c55e22; color: #22c55e; border: 1px solid #22c55e; }
    .agent-done   { background: #3b82f622; color: #3b82f6; border: 1px solid #3b82f6; }
    .agent-wait   { background: #6b728022; color: #6b7280; border: 1px solid #6b7280; }
    .agent-error  { background: #ef444422; color: #ef4444; border: 1px solid #ef4444; }
</style>
""", unsafe_allow_html=True)


AGENT_DESCRIPTIONS = {
    "analyzer": "Profiles uploaded data files — columns, types, stats",
    "planner": "Creates step-by-step analysis plan",
    "coder": "Generates Python code to execute the plan",
    "executor": "Runs generated code in a sandbox",
    "verifier": "Checks if the answer is sufficient",
    "router": "Decides: refine an existing step or add a new one",
    "debugger": "Fixes code errors and retries execution",
    "finalyzer": "Produces the final answer",
}


def render_pipeline_diagram():
    """Show the DS-STAR agent pipeline."""
    st.markdown("### Agent Pipeline")
    st.markdown("""
    ```
    ┌──────────┐   ┌──────────┐   ┌────────┐   ┌──────────┐
    │ Analyzer │──▶│ Planner  │──▶│ Coder  │──▶│ Executor │
    └──────────┘   └──────────┘   └────────┘   └──────────┘
                                                     │
                                          ┌──────────┴──────────┐
                                          ▼                     ▼
                                    ┌──────────┐          ┌──────────┐
                                    │ Debugger │          │ Verifier │
                                    └──────────┘          └──────────┘
                                                               │
                                                    ┌──────────┴──────────┐
                                                    ▼                     ▼
                                              ┌──────────┐          ┌───────────┐
                                              │  Router  │          │ Finalyzer │──▶ Answer
                                              └──────────┘          └───────────┘
                                                    │
                                                    └──▶ Planner (refine loop)
    ```
    """)


def render_agent_log(log: list[dict]):
    """Render the agent activity feed."""
    if not log:
        return

    for entry in log:
        agent = entry.get("agent", "unknown")
        status = entry.get("status", "ok")
        css_class = "agent-done" if status != "error" else "agent-error"
        details = {k: v for k, v in entry.items() if k not in ("agent", "status")}
        detail_str = " · ".join(f"{k}={v}" for k, v in details.items())

        st.markdown(
            f'<span class="agent-badge {css_class}">{agent}</span> {detail_str}',
            unsafe_allow_html=True,
        )


def check_env():
    """Verify Azure credentials are set."""
    required = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        st.error(f"Missing environment variables: {', '.join(missing)}")
        st.info("Create a `.env` file from `.env.example` and fill in your Azure AI Foundry credentials.")
        st.stop()


def main():
    st.title("DS-Agents")
    st.caption("Multi-agent data science system — powered by LangGraph + Azure OpenAI")

    check_env()

    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        max_rounds = st.slider("Max refinement rounds", 1, 10, 5)
        st.divider()
        render_pipeline_diagram()
        st.divider()
        st.markdown("**Agents**")
        for name, desc in AGENT_DESCRIPTIONS.items():
            st.markdown(f"**{name}** — {desc}")

    # Main area
    col1, col2 = st.columns([1, 1])

    with col1:
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

    with col2:
        st.subheader("Agent Activity")
        activity_container = st.container()

    # Run button
    if st.button("Run Analysis", type="primary", use_container_width=True):
        if not uploaded_files:
            st.warning("Please upload at least one data file.")
            return
        if not query.strip():
            st.warning("Please enter a question.")
            return

        # Save uploaded files to temp dir
        tmp_dir = Path(tempfile.mkdtemp(prefix="ds_agents_"))
        data_paths = []
        for f in uploaded_files:
            path = tmp_dir / f.name
            path.write_bytes(f.getvalue())
            data_paths.append(str(path))

        # Import and run the graph
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

        # Display results
        with activity_container:
            render_agent_log(result.get("agent_log", []))

        st.divider()
        st.subheader("Result")
        st.success(result.get("final_result", "No result produced."))

        # Show plan
        with st.expander("Plan Steps", expanded=False):
            for i, step in enumerate(result.get("plan", [])):
                st.markdown(f"**Step {i+1}:** {step}")

        # Show final code
        with st.expander("Generated Code", expanded=False):
            st.code(result.get("final_code", ""), language="python")


if __name__ == "__main__":
    main()
