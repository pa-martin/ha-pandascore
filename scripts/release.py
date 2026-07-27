#!/usr/bin/env python3

import json
import os
import re
import subprocess
from pathlib import Path

MANIFEST_PATH = Path("custom_components/pandascore/manifest.json")


def run(*args: str) -> str:
    """Run a command and return its output."""
    result = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_current_version() -> str:
    """Read the current integration version."""
    manifest = json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8",
        )
    )

    version = manifest.get("version")

    if not version:
        raise RuntimeError(f"No version found in {MANIFEST_PATH}")

    return version


def get_latest_tag() -> str | None:
    """Return the latest version tag."""
    try:
        return run(
            "git",
            "describe",
            "--tags",
            "--match",
            "v*",
            "--abbrev=0",
        )
    except subprocess.CalledProcessError:
        return None


def get_commits_since(tag: str | None) -> list[str]:
    """Return commit messages since the last release."""
    if tag:
        output = run(
            "git",
            "log",
            f"{tag}..HEAD",
            "--pretty=format:%s%n%b",
        )
    else:
        output = run(
            "git",
            "log",
            "--pretty=format:%s%n%b",
        )

    return [line.strip() for line in output.splitlines() if line.strip()]


def determine_bump(commits: list[str]) -> str | None:
    """Determine the required version bump."""
    for commit in commits:
        if "BREAKING CHANGE" in commit or re.match(
            r"^[a-z]+(\([^)]*\))?!:",
            commit,
        ):
            return "major"

    for commit in commits:
        if re.match(
            r"^feat(\([^)]*\))?:",
            commit,
        ):
            return "minor"

    for commit in commits:
        if re.match(
            r"^fix(\([^)]*\))?:",
            commit,
        ):
            return "patch"

    return None


def bump_version(
    version: str,
    bump: str,
) -> str:
    """Increment a semantic version."""
    match = re.fullmatch(
        r"(\d+)\.(\d+)\.(\d+)",
        version,
    )

    if not match:
        raise ValueError(f"Invalid semantic version: {version}")

    major, minor, patch = map(
        int,
        match.groups(),
    )

    if bump == "major":
        major += 1
        minor = 0
        patch = 0

    elif bump == "minor":
        minor += 1
        patch = 0

    elif bump == "patch":
        patch += 1

    else:
        raise ValueError(f"Unknown bump type: {bump}")

    return f"{major}.{minor}.{patch}"


def update_manifest(version: str) -> None:
    """Update manifest.json version."""
    manifest = json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8",
        )
    )

    manifest["version"] = version

    MANIFEST_PATH.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def set_github_output(
    name: str,
    value: str,
) -> None:
    """Set a GitHub Actions output."""
    github_output = os.environ.get("GITHUB_OUTPUT")

    if not github_output:
        return

    with Path(github_output).open(
        "a",
        encoding="utf-8",
    ) as output:
        output.write(f"{name}={value}\n")


def main() -> None:
    """Prepare a new release."""
    current_version = get_current_version()
    latest_tag = get_latest_tag()

    commits = get_commits_since(latest_tag)

    if not commits:
        print("No commits since the last release.")
        set_github_output(
            "release",
            "false",
        )
        return

    bump = determine_bump(commits)

    if bump is None:
        print("No release required. No feat, fix or breaking change found.")
        set_github_output(
            "release",
            "false",
        )
        return

    next_version = bump_version(
        current_version,
        bump,
    )

    print(f"Current version: {current_version}")
    print(f"Latest tag: {latest_tag}")
    print(f"Version bump: {bump}")
    print(f"Next version: {next_version}")

    update_manifest(next_version)

    print(f"Updated {MANIFEST_PATH} to version {next_version}")

    set_github_output(
        "version",
        next_version,
    )
    set_github_output(
        "bump",
        bump,
    )
    set_github_output(
        "release",
        "true",
    )


if __name__ == "__main__":
    main()
