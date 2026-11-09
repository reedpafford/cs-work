#!/usr/bin/env python3
"""Readiness scanner for ad drafts. Usage: speech-scan.py draft.txt [--pass] [--lfs | --movie]
Default (spoken script): flags fragment runs, repeated sentence shapes, digits, symbols, caps,
filler budget, word count.
--lfs (long-form static, read not spoken): digits and $ are receipts and fragments are rhythm,
so those checks are off; caps become a note; body formatting (headers, bullets, bold, emoji)
is a hard fail; repeated shapes still fail. Reports read time, first "you", first product name,
wall paragraphs, em-dash rate.
With --pass and zero hard fails, records a token the Notion write hook accepts
(see .claude/hooks/notion-script-gate.py). The token is format-agnostic."""
import sys, re, hashlib, json, os, time

FILLERS = ["honestly","i guess","i think","pretty sure","i'm sure","kind of","kinda","-ish","bout ","look,","god,","you know"]
STUMBLE = re.compile(r"\b(\w+), \1\b", re.I)

def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

CAPS_OK = ("ER","UGC","LFS","P.S","PS","AM","PM","TV","GPS","ICU","CVS","LDL","HDL","DOT","NA","MD","TSA","RA","SUV","ATM","YMCA")
BANNED = re.compile(r"\b(gang[- ]?rap\w*|rap(?:e|ed|es|ing|ist|ists)|sexual(?:ly)?\s+(?:assault\w*|violence|abuse)|molest\w*|kill(?:s|ed|ing|er|ers)?|murder\w*)\b", re.I)
FORMATTING = re.compile(r'^\s*(#{1,6}\s|[-*•]\s|\d+\.\s)|\*\*|__|[\U0001F300-\U0001FAFF\u2600-\u27BF]')

