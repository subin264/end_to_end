"""
run the full modeling pipeline (topsis -> scenarios -> validation).

- step 1: topsis_modeling.py
- step 2: 2~5_scenario_analysis.py
- step 3: topsis_validation.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List


def run_step(script_path: Path) -> None:
    """run a single pipeline step."""
    if not script_path.exists():
        raise FileNotFoundError(f"script not found: {script_path}")

    python_exec = Path(sys.executable)

    completed = subprocess.run(
        [str(python_exec), str(script_path)],
        check=True,
    )

    if completed.returncode != 0:
        raise RuntimeError(f"script failed: {script_path}, code={completed.returncode}")


def main() -> None:
    """Run the entire pipeline."""
    base_dir = Path(__file__).resolve().parent

    steps: List[Path] = [
        base_dir / "topsis_modeling.py",
        base_dir / "2~5_scenario_analysis.py",
        base_dir / "topsis_validation.py",
    ]

    print("running full topsis pipeline...")

    for idx, script in enumerate(steps, start=1):
        print(f"step {idx}: running {script.name}")
        run_step(script)

    print("pipeline finished: all steps completed")


if __name__ == "__main__":
    main()


