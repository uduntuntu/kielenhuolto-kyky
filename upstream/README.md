# Upstream Sources

This directory contains Git submodules for the original source projects used to maintain this skill.

- `finnish-humanizer/`: Harri Sipola's Finnish Humanizer and AI-pattern taxonomy.
- `suomi-finnish-skill/`: Aku Nikkola's Finnish proofreading and grammar guidance.

These submodules are maintenance sources, not runtime references. The skill itself uses the curated files in `references/`.

Do not edit files under `upstream/` directly. Update the submodules, review their diffs, and merge relevant changes into `references/patterns.md` or `references/kielioppi.md`.
