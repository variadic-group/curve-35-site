"""Narration for the films, with the speech model that is already in this workspace (Kokoro v1.0, voice "af_heart": a machine voice under an open licence, put here on 14 November for the course films).
Nothing is downloaded.  Each line is made once and kept (build/voice/<hash>.wav).  A human voice can replace any line later: put a recording at the same file name."""
import os, re, json, math, hashlib, subprocess, numpy as np, soundfile as sf
TTS = "/home/claude/course/tts/"; VOICE = "af_heart"; SPEED = 0.92; OUT = "build/voice"; SR = 24000; GAIN = 1.0; os.makedirs(OUT, exist_ok=True)
_k = None
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
    global VOICE, SPEED; VOICE, SPEED = voice, speed
def _style(v):
    if ":" not in v: return v
    parts = [p.split(":") for p in v.split("+")]; tot = sum(float(w) for _, w in parts)
    return sum(_k.get_voice_style(n) * np.float32(float(w) / tot) for n, w in parts)
def master(wav, out):
    """a narration track made easy to listen to: no hard clip.  Rumble off, a little warmth, the harsh band and the s sounds eased, gentle compression,
    then loudness set to -16 LUFS with peaks under -1.5 dB (two passes, so the gain is one number for the whole film and nothing pumps).  48 kHz out."""
    pre = "highpass=f=75,equalizer=f=210:t=q:w=0.9:g=1.5,equalizer=f=3400:t=q:w=1.4:g=-1,deesser=i=0.4:m=0.5:f=0.5,acompressor=threshold=-21dB:ratio=2.2:attack=10:release=150:makeup=1.5"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af", pre + ",loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True, check=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    ln = f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
    tmp = out[:-4] + ".part.wav"; subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-af", pre + "," + ln, "-ar", "48000", "-ac", "1", tmp], check=True); os.replace(tmp, out); return out
def say(text):
    """-> (wav file, seconds).  The file is cut to the speech with 60 ms of quiet either side."""
    global _k
    sp = speakable(text); f = f"{OUT}/{hashlib.sha1((VOICE + str(SPEED) + sp).encode()).hexdigest()[:14]}.wav"
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
