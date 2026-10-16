"""Check source identities, published install pins, and current component claims.

Source package metadata is authoritative for source identities. The reviewed
publication inventory is authoritative for PyPI install examples. Schema,
protocol, compatibility-floor, and historical versions are independent.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
from pathlib import Path
import re
import subprocess
import tomllib
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ".ai-safe2/component-versions.json"


def package_version(root: Path, path: str) -> str:
    return tomllib.loads((root / path).read_text(encoding="utf-8"))["project"]["version"]


def python_version(root: Path, path: str, name: str) -> str:
    tree = ast.parse((root / path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            value = node.value
            if isinstance(value, ast.Call) and len(value.args) == 2:
                value = value.args[1]  # os.getenv override, with explicit source default
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return value.value
    raise ValueError(f"{path}: missing literal/default {name}")


def normalized(version: str) -> tuple[int, ...]:
    parts = tuple(int(part) for part in version.split("."))
    return parts + (0,) * (3 - len(parts))


def scan(root: Path, *, check_pypi: bool = False) -> list[str]:
    inventory = json.loads((root / INVENTORY).read_text(encoding="utf-8"))
    manifest = json.loads((root / "ai-safe2.manifest.json").read_text(encoding="utf-8"))
    versions = {
        "framework": manifest["framework"]["version"],
        "cli": package_version(root, "pyproject.toml"),
        "nexus": package_version(root, "NEXUS/pyproject.toml"),
        "gateway": python_version(root, "gateway/main.py", "GATEWAY_VERSION"),
        "mcp": package_version(root, "skills/mcp/pyproject.toml"),
        "developer_workflow": (root / "developer-workflow/VERSION").read_text().strip(),
    }
    published = inventory["published"]
    errors: list[str] = []

    def expect(path: str, actual: str, expected: str) -> None:
        if normalized(actual) != normalized(expected):
            errors.append(f"{path}: {actual}; expected {expected}")

    for key, path, pattern in [
        ("framework", "README.md", r"badge/version-([\d.]+)-"),
        ("framework", "AGENTS.md", r"AI SAFE² Framework: v([\d.]+)"),
        ("cli", "AGENTS.md", r"AI SAFE² CLI: v([\d.]+)"),
        ("nexus", "AGENTS.md", r"- NEXUS: v([\d.]+)"),
        ("gateway", "AGENTS.md", r"- Gateway: v([\d.]+)"),
        (
            "framework",
            "skills/ai-safe2-secure-build-copilot/SKILL.md",
            r"framework_version: v([\d.]+)",
        ),
        ("cli", "docs/COMPONENT-VERSIONS.md", r"\| AI SAFE² CLI \| ([\d.]+)"),
        (
            "nexus",
            "docs/COMPONENT-VERSIONS.md",
            r"\| NEXUS SDK and Sovereign Gateway scaffold \| ([\d.]+)",
        ),
        (
            "gateway",
            "docs/COMPONENT-VERSIONS.md",
            r"\| Core Gateway, north-south provider proxy \| ([\d.]+)",
        ),
        ("mcp", "docs/COMPONENT-VERSIONS.md", r"\| MCP knowledge server \| ([\d.]+)"),
        ("developer_workflow", "docs/COMPONENT-VERSIONS.md", r"\| Developer Workflow \| ([\d.]+)"),
        (
            "nexus",
            "NEXUS/docker/otel/collector-config.yaml",
            r'key: "ocsf.product.version"\s+value: "([\d.]+)"',
        ),
    ]:
        match = re.search(pattern, (root / path).read_text(encoding="utf-8"))
        if not match:
            errors.append(f"{path}: missing {key} version reference")
        else:
            expect(path, match[1], versions[key])
    expect(
        "MCP runtime framework binding",
        python_version(root, "skills/mcp/src/mcp_server/config.py", "FRAMEWORK_VERSION"),
        versions["framework"],
    )
    for key, label in [
        ("cli", "`ai-safe2` CLI package"),
        ("nexus", "NEXUS reference implementation"),
    ]:
        minor = ".".join(versions[key].split(".")[:2])
        if f"| {label} | {minor}.x |" not in (root / "SECURITY.md").read_text(encoding="utf-8"):
            errors.append(f"SECURITY.md: missing source support/status row for {key} {minor}.x")
    version_map = (root / "docs/COMPONENT-VERSIONS.md").read_text(encoding="utf-8")
    for key, label in [("cli", "CLI"), ("nexus", "SDK")]:
        match = re.search(r"Published " + label + r" ([\d.]+)", version_map)
        if match:
            expect(
                "docs/COMPONENT-VERSIONS.md:published " + key, match[1], published[key]["version"]
            )
        else:
            errors.append("docs/COMPONENT-VERSIONS.md: missing published " + key)
    if (
        tomllib.loads((root / "NEXUS/pyproject.toml").read_text())["project"]["license"]
        != "Apache-2.0"
    ):
        errors.append("NEXUS/pyproject.toml: must preserve the designated Apache-2.0 license")

    for key, path, field in [
        ("cli", "safe2/__init__.py", "__package_version__"),
        ("nexus", "NEXUS/sdk/python/nexus_sdk/__init__.py", "__version__"),
        ("nexus", "NEXUS/docker/gateway/gateway.py", "NEXUS_VERSION"),
        ("gateway", "gateway/provider_adapters.py", "GATEWAY_VERSION"),
        ("gateway", "examples/openclaw/gateway/gateway.py", "GATEWAY_VERSION"),
        ("gateway", "examples/openclaw/gateway/provider_adapters.py", "GATEWAY_VERSION"),
    ]:
        expect(path, python_version(root, path, field), versions[key])
    for key, actual in [
        ("cli", manifest["discovery"]["cli"]["version"]),
        ("nexus", manifest["implementations"]["nexus"]["version"]),
        ("gateway", manifest["implementations"]["gateway"]["version"]),
    ]:
        expect("ai-safe2.manifest.json:" + key, actual, versions[key])
    for key, path in [
        ("cli", "safe2/safe2-docs.manifest.json"),
        ("nexus", "NEXUS/nexus-docs.manifest.json"),
        ("developer_workflow", "developer-workflow/MANIFEST.json"),
    ]:
        data = json.loads((root / path).read_text(encoding="utf-8"))
        expect(
            path,
            data["version" if key == "developer_workflow" else "component_version"],
            versions[key],
        )
    workflow = json.loads(
        (root / "developer-workflow/repository-template/.ai-safe2/workflow.json").read_text()
    )
    workflow_manifest = json.loads((root / "developer-workflow/MANIFEST.json").read_text())
    expect(
        "developer-workflow minimum CLI",
        workflow["minimum_cli_version"],
        workflow_manifest["minimum_ai_safe2_cli"],
    )
    if normalized(workflow["minimum_cli_version"]) > normalized(published["cli"]["version"]):
        errors.append("developer-workflow requires an unpublished CLI")
    lock = json.loads((root / "developer-workflow/upstreams.lock.json").read_text())
    pin = next(item["pin"] for item in lock["upstreams"] if item["id"] == "ai-safe2-cli")
    expect("developer-workflow/upstreams.lock.json:cli", pin, published["cli"]["version"])

    files = (
        subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True)
        .stdout.decode()
        .split("\0")
    )
    history_line = re.compile(inventory["history_line_pattern"])
    rules = [
        ("cli", r"(?<!Minimum_)CLI-v?(\d+\.\d+\.\d+)"),
        ("cli", r"AI\s*SAFE(?:2|²)\s+CLI\s*:?\s+v?(\d+\.\d+\.\d+)"),
        ("nexus", r"(?<![-\w])NEXUS(?: remains(?: an optional)?)? v(\d+\.\d+(?:\.\d+)?)\b"),
        ("gateway", r"Gateway-v?(\d+\.\d+(?:\.\d+)?)"),
        ("developer_workflow", r"Developer_Workflow-v(\d+\.\d+\.\d+)"),
    ]
    for rel in filter(None, files):
        if (
            rel.startswith(("tests/", "scripts/"))
            or "/tests/" in rel
            or rel == INVENTORY
            or any(fnmatch.fnmatch(rel, pattern) for pattern in inventory["historical_paths"])
        ):
            continue
        path = root / rel
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        raw = path.read_bytes()
        if b"\0" in raw[:8192]:
            continue
        for number, line in enumerate(raw.decode("utf-8", "replace").splitlines(), 1):
            # Installation commands must remain obtainable, even near history prose.
            for key, package in [("cli", "ai-safe2"), ("nexus", "nexus-a2a-sdk")]:
                for match in re.finditer(
                    r"(?<![-\w])" + package + r"(?:\[[^]]+\])?==(\d+\.\d+\.\d+)", line
                ):
                    expect(
                        f"{rel}:{number}:published {package} pin",
                        match[1],
                        published[key]["version"],
                    )
            if not history_line.search(line):
                for key, pattern in rules:
                    for match in re.finditer(pattern, line):
                        expected = (
                            published[key]["version"]
                            if key in published and re.search(r"(?i)released|published|PyPI", line)
                            else versions[key]
                        )
                        expect(f"{rel}:{number}:{key} version claim", match[1], expected)
            if rel.startswith("NEXUS/docker/"):
                for pattern in [
                    r"csi/nexus-gateway:(\d+\.\d+\.\d+)",
                    r'NEXUS_VERSION:\s*"(\d+\.\d+\.\d+)"',
                    r"service.version=(\d+\.\d+\.\d+)",
                    r'(?:image.version=|com.cyberstrategyinstitute.version:\s*)"(\d+\.\d+\.\d+)"',
                ]:
                    for match in re.finditer(pattern, line):
                        expect(
                            f"{rel}:{number}:nexus deployment metadata", match[1], versions["nexus"]
                        )

    if check_pypi:
        for key, entry in published.items():
            with urllib.request.urlopen(
                f"https://pypi.org/pypi/{entry['package']}/json", timeout=20
            ) as response:
                data = json.load(response)
            expect(INVENTORY + ":published " + key, entry["version"], data["info"]["version"])
            if not data["releases"].get(entry["version"]):
                errors.append(
                    f"{entry['package']} {entry['version']} has no published distribution"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--check-pypi", action="store_true", help="Verify the reviewed publication inventory live"
    )
    args = parser.parse_args()
    try:
        errors = scan(args.root, check_pypi=args.check_pypi)
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError) as exc:
        print(f"Component version configuration error: {exc}")
        return 2
    print(
        "\n".join(errors)
        if errors
        else "Component source versions and published installation pins are consistent"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
