"""safe2 - the unified AI SAFE2 CLI.

Collapses the scanner, Skill Trust Gate, and MCP Security Toolkit
(mcp-score / mcp-scan / mcp-safe-wrap) - previously three separately
versioned, separately released (and in the MCP toolkit's case, never
actually released) projects - into one installable package with five
subcommand groups: scan, gate, score, report, mcp. Plus `serve`, a thin
launcher for the (separately packaged) runtime enforcement gateway.

See PART 3 of the CSI roadmap: "Collapse everything into one safe2 CLI
with subcommands... Ship criterion is a cold git clone on a clean
machine, one install command, full test suite green."
"""
from __future__ import annotations

import shutil
import subprocess
import sys

import click

from safe2 import __version__
from safe2.commands.aism import aism
from safe2.commands.doctor import doctor
from safe2.commands.evidence import evidence
from safe2.commands.example import example
from safe2.commands.feedback import feedback
from safe2.commands.gate import gate
from safe2.commands.mcp import mcp
from safe2.commands.report import report
from safe2.commands.scan import scan
from safe2.commands.schema import schema
from safe2.commands.score import score


@click.group()
@click.version_option(__version__, prog_name="safe2")
def cli():
    """AI SAFE2 v3.1 - agent-facing governance and evidence CLI.

    \b
    safe2 scan project .            161-control static audit, findings only
    safe2 scan skill ./my-skill     skill package static scan, findings only
    safe2 scan mcp ./my-server      MCP server source scan, findings only
    safe2 gate project . --tier Tier2       exit 0/1 for CI
    safe2 gate skill ./my-skill --strict    exit 0/1/2 for CI
    safe2 gate mcp https://host/mcp         exit 0/1 for CI
    safe2 score project .                    score + verdict only
    safe2 score mcp https://host/mcp         remote MCP server score
    safe2 report project . --format all      json + sarif + markdown
    safe2 evidence nexus ./NEXUS             attributed implementation evidence
    safe2 doctor .                            multi-harness environment inventory
    safe2 feedback record ...                 operational friction evidence
    safe2 schema list                         machine-readable evidence contracts
    safe2 aism score assessment.json         human Decision Card
    safe2 example verify aism-decision-card  executable reference validation
    safe2 mcp wrap-stdio -- python -m server runtime injection scanning
    safe2 serve                              launch the enforcement gateway
    """


cli.add_command(scan)
cli.add_command(aism)
cli.add_command(evidence)
cli.add_command(example)
cli.add_command(doctor)
cli.add_command(feedback)
cli.add_command(gate)
cli.add_command(score)
cli.add_command(report)
cli.add_command(mcp)
cli.add_command(schema)


@cli.command("serve")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, type=int)
def serve(host, port):
    """Launch the AI SAFE2 sovereign runtime gateway (gateway/main.py)."""
    try:
        import gateway.main  # noqa: F401
    except ImportError:
        click.echo(
            "The gateway extra isn't installed. Run:\n  pip install ai-safe2[gateway]\n",
            err=True,
        )
        sys.exit(3)

    if shutil.which("uvicorn"):
        raise SystemExit(subprocess.call(["uvicorn", "gateway.main:app", "--host", host, "--port", str(port)]))

    import uvicorn  # type: ignore

    uvicorn.run("gateway.main:app", host=host, port=port)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
