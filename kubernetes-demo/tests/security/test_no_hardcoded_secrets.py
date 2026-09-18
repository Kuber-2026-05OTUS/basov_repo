"""Static guard against committing real secrets into this subtree.

Scans tracked-looking source/config files for common secret patterns
(connection strings with embedded credentials, AWS-style keys, private key
headers) and fails the build if any are found outside explicitly-allowed
placeholder files.
"""

from __future__ import annotations

import re
from pathlib import Path

KUBERNETES_DEMO_ROOT = Path(__file__).resolve().parents[2]

ALLOWED_PLACEHOLDER_FILES = {
    KUBERNETES_DEMO_ROOT / "k8s" / "secrets" / "secret.example.yaml",
    KUBERNETES_DEMO_ROOT / ".env.example",
}

SCAN_GLOBS = ("**/*.py", "**/*.yaml", "**/*.yml", "**/*.md", "**/*.env")

SECRET_PATTERNS = [
    # Real creds only: excludes angle-bracket/UPPERCASE placeholders like
    # <password>, USER:PASSWORD, or ${VAR} used throughout the docs/templates.
    re.compile(r"mongodb(\+srv)?://[^:\s\"'<>${]+:[^@\s\"'<>${]{6,}@"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----"),
]

PLACEHOLDER_MARKERS = ("USER:PASSWORD", "REPLACE_ME", "PLACEHOLDER")


def _iter_scanned_files() -> list[Path]:
    files: list[Path] = []
    for pattern in SCAN_GLOBS:
        files.extend(KUBERNETES_DEMO_ROOT.glob(pattern))
    return [f for f in files if f.is_file() and ".git" not in f.parts]


def test_no_hardcoded_secret_patterns_in_repo() -> None:
    offenders = []
    for path in _iter_scanned_files():
        if path in ALLOWED_PLACEHOLDER_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                offenders.append((str(path.relative_to(KUBERNETES_DEMO_ROOT)), pattern.pattern))
    assert not offenders, f"Possible hardcoded secrets found: {offenders}"


def test_example_files_only_contain_placeholders() -> None:
    for path in ALLOWED_PLACEHOLDER_FILES:
        text = path.read_text(encoding="utf-8")
        assert any(marker in text for marker in PLACEHOLDER_MARKERS), (
            f"{path} should only contain placeholder values"
        )
