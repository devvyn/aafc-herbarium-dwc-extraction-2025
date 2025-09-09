import os
import subprocess
import sys

from scripts.create_roadmap_issues import parse_roadmap, replace_issue_links


def test_parse_roadmap_extracts_tasks():
    text = """
- Task one — **High**, Q2 2025 (Issue TBD)
- Task two — **Low**, Q4 2025
"""
    tasks = parse_roadmap(text)
    assert len(tasks) == 1
    task = tasks[0]
    assert task.description == "Task one"
    assert task.priority == "High"
    assert task.milestone == "Q2 2025"


def test_replace_issue_links():
    text = "- Task one — **High**, Q2 2025 (Issue TBD)\n"
    replacements = {0: "https://example.com/1"}
    updated = replace_issue_links(text, replacements)
    assert "(https://example.com/1)" in updated


def test_dry_run_does_not_modify_file(tmp_path, monkeypatch):
    text = "- Task one — **High**, Q2 2025 (Issue TBD)\n"
    roadmap = tmp_path / "roadmap.md"
    roadmap.write_text(text)

    env = os.environ.copy()
    env["GITHUB_TOKEN"] = "x"
    subprocess.run(
        [
            sys.executable,
            "scripts/create_roadmap_issues.py",
            "--repo",
            "org/repo",
            "--roadmap",
            str(roadmap),
            "--dry-run",
        ],
        check=True,
        env=env,
    )

    assert roadmap.read_text() == text