def scan(text, lfs=False):
    hard, soft = [], []
    lines = [l for l in text.splitlines() if l.strip()]
    words = len(text.split())
    # Meta compliance (Reed, 2026-09-29): JC40 V1 and JC41 V2/V3 were disapproved under Adult Sexual
    # Exploitation ("sexual violence"). The ceiling word is now "assaulted"; death is implied, never said.
    for ln, line in enumerate(lines, 1):
        hits = BANNED.findall(line)
        if hits:
            hard.append(f"L{ln} BANNED WORD {sorted(set(h[0] if isinstance(h, tuple) else h for h in hits))}: say 'assaulted' or 'abducted', imply death: {line[:90]}")
    for ln, line in enumerate(lines, 1):
        ss = sentences(line)
        if not lfs:
            # fragment runs, per line: a pair or a triple of short sentences is a NOTE (a deliberate
            # pair that lands an emotion, Reed 2026-09-14; a triple that sounds like a person talking,
            # "First of all. Hell no. Red flag.", Reed 2026-09-17: "my mom would say that");
            # four or more in a row is a hard FAIL
            run = []
            for s in ss:
                n = len(s.split())
                if n < 6:
                    run.append(s)
                    if len(run) == 2:
                        soft.append(f"L{ln} FRAGMENT PAIR (ok if intentional): {' '.join(run)}")
                    elif len(run) == 3:
                        soft.append(f"L{ln} FRAGMENT TRIPLE (ok if it's how she'd say it): {' '.join(run)}")
                    elif len(run) >= 4:
                        hard.append(f"L{ln} FRAGMENT RUN: {' '.join(run)}")
                else:
                    run = []
        # repeated shape: 3 sentences in a row starting with same 2 words (both formats)
        for i in range(len(ss) - 2):
            heads = [' '.join(x.lower().split()[:2]) for x in ss[i:i+3]]
            if len(set(heads)) == 1 and heads[0]:
                msg = f"L{ln} REPEATED SHAPE: {' | '.join(ss[i:i+3])}"
                (soft if lfs else hard).append(msg + (" (a refrain is allowed once per piece)" if lfs else ""))
    for ln, line in enumerate(lines, 1):
        caps = [w for w in re.findall(r'\b[A-Z]{3,}\b', line) if w not in CAPS_OK]
        if lfs:
            # read, not spoken: digits and $ are receipts; caps are emphasis, noted not failed;
            # nothing in the body may look like an ad
            if caps: soft.append(f"L{ln} CAPS {caps} (emphasis on the page is allowed once or twice): {line[:80]}")
            bare = line.strip().lstrip('*').strip()
            is_ps = re.match(r'^(P\.)+S\.', bare) is not None
            if FORMATTING.search(line) and not is_ps and not bare.startswith(("http","👉","[http")):
                hard.append(f"L{ln} FORMATTING IN BODY (headers, bullets, bold, emoji): {line[:80]}")
        else:
            # digits are allowed in a spoken script (Reed, 2026-09-21): MiniMax reads them fine,
            # so "50 feet" and "I-70" are no longer failures. Spelling them out is still fine, never required.
            if re.search(r'[$%]', line): hard.append(f"L{ln} SYMBOL: {line[:80]}")
            if caps: hard.append(f"L{ln} ALL CAPS {caps}: {line[:80]}")
    low = text.lower()
    if lfs:
        # LFS report: the ratios LFS.md §5 cares about, as information
        def first_pct(pat):
            c = 0
            for l in lines:
                if re.search(pat, l, re.I): return round(100*c/max(words,1))
                c += len(l.split())
            return None
        you = first_pct(r"I'm telling you this|I'm writing this|you're reading this|you are reading this|^\s*if you're|^\s*if your\b|^\s*if you\b")
        prod = first_pct(r"palace guard")
        walls = [ln for ln, l in enumerate(lines, 1) if len(l.split()) > 70]
        dashes = text.count('—') + text.count(' - ')
        stum = len(STUMBLE.findall(text))
        soft.append(f"WORDS: {words}  ~{words/230:.0f} min read @230wpm  paragraphs: {len(lines)}")
        soft.append(f"FIRST LINE TO THE READER: {you}%  (winners: ~85%+)   FIRST 'Palace Guard': {prod}%  (indirect: 60-78%)")
        if walls: soft.append(f"WALL PARAGRAPHS (>70 words) at L{walls} — break them")
        soft.append(f"EM-DASHES: {dashes} ({dashes/max(words,1)*1000:.1f} per 1000; winners 10-16)")
        if stum: soft.append(f"STUMBLES: {stum} (spoken tic; on the page these read as typos)")
        fill = sum(low.count(f) for f in ("um,","uh,"))
        if fill: soft.append(f"SPOKEN FILLER (um/uh): {fill} — not for the page")
        if not re.search(r"^\s*\**P\.S\.", text, re.M): soft.append("NO P.S. STACK found (every LFS gets one, LFS.md §8)")
    else:
        # whole-word match, so "bout" no longer hits every "about" and "kind of" skips "the kind of girl" (2026-10-18)
        def _count(f):
            f = f.strip()
            if f == "-ish": return low.count("-ish")
            if f == "kind of": return len(re.findall(r"(?<![a-z])kind of(?! (?:girl|guy|man|woman|thing|person|people|place))", low))
            return len(re.findall(r"(?<![a-z])" + re.escape(f) + r"(?![a-z])", low))
        fill = sum(_count(f) for f in FILLERS) + sum(low.count(f) for f in ("um,", "uh,", ", like,", " like, "))
        stum = len(STUMBLE.findall(text))
        hook = (lines[0] if lines else "").lower()
        # Reed, 2026-10-16: "add some filler words here and there, like, um, and" -- aim 4-8 per script, never in the hook or the product facts
        if fill < 4: soft.append(f"FILLERS: {fill} (too clean: add um / like / and here and there, aim 4-8, Reed 2026-10-16)")
        elif fill > 10: soft.append(f"FILLERS: {fill} (over 10 reads as a tic; aim 4-8)")
        else: soft.append(f"FILLERS: {fill} (in range 4-8)")
        if any(f in hook for f in ("um,", "uh,", " like,")): soft.append("FILLER IN THE HOOK: take it out")
        if stum > 1: soft.append(f"STUMBLES: {stum} (budget 1, persona may override)")
        soft.append(f"WORDS: {words}  ~{words/190*60:.0f}s @190wpm  ~{words/160*60:.0f}s @160wpm")
    return hard, soft, words


