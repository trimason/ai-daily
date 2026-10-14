#!/usr/bin/env python3
"""Preview or publish audited source files to trimason/ai-daily using gh."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = "trimason/ai-daily"
SITE = "https://trimason.github.io/ai-daily"
ROOT = Path(__file__).absolute().parents[1]
GH_FALLBACK = Path.home() / ".local/share/ai-daily-tools/gh"
FIXED = (
    ".github/workflows/pages.yml", ".gitignore", ".nojekyll", "README.md",
    "content/radar.json", "content/keywords.json", "content/recent-signals.json",
)
GROUPS = {"scripts": {".py"}, "assets": {".js", ".css", ".svg"},
          "content/issues": {".json"}}


def safe_path(path):
    """Reject links at any level within this isolated project."""
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f"Refusing symlink: {part}")
        if part == ROOT:
            break
    return path


def source_files():
    paths = [safe_path(ROOT / name) for name in FIXED]
    for folder, extensions in GROUPS.items():
        directory = safe_path(ROOT / folder)
        paths.extend(safe_path(path) for path in directory.iterdir()
                     if path.suffix in extensions)
    sources = {}
    for path in sorted(paths):
        if not path.is_file():
            raise ValueError(f"Expected source file: {path}")
        name = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        content = data.decode("utf-8")
        sha = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        sources[name] = {"sha": sha, "content": content}
    return sources


def gh_api(gh, endpoint, method="GET", body=None):
    command = [gh, "api", f"repos/{REPO}/{endpoint}", "--method", method,
               "--header", "Accept: application/vnd.github+json"]
    if body is not None:
        command += ["--input", "-"]
    result = subprocess.run(command, input=json.dumps(body) if body is not None else None,
                            text=True, capture_output=True, shell=False, cwd=ROOT)
    if result.returncode:
        # Do not echo CLI output: an authentication error may include sensitive context.
        raise RuntimeError(f"gh API {method} {endpoint} failed (exit {result.returncode}); "
                           "check gh authentication and repository access.")
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--publish", action="store_true", help="commit changes; default is dry-run")
    mode.add_argument("--dry-run", action="store_true", help="preview source changes (the default)")
    parser.add_argument("--gh", help="path to official GitHub CLI")
    parser.add_argument("--message", help="Git commit message")
    args = parser.parse_args()
    gh = args.gh or shutil.which("gh") or (str(GH_FALLBACK) if GH_FALLBACK.is_file() else None)
    if not gh:
        parser.error("gh was not found; install/login to the official GitHub CLI or use --gh")

    # Validate the source boundary before executing the local build script.
    source_files()
    safe_path(ROOT / "dist")
    subprocess.run([sys.executable, str(ROOT / "scripts/build.py"), "--base-path", "/ai-daily",
                    "--site-url", SITE], cwd=ROOT, check=True, shell=False)
    sources = source_files()
    head = gh_api(gh, "git/ref/heads/main")["object"]["sha"]
    commit = gh_api(gh, f"git/commits/{head}")
    base_tree = commit["tree"]["sha"]
    remote = gh_api(gh, f"git/trees/{base_tree}?recursive=1")
    if remote.get("truncated"):
        raise RuntimeError("Remote tree is truncated; refusing an incomplete comparison")
    entries = {entry["path"]: entry for entry in remote["tree"]}
    for name in sources:
        if entries.get(name, {}).get("type") == "tree":
            raise RuntimeError(f"Remote directory conflicts with local file: {name}")
        for parent in Path(name).parents:
            if parent.as_posix() == ".":
                continue
            if parent.as_posix() in entries and entries[parent.as_posix()]["type"] != "tree":
                raise RuntimeError(f"Remote file conflicts with local directory: {parent}")
    changed = [name for name, local in sources.items()
               if entries.get(name, {}).get("sha") != local["sha"]
               or entries.get(name, {}).get("mode") != "100644"]
    print(f"Target: {REPO} / main; current commit: {head}")
    if not changed:
        print("No source changes; nothing to publish.")
        return
    for name in changed:
        print(f"  {'update' if name in entries else 'add'}: {name}")
    if not args.publish:
        print(f"Dry-run: {len(changed)} file(s) would change. Use --publish to commit them.")
        return

    if source_files() != sources:
        raise RuntimeError("Local sources changed during comparison; rerun before publishing")
    if gh_api(gh, "git/ref/heads/main")["object"]["sha"] != head:
        raise RuntimeError("Remote main moved during comparison; rerun before publishing")
    # base_tree preserves all existing remote files; this command never deletes them.
    tree = gh_api(gh, "git/trees", "POST", {
        "base_tree": base_tree,
        "tree": [{"path": name, "mode": "100644", "type": "blob",
                  "content": sources[name]["content"]} for name in changed],
    })
    new_commit = gh_api(gh, "git/commits", "POST", {
        "message": args.message or f"Update AI daily sources {datetime.now().date().isoformat()}",
        "tree": tree["sha"], "parents": [head],
    })
    if gh_api(gh, "git/ref/heads/main")["object"]["sha"] != head:
        raise RuntimeError("Remote main moved before publishing; no branch update was made")
    result = gh_api(gh, "git/refs/heads/main", "PATCH", {"sha": new_commit["sha"], "force": False})
    if result["object"]["sha"] != new_commit["sha"]:
        raise RuntimeError("Unexpected branch-update response; verify the repository before retrying")
    print(f"Published source commit: https://github.com/{REPO}/commit/{new_commit['sha']}")
    print(f"Deployment workflow: https://github.com/{REPO}/actions/workflows/pages.yml")
    print("Source commit completed. Verify the workflow and public pages before reporting deployment success.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
