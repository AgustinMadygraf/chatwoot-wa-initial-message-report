"""
Path: scripts/generate_changelog.py
"""

import argparse
import datetime
import subprocess


def _last_tag() -> str | None:
    try:
        value = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"], encoding="utf-8"
        ).strip()
        return value
    except subprocess.CalledProcessError:
        return None


def _collect_commits(since: str | None) -> list[str]:
    cmd = ["git", "log", "--pretty=format:%s", "--no-merges"]
    if since:
        cmd.append(f"{since}..HEAD")
    return subprocess.check_output(cmd, encoding="utf-8").splitlines()


def _render_entry(version: str, commits: list[str]) -> str:
    date = datetime.date.today().isoformat()
    lines = [f"## {version} - {date}", ""]
    for commit in commits:
        lines.append(f"- {commit}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera un entry de changelog para release.")
    parser.add_argument("version", help="Versión SemVer (ej. v1.2.3)")
    parser.add_argument(
        "--changelog", default="CHANGELOG.md", help="Ruta al changelog"
    )
    args = parser.parse_args()

    commits = _collect_commits(_last_tag())
    if not commits:
        print("No se encontraron commits nuevos.")
        return

    entry = _render_entry(args.version, commits)

    with open(args.changelog, "r+", encoding="utf-8") as handle:
        content = handle.read()
        handle.seek(0)
        if "## [Unreleased]" not in content:
            raise ValueError("CHANGELOG.md debe contener sección '## [Unreleased]'.")
        updated = content.replace("## [Unreleased]\n", f"## [Unreleased]\n\n{entry}")
        handle.write(updated)
        handle.truncate()

    print(f"Changelog actualizado con {args.version}.")


if __name__ == "__main__":
    main()
