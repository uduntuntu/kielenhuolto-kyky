#!/usr/bin/env python3
"""Merge curated reference files with their upstream sources."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MANIFEST_PATH = Path("references/upstream-sources.json")
LEGACY_MANIFEST_PATH = Path("references/.upstream-sources.json")
GIT_DIFF_DIFFERENCE = 1


@dataclass(frozen=True)
class Comparison:
    name: str
    title: str
    submodule: str
    upstream_path: Path
    local_path: Path


COMPARISONS = {
    "patterns": Comparison(
        name="patterns",
        title="Finnish Humanizer patterns",
        submodule="upstream/finnish-humanizer",
        upstream_path=Path(
            "upstream/finnish-humanizer/finnish-humanizer/references/patterns.md"
        ),
        local_path=Path("references/patterns.md"),
    ),
    "kielioppi": Comparison(
        name="kielioppi",
        title="Suomettaja grammar guidance",
        submodule="upstream/suomettaja-skill",
        upstream_path=Path("upstream/suomettaja-skill/references/kielioppi.md"),
        local_path=Path("references/kielioppi.md"),
    ),
}


def run_git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True)


def git_output(args: list[str], cwd: Path) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout


def git_result(args: list[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return Path(result.stdout.strip())


def git_text(args: list[str], cwd: Path) -> str:
    return git_output(args, cwd).decode("utf-8").strip()


def git_error(result: subprocess.CompletedProcess[bytes]) -> str:
    return result.stderr.decode("utf-8", errors="replace").strip()


def require_conflict_parser() -> tuple[Any, Any, Any]:
    try:
        from conflict_parser import ConflictSegment, MergedFile, MergeMetadata
    except ImportError as error:
        raise SystemExit(
            "Conflict commands require conflict-parser. Install it with "
            "`python -m pip install -r scripts/requirements.txt`."
        ) from error
    return ConflictSegment, MergedFile, MergeMetadata


def run_no_index_diff(
    comparison: Comparison,
    root: Path,
    *extra_args: str,
) -> subprocess.CompletedProcess[bytes]:
    return git_result(
        [
            "diff",
            "--no-index",
            *extra_args,
            "--",
            str(comparison.upstream_path),
            str(comparison.local_path),
        ],
        root,
    )


def ensure_diff_result(result: subprocess.CompletedProcess[bytes]) -> bool:
    if result.returncode == 0:
        return False
    if result.returncode != GIT_DIFF_DIFFERENCE:
        raise SystemExit(git_error(result))
    return True


def diff_bytes_to_file(
    base_content: bytes,
    file_path: Path,
    root: Path,
    *extra_args: str,
) -> subprocess.CompletedProcess[bytes]:
    with tempfile.NamedTemporaryFile() as base_file:
        base_file.write(base_content)
        base_file.flush()
        return git_result(
            [
                "diff",
                "--no-index",
                *extra_args,
                "--",
                base_file.name,
                str(file_path),
            ],
            root,
        )


def print_shortstat_result(label: str, result: subprocess.CompletedProcess[bytes]) -> bool:
    if not ensure_diff_result(result):
        print(f"{label}: no changes")
        return False

    stat = result.stdout.decode("utf-8").strip()
    print(f"{label}: {stat}")
    return True


def print_stat(comparison: Comparison, root: Path) -> bool:
    result = run_no_index_diff(comparison, root, "--shortstat")
    return print_shortstat_result(f"{comparison.local_path}: current upstream", result)


def print_patch(comparison: Comparison, root: Path) -> bool:
    result = run_no_index_diff(comparison, root, "--color=always", "-U0")
    if not ensure_diff_result(result):
        return False

    print()
    print(f"## {comparison.title}")
    sys.stdout.buffer.write(result.stdout)
    return True


def load_manifest(root: Path) -> dict[str, dict[str, str]]:
    manifest_path = root / MANIFEST_PATH
    if not manifest_path.exists():
        manifest_path = root / LEGACY_MANIFEST_PATH
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def write_manifest(manifest: dict[str, dict[str, str]], root: Path) -> None:
    manifest_path = root / MANIFEST_PATH
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def relative_upstream_path(comparison: Comparison) -> Path:
    return comparison.upstream_path.relative_to(comparison.submodule)


def current_upstream_commit(comparison: Comparison, root: Path) -> str:
    return git_text(["rev-parse", "HEAD"], root / comparison.submodule)


def manifest_entry(comparison: Comparison, root: Path) -> dict[str, str]:
    return {
        "submodule": comparison.submodule,
        "upstream_path": str(relative_upstream_path(comparison)),
        "upstream_commit": current_upstream_commit(comparison, root),
    }


def update_manifest(
    comparisons: list[Comparison],
    root: Path,
    manifest: dict[str, dict[str, str]] | None = None,
) -> None:
    if manifest is None:
        manifest = load_manifest(root)
    for comparison in comparisons:
        manifest[str(comparison.local_path)] = manifest_entry(comparison, root)
    write_manifest(manifest, root)


def print_manifest_status(
    comparison: Comparison,
    root: Path,
    manifest: dict[str, dict[str, str]],
) -> None:
    entry = manifest.get(str(comparison.local_path))
    if not entry:
        return

    recorded_commit = entry.get("upstream_commit")
    current_commit = current_upstream_commit(comparison, root)
    if recorded_commit and recorded_commit != current_commit:
        print(
            f"{comparison.local_path}: upstream {recorded_commit[:12]} -> "
            f"{current_commit[:12]}"
        )

    local_drift = diff_against_recorded_upstream(comparison, entry, root)
    if local_drift:
        added, removed = local_drift
        print(
            f"{comparison.local_path}: local changes since recorded upstream "
            f"+{added} -{removed}"
        )


def upstream_has_changed(
    comparison: Comparison,
    manifest: dict[str, dict[str, str]],
    root: Path,
) -> bool:
    entry = manifest.get(str(comparison.local_path))
    if not entry:
        print(f"{comparison.local_path}: missing recorded upstream base in {MANIFEST_PATH}")
        return True

    recorded_commit = entry.get("upstream_commit")
    if not recorded_commit:
        print(f"{comparison.local_path}: missing upstream_commit in {MANIFEST_PATH}")
        return True

    return recorded_commit != current_upstream_commit(comparison, root)


def upstream_update_comparisons(
    comparisons: list[Comparison],
    root: Path,
    manifest: dict[str, dict[str, str]],
) -> list[Comparison]:
    changed_comparisons = []
    for comparison in comparisons:
        print_manifest_status(comparison, root, manifest)
        if upstream_has_changed(comparison, manifest, root):
            changed_comparisons.append(comparison)
    return changed_comparisons


def diff_against_recorded_upstream(
    comparison: Comparison, entry: dict[str, str], root: Path
) -> tuple[int, int] | None:
    recorded_commit = entry.get("upstream_commit")
    upstream_path = entry.get("upstream_path")
    submodule = entry.get("submodule")
    if not recorded_commit or not upstream_path or not submodule:
        return None

    base_content = file_at_revision(recorded_commit, Path(upstream_path), root / submodule)
    if base_content is None:
        return None

    local_content = (root / comparison.local_path).read_bytes()
    if base_content == local_content:
        return None

    result = diff_bytes_to_file(
        base_content,
        root / comparison.local_path,
        root,
        "--shortstat",
    )
    if result.returncode not in {0, GIT_DIFF_DIFFERENCE}:
        raise SystemExit(git_error(result))
    return parse_shortstat(result.stdout.decode("utf-8"))


def apply_upstream(comparison: Comparison, root: Path) -> Path:
    local_path = root / comparison.local_path
    backup_path = local_path.with_name(f"{local_path.name}.0")
    if backup_path.exists():
        raise SystemExit(f"Backup already exists: {backup_path.relative_to(root)}")
    shutil.move(local_path, backup_path)
    shutil.copyfile(root / comparison.upstream_path, local_path)
    return backup_path


def replace_with_upstream(comparison: Comparison, root: Path) -> None:
    shutil.copyfile(root / comparison.upstream_path, root / comparison.local_path)


def confirm_default_yes(comparisons: list[Comparison]) -> bool:
    print()
    print("Päivitetäänkö referenssit upstream-versioista?")
    for comparison in comparisons:
        print(f"- {comparison.local_path} <- {comparison.upstream_path}")
    answer = input("Oletus kyllä. Paina Enter tai kirjoita yes/kyllä: ").strip().lower()
    if answer in {"", "yes", "kyllä"}:
        return True
    print("Keskeytetty.")
    return False


def file_at_revision(revision: str, path: Path, cwd: Path) -> bytes | None:
    try:
        return git_output(["show", f"{revision}:{path}"], cwd)
    except subprocess.CalledProcessError:
        return None


def recorded_upstream_content(
    comparison: Comparison,
    manifest: dict[str, dict[str, str]],
    root: Path,
) -> tuple[str, bytes] | None:
    entry = manifest.get(str(comparison.local_path))
    if not entry:
        return None

    recorded_commit = entry.get("upstream_commit")
    upstream_path = entry.get("upstream_path")
    submodule = entry.get("submodule")
    if not recorded_commit or not upstream_path or not submodule:
        return None
    if submodule != comparison.submodule:
        return None

    content = file_at_revision(recorded_commit, Path(upstream_path), root / submodule)
    if content is None:
        return None
    return recorded_commit, content


def merge_backup(
    comparison: Comparison,
    backup_path: Path,
    manifest: dict[str, dict[str, str]],
    root: Path,
) -> bool:
    recorded = recorded_upstream_content(comparison, manifest, root)
    if not recorded:
        print(
            f"- {comparison.local_path}: no recorded upstream base found; "
            f"manual merge needed from {backup_path.relative_to(root)}"
        )
        return False

    recorded_commit, base_content = recorded
    if backup_path.read_bytes() == base_content:
        print(
            f"- {comparison.local_path}: local file matched recorded upstream "
            f"{recorded_commit[:12]}; no local changes to merge"
        )
        return True

    has_conflict = merge_backup_into_local(comparison, backup_path, base_content, root)
    if not has_conflict:
        print(
            f"- {comparison.local_path}: merged cleanly from recorded upstream "
            f"{recorded_commit[:12]}"
        )
        print_patch(comparison, root)
        return True

    print(
        f"- {comparison.local_path}: merged with conflict markers; "
        f"resolve using {backup_path.relative_to(root)}"
    )
    if not sys.stdin.isatty():
        return False
    return resolve_conflicts_interactively(comparison, root)


def try_merge(
    applied: list[tuple[Comparison, Path]],
    manifest: dict[str, dict[str, str]],
    root: Path,
) -> bool:
    print()
    print("Merge:")
    all_merged = True
    for comparison, backup_path in applied:
        merged = merge_backup(comparison, backup_path, manifest, root)
        all_merged = merged and all_merged
    return all_merged


def merge_backup_into_local(
    comparison: Comparison, backup_path: Path, base_content: bytes, root: Path
) -> bool:
    local_path = root / comparison.local_path

    with tempfile.NamedTemporaryFile() as base_file:
        base_file.write(base_content)
        base_file.flush()
        result = subprocess.run(
            [
                "git",
                "merge-file",
                "-p",
                "--diff3",
                str(local_path),
                base_file.name,
                str(backup_path),
            ],
            stdout=subprocess.PIPE,
        )

    if result.returncode < 0 or result.returncode > 127:
        raise SystemExit(f"git merge-file failed for {comparison.local_path}")

    local_path.write_bytes(result.stdout)
    return result.returncode > 0


def cleanup_backups(applied: list[tuple[Comparison, Path]], root: Path) -> None:
    for _, backup_path in applied:
        cleanup_backup_path(backup_path, root)


def cleanup_backup_for_comparison(comparison: Comparison, root: Path) -> None:
    backup_path = backup_path_for_comparison(comparison, root)
    if backup_path.exists():
        backup_path.unlink()
        print(f"Removed {backup_path.relative_to(root)}")


def cleanup_backup_path(backup_path: Path, root: Path) -> None:
    if backup_path.exists():
        backup_path.unlink()
        print(f"Removed {backup_path.relative_to(root)}")


def backup_path_for_comparison(comparison: Comparison, root: Path) -> Path:
    return (root / comparison.local_path).with_name(f"{comparison.local_path.name}.0")


def list_conflicts(comparison: Comparison, root: Path) -> int:
    ConflictSegment, MergedFile, MergeMetadata = require_conflict_parser()
    local_path = root / comparison.local_path
    merged_file = MergedFile.from_file(
        local_path,
        MergeMetadata(conflict_style="diff3"),
    )
    conflicts = [
        segment
        for segment in merged_file.segments
        if isinstance(segment, ConflictSegment)
    ]

    if not conflicts:
        print(f"{comparison.local_path}: no conflicts")
        return 0

    print(f"{comparison.local_path}: {len(conflicts)} conflict(s)")
    for index, conflict in enumerate(conflicts, start=1):
        print()
        print(f"## Conflict {index} at line {conflict.start_line_no}")
        print_block("lähde (upstream)", conflict.ours_lines)
        print_block("oma muutos", conflict.theirs_lines)
    return len(conflicts)


def resolve_conflicts_interactively(comparison: Comparison, root: Path) -> bool:
    ConflictSegment, MergedFile, MergeMetadata = require_conflict_parser()
    local_path = root / comparison.local_path
    merged_file = MergedFile.from_file(
        local_path,
        MergeMetadata(conflict_style="diff3"),
    )
    conflicts = [
        segment
        for segment in merged_file.segments
        if isinstance(segment, ConflictSegment)
    ]
    if not conflicts:
        print(f"{comparison.local_path}: no conflicts")
        cleanup_backup_for_comparison(comparison, root)
        return True

    print(f"{comparison.local_path}: resolving {len(conflicts)} conflict(s)")
    resolved_segments = []
    all_resolved = True
    conflict_index = 0

    for segment in merged_file.segments:
        if not isinstance(segment, ConflictSegment):
            resolved_segments.extend(segment.lines)
            continue

        conflict_index += 1
        print()
        print(f"## Conflict {conflict_index}/{len(conflicts)} at line {segment.start_line_no}")
        print_block("1 lähde (upstream)", segment.ours_lines)
        print_block("2 oma muutos", segment.theirs_lines)

        choice = conflict_choice()
        if choice == "1":
            resolved_segments.extend(segment.ours_lines)
        elif choice == "2":
            resolved_segments.extend(segment.theirs_lines)
        elif choice == "3":
            resolved_segments.extend(edit_conflict(segment, root))
        else:
            resolved_segments.extend(conflict_to_original(segment, merged_file.metadata))
            all_resolved = False

    local_path.write_text("".join(resolved_segments), encoding="utf-8")
    if all_resolved:
        print(f"{comparison.local_path}: conflicts resolved")
        cleanup_backup_for_comparison(comparison, root)
    else:
        print(f"{comparison.local_path}: unresolved conflicts left in file")
    return all_resolved


def conflict_choice() -> str:
    while True:
        answer = input(
            "Valitse 1 lähde, 2 oma muutos, 3 kirjoita uusi, enter ohittaa: "
        ).strip()
        if answer in {"1", "2", "3", ""}:
            return answer
        print("Vastaa 1, 2, 3 tai tyhjä.")


def edit_conflict(conflict: ConflictSegment, root: Path) -> list[str]:
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
    initial = "".join(conflict.theirs_lines or conflict.ours_lines)
    with tempfile.NamedTemporaryFile(
        mode="w+",
        encoding="utf-8",
        suffix=".md",
        dir=root,
        delete=False,
    ) as tmp:
        tmp.write(initial)
        tmp_path = Path(tmp.name)

    try:
        subprocess.run([editor, str(tmp_path)], check=True)
        return tmp_path.read_text(encoding="utf-8").splitlines(keepends=True)
    finally:
        tmp_path.unlink(missing_ok=True)


def conflict_to_original(conflict: ConflictSegment, metadata: MergeMetadata) -> list[str]:
    ms = metadata.marker_size
    lines = [f"{'<' * ms} {conflict.ours_label}\n"]
    lines.extend(conflict.ours_lines)
    if metadata.conflict_style == "diff3":
        lines.append(f"{'|' * ms} {conflict.base_label or ''}\n")
        lines.extend(conflict.base_lines or [])
    lines.append(f"{'=' * ms}\n")
    lines.extend(conflict.theirs_lines)
    lines.append(f"{'>' * ms} {conflict.theirs_label}\n")
    return lines


def print_block(title: str, lines: list[str] | None) -> None:
    print(f"[{title}]")
    if not lines:
        print("(empty)")
        return
    print("".join(lines), end="")


def parse_shortstat(stat: str) -> tuple[int, int]:
    added = 0
    removed = 0
    for part in stat.split(","):
        part = part.strip()
        words = part.split()
        if len(words) < 2:
            continue
        if words[1].startswith("insertion"):
            added = int(words[0])
        elif words[1].startswith("deletion"):
            removed = int(words[0])
    return added, removed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh upstream source submodules and merge upstream updates into "
            "curated reference files."
        )
    )
    parser.add_argument(
        "comparisons",
        nargs="*",
        choices=sorted(COMPARISONS),
        help="Limit diff to one or more comparisons. Defaults to all.",
    )
    parser.add_argument(
        "--no-refresh",
        dest="no_refresh",
        action="store_true",
        help="Do not refresh upstream submodules before comparing or merging.",
    )
    parser.add_argument(
        "--no-update",
        dest="no_refresh",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-p",
        "--patch",
        action="store_true",
        help="In dry-run mode, show patch output instead of changed-file statistics.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Only compare references against recorded and current upstream sources; "
            "do not modify files."
        ),
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Record current upstream source commits without overwriting references.",
    )
    parser.add_argument(
        "--merge-existing",
        action="store_true",
        help="Merge existing .0 backup files into the current reference files.",
    )
    parser.add_argument(
        "--list-conflicts",
        action="store_true",
        help="List conflict blocks in current reference files.",
    )
    parser.add_argument(
        "--resolve-conflicts",
        action="store_true",
        help="Interactively resolve conflict blocks in current reference files.",
    )
    args = parser.parse_args()
    if args.record and args.merge_existing:
        parser.error("--record cannot be combined with --merge-existing")
    return args


def selected_comparisons(names: list[str]) -> list[Comparison]:
    if not names:
        return list(COMPARISONS.values())
    return [COMPARISONS[name] for name in names]


def refresh_upstreams(comparisons: list[Comparison], root: Path) -> None:
    submodules = sorted({comparison.submodule for comparison in comparisons})
    print("Updating upstream submodules...", flush=True)
    run_git(["submodule", "update", "--init", "--remote", *submodules], root)


def diff_comparisons(
    comparisons: list[Comparison],
    root: Path,
    manifest: dict[str, dict[str, str]],
    show_patch: bool,
) -> list[Comparison]:
    changed_comparisons = []
    for comparison in comparisons:
        print_manifest_status(comparison, root, manifest)
        if show_patch:
            has_differences = print_patch(comparison, root)
        else:
            has_differences = print_stat(comparison, root)
        if has_differences:
            changed_comparisons.append(comparison)
    return changed_comparisons


def print_recorded_comparison(
    comparison: Comparison,
    manifest: dict[str, dict[str, str]],
    root: Path,
    show_patch: bool,
) -> None:
    recorded = recorded_upstream_content(comparison, manifest, root)
    label = f"{comparison.local_path}: recorded upstream"
    if not recorded:
        print(f"{label}: missing base in {MANIFEST_PATH}")
        return

    recorded_commit, base_content = recorded
    print(f"{label} {recorded_commit[:12]}")
    if show_patch:
        result = diff_bytes_to_file(
            base_content,
            root / comparison.local_path,
            root,
            "--color=always",
            "-U0",
        )
        if ensure_diff_result(result):
            sys.stdout.buffer.write(result.stdout)
        else:
            print(f"{comparison.local_path}: no local changes since recorded upstream")
        return

    result = diff_bytes_to_file(
        base_content,
        root / comparison.local_path,
        root,
        "--shortstat",
    )
    print_shortstat_result(
        f"{comparison.local_path}: local vs recorded upstream",
        result,
    )


def dry_run_comparisons(
    comparisons: list[Comparison],
    root: Path,
    manifest: dict[str, dict[str, str]],
    show_patch: bool,
) -> list[Comparison]:
    changed_comparisons = []
    for comparison in comparisons:
        print_manifest_status(comparison, root, manifest)
        print_recorded_comparison(comparison, manifest, root, show_patch)
        if show_patch:
            has_differences = print_patch(comparison, root)
        else:
            has_differences = print_stat(comparison, root)
        if has_differences:
            changed_comparisons.append(comparison)
    return changed_comparisons


def existing_backups(
    comparisons: list[Comparison],
    root: Path,
) -> list[tuple[Comparison, Path]]:
    return [
        (comparison, backup_path)
        for comparison in comparisons
        if (backup_path := backup_path_for_comparison(comparison, root)).exists()
    ]


def merge_existing_backups(
    comparisons: list[Comparison],
    manifest: dict[str, dict[str, str]],
    root: Path,
) -> None:
    applied = existing_backups(comparisons, root)
    if not applied:
        raise SystemExit("No .0 backup files found for selected comparisons.")

    backups_can_be_removed = try_merge(applied, manifest, root)
    update_manifest([comparison for comparison, _ in applied], root)
    if backups_can_be_removed:
        cleanup_backups(applied, root)


def list_selected_conflicts(comparisons: list[Comparison], root: Path) -> bool:
    conflict_count = sum(list_conflicts(comparison, root) for comparison in comparisons)
    return conflict_count == 0


def resolve_selected_conflicts(comparisons: list[Comparison], root: Path) -> bool:
    if not sys.stdin.isatty():
        raise SystemExit("--resolve-conflicts requires an interactive terminal")
    all_resolved = True
    for comparison in comparisons:
        all_resolved = resolve_conflicts_interactively(comparison, root) and all_resolved
    return all_resolved


def apply_changed_upstreams(
    comparisons: list[Comparison],
    manifest: dict[str, dict[str, str]],
    root: Path,
) -> bool:
    if not comparisons:
        return True

    all_applied = True
    applied_comparisons = []
    for comparison in comparisons:
        recorded = recorded_upstream_content(comparison, manifest, root)
        if not recorded:
            print(
                f"{comparison.local_path}: missing recorded upstream base in "
                f"{MANIFEST_PATH}; run --record after aligning the file manually"
            )
            all_applied = False
            continue

        _, base_content = recorded
        local_path = root / comparison.local_path
        local_content = local_path.read_bytes()
        if local_content == base_content:
            replace_with_upstream(comparison, root)
            update_manifest([comparison], root, manifest)
            applied_comparisons.append(comparison)
            print(f"{comparison.local_path}: no local updates; replaced with upstream")
            continue

        backup_path = apply_upstream(comparison, root)
        if merge_backup(comparison, backup_path, manifest, root):
            cleanup_backup_path(backup_path, root)
            update_manifest([comparison], root, manifest)
            applied_comparisons.append(comparison)
        else:
            all_applied = False

    if applied_comparisons:
        write_manifest(manifest, root)
    return all_applied


def main() -> int:
    args = parse_args()
    root = repo_root()
    comparisons = selected_comparisons(args.comparisons)

    if not args.no_refresh:
        refresh_upstreams(comparisons, root)

    manifest = load_manifest(root)

    if args.record:
        update_manifest(comparisons, root, manifest)
        print(f"Recorded upstream source commits in {MANIFEST_PATH}.")
        return 0

    if args.merge_existing:
        merge_existing_backups(comparisons, manifest, root)
        return 0

    if args.list_conflicts:
        if not list_selected_conflicts(comparisons, root):
            return 1
        return 0

    if args.resolve_conflicts:
        if not resolve_selected_conflicts(comparisons, root):
            return 1
        return 0

    if args.dry_run:
        changed_comparisons = dry_run_comparisons(
            comparisons,
            root,
            manifest,
            args.patch,
        )
        return 1 if changed_comparisons else 0

    update_comparisons = upstream_update_comparisons(comparisons, root, manifest)
    if not update_comparisons:
        return 0
    if not sys.stdin.isatty():
        raise SystemExit("Merging references requires an interactive terminal.")
    if not confirm_default_yes(update_comparisons):
        return 1
    if not apply_changed_upstreams(update_comparisons, manifest, root):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
