"""Narration for the films, with the speech model that is already in this workspace (Kokoro v1.0, voice "af_heart": a machine voice under an open licence, put here on 14 November for the course films).
Nothing is downloaded.  Each line is made once and kept (build/voice/<hash>.wav).

A voice from outside replaces it (24 November 2026: the owner turned the model's voice down three times).  When course/voice.json names a voice, every
say() and tell() is a take: a recording of exactly those words, kept in course/narration/takes/ under a name made from the words, with the time of every
letter beside it.  Nothing is guessed from pauses then, and a film that asks for words with no take stops and says which.  course/VOICE.md has the route.
VOICE_ORDER=<file> lists every passage the films ask for instead of speaking it; VOICE_MODEL=1 builds with the model's voice whatever voice.json says."""
import os, re, sys, json, math, atexit, hashlib, subprocess, numpy as np, soundfile as sf
TTS = "/home/claude/course/tts/"; VOICE = "af_heart"; SPEED = 0.92; OUT = "build/voice"; SR = 24000; GAIN = 1.0; os.makedirs(OUT, exist_ok=True)
_k = None
CONF, TAKES = "course/voice.json", "course/narration/takes"
ORDER = os.environ.get("VOICE_ORDER")
TAKE = None if os.environ.get("VOICE_MODEL") or not os.path.exists(CONF) else json.load(open(CONF))                # the chosen voice: {"voice": its name, "id": ..., "model": ...}
if TAKE or ORDER: VOICE = "take:" + str((TAKE or {}).get("id", "order")); SPEED = 1.0; SR = 48000              # a take keeps its own pace, and all of its sound
film = ""; _asked = {}                           # order mode: which film is asking; what has been asked for
NUM = {"1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten", "12": "twelve"}
SAY = [(r"\bCURVE 35\b", "Curve thirty-five"), (r"\b35 mm\b", "thirty-five millimetre"), (r"\bISO\b", "I S O"), (r"f/120\b", "f one twenty"), (r"f/16\b", "f sixteen"), (r"f/11\b", "f eleven"), (r"f/8\b", "f eight"),
       (r"(\d) ?mm\b", r"\1 millimetres"), (r"\bc\. ", "around "), (r"\bBC\b", "B C"), (r"Nicéphore Niépce", "Nee-say-for Nee-eps"), (r"\bMozi\b", "Moh-dzuh"), (r"\bLeuven\b", "Lurven"), (r"\b1544\b", "fifteen forty-four"),
       (r"\b1550 to 1568\b", "fifteen fifty to fifteen sixty-eight"), (r"\b1604\b", "sixteen oh four"), (r"\b1826 or 1827\b", "eighteen twenty-six or twenty-seven"), (r"\b1021\b", "ten twenty-one"), (r"\b2,400\b", "two thousand four hundred"),
       (r"\b1/300\b", "one three-hundredth"), (r"\((.*?)\)", r", \1,"), (r"\s+", " ")]
