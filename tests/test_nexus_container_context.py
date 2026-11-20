"""Prevent the documented gateway image from losing its SDK build inputs."""
from pathlib import Path
import shlex

ROOT = Path(__file__).resolve().parents[1]


def test_gateway_copy_sources_fit_compose_context():
    compose = (ROOT / "NEXUS/docker/docker-compose.yml").read_text()
    assert "context: ..\n      dockerfile: docker/gateway/Dockerfile" in compose
    context = ROOT / "NEXUS"
    dockerfile = (context / "docker/gateway/Dockerfile").read_text()
    for line in dockerfile.splitlines():
        if line.startswith("COPY "):
            for source in shlex.split(line)[1:-1]:
                resolved = (context / source).resolve()
                assert resolved.is_relative_to(context.resolve())
                assert resolved.exists(), source
    assert "COPY pyproject.toml LICENSE NOTICE /app/nexus/" in dockerfile
    assert '"/app/nexus[full]" fastapi uvicorn' in dockerfile
