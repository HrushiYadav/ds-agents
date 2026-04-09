import yaml
from pathlib import Path

_PROMPTS: dict[str, str] | None = None


def get_prompts() -> dict[str, str]:
    global _PROMPTS
    if _PROMPTS is None:
        prompts_path = Path(__file__).resolve().parent.parent.parent / "prompts.yaml"
        with open(prompts_path, "r") as f:
            _PROMPTS = yaml.safe_load(f)
    return _PROMPTS