_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
def _two(n): return _ONES[n] if n < 20 else _TENS[n // 10] + ("-" + _ONES[n % 10] if n % 10 else "")
def _year(m):                                   # a year as people say it: 1727 seventeen twenty-seven, 1900 nineteen hundred, 1907 nineteen oh seven, 2006 two thousand six
    y = int(m.group(0)); hi, lo = divmod(y, 100)
    if 2000 <= y < 2010: return "two thousand" + (" " + _ONES[lo] if lo else "")
    return _two(hi) + (" hundred" if lo == 0 else " oh " + _ONES[lo] if lo < 10 else " " + _two(lo))
def speakable(t):
    for a, b in SAY: t = re.sub(a, b, t)
    t = re.sub(r"(?<![\d.,$])\b(1[0-9]\d\d|20[0-2]\d)\b(?![\d.,]\d)(?!\s*(mm|m|s|g|N|%|pictures|rays|cases|positions|million|turns|layers))", _year, t)      # v2.14: the voice read "By 1727," as a plain number
    return t.strip()
def use(voice, speed):
    """another voice for the films that ask for one: a name, or a blend such as 'af_bella:0.6+af_heart:0.4'.  The cache key carries both, so two voices never share a line"""
    global VOICE, SPEED
    if TAKE or ORDER: return                     # one voice from outside tells every film
    VOICE, SPEED = voice, speed
def _style(v):
    if ":" not in v: return v
    parts = [p.split(":") for p in v.split("+")]; tot = sum(float(w) for _, w in parts)
    return sum(_k.get_voice_style(n) * np.float32(float(w) / tot) for n, w in parts)
def master(wav, out):
    """a narration track made easy to listen to: no hard clip.  Rumble off, a little warmth, the harsh band and the s sounds eased, gentle compression,
    then loudness set to -16 LUFS with peaks under -1.5 dB (two passes, so the gain is one number for the whole film and nothing pumps).  48 kHz out."""
    pre = "highpass=f=75,equalizer=f=210:t=q:w=0.9:g=1.5,equalizer=f=3400:t=q:w=1.4:g=-1,deesser=i=0.4:m=0.5:f=0.5,acompressor=threshold=-21dB:ratio=2.2:attack=10:release=150:makeup=1.5"
    if TAKE: pre = "highpass=f=60"               # a take is already a finished voice: only its level is set (the shaping above was fitted to the model's voice, by numbers)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af", pre + ",loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True, check=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    ln = f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
    tmp = out[:-4] + ".part.wav"; subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-af", pre + "," + ln, "-ar", "48000", "-ac", "1", tmp], check=True); os.replace(tmp, out); return out
def take_id(kind, texts): return hashlib.sha1((kind + "\n" + "\n".join(texts)).encode()).hexdigest()[:16]
def _ask(kind, texts):
    if ORDER is None: return
    if not _asked: atexit.register(lambda: json.dump(list(_asked.values()), open(ORDER, "w"), indent=1))
    r = _asked.setdefault(take_id(kind, texts), dict(id=take_id(kind, texts), kind=kind, text=" ".join(texts), pieces=len(texts), films=[]))
    if film and film not in r["films"]: r["films"].append(film)
def _standin(kind, texts):
    """order mode: silence as long as the words would take, so a film can be planned before a word of it is recorded"""
    d = 0.5 + 0.38 * sum(len(t.split()) for t in texts); os.makedirs(f"{OUT}/_order", exist_ok=True); f = f"{OUT}/_order/{take_id(kind, texts)}.wav"; n = [max(1, len(t)) for t in texts]
    if not os.path.exists(f): sf.write(f, np.zeros(int(d * SR), np.float32), SR)
    return f, d, [d * sum(n[:i + 1]) / sum(n) for i in range(len(n))]
def tidy(sp):
    """words as a take is asked for them: speakable() leaves " , seen from behind,." where a bracket was, which the model's voice read well enough"""
    return re.sub(r",+(?=[.?!;:])", "", re.sub(r",(\s*,)+", ",", re.sub(r"\s+(?=[,.;:?!])", "", sp))).strip()
def letter_times(al, text):
    """the time the service gave for every letter of `text` -> ([start], [end]) by place in text (None at a blank), or None if what came back is not these letters"""
    ch, t0, t1 = (al.get(k) or [] for k in ("characters", "character_start_times_seconds", "character_end_times_seconds"))
    got = [(c, a, b) for c, a, b in zip(ch, t0, t1) if not c.isspace()]; at = [i for i, c in enumerate(text) if not c.isspace()]
    if not len(ch) == len(t0) == len(t1) or len(got) != len(at) or any(g[0] != text[i] for g, i in zip(got, at)): return None
    S = [None] * len(text); E = [None] * len(text)
    for (c, a, b), i in zip(got, at): S[i] = a; E[i] = b
    return S, E
def _take(kind, texts):
    """the take of these words -> (where its sound is kept at SR, cut to the speech; seconds before that cut, on the take's own clock; what came with it), or None if there is none in the chosen voice.
    A short line may be part of a longer recording (several lines said in one go): its note then names that file and where the line lies in it"""
    i = take_id(kind, texts); j = f"{TAKES}/{i}.json"
    if not os.path.exists(j): return None
    m = json.load(open(j)); src = f"{TAKES}/{m['file']}" if m.get("file") else next((f"{TAKES}/{i}.{x}" for x in ("mp3", "wav", "m4a", "ogg") if os.path.exists(f"{TAKES}/{i}.{x}")), None)
    if src is None or not os.path.exists(src) or (TAKE and m.get("voice_id") != TAKE.get("id")): return None
    st = os.stat(src); f = f"{OUT}/k_{i}_{st.st_size:x}{int(st.st_mtime):x}.wav"                                     # a take made again is a new file here
    if not (os.path.exists(f) and os.path.exists(f[:-4] + ".cut")):
        a = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)
        b0 = int(m.get("from", 0) * SR); a = a[b0:int(m["to"] * SR) if m.get("to") else len(a)]
        on = np.nonzero(np.abs(a) > 0.01)[0]; i0 = max(0, on[0] - int(0.06 * SR)) if len(on) else 0; i1 = min(len(a), on[-1] + int(0.06 * SR)) if len(on) else len(a)
        sf.write(f, a[i0:i1], SR); open(f[:-4] + ".cut", "w").write(str((b0 + i0) / SR))
    return f, float(open(f[:-4] + ".cut").read()), m
