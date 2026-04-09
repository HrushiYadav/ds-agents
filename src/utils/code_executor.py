import subprocess
import sys
import uuid
import tempfile
from pathlib import Path


def execute_code(code: str, timeout: int = 120) -> tuple[str, str | None]:
    """Execute Python code in an isolated subprocess.

    Returns (stdout, error_or_none).
    """
    tmp_dir = Path(tempfile.gettempdir()) / "ds_agents"
    tmp_dir.mkdir(exist_ok=True)
    script_path = tmp_dir / f"exec_{uuid.uuid4().hex[:8]}.py"
    script_path.write_text(code, encoding="utf-8")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.cwd(),
        )
        if result.returncode == 0:
            return result.stdout, None
        return result.stdout, result.stderr or "Unknown execution error"
    except subprocess.TimeoutExpired:
        return "", f"Timeout after {timeout}s"
    except Exception as e:
        return "", str(e)
    finally:
        script_path.unlink(missing_ok=True)
