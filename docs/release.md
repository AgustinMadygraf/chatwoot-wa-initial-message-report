# Release Process

1. **Branching**: push work to `main`; release branches optional but not required.
2. **Versioning**: update `pyproject.toml` `version = "X.Y.Z"` following SemVer.
3. **Changelog**: append entry under top `## [Unreleased]`, move to release heading once tagged.
4. **Tagging**: `git tag vX.Y.Z && git push --tags`.
5. **CI/CD Release workflow** (see `.github/workflows/release.yml`):
   - Triggered on push tags `v*`.
   - Runs lint/typecheck/tests/build.
   - Publishes GitHub release with `dist/*`.
6. **Post-release**: bump `pyproject.toml` to next patch/pre-release and add new `## [Unreleased]` section.
7. **Changelog automation**: run `scripts/generate_changelog.py vX.Y.Z` before tagging to push conventional entries into the `## [Unreleased]` section.