def _ends(m, texts, cut, d):
    """when each piece ends, from the time the service gave for every letter: midway between a piece's last letter and the next one's first.
    None if the letters that came back are not the words that were sent (the pauses are used then)"""
    lt = letter_times(m.get("alignment") or {}, " ".join(texts))
    if lt is None: return None
    S, E = lt; out = []; n = 0
    for p in texts[:-1]: n += len(p); out.append(min(d, max(out[-1] if out else 0.0, (E[n - 1] + S[n + 1]) / 2 - cut))); n += 1
    return out + [d]
def _none(texts): sys.exit(f"voice: no take in the chosen voice ({TAKE.get('voice')}) for \"{' '.join(texts)[:70]}...\" (take {take_id('tell', texts)} or {take_id('say', texts)}).  python3 course/voicekit/takes.py status")
def own(path):
    """a person's own recording, as the films use sound: one channel at SR, cut to the speech -> file"""
    st = os.stat(path); f = f"{OUT}/o_{hashlib.sha1(path.encode()).hexdigest()[:10]}_{st.st_size:x}{int(st.st_mtime):x}_{SR}.wav"
    if not os.path.exists(f):
        a = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)
        on = np.nonzero(np.abs(a) > 0.01)[0]; sf.write(f, a[max(0, on[0] - int(0.06 * SR)):on[-1] + int(0.06 * SR)] if len(on) else a, SR)
    return f
def say(text):
    """-> (wav file, seconds).  The file is cut to the speech with 60 ms of quiet either side."""
    global _k
    sp = speakable(text); f = f"{OUT}/{hashlib.sha1((VOICE + str(SPEED) + sp).encode()).hexdigest()[:14]}.wav"
    if TAKE or ORDER:
        sp = tidy(sp); _ask("say", [sp])
        if ORDER: return _standin("say", [sp])[:2]
        got = _take("say", [sp]) or _none([sp]); return got[0], sf.info(got[0]).duration
    if not os.path.exists(f):
        if _k is None:
            from kokoro_onnx import Kokoro; _k = Kokoro(TTS + "kokoro-v1.0.int8.onnx", TTS + "voices-v1.0.bin")
        a, sr = _k.create(sp, voice=_style(VOICE), speed=SPEED, lang="en-us"); a = np.asarray(a, np.float32); assert sr == SR
        on = np.nonzero(np.abs(a) > 0.01)[0]; a = a[max(0, on[0] - 1440):min(len(a), on[-1] + 1440)] if len(on) else a; sf.write(f, a, SR)
    return f, sf.info(f).duration
def pauses(f, least=0.12):
    """the quiet runs inside a spoken file: [(middle in seconds, length in seconds)], each at least `least` long"""
    a, sr = sf.read(f, dtype="float32"); fr = int(0.01 * sr); n = len(a) // fr; q = np.sqrt((a[:n * fr].reshape(n, fr) ** 2).mean(1)) < 0.012; out = []; i = 0
    while i < n:
        if not q[i]: i += 1; continue
        j = i
        while j < n and q[j]: j += 1
        if i > 0 and j < n and (j - i) * 0.01 >= least: out.append(((i + j) * 0.005, (j - i) * 0.01))
        i = j
    return out
def align(f, pieces, t0=0.06, t1=None):
    """when each piece of a passage that was spoken in one go ends, in seconds from the start of its file (t0, t1: only the stretch of the file that holds them).
    A first guess by each piece's share of the letters, then moved to the pause the voice really left near it (the longest one, weighed against how far off it is);
    each piece is guessed from the last one found, so an error does not run on.  The model does not say when it speaks each word; its pauses do."""
    d = sf.info(f).duration if t1 is None else t1; runs = pauses(f); t = t0; out = []; n = [max(1, len(p)) for p in pieces]
    for i, p in enumerate(pieces[:-1]):
        guess = t + (d - (0.06 if t1 is None else 0) - t) * n[i] / sum(n[i:]); stop = p.rstrip()[-1:] in ".?!"; tol = 1.6 if stop else 1.0
        near = [(m, ln) for m, ln in runs if abs(m - guess) < tol and t + 0.3 < m < d - 0.3 and ln >= (0.22 if stop else 0.12)]
        t = max(near, key=lambda r: r[1] - 0.3 * abs(r[0] - guess))[0] if near else guess; out.append(t)
    return out + [d]
