from gcpclaw.agent import discover_skills, format_skills_index


def test_discover_skills_finds_skill_md(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: test\ndescription: A test skill\n---\n",
        encoding="utf-8",
    )
    skills = discover_skills([tmp_path])
    assert len(skills) == 1
    assert skills[0]["name"] == "test"


def test_format_skills_index_empty():
    assert format_skills_index([]) == "(no skills installed)"


def test_format_skills_index_with_skills():
    skills = [{"name": "foo", "description": "bar"}]
    result = format_skills_index(skills)
    assert "foo" in result
    assert "bar" in result
