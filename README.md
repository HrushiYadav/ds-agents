# DS-Agents

Multi-agent data science system inspired by Google's [DS-STAR](https://arxiv.org/abs/2509.21825) research paper. 7 specialized AI agents collaborate to answer complex data analysis questions — built with **LangGraph** for orchestration and **Azure OpenAI** for inference.

## Architecture

```
User Query + Data Files
         │
         ▼
   ┌───────────┐    ┌──────────┐    ┌────────┐    ┌──────────┐
   │  Analyzer  │──▶│  Planner  │──▶│  Coder  │──▶│ Executor  │
   └───────────┘    └──────────┘    └────────┘    └──────────┘
                                                       │
                                            ┌──────────┴──────────┐
                                            ▼                     ▼
                                      ┌──────────┐         ┌──────────┐
                                      │ Debugger  │         │ Verifier  │
                                      └──────────┘         └──────────┘
                                                                 │
                                                      ┌──────────┴──────────┐
                                                      ▼                     ▼
                                                ┌──────────┐         ┌───────────┐
                                                │  Router   │         │ Finalyzer  │──▶ Answer
                                                └──────────┘         └───────────┘
                                                      │
                                                      └──▶ Planner (refine loop)
```

### Agents

| Agent | Role |
|-------|------|
| **Analyzer** | Profiles uploaded data files — columns, types, stats, sample rows |
| **Planner** | Creates an iterative step-by-step analysis plan |
| **Coder** | Generates Python code to execute each plan step |
| **Executor** | Runs generated code in a sandboxed subprocess |
| **Verifier** | Checks if the current output sufficiently answers the query |
| **Router** | Decides: revise an existing step or add a new one |
| **Debugger** | Fixes code execution errors and retries |
| **Finalyzer** | Produces the final answer code and executes it |

## Tech Stack

- **LangGraph** — agent orchestration via `StateGraph` with conditional edges
- **Azure OpenAI (AI Foundry)** — LLM inference (GPT-4o)
- **Streamlit** — interactive web UI
- **Pandas** — data processing
- **Python 3.11+**

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/HrushiYadav/ds-agents.git
cd ds-agents
pip install -r requirements.txt
```

### 2. Configure Azure OpenAI

```bash
cp .env.example .env
```

Edit `.env` with your Azure AI Foundry credentials:

```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

### 3. Run the app

```bash
streamlit run app.py
```

### 4. Use it

1. Upload a CSV, Excel, or JSON file
2. Ask a question about your data (e.g., "What is the total revenue by region?")
3. Watch the agents collaborate to produce the answer

## Differences from the Paper

| DS-STAR Paper | This Implementation |
|---------------|-------------------|
| Gemini models | Azure OpenAI (GPT-4o) |
| Sequential function calls | LangGraph StateGraph with conditional edges |
| CLI only | Streamlit web UI with agent activity feed |
| Single provider | Extensible provider pattern |
| No UI feedback | Real-time agent status + activity log |

## Project Structure

```
ds-agents/
├── app.py                    # Streamlit UI
├── prompts.yaml              # Prompt templates for all agents
├── .env.example              # Azure credentials template
├── requirements.txt
├── pyproject.toml
├── data/
│   └── sample_sales.csv      # Demo dataset
└── src/
    ├── agents/               # Agent node implementations
    │   ├── analyzer.py
    │   ├── planner.py
    │   ├── coder.py
    │   ├── verifier.py
    │   ├── router.py
    │   ├── debugger.py
    │   └── finalyzer.py
    ├── graph/
    │   ├── state.py          # LangGraph TypedDict state
    │   └── workflow.py       # StateGraph with conditional routing
    ├── providers/
    │   └── azure.py          # Azure OpenAI client
    └── utils/
        ├── code_executor.py  # Sandboxed code execution
        └── prompts.py        # Prompt template loader
```

## References

- [DS-STAR: A Data Science Agent Framework using LLMs](https://arxiv.org/abs/2509.21825) — Kwon et al., Google Research
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)

## License

MIT
