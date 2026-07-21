from pathlib import Path


def test_docker_image_runs_the_complete_service_as_non_root():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert dockerfile.startswith("FROM python:3.13.5-slim")
    assert "COPY --chown=nalmai:nalmai app ./app" in dockerfile
    assert "COPY --chown=nalmai:nalmai public ./public" in dockerfile
    assert "COPY --chown=nalmai:nalmai data ./data" in dockerfile
    assert "USER nalmai" in dockerfile
    assert "EXPOSE 8000" in dockerfile
    assert '"--workers", "1"' in dockerfile
    assert "/api/health" in dockerfile


def test_docker_context_never_includes_local_secrets_or_databases():
    ignored = Path(".dockerignore").read_text(encoding="utf-8").splitlines()

    assert ".env" in ignored
    assert ".git" in ignored
    assert "data/*.db" in ignored
    assert "data/*.db-wal" in ignored
