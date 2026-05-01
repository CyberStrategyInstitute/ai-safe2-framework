"""
AI SAFE2 MCP Security Toolkit — mcp-scan: Dependency CVE Checker
Checks pyproject.toml, requirements.txt, and package.json for
MCP-related dependencies with known CVEs.

This module was NOT implemented in the initial delivery. It is new.

Coverage: MCP-related dependency CVEs from the CSI Threat Intelligence
Report April 2026. Checks pinned and unpinned versions against known
vulnerable ranges.

Note: This is not a full SCA scanner. It covers only the MCP-specific
CVE list from the CSI threat report. For comprehensive dependency scanning,
pair with safety, pip-audit, or Snyk.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from aisafe2_mcp_tools.scan.findings import Finding


@dataclass
class VulnerableRange:
    """A version range known to be vulnerable."""
    package: str
    cve: str
    affected_below: str     # Semantic: affected if version < this
    description: str
    severity: str


# Known vulnerable MCP-ecosystem package ranges from CSI Threat Intel Report
VULNERABLE_RANGES: list[VulnerableRange] = [
    VulnerableRange(
        "litellm", "CVE-2026-30623", "1.40.0",
        "STDIO command injection via unsanitized user input in MCP configuration UI",
        "critical",
    ),
    VulnerableRange(
        "langchain-mcp", "CVE-2026-30623", "0.1.3",
        "STDIO command injection via LangChain MCP adapter",
        "critical",
    ),
    VulnerableRange(
        "langflow", "CVE-2026-30623", "1.2.1",
        "STDIO command injection via LangFlow web UI",
        "critical",
    ),
    VulnerableRange(
        "fastmcp", "CVE-2026-27124", "2.1.0",
        "OAuth confused deputy — authorization codes not bound to user sessions",
        "critical",
    ),
    VulnerableRange(
        "fastmcp", "CVE-2025-69196", "2.0.8",
        "OAuth token cross-server reuse — missing audience validation",
        "high",
    ),
    VulnerableRange(
        "mcp-server-kubernetes", "CVE-2026-39884", "3.5.0",
        "Argument injection via kubectl port_forward parameters",
        "critical",
    ),
    VulnerableRange(
        "mcp", "CVE-2025-68145", "1.2.0",
        "JSON-RPC deserialization RCE — affects Python MCP SDK",
        "critical",
    ),
]

# Package names that warrant a warning if unpinned
SENSITIVE_PACKAGES: set[str] = {
    "mcp", "fastmcp", "litellm", "langchain", "langchain-mcp",
    "langflow", "mcp-server-kubernetes", "openai", "anthropic",
    "crewai", "autogen", "langraph", "n8n",
}

_VERSION_RE = re.compile(r'[=<>!~^]+\s*(\d+\.\d+[\.\d]*)')
_PACKAGE_LINE_RE = re.compile(r'^([a-zA-Z0-9_\-]+)\s*([=<>!~^][^\s#]*)?', re.MULTILINE)
_TOML_DEP_RE = re.compile(r'"([a-zA-Z0-9_\-]+)(?:[>=<~^!][^"]*)?"\s*,?\s*$', re.MULTILINE)


def _parse_version(version_str: str) -> tuple[int, ...] | None:
    """Parse a version string into a comparable tuple. Returns None on failure."""
    try:
        clean = re.sub(r'[^0-9.]', '', version_str.strip())
        return tuple(int(x) for x in clean.split('.') if x)
    except (ValueError, AttributeError):
        return None


def _version_less_than(v1: str, v2: str) -> bool:
    """Return True if v1 < v2 (both as version strings)."""
    t1 = _parse_version(v1)
    t2 = _parse_version(v2)
    if t1 is None or t2 is None:
        return False
    # Pad to same length
    max_len = max(len(t1), len(t2))
    t1 = t1 + (0,) * (max_len - len(t1))
    t2 = t2 + (0,) * (max_len - len(t2))
    return t1 < t2


class DependencyChecker:
    """
    Checks dependency files for MCP-related CVEs and unpinned sensitive packages.

    Supported dependency file formats:
      - pyproject.toml (dependencies = [...])
      - requirements.txt / requirements*.txt
      - package.json (dependencies / devDependencies)
    """

    def check_directory(self, directory: str) -> Iterator[Finding]:
        """Scan all dependency files in a directory tree."""
        root = Path(directory)
        for dep_file in self._find_dependency_files(root):
            yield from self._check_file(dep_file, root)

    def _find_dependency_files(self, root: Path) -> list[Path]:
        """Find all dependency files in directory."""
        candidates: list[Path] = []
        for pattern in ("pyproject.toml", "requirements*.txt", "package.json"):
            candidates.extend(root.rglob(pattern))
        return candidates

    def _check_file(self, dep_file: Path, root: Path) -> Iterator[Finding]:
        """Check a single dependency file."""
        try:
            content = dep_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        rel_path = str(dep_file.relative_to(root))

        # Extract package:version pairs from the file
        packages = self._extract_packages(content, dep_file.name)

        for pkg_name, version in packages:
            pkg_lower = pkg_name.lower().replace("_", "-")

            # Check against known CVE ranges
            for vuln in VULNERABLE_RANGES:
                if vuln.package.lower() != pkg_lower:
                    continue
                if version and _version_less_than(version, vuln.affected_below):
                    yield Finding(
                        finding_id="DEP-002",
                        severity=vuln.severity,
                        cp5_control="MCP-3",
                        title=f"Vulnerable dependency: {pkg_name} < {vuln.affected_below}",
                        description=(
                            f"{pkg_name} version {version} is affected by {vuln.cve}. "
                            f"{vuln.description}"
                        ),
                        file=rel_path,
                        line=self._find_line(content, pkg_name),
                        code_snippet=f'{pkg_name}=={version}',
                        remediation=(
                            f"Update {pkg_name} to >= {vuln.affected_below}. "
                            f"Run: pip install '{pkg_name}>={vuln.affected_below}'. "
                            f"See: {vuln.cve}"
                        ),
                        cve_refs=[vuln.cve],
                        auto_fixable=False,
                        manual_required=(vuln.severity == "critical"),
                    )

            # Check for unpinned sensitive packages
            if pkg_lower in SENSITIVE_PACKAGES and not version:
                yield Finding(
                    finding_id="DEP-001",
                    severity="low",
                    cp5_control="MCP-3",
                    title=f"Unpinned sensitive dependency: {pkg_name}",
                    description=(
                        f"{pkg_name} is a sensitive MCP-ecosystem package with no pinned version. "
                        "Unpinned dependencies can silently upgrade to vulnerable versions. "
                        "AI SAFE2 v3.0 CP.5.MCP-3 requires registry provenance verification."
                    ),
                    file=rel_path,
                    line=self._find_line(content, pkg_name),
                    code_snippet=pkg_name,
                    remediation=(
                        f"Pin to an exact version: {pkg_name}==X.Y.Z. "
                        "Use pip-compile or poetry.lock to lock all transitive deps."
                    ),
                    cve_refs=[],
                    auto_fixable=False,
                )

    def _extract_packages(
        self, content: str, filename: str
    ) -> list[tuple[str, str | None]]:
        """
        Extract (package_name, version_or_None) pairs from dependency file.
        Returns empty list on parse failure.
        """
        results: list[tuple[str, str | None]] = []

        if filename == "pyproject.toml":
            # Match strings like "mcp>=1.3.0" or "fastmcp" in dependencies arrays
            for m in _TOML_DEP_RE.finditer(content):
                pkg = m.group(1)
                # Try to extract version from the full match
                ver_match = _VERSION_RE.search(m.group(0))
                results.append((pkg, ver_match.group(1) if ver_match else None))

        elif "requirements" in filename:
            for m in _PACKAGE_LINE_RE.finditer(content):
                pkg = m.group(1)
                if pkg.startswith("#") or not pkg:
                    continue
                spec = m.group(2) or ""
                ver_match = _VERSION_RE.search(spec)
                results.append((pkg, ver_match.group(1) if ver_match else None))

        elif filename == "package.json":
            # Basic JSON parsing for npm dependencies
            dep_pattern = re.compile(r'"([a-zA-Z0-9@/_\-]+)"\s*:\s*"([^"]*)"')
            for m in dep_pattern.finditer(content):
                pkg = m.group(1)
                ver_str = m.group(2).lstrip("^~>=")
                results.append((pkg, ver_str if ver_str else None))

        return results

    @staticmethod
    def _find_line(content: str, package_name: str) -> int:
        """Find the first line number containing the package name."""
        for i, line in enumerate(content.splitlines(), 1):
            if package_name.lower() in line.lower():
                return i
        return 1
