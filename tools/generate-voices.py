#!/usr/bin/env python3
"""Generate the missing Spiraling voice lines through the ElevenLabs API (works on the free plan).

The API key is read from the macOS Keychain (service "elevenlabs"), never from this file.
Kait stores it once herself:
    security add-generic-password -a "$USER" -s elevenlabs -w
(macOS then asks for the key; paste it there.)

Usage:  python3 tools/generate-voices.py            # makes every line that is not in audio/raw yet
        python3 tools/generate-voices.py --list     # just list the voices in the account
Then:   ./process-voices.sh
"""
import json, os, subprocess, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "audio", "raw")
API = "https://api.elevenlabs.io/v1"
MODEL = "eleven_v3"

LINES = {
    # file name: (character, text)
    "vo-doctor-wake":     ("doctor",   "[softly] Shh. Don't move yet. [pause] Good morning. [long pause] You died again."),
    "vo-doctor-pump":     ("doctor",   "Your heart is only a pump. Your brain is only a current. We can build you better ones."),
    "vo-doctor-choose":   ("doctor",   "[softly] Which part of you shall we improve today? [pause] Choose. It is safe."),
    "vo-doctor-palms":    ("doctor",   "[pleased] Good. Now you can feel where the current wants to go."),
    "vo-doctor-eyes":     ("doctor",   "[quietly] Hold still. You will see everything."),
    "vo-doctor-again":    ("doctor",   "[patiently] There you are. [pause] Let's try again."),
    "vo-doctor-remember": ("doctor",   "[softly] There. Do you remember now? [pause] Don't worry. It will pass."),
    "vo-facility-01":     ("facility", "Patient awake. Resurrection complete. To earn your second life, you must become... the perfect machine."),
    "vo-facility-death":  ("facility", "Subject deceased. Returning to storage."),
    "vo-facility-end":    ("facility", "Thank you for your attention. Please return to your bag."),
    "vo-patient-machine": ("patient",  "[whispers] i am a perfect machine."),
}

# Existing voice names to use first; if missing, the voice is designed from the prompt and saved.
VOICES = {
    "doctor":   ("Spiraling Doctor", None, {"stability": 0.5, "similarity_boost": 0.75}),
    "facility": ("Spiraling Facility",
                 "A genderless synthetic public-address voice from an old hospital intercom. Flat, polite, institutional, "
                 "perfectly even pacing, no emotion at all. Slightly metallic. Clear diction, like an automated announcement in an empty building.",
                 {"stability": 0.85, "similarity_boost": 0.7}),
    "patient":  ("Spiraling Patient",
                 "A young man in his twenties, hoarse and exhausted, whispering. Breathy, close to the microphone, slightly trembling.",
                 {"stability": 0.4, "similarity_boost": 0.75}),
}


def key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if k:
        return k
    try:
        return subprocess.check_output(["security", "find-generic-password", "-s", "elevenlabs", "-w"], text=True).strip()
    except subprocess.CalledProcessError:
        sys.exit("No ElevenLabs key found. Store it once with:\n  security add-generic-password -a \"$USER\" -s elevenlabs -w")


def call(method, path, body=None, raw=False):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
            return data if raw else json.loads(data)
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs {method} {path} failed: {e.code} {e.read().decode()[:400]}")


def find_or_design(character):
    name, prompt, _ = VOICES[character]
    voices = call("GET", "/voices")["voices"]
    for v in voices:
        if v["name"].strip().lower() == name.lower():
            return v["voice_id"]
    if not prompt:
        sys.exit(f'Voice "{name}" not found in the account. Voices: ' + ", ".join(v["name"] for v in voices))
    print(f"Designing {name} ...")
    sample = "Patient awake. Resurrection complete. Please remain still while the procedure begins. Thank you for your cooperation."
    prev = call("POST", "/text-to-voice/create-previews", {"voice_description": prompt, "text": sample})
    gid = prev["previews"][0]["generated_voice_id"]
    made = call("POST", "/text-to-voice/create-voice-from-preview",
                {"voice_name": name, "voice_description": prompt, "generated_voice_id": gid})
    return made["voice_id"]


if __name__ == "__main__":
    KEY = key()
    if "--list" in sys.argv:
        for v in call("GET", "/voices")["voices"]:
            print(v["voice_id"], v["name"])
        sys.exit()
    os.makedirs(RAW, exist_ok=True)
    ids = {}
    for fname, (character, text) in LINES.items():
        out = os.path.join(RAW, fname + ".mp3")
        if os.path.exists(out):
            continue
        if character not in ids:
            ids[character] = find_or_design(character)
        print(f"Generating {fname} ...")
        audio = call("POST", f"/text-to-speech/{ids[character]}?output_format=mp3_44100_128",
                     {"text": text, "model_id": MODEL, "voice_settings": VOICES[character][2]}, raw=True)
        with open(out, "wb") as f:
            f.write(audio)
    print("Done. Now run ./process-voices.sh")
