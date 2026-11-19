"""Narration for the films, with the speech model that is already in this workspace (Kokoro v1.0, voice "af_heart": a machine voice under an open licence, put here on 14 November for the course films).
Nothing is downloaded.  Each line is made once and kept (build/voice/<hash>.wav).  A human voice can replace any line later: put a recording at the same file name."""
import os, re, json, hashlib, subprocess, numpy as np, soundfile as sf
TTS = "/home/claude/course/tts/"; VOICE = "af_heart"; SPEED = 1.0; OUT = "build/voice"; SR = 24000; GAIN = 1.25; os.makedirs(OUT, exist_ok=True)
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
def say(text):
    """-> (wav file, seconds).  The file is cut to the speech with 60 ms of quiet either side."""
    global _k
    sp = speakable(text); f = f"{OUT}/{hashlib.sha1((VOICE + str(SPEED) + sp).encode()).hexdigest()[:14]}.wav"
    if not os.path.exists(f):
        if _k is None:
            from kokoro_onnx import Kokoro; _k = Kokoro(TTS + "kokoro-v1.0.int8.onnx", TTS + "voices-v1.0.bin")
        a, sr = _k.create(sp, voice=VOICE, speed=SPEED, lang="en-us"); a = np.asarray(a, np.float32); assert sr == SR
        on = np.nonzero(np.abs(a) > 0.01)[0]; a = a[max(0, on[0] - 1440):min(len(a), on[-1] + 1440)] if len(on) else a; sf.write(f, a, SR)
    return f, sf.info(f).duration
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
    import time; t = time.time(); f, d = say("Slide the spool, big red knob up, into the round chamber on the right, seen from behind."); print(f, round(d, 2), "s of speech in", round(time.time() - t, 1), "s")