def short(text, most=90):
    """a sentence as captions show it: whole if it is short, else cut at the comma, colon or semicolon nearest its middle (a phone shows two lines of about 42 letters)"""
    if len(text) <= most: return [text]
    at = [m.end() for m in re.finditer(r"[,;:] ", text) if 12 < m.end() < len(text) - 12] or [m.end() for m in re.finditer(r" ", text)]
    if not at: return [text]
    i = min(at, key=lambda i: abs(i - len(text) / 2)); return short(text[:i].strip(), most) + short(text[i:].strip(), most)
def cues(f, pieces, ends, start=0.0):
    """the captions of a told passage: [(from, to, words)] in seconds of its file, each piece cut short enough to read and each cut put on the voice's pause"""
    out = []; a = start
    for p, e in zip(pieces, ends):
        sub = [x for b in re.split(r"(?<=[.?!])\s+", p) if b for x in short(b)]; se = align(f, sub, a, e) if f and len(sub) > 1 else [a + (e - a) * sum(len(x) for x in sub[:i + 1]) / sum(len(x) for x in sub) for i in range(len(sub))]
        for x, y in zip(sub, se): out.append((a, y, x)); a = y
    return out
def passages(pieces, most=48):
    """consecutive pieces gathered into passages of about `most` words at most, even in size, cut only where a sentence ends: [[index, ...], ...].
    The model hurries through a long passage (88 words came out a twelfth quicker than the same sentences alone) and starts each short one afresh;
    a few sentences at a time keeps one pace and still lets a sentence lean on the one before."""
    w = [len(p.split()) for p in pieces]; k = max(1, math.ceil(sum(w) / most)); aim = sum(w) / k; out = [[]]; acc = 0
    for i, n in enumerate(w):
        if out[-1] and len(out) < k and acc + n / 2 > aim and pieces[i - 1].rstrip()[-1:] in ".?!": out.append([]); acc = 0
        out[-1].append(i); acc += n
    return out
def tell(pieces, gap=0.5, make=True):
    """a paragraph given as its pieces (sentences, or parts of long ones), told a passage at a time -> (wav file, seconds, [when each piece ends]).
    make=False: only if it has been told before, else None."""
    if TAKE or ORDER:                                # the whole paragraph is one take, in one breath
        texts = [tidy(speakable(p)) for p in pieces]; _ask("tell", texts)
        if ORDER: return _standin("tell", texts)
        got = _take("tell", texts)
        if not got: return None if not make else _none(texts)
        f, cut, m = got; d = sf.info(f).duration; return f, d, [round(x, 3) for x in (_ends(m, texts, cut, d) or align(f, pieces))]
    f = f"{OUT}/t_{hashlib.sha1((VOICE + str(SPEED) + str(gap) + '|'.join(speakable(p) for p in pieces)).encode()).hexdigest()[:14]}.wav"; j = f[:-4] + ".json"
    if not (os.path.exists(f) and os.path.exists(j)):
        if not make: return None
        parts = []; ends = []; t = 0.0; G = passages(pieces)
        for gi, g in enumerate(G):
            w, d = say(" ".join(pieces[i] for i in g)); a, _ = sf.read(w, dtype="float32"); ends += [t + x for x in align(w, [pieces[i] for i in g])]; parts.append(a); t += len(a) / SR
            if gi < len(G) - 1: q = np.zeros(int((gap - 0.12) * SR), np.float32); parts.append(q); t += len(q) / SR; ends[-1] += len(q) / SR / 2
        sf.write(f, np.concatenate(parts), SR); json.dump([round(x, 3) for x in ends], open(j, "w"))
    return f, sf.info(f).duration, json.load(open(j))
def track(lines, seconds, path):
    """one clip's sound: each (start in seconds, wav file) laid on silence of the clip's exact length"""
    n = int(round(seconds * SR)); out = np.zeros(n, np.float32)
    for t, f in lines:
        a, _ = sf.read(f, dtype="float32"); i = int(round(t * SR)); a = a[:max(0, n - i)]; out[i:i + len(a)] += a
    sf.write(path, np.clip(out * GAIN, -0.98, 0.98), SR); return path
def join(wavs, path):
    sf.write(path, np.concatenate([sf.read(f, dtype="float32")[0] for f in wavs]), SR); return path
def mux(video, wav, out):
    tmp = out[:-4] + ".part.mp4"; subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", tmp], check=True); os.replace(tmp, out); return out
if __name__ == "__main__":
    import time; t = time.time(); f, d = say("Lower the spool, red winder up, into the round chamber on the right, seen from behind."); print(f, round(d, 2), "s of speech in", round(time.time() - t, 1), "s")