SPEAKER = re.compile(r"^\s*([A-Z][\w .'-]{0,40}?)\s*(\((?:V\.O\.|O\.S\.|[^)]{0,20})\))?\s*:\s*(.*)$")

def scan_movie(text):
    """Movie mode (movie.md): banned words fail anywhere, speech or direction. Symbols and ALL CAPS fail in speech.
    Fragment runs and repeated shapes are off: dialogue is short by nature."""
    hard, soft = [], []
    lines = [l for l in text.splitlines() if l.strip()]
    speech_words, speakers, scenes = 0, {}, 0
    for ln, line in enumerate(lines, 1):
        hits = BANNED.findall(line)
        if hits:
            hard.append(f"L{ln} BANNED WORD {sorted(set(h[0] if isinstance(h, tuple) else h for h in hits))}: say 'assaulted' or 'abducted', imply death: {line[:90]}")
        bare = line.strip()
        if bare.startswith("["):
            scenes += 1; continue
        if bare.startswith("("):
            continue
        m = SPEAKER.match(line)
        who, said = (m.group(1).strip(), m.group(3)) if m else ("(unlabeled)", bare)
        said = re.sub(r"\([^)]*\)", "", said)
        speakers[who] = speakers.get(who, 0) + len(said.split())
        speech_words += len(said.split())
        if re.search(r"[$%]", said): hard.append(f"L{ln} SYMBOL: {line[:80]}")
        caps = [w for w in re.findall(r"\b[A-Z]{3,}\b", said) if w not in CAPS_OK]
        if caps: hard.append(f"L{ln} ALL CAPS {caps}: {line[:80]}")
    soft.append(f"SCENES: {scenes}  SPOKEN WORDS: {speech_words}  ~{speech_words/160:.1f} min @160wpm")
    soft.append("SPEAKERS: " + ", ".join(f"{k} {v}w" for k, v in sorted(speakers.items(), key=lambda x: -x[1])))
    return hard, soft, speech_words


def norm(s):
    """Shared normalization: strip Notion markup, cut at Primary Text, drop **header** lines, collapse whitespace."""
    s = re.sub(r'<[^>]+>', ' ', s)
    s = s.split('**Primary Text:**')[0]
    s = '\n'.join(l for l in s.splitlines() if not l.strip().startswith('**') and l.strip() not in ('---',))
    return re.sub(r'\s+', ' ', s).strip()

def token_path():
    return os.path.expanduser("~/.claude/ecom-speech-gate.json")

def record_pass(text):
    h = hashlib.sha256(norm(text).encode()).hexdigest()
    p = token_path()
    data = {}
    if os.path.exists(p):
        try: data = json.load(open(p))
        except Exception: data = {}
    data[h] = time.time()
    # keep last 20
    for k in sorted(data, key=data.get)[:-20]: del data[k]
    json.dump(data, open(p, 'w'))
    return h

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    text = open(sys.argv[1]).read()
    lfs = "--lfs" in sys.argv
    movie = "--movie" in sys.argv
    hard, soft, _ = scan_movie(text) if movie else scan(text, lfs=lfs)
    print("MODE:", "MOVIE (scenes, several speakers)" if movie else "LFS (read)" if lfs else "SCRIPT (spoken)")
    for h in hard: print("FAIL", h)
    for s in soft: print("NOTE", s)
    if hard:
        print(f"\n{len(hard)} hard fail(s). Fix and rescan."); sys.exit(1)
    print("\nCLEAN.")
    if "--pass" in sys.argv:
        print("pass token:", record_pass(text)[:12])
