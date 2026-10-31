"""فایل‌های صوتی کلمه‌ها را با espeak-ng (آفلاین) می‌سازد: audio/<lang>-<i>.mp3

اجرا:  python3 -m venv .venv && .venv/bin/pip install espeakng-loader
       .venv/bin/python tools/make_audio.py      (ffmpeg لازم است)
"""
import ctypes, os, subprocess, sys, wave, array
import espeakng_loader as E

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "audio")
# متن برای خواندن (عربی با اعراب برای تلفظ بهتر). ترتیب: سلام، حالت چطوره، ممنون، بله، نه، لطفاً، خداحافظ، دوست، آب، یک دو سه
WORDS = {
  "fa": ("fa", ["سلام", "حالت چطوره؟", "ممنون", "بله", "نه", "لطفاً", "خداحافظ", "دوست", "آب", "یک، دو، سه"]),
  "ar": ("ar", ["مَرْحَبَا", "كَيْفَ حَالُكَ؟", "شُكْرًا", "نَعَمْ", "لَا", "مِنْ فَضْلِكَ", "مَعَ السَّلَامَةِ", "صَدِيق", "مَاء", "وَاحِد، اِثْنَان، ثَلَاثَة"]),
  "ku": ("ku", ["Slaw", "Çonî?", "Supas", "Belê", "Nexêr", "Tikaye", "Xwat legel", "Hawrê", "Aw", "Yek, dû, sê"]),
  "tr": ("tr", ["Merhaba", "Nasılsın?", "Teşekkürler", "Evet", "Hayır", "Lütfen", "Hoşça kal", "Arkadaş", "Su", "Bir, iki, üç"]),
  # عبری espeak با دگش/نقطهٔ شین درست کار نمی‌کند؛ دو کلمه با صدای ایتالیایی و حروف لاتین خوانده می‌شوند
  "he": ("he", ["שלום", "מה שלומך?", "תודה", "כן", "לא", ("it", "bevacàscia"), ("it", "leitraòt"), "חָבֵר", "מים", "אַחַת, שתיים, שלוש"]),
  "el": ("el", ["Γεια σου", "Τι κάνεις;", "Ευχαριστώ", "Ναι", "Όχι", "Παρακαλώ", "Αντίο", "Φίλος", "Νερό", "Ένα, δύο, τρία"]),
}
# «حالت چطوره؟» به لهجه‌ها
EXTRA = {"ar-how-iq": ("ar", "شْلُونَكْ؟"), "ar-how-lev": ("ar", "كِيفَكْ؟"), "ar-how-eg": ("ar", "إِزَّيَّكْ؟")}

lib = ctypes.CDLL(E.get_library_path())
SYNTH_CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)
buf = array.array("h")
@SYNTH_CB
def cb(wav, n, events):
    if n > 0: buf.extend(wav[:n])
    return 0
rate = lib.espeak_Initialize(2, 0, E.get_data_path().encode(), 0)  # AUDIO_OUTPUT_SYNCHRONOUS
lib.espeak_SetSynthCallback(cb)

def synth(voice, text, path):
    del buf[:]
    if lib.espeak_SetVoiceByName((voice + "+f3").encode()) != 0:
        sys.exit(f"voice {voice} not found")
    lib.espeak_SetParameter(1, 135, 0)   # سرعت
    lib.espeak_SetParameter(3, 62, 0)    # زیر و بمی (کمی زیرتر، بامزه‌تر)
    t = text.encode("utf-8")
    lib.espeak_Synth(t, len(t) + 1, 0, 0, 0, 0x01, None, None)  # espeakCHARS_UTF8
    lib.espeak_Synchronize()
    tmp = path + ".wav"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(buf.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af", "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,volume=1.6",
                    "-ac", "1", "-ar", "22050", "-b:a", "40k", path], check=True)
    os.remove(tmp)

os.makedirs(OUT, exist_ok=True)
for lk, (voice, words) in WORDS.items():
    for i, w in enumerate(words):
        v, t = w if isinstance(w, tuple) else (voice, w)
        synth(v, t, os.path.join(OUT, f"{lk}-{i}.mp3"))
for name, (voice, w) in EXTRA.items():
    synth(voice, w, os.path.join(OUT, f"{name}.mp3"))
print("done:", len(os.listdir(OUT)), "files")
