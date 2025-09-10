import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import requests


@dataclass
class RoadmapTask:
    line_index: int
    description: str
    priority: str
    milestone: str


TASK_RE = re.compile(
    r"- (?P<desc>.*?) — \*\*(?P<priority>High|Medium|Low)\*\*, (?P<milestone>Q[1-4] \d{4}) \(Issue TBD\)"
)


def parse_roadmap(text: str) -> List[RoadmapTask]:
    """Return tasks with '(Issue TBD)' markers."""
    tasks: List[RoadmapTask] = []
    for idx, line in enumerate(text.splitlines()):
        match = TASK_RE.search(line)
        if match:
            tasks.append(
                RoadmapTask(
                    line_index=idx,
                    description=match.group("desc").strip(),
                    priority=match.group("priority"),
                    milestone=match.group("milestone"),
                )
            )
    return tasks


def replace_issue_links(text: str, replacements: Dict[int, str]) -> str:
    """Replace '(Issue TBD)' with issue URLs using line numbers."""
    lines = text.splitlines()
    for idx, url in replacements.items():
        lines[idx] = lines[idx].replace("(Issue TBD)", f"({url})")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def ensure_label(repo: str, token: str, name: str) -> None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"https://api.github.com/repos/{repo}/labels/{requests.utils.quote(name)}"
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code == 404:
        requests.post(
            f"https://api.github.com/repos/{repo}/labels",
            headers=headers,
            json={"name": name, "color": "ededed"},
            verify=False,
        )


def ensure_milestone(repo: str, token: str, title: str) -> int:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(
        f"https://api.github.com/repos/{repo}/milestones",
        headers=headers,
        params={"state": "all"},
        verify=False,
    )
    for ms in resp.json():
        if ms.get("title") == title:
            return ms["number"]
    resp = requests.post(
        f"https://api.github.com/repos/{repo}/milestones",
        headers=headers,
        json={"title": title},
        verify=False,
    )
    return resp.json()["number"]


def create_issue(repo: str, token: str, task: RoadmapTask) -> str:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    label = f"priority: {task.priority.lower()}"
    ensure_label(repo, token, label)
    milestone_num = ensure_milestone(repo, token, task.milestone)
    resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers=headers,
        json={
            "title": task.description,
            "labels": [label],
            "milestone": milestone_num,
        },
        verify=False,
    )
    resp.raise_for_status()
    return resp.json()["html_url"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create GitHub issues from roadmap")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--roadmap", default="docs/roadmap.md", help="Path to roadmap Markdown")
    parser.add_argument("--dry-run", action="store_true", help="Do not call GitHub")
    args = parser.parse_args()

    token = os.environ.get("AAFC_ISSUES") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("AAFC_ISSUES or GITHUB_TOKEN must be set")

    roadmap_path = Path(args.roadmap)
    text = roadmap_path.read_text(encoding="utf-8")
    tasks = parse_roadmap(text)
    if not tasks:
        print("No '(Issue TBD)' entries found.")
        return

    replacements: Dict[int, str] = {}
    for task in tasks:
        if args.dry_run:
            url = "https://example.com/issue"
        else:
            url = create_issue(args.repo, token, task)
        replacements[task.line_index] = url
        print(f"Created issue for '{task.description}': {url}")

    new_text = replace_issue_links(text, replacements)
    if args.dry_run:
        print("Dry run; roadmap not modified")
    else:
        roadmap_path.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    main()
