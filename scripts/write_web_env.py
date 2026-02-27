from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    root_dir = Path.cwd()
    env_target = root_dir / "web" / ".env"
    env_target.parent.mkdir(parents=True, exist_ok=True)

    symlink_source = os.getenv("DOT_ENV_SYMLINK_SOURCE", "").strip()
    if symlink_source:
        if env_target.exists() or env_target.is_symlink():
            env_target.unlink()
        env_target.symlink_to(Path(symlink_source).expanduser())
        return

    env_contents = os.getenv("OPENBASE_WEB_ENV_CONTENT")
    if env_contents is None:
        raise ValueError(
            "OPENBASE_WEB_ENV_CONTENT must be set when DOT_ENV_SYMLINK_SOURCE is empty"
        )

    env_target.write_text(env_contents, encoding="utf-8")


if __name__ == "__main__":
    main()
