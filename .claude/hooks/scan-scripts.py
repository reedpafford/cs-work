#!/usr/bin/env python3
"""PostToolUse hook: after any edit to scripts/*.md, run speech-scan.py on every `### Script` section.
Hard fails go back to Claude (exit 2) so they get fixed before the script is handed back. Notes are ignored here."""
import json, os, re, subprocess, sys, tempfile, importlib.util

data = json.load(sys.stdin)
path = (data.get("tool_input") or {}).get("file_path", "")
root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
if not path or not os.path.isfile(path):
    sys.exit(0)
rel = os.path.relpath(os.path.abspath(path), root)
if not (rel.startswith("scripts" + os.sep) and rel.endswith(".md")):
    sys.exit(0)

text = open(path, encoding="utf-8").read()
lfs = re.search(r"^Format:.*\bLFS\b|·\s*Format:\s*LFS", text, re.M | re.I) is not None
movie = re.search(r"Format:\s*Movie\b", text, re.I) is not None
scanner = os.path.join(root, "speech-scan.py")
_spec = importlib.util.spec_from_file_location("speech_scan", scanner)
_mod = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_mod)
BANNED = _mod.BANNED

variation, failures = "", []
blocks, cur = [], None
for line in text.splitlines():
    m = re.match(r"^(#{1,3})\s+(.*)", line)
    if m:
        if cur: blocks.append(cur)
        cur = None
        if m.group(1) == "##": variation = m.group(2).strip()
        elif m.group(1) == "###" and m.group(2).strip().lower() == "script":
            cur = [variation or "Script", []]
        elif m.group(1) == "###" and m.group(2).strip().lower() == "b-roll":
            cur = [(variation or "") + " B-roll", [], "broll"]
        continue
    if cur is not None:
        cur[1].append(line.replace("**", ""))  # bold marks Claude's new lines; not part of the script
if cur: blocks.append(cur)

for block in blocks:
    name, lines = block[0], block[1]
    body = "\n".join(lines).strip()
    if not body:
        continue
    if len(block) > 2:  # B-roll: shot notes, not speech; only the banned-word rule applies
        bad = [f"FAIL BANNED WORD: {l.strip()[:90]}" for l in lines if BANNED.search(l)]
        if bad: failures.append(f"{name}:\n  " + "\n  ".join(bad))
        continue
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(body)
    args = [sys.executable, scanner, f.name] + (["--movie"] if movie else ["--lfs"] if lfs else [])
    out = subprocess.run(args, capture_output=True, text=True).stdout
    os.unlink(f.name)
    fails = [l for l in out.splitlines() if l.startswith("FAIL")]
    if fails:
        failures.append(f"{name}:\n  " + "\n  ".join(fails))

if failures:
    sys.stderr.write(f"speech-scan hard fails in {rel} — fix before handing the script back "
                     "(banned words: use 'assaulted'/'abducted', imply death):\n" + "\n".join(failures) + "\n")
    sys.exit(2)
