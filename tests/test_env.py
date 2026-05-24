from pathlib import Path

import worldcup_tracker.env as env_module


def test_load_env_file_reads_variables(tmp_path: Path, monkeypatch) -> None:
    env_module._LOADED = False
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("PUSHOVER_USER_KEY=from_dotenv\n", encoding="utf-8")
    monkeypatch.delenv("PUSHOVER_USER_KEY", raising=False)

    loaded = env_module.load_env_file()

    assert loaded == tmp_path / ".env"
    import os

    assert os.environ.get("PUSHOVER_USER_KEY") == "from_dotenv"
