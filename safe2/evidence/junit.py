"""Bounded conservative JUnit XML import. Never execute report content."""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from typing import Any

from defusedxml import ElementTree as SafeET
from defusedxml.common import DefusedXmlException

from safe2.contracts import validate_artifact


def import_junit(payload: bytes, *, task_id: str, revision: str, environment: str,
                 exit_code: int) -> dict[str, Any]:
    """Count testcase outcomes, checking declared totals rather than trusting them.

    Only a narrow UTF-8 JUnit subset is supported. DTD/entities and unknown outcome
    extensions are rejected; external lookup, XML transforms, and execution are absent.
    Exit code and run labels remain supplied declarations, not witnessed execution.
    """
    if len(payload) > 1_000_000:
        raise ValueError("JUnit report exceeds 1 MB")
    try:
        source = payload.decode("utf-8-sig")
        if "\x00" in source or "<!DOCTYPE" in source.upper() or "<!ENTITY" in source.upper():
            raise ValueError("DTD, entities, and non-UTF-8 XML are not supported")
        root = SafeET.fromstring(source)
    except (UnicodeError, ET.ParseError, DefusedXmlException) as exc:
        raise ValueError("Invalid UTF-8 JUnit XML") from exc
    if root.tag not in {"testsuites", "testsuite"}:
        raise ValueError("Expected testsuites or testsuite root")
    identities: set[tuple[str, str]] = set()
    nodes = 0

    def counts_for(node: ET.Element, depth: int = 0) -> dict[str, int]:
        nonlocal nodes
        nodes += 1
        if depth > 32 or nodes > 20000:
            raise ValueError("JUnit structure limit exceeded")
        if "disabled" in node.attrib:
            raise ValueError("Disabled-suite metadata requires explicit normalization")
        counts = {key: 0 for key in ("total", "passed", "failed", "errors", "skipped")}
        for child in node:
            if child.tag == "testsuite":
                nested = counts_for(child, depth + 1)
                for key in counts:
                    counts[key] += nested[key]
            elif child.tag == "testcase" and node.tag == "testsuite":
                nodes += 1
                if set(child.attrib) - {"name", "classname", "time", "file", "line", "assertions"}:
                    raise ValueError("Unsupported testcase attributes")
                identity = (child.get("classname", ""), child.get("name", ""))
                if not identity[1] or identity in identities or len(identities) >= 10000:
                    raise ValueError("Test cases need unique class/name identities within report bounds")
                identities.add(identity)
                outcomes = [item.tag for item in child if item.tag in {"failure", "error", "skipped"}]
                if len(outcomes) > 1 or any(item.tag not in {
                    "failure", "error", "skipped", "system-out", "system-err", "properties",
                } for item in child):
                    raise ValueError("Ambiguous or unsupported testcase outcome")
                for item in child:
                    check_metadata(item)
                counts["total"] += 1
                state = {"failure": "failed", "error": "errors", "skipped": "skipped"}.get(
                    outcomes[0] if outcomes else "", "passed")
                counts[state] += 1
            elif child.tag not in {"properties", "system-out", "system-err"}:
                raise ValueError("Unsupported JUnit structure")
            else:
                check_metadata(child)
        for attribute, key in {"tests": "total", "failures": "failed", "errors": "errors", "skipped": "skipped"}.items():
            value = node.get(attribute)
            if value is not None and (not value.isascii() or not value.isdigit() or len(value) > 8
                                      or int(value) != counts[key]):
                raise ValueError("Declared JUnit totals disagree with testcase outcomes")
        return counts

    def check_metadata(node: ET.Element) -> None:
        if node.tag == "properties":
            if any(item.tag != "property" or len(item) for item in node):
                raise ValueError("Unsupported property structure")
        elif len(node):
            raise ValueError("Nested report markup requires explicit normalization")

    counts = counts_for(root)
    report = {
        "schema_version": "safe2.test-result.v1", "task_id": task_id, "revision": revision,
        "environment": environment, "source_ref": "junit-sha256:" + hashlib.sha256(payload).hexdigest(),
        "exit_code": exit_code, "counts": counts,
        "import_provenance": {"format": "junit-xml", "source_sha256": hashlib.sha256(payload).hexdigest(),
                              "execution_binding": "operator_declared"},
    }
    if validate_artifact("test-result-v1", report):
        raise ValueError("Invalid run metadata or exit code")
    return report
