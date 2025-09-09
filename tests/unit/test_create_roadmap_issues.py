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
