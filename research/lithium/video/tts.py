import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from narration import SCENES
VOICE, SPEED = "af_heart", 1.04
k = Kokoro("models/kokoro.onnx", "models/voices.bin")
SR = 24000
LEAD, GAP_LINE, GAP_SCENE, TAIL = 0.7, 0.35, 0.75, 3.0
audio = [np.zeros(int(LEAD*SR), dtype=np.float32)]; t = LEAD; timing = []
for si,(sid, title, lines) in enumerate(SCENES):
    sc = {"id": sid, "title": title, "start": round(t - (LEAD if si==0 else 0.35), 3), "lines": []}
    for li, text in enumerate(lines):
        s, sr = k.create(text, voice=VOICE, speed=SPEED, lang="en-us"); assert sr == SR
        s = s.astype(np.float32)
        sc["lines"].append({"t": round(t, 3), "d": round(len(s)/SR, 3), "text": text})
        audio.append(s); t += len(s)/SR
        g = GAP_LINE if li < len(lines)-1 else (GAP_SCENE if si < len(SCENES)-1 else TAIL)
        audio.append(np.zeros(int(g*SR), dtype=np.float32)); t += g
    sc["end"] = round(t - 0.35 if si < len(SCENES)-1 else t, 3)
    timing.append(sc)
wav = np.concatenate(audio)
peak = np.abs(wav).max(); wav = wav / peak * 0.89
sf.write("narration.wav", wav, SR)
json.dump({"total": round(t,3), "voice": VOICE, "scenes": timing}, open("timing.json","w"), indent=1)
print("total", round(t,1), "s")
for sc in timing: print(sc["id"], sc["start"], sc["end"])
