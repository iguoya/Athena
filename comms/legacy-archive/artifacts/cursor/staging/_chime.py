# -*- coding: utf-8 -*-
import math, struct, tempfile, wave, os

path = tempfile.mktemp(suffix=".wav")
rate, seconds = 22050, 5.2
melody = [
    (523.25, 0.00, 0.22),
    (659.25, 0.22, 0.22),
    (783.99, 0.44, 0.22),
    (1046.50, 0.66, 0.36),
    (783.99, 1.10, 0.18),
    (880.00, 1.28, 0.18),
    (987.77, 1.46, 0.18),
    (1046.50, 1.64, 0.40),
    (659.25, 2.20, 0.18),
    (698.46, 2.38, 0.18),
    (783.99, 2.56, 0.18),
    (880.00, 2.74, 0.18),
    (987.77, 2.92, 0.18),
    (1046.50, 3.10, 0.18),
    (1174.66, 3.28, 0.22),
    (1318.51, 3.50, 0.55),
    (1046.50, 4.20, 0.20),
    (1318.51, 4.40, 0.20),
    (1567.98, 4.60, 0.55),
]
with wave.open(path, "w") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    nframes = int(rate * seconds)
    for i in range(nframes):
        t = i / rate
        sample = 0.0
        for freq, start, dur in melody:
            if not (start <= t < start + dur):
                continue
            local = t - start
            attack = min(1.0, local * 40)
            release = max(0.0, 1.0 - max(0.0, local - (dur - 0.06)) / 0.06)
            env = attack * release * math.exp(-2.2 * local)
            tone = math.sin(2 * math.pi * freq * local)
            tone += 0.22 * math.sin(2 * math.pi * freq * 2 * local)
            sample += env * tone
        for beat in (0.0, 0.44, 0.88, 1.32, 1.76, 2.20, 2.64, 3.08, 3.52, 4.20, 4.60):
            d = t - beat
            if 0 <= d < 0.04:
                sample += (1.0 - d / 0.04) * 0.35 * math.sin(2 * math.pi * 90 * d)
        sample = int(max(-1.0, min(1.0, sample * 0.32)) * 32767)
        w.writeframes(struct.pack("<h", sample))
try:
    import winsound

    winsound.PlaySound(path, winsound.SND_FILENAME)
finally:
    os.remove(path)
