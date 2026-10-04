from scripts.classify_pr_change import classify


def test_solution_change_cannot_be_downgraded_by_label():
    value = classify(["safe2/cli.py", "README.md"], ["review:content"])
    assert value["route"] == "solution"
    assert value["pr_agent_required"] is True


def test_normative_framework_text_uses_impact_route():
    value = classify(["00-cross-pillar/CONTROL.md"])
    assert value["route"] == "framework"
    assert value["compliance_posture"] == "partially_compliant"


def test_research_images_and_editorial_text_use_lightweight_route():
    value = classify(["research/025_note.md", "assets/diagram.png", "README.md"])
    assert value["route"] == "content"
    assert value["pr_agent_required"] is False
    assert value["greptile_eligible"] is False


def test_framework_label_escalates_ordinary_documentation():
    value = classify(["docs/CONCEPT.md"], ["review:framework"])
    assert value["route"] == "framework"


def test_conflicting_route_labels_are_rejected():
    try:
        classify(["README.md"], ["review:framework", "review:content"])
    except ValueError as error:
        assert "Only one" in str(error)
    else:
        raise AssertionError("conflicting route labels must fail closed")
