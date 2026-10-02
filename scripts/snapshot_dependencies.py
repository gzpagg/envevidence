"""Record installed versions without editable-install or local-directory paths."""

import platform
from importlib import metadata
from pathlib import Path

packages = sorted(
    {
        f"{dist.metadata['Name']}=={dist.version}"
        for dist in metadata.distributions()
        if dist.metadata["Name"].lower() != "envevidence"
    },
    key=str.lower,
)
target = Path(__file__).resolve().parents[1] / "requirements-lock.txt"
target.write_text(
    f"# Tested on Windows / Python {platform.python_version()}. Optional local reproducibility snapshot.\n"
    "# Install project separately: python -m pip install -e .\n"
    + "\n".join(packages)
    + "\n",
    encoding="utf-8",
)
