#!/usr/bin/env python3
"""Download Phi-3 Mini GGUF from Hugging Face and set LLAMA_MODEL_PATH in .env.

Saves the model to ./models/ (project root) and updates .env so the app
and smoke test can use it. Run once after cloning or when setting up a new machine.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

REPO_ID = "microsoft/Phi-3-mini-4k-instruct-gguf"
FILENAME = "Phi-3-mini-4k-instruct-q4.gguf"


def main() -> int:
    """Download Phi-3 Mini Q4 GGUF and set LLAMA_MODEL_PATH in .env."""
    models_dir = PROJECT_DIR / "models"
    models_dir.mkdir(exist_ok=True)
    local_dir = str(models_dir)

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("huggingface_hub is not installed. Run: pip install huggingface_hub")
        return 1

    print("Downloading Phi-3 Mini Q4 GGUF from Hugging Face...")
    print(f"  repo_id={REPO_ID!r}, filename={FILENAME!r}")
    print(f"  local_dir={local_dir!r}")
    print("  (this may take a few minutes, ~2.2 GB)")
    try:
        path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=local_dir,
        )
    except Exception as e:
        print(f"Download failed: {e}")
        return 1

    model_path = Path(path).resolve()
    print(f"Downloaded to: {model_path}")

    # Update .env
    env_file = PROJECT_DIR / ".env"
    line = f"LLAMA_MODEL_PATH={model_path}\n"
    if env_file.exists():
        content = env_file.read_text()
        lines = content.splitlines()
        found = False
        for i, ln in enumerate(lines):
            if ln.strip().startswith("LLAMA_MODEL_PATH="):
                lines[i] = line.rstrip()
                found = True
                break
        if not found:
            lines.append(line.rstrip())
        env_file.write_text("\n".join(lines) + "\n")
    else:
        env_file.write_text(line)

    print(f"Updated {env_file} with LLAMA_MODEL_PATH={model_path}")
    print("Done. Run: ./venv/bin/python scripts/smoke_test_llm.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
