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


# ================== اروپا: کلمه‌ها، صدا و تلفظ خودکار ==================
# Europe: words, audio, and pronunciation (Persian letters + Latin respelling) generated from espeak's IPA
# code: (espeak voice, Persian name, English name, device TTS code, [10 words], optional notes {index: (fa, en)})
EU = {
  "sq": ("sq", "آلبانیایی", "Albanian", "sq-AL", ["Përshëndetje", "Si je?", "Faleminderit", "Po", "Jo", "Të lutem", "Mirupafshim", "Mik", "Ujë", "Një, dy, tre"]),
  "ca": ("ca", "کاتالان", "Catalan", "ca-ES", ["Hola", "Com estàs?", "Gràcies", "Sí", "No", "Si us plau", "Adéu", "Amic", "Aigua", "Un, dos, tres"]),
  "de": ("de", "آلمانی", "German", "de-DE", ["Hallo", "Wie geht's?", "Danke", "Ja", "Nein", "Bitte", "Tschüss", "Freund", "Wasser", "Eins, zwei, drei"]),
  "be": ("be", "بلاروسی", "Belarusian", "be-BY", ["Прывітанне", "Як справы?", "Дзякуй", "Так", "Не", "Калі ласка", "Да пабачэння", "Сябар", "Вада", "Адзін, два, тры"]),
  "ru": ("ru", "روسی", "Russian", "ru-RU", ["Привет", "Как дела?", "Спасибо", "Да", "Нет", "Пожалуйста", "До свидания", "Друг", "Вода", "Один, два, три"]),
  "nl": ("nl", "هلندی", "Dutch", "nl-NL", ["Hallo", "Hoe gaat het?", "Dank je", "Ja", "Nee", "Alsjeblieft", "Tot ziens", "Vriend", "Water", "Een, twee, drie"]),
  "fr": ("fr", "فرانسوی", "French", "fr-FR", ["Bonjour", "Comment ça va ?", "Merci", "Oui", "Non", "S'il vous plaît", "Au revoir", "Ami", "Eau", "Un, deux, trois"]),
  "bs": ("bs", "بوسنیایی", "Bosnian", "bs-BA", ["Zdravo", "Kako si?", "Hvala", "Da", "Ne", "Molim", "Doviđenja", "Prijatelj", "Voda", "Jedan, dva, tri"]),
  "bg": ("bg", "بلغاری", "Bulgarian", "bg-BG", ["Здравей", "Как си?", "Благодаря", "Да", "Не", "Моля", "Довиждане", "Приятел", "Вода", "Едно, две, три"]),
  "hr": ("hr", "کرواتی", "Croatian", "hr-HR", ["Bok", "Kako si?", "Hvala", "Da", "Ne", "Molim", "Doviđenja", "Prijatelj", "Voda", "Jedan, dva, tri"]),
  "cs": ("cs", "چکی", "Czech", "cs-CZ", ["Ahoj", "Jak se máš?", "Děkuji", "Ano", "Ne", "Prosím", "Na shledanou", "Přítel", "Voda", "Jedna, dva, tři"]),
  "da": ("da", "دانمارکی", "Danish", "da-DK", ["Hej", "Hvordan har du det?", "Tak", "Ja", "Nej", "Vær så venlig", "Farvel", "Ven", "Vand", "En, to, tre"]),
  "et": ("et", "استونیایی", "Estonian", "et-EE", ["Tere", "Kuidas läheb?", "Aitäh", "Jah", "Ei", "Palun", "Head aega", "Sõber", "Vesi", "Üks, kaks, kolm"]),
  "fi": ("fi", "فنلاندی", "Finnish", "fi-FI", ["Hei", "Mitä kuuluu?", "Kiitos", "Kyllä", "Ei", "Ole kiltti", "Näkemiin", "Ystävä", "Vesi", "Yksi, kaksi, kolme"]),
  "sv": ("sv", "سوئدی", "Swedish", "sv-SE", ["Hej", "Hur mår du?", "Tack", "Ja", "Nej", "Snälla", "Hej då", "Vän", "Vatten", "Ett, två, tre"]),
  "hu": ("hu", "مجاری", "Hungarian", "hu-HU", ["Szia", "Hogy vagy?", "Köszönöm", "Igen", "Nem", "Kérem", "Viszlát", "Barát", "Víz", "Egy, kettő, három"]),
  "is": ("is", "ایسلندی", "Icelandic", "is-IS", ["Halló", "Hvað segirðu?", "Takk", "Já", "Nei", "Vinsamlegast", "Bless", "Vinur", "Vatn", "Einn, tveir, þrír"]),
  "ga": ("ga", "ایرلندی", "Irish", "ga-IE", ["Dia duit", "Conas atá tú?", "Go raibh maith agat", "Sea", "Ní hea", "Le do thoil", "Slán", "Cara", "Uisce", "A haon, a dó, a trí"],
         {3: ("ایرلندی کلمهٔ جداگانه‌ای برای «بله/نه» ندارد؛ «Sea» یعنی «هست».", "Irish has no single word for yes/no — “Sea” means “it is”."),
          4: ("«Ní hea» یعنی «نیست».", "“Ní hea” means “it is not”.")}),
  "en": ("en", "انگلیسی", "English", "en-GB", ["Hello", "How are you?", "Thank you", "Yes", "No", "Please", "Goodbye", "Friend", "Water", "One, two, three"]),
  "it": ("it", "ایتالیایی", "Italian", "it-IT", ["Ciao", "Come stai?", "Grazie", "Sì", "No", "Per favore", "Arrivederci", "Amico", "Acqua", "Uno, due, tre"]),
  "lv": ("lv", "لتونیایی", "Latvian", "lv-LV", ["Sveiki", "Kā tev iet?", "Paldies", "Jā", "Nē", "Lūdzu", "Uz redzēšanos", "Draugs", "Ūdens", "Viens, divi, trīs"]),
  "lt": ("lt", "لیتوانیایی", "Lithuanian", "lt-LT", ["Labas", "Kaip sekasi?", "Ačiū", "Taip", "Ne", "Prašau", "Viso gero", "Draugas", "Vanduo", "Vienas, du, trys"]),
  "lb": ("lb", "لوکزامبورگی", "Luxembourgish", "lb-LU", ["Moien", "Wéi geet et?", "Merci", "Jo", "Neen", "Wann ech gelift", "Äddi", "Frënd", "Waasser", "Eent, zwee, dräi"]),
  "mt": ("mt", "مالتی", "Maltese", "mt-MT", ["Bonġu", "Kif inti?", "Grazzi", "Iva", "Le", "Jekk jogħġbok", "Saħħa", "Ħabib", "Ilma", "Wieħed, tnejn, tlieta"]),
  "ro": ("ro", "رومانیایی", "Romanian", "ro-RO", ["Bună", "Ce faci?", "Mulțumesc", "Da", "Nu", "Te rog", "La revedere", "Prieten", "Apă", "Unu, doi, trei"]),
  "sr": ("sr", "صربی", "Serbian", "sr-RS", ["Здраво", "Како си?", "Хвала", "Да", "Не", "Молим", "Довиђења", "Пријатељ", "Вода", "Један, два, три"]),
  "cnr": ("bs", "مونته‌نگرویی", "Montenegrin", "sr-ME", ["Zdravo", "Kako si?", "Hvala", "Da", "Ne", "Molim", "Doviđenja", "Prijatelj", "Voda", "Jedan, dva, tri"]),
  "mk": ("mk", "مقدونی", "Macedonian", "mk-MK", ["Здраво", "Како си?", "Благодарам", "Да", "Не", "Те молам", "Довидување", "Пријател", "Вода", "Еден, два, три"]),
  "nb": ("nb", "نروژی", "Norwegian", "nb-NO", ["Hei", "Hvordan går det?", "Takk", "Ja", "Nei", "Vær så snill", "Ha det", "Venn", "Vann", "En, to, tre"]),
  "pl": ("pl", "لهستانی", "Polish", "pl-PL", ["Cześć", "Jak się masz?", "Dziękuję", "Tak", "Nie", "Proszę", "Do widzenia", "Przyjaciel", "Woda", "Jeden, dwa, trzy"]),
  "pt": ("pt", "پرتغالی", "Portuguese", "pt-PT", ["Olá", "Como estás?", "Obrigado", "Sim", "Não", "Por favor", "Adeus", "Amigo", "Água", "Um, dois, três"]),
  "sk": ("sk", "اسلواکی", "Slovak", "sk-SK", ["Ahoj", "Ako sa máš?", "Ďakujem", "Áno", "Nie", "Prosím", "Dovidenia", "Priateľ", "Voda", "Jeden, dva, tri"]),
  "sl": ("sl", "اسلوونیایی", "Slovenian", "sl-SI", ["Živjo", "Kako si?", "Hvala", "Ja", "Ne", "Prosim", "Nasvidenje", "Prijatelj", "Voda", "Ena, dva, tri"]),
  "es": ("es", "اسپانیایی", "Spanish", "es-ES", ["Hola", "¿Cómo estás?", "Gracias", "Sí", "No", "Por favor", "Adiós", "Amigo", "Agua", "Uno, dos, tres"]),
  "uk": ("uk", "اوکراینی", "Ukrainian", "uk-UA", ["Привіт", "Як справи?", "Дякую", "Так", "Ні", "Будь ласка", "До побачення", "Друг", "Вода", "Один, два, три"]),
  "la": ("la", "لاتین", "Latin", "la", ["Salve", "Quid agis?", "Gratias", "Ita", "Minime", "Quaeso", "Vale", "Amicus", "Aqua", "Unus, duo, tres"]),
}

# تصحیح دستی تلفظ‌هایی که خروجی خودکار خوب نبود: {زبان: {شمارهٔ کلمه: (فارسی، لاتین)}}
# Hand-fixed pronunciations where the automatic IPA conversion was poor
PRON_FIX = {
  "ga": {0:("دیا گوئیت","dee-a gwit"), 1:("کوناس آتا تو؟","kun-us a-taw too?"), 2:("گو رِو ما آگوت","guh rev mah a-gut"), 3:("شا","sha"), 4:("نی ها","nee ha"),
         5:("لِ دو هُل","leh duh hull"), 6:("سلان","slawn"), 7:("کارا","ka-ra"), 8:("ایشکه","ish-ke"), 9:("آ هین، آ دو، آ تری","a hayn, a doe, a tree")},
  "mt": {0:("بونجو","bon-joo"), 1:("کیف اینتی؟","keef in-tee?"), 2:("گراتسی","grat-tsi"), 3:("ایوا","ee-va"), 4:("له","leh"), 5:("یِک یوجبوک","yek yoj-bok"),
         6:("ساحا","sah-ha"), 7:("حبیب","ha-beeb"), 8:("ایلما","il-ma"), 9:("ویحِد، تنِین، تلیتا","wee-hed, tnayn, tlee-ta")},
  "is": {0:("هالو","hal-lo"), 1:("کواث سِییرذو؟","kvath seh-yir-thu?"), 2:("تاک","tahk"), 3:("یاو","yow"), 4:("نِی","nay"), 5:("وینساملِگاست","vin-sam-leh-gast"),
         6:("بلِس","bless"), 7:("وینور","vi-nur"), 8:("واتن","vatn"), 9:("اِیدن، توِیر، ثریر","aydn, tvayr, threer")},
  "da": {0:("های","hai"), 1:("وُردان ها دو دِ؟","vor-dan haa du de?"), 2:("تاک","tak"), 3:("یا","ya"), 4:("نای","nai"), 5:("وِر سو وِنلی","vair so ven-li"),
         6:("فاوِل","fa-vel"), 7:("وِن","ven"), 8:("وان","van"), 9:("اِین، تو، تره","ayn, toh, tray")},
  "en": {0:("هِلو","heh-lo"), 1:("هاو آر یو؟","how ar yoo?"), 2:("تَنک یو","thank yoo"), 3:("یِس","yes"), 4:("نو","no"), 5:("پلیز","pleez"),
         6:("گودبای","good-bye"), 7:("فرِند","frend"), 8:("واتِر","waw-ter"), 9:("وان، تو، ثری","wun, too, three")},
  "ru": {1:("کاک دِلا؟","kak dye-la?"), 5:("پاژالوستا","pa-zhaa-lus-ta")},
  "lb": {1:("وِی گِیت اِت؟","vay gayt et?"), 9:("اِینت، تسوِی، درای","aynt, tsvay, drai"), 8:("واسِر","vaa-ser")},
  "lt": {1:("کایپ سِکاسی؟","kaip se-ka-si?")},
  "pl": {9:("یِدِن، دوا، تشی","ye-den, dva, tshi")},
  "de": {7:("فرُینت","froynt"), 8:("واسِر","vas-ser")},
  "pt": {1:("کومو ایشتاش؟","ko-mu ish-tash?"), 4:("ناوم","nowng"), 3:("سین","seeng"), 9:("اوم، دویش، ترِش","oom, doysh, tresh")},
  "ca": {0:("اولا","o-la"), 6:("آدِئو","a-deh-oo"), 7:("آمیک","a-meek"), 8:("آیگوا","ai-gwa")},
  "hu": {2:("کوسونوم","kö-sö-nöm")},
  "sl": {0:("ژیویو","zhiv-yo")},
  "es": {6:("آدیوس","a-dyos"), 7:("آمیگو","a-mee-go"), 8:("آگوا","a-gwa")},
  "et": {4:("اِی","ay")},
  "sq": {0:("پِرشِندِتیه","per-shen-de-tye")},
  "cs": {6:("نا سخلِدانو","na skhle-da-noh")},
}
# متن جایگزین برای ساخت صدا وقتی صدای espeak برای آن زبان غلط می‌خواند: (صدا، متن)
# Audio text overrides where espeak's own voice mispronounces: (voice, text)
AUDIO_FIX = {
  ("ga",0):("en","dee-a gwit"), ("ga",1):("en","kunnus a-taw too?"), ("ga",2):("en","guh rev mah aggut"), ("ga",3):("en","sha"), ("ga",4):("en","nee ha"),
  ("ga",5):("en","leh duh hull"), ("ga",6):("en","slawn"), ("ga",7):("en","karra"), ("ga",8):("en","ishka"), ("ga",9):("en","a hayn, a doe, a tree"),
  ("mt",1):("it","kif ìnti?"), ("mt",2):("it","gràtsi"), ("mt",5):("it","iek iògbok"), ("mt",6):("es","sája"), ("mt",7):("es","jabíb"), ("mt",9):("it","uìed, tnèin, tlièta"),
}

import re, json
lib.espeak_TextToPhonemes.restype = ctypes.c_char_p
def ipa(voice, text):
    lib.espeak_SetVoiceByName(voice.encode())
    b = ctypes.c_char_p(text.encode()); p = ctypes.pointer(b); out = []
    while p.contents.value:
        r = lib.espeak_TextToPhonemes(p, 1, 0x02)
        if r: out.append(r.decode())
    s = " ".join(out)
    s = re.sub(r"\([a-z-]+\)", "", s)          # language switch markers like (en)
    return re.sub(r"[ˈˌ‿.͡]", "", s).strip()

# IPA → Persian letters / English-style respelling (longest match first)
CONS = [("tʃ","چ","ch"),("tɕ","چ","ch"),("ʈʂ","چ","ch"),("dʒ","ج","j"),("dʑ","ج","j"),("ɖʐ","ج","j"),("ts","تس","ts"),("dz","دز","dz"),
        ("r̝","رژ","rzh"),("ʃ","ش","sh"),("ɕ","ش","sh"),("ʂ","ش","sh"),("ʒ","ژ","zh"),("ʑ","ژ","zh"),("ʐ","ژ","zh"),
        ("x","خ","kh"),("χ","خ","kh"),("ç","خ","kh"),("ɣ","غ","gh"),("θ","ث","th"),("ð","ذ","dh"),("ŋ","نگ","ng"),("ɲ","نی","ny"),
        ("ʎ","لی","ly"),("ɫ","ل","l"),("ɾ","ر","r"),("ɹ","ر","r"),("ʁ","ر","r"),("ʀ","ر","r"),("r","ر","r"),("ɦ","ه","h"),("h","ه","h"),
        ("ʋ","و","v"),("β","و","v"),("v","و","v"),("w","و","w"),("ɥ","و","w"),("j","ی","y"),("c","تی","ty"),("ɟ","دی","dy"),("ɡ","گ","g"),
        ("g","گ","g"),("k","ک","k"),("q","ق","k"),("b","ب","b"),("p","پ","p"),("t","ت","t"),("d","د","d"),("f","ف","f"),("s","س","s"),
        ("z","ز","z"),("m","م","m"),("ɱ","م","m"),("n","ن","n"),("l","ل","l"),("ʔ","","")]
# vowel classes: (ipa chars, persian medial, persian initial, persian final, english, english long)
VOW = [("aɑɐæäʌɒ", "ا", "آ", "ا", "a", "aa"), ("eɛəɜɘɞ", "ِ", "اِ", "ه", "e", "ay"), ("iɪɨ", "ی", "ای", "ی", "i", "ee"),
       ("oɔɤ", "و", "او", "و", "o", "o"), ("uʊɯ", "و", "او", "و", "u", "oo"), ("yʏøœʉɵ", "و", "او", "و", "ü", "ü")]
def vclass(ch):
    for v in VOW:
        if ch in v[0]: return v
def convert(ipa_word, lang):
    out_fa, out_en, i, n = [], [], 0, len(ipa_word)
    while i < n:
        ch = ipa_word[i]
        if ch in "ːˑ": i += 1; continue
        if ch == "̃":                            # nasal vowel
            out_fa.append("ن"); out_en.append("n"); i += 1; continue
        if ch in "ʲʰʷ̩̯̥̪ˠ": i += 1; continue
        v = vclass(ch)
        if v:
            long_ = i+1 < n and ipa_word[i+1] == "ː"
            last = i == n-1 or (i+1 < n and ipa_word[i+1:] in ("ː",))
            if not out_fa: out_fa.append(v[2])
            elif last: out_fa.append(v[3])
            else: out_fa.append(v[1])
            out_en.append(v[5] if long_ else v[4]); i += 1; continue
        for k, f, e in CONS:
            if ipa_word.startswith(k, i):
                out_fa.append(f); out_en.append(e); i += len(k); break
        else:
            i += 1
    fa = "".join(out_fa).replace("ِِ", "ِ")
    return fa, "".join(out_en)
def pron(voice, text):
    q = text.strip().endswith("?") or text.strip().endswith(";")
    chunks = [c for c in re.split(r"[,،]", text.replace("¿", "").replace("?", "").replace(";", "")) if c.strip()]
    fa, en = [], []
    for c in chunks:
        words = ipa(voice, c).split()
        conv = [convert(w, voice) for w in words]
        fa.append(" ".join(x[0] for x in conv)); en.append(" ".join(x[1] for x in conv))
    return "، ".join(fa) + ("؟" if q else ""), ", ".join(en) + ("?" if q else "")

def build_words(table, var, out_name):
    """Synthesize audio and write the JS word table for one group of languages.
    table entry: (voice, fa name, en name, tts code, words, [notes], [extra])
    extra (optional dict): rom = Latin pronunciation list, fa = Persian pronunciation list,
                           audio = (voice, texts) when espeak has no voice for the language."""
    js = {}
    for code, (voice, nfa, nen, tts, words, *rest) in table.items():
        notes = rest[0] if rest else {}
        extra = rest[1] if len(rest) > 1 else {}
        av, atexts = extra.get("audio", (voice, words))
        prs = []
        for i, w in enumerate(words):
            if w is None: prs.append(("", "")); continue
            fix = PRON_FIX.get(code, {}).get(i)
            auto = pron(av, atexts[i]) if not fix else fix
            fa = (extra.get("fa") or [None]*10)[i] or auto[0]
            en = (extra.get("rom") or [None]*10)[i] or auto[1]
            prs.append((fa, en))
            v, txt = AUDIO_FIX.get((code, i), (av, atexts[i]))
            synth(v, txt, os.path.join(OUT, f"{code}-{i}.mp3"))
        js[code] = {"name": [nfa, nen], "tts": tts, "w": words, "fa": [p[0] for p in prs], "en": [p[1] for p in prs],
                    "notes": {str(k): v for k, v in notes.items()}}
    with open(os.path.join(ROOT, "src", out_name), "w", encoding="utf-8") as f:
        f.write("// Generated by tools/make_audio.py — words and pronunciations (Persian / Latin letters)\n")
        f.write(f"const {var} = " + json.dumps(js, ensure_ascii=False, indent=1) + ";\n")
    print(out_name, len(table), "languages")

build_words(EU, "EU_WORDS", "europe_words.js")


# ================== آسیا ==================
# Asia. rom = Latin pronunciation; "audio" = (voice, texts) for languages espeak can't speak (read phonetically by a close voice)
ROM_ZH = ["ni hao", "ni hao ma?", "xie xie", "shi", "bu shi", "qing", "zai jian", "peng you", "shui", "yi, er, san"]
FA_ZH = ["نی هائو", "نی هائو ما؟", "شیه شیه", "شی", "بو شی", "چینگ", "زای جیِن", "پنگ یو", "شویی", "یی، اَر، سان"]
ASIA = {
  "zh": ("cmn", "چینی (ماندارین)", "Chinese (Mandarin)", "zh-CN", ["你好", "你好吗？", "谢谢", "是", "不是", "请", "再见", "朋友", "水", "一、二、三"], {}, {"rom": ROM_ZH, "fa": FA_ZH}),
  "zht": ("cmn", "چینی ماندارین (خط سنتی)", "Mandarin Chinese (traditional script)", "zh-TW", ["你好", "你好嗎？", "謝謝", "是", "不是", "請", "再見", "朋友", "水", "一、二、三"], {}, {"rom": ROM_ZH, "fa": FA_ZH}),
  "ja": ("ja", "ژاپنی", "Japanese", "ja-JP", ["こんにちは", "お元気ですか？", "ありがとう", "はい", "いいえ", "お願いします", "さようなら", "友達", "水", "いち、に、さん"], {},
         {"rom": ["kon-ni-chi-wa", "o-gen-ki des ka?", "a-ri-ga-to", "hai", "ii-e", "o-ne-gai shi-mas", "sa-yo-na-ra", "to-mo-da-chi", "mi-zu", "i-chi, ni, san"],
          "fa": ["کونیچیوا", "اوگنکی دِس کا؟", "آریگاتو", "های", "ایی‌اِ", "اونِگای شیماس", "سایونارا", "توموداچی", "میزو", "ایچی، نی، سان"]}),
  "ko": ("ko", "کره‌ای", "Korean", "ko-KR", ["안녕하세요", "잘 지내요?", "감사합니다", "네", "아니요", "주세요", "안녕히 가세요", "친구", "물", "하나, 둘, 셋"], {},
         {"rom": ["an-nyeong-ha-se-yo", "jal ji-nae-yo?", "gam-sa-ham-ni-da", "ne", "a-ni-yo", "ju-se-yo", "an-nyeong-hi ga-se-yo", "chin-gu", "mul", "ha-na, dul, set"],
          "fa": ["آنیونگ‌هاسِیو", "چال جینِیو؟", "کامساهامنیدا", "نه", "آنیو", "جوسِیو", "آنیونگی کاسِیو", "چینگو", "مول", "هانا، دول، سِت"]}),
  "mn": ("ru", "مغولی", "Mongolian", "mn-MN", ["Сайн байна уу", "Юу байна?", "Баярлалаа", "Тийм", "Үгүй", "Гуйя", "Баяртай", "Найз", "Ус", "Нэг, хоёр, гурав"], {},
         {"rom": ["sain baina uu", "yoo baina?", "bayarlalaa", "teem", "ügüi", "guiya", "bayartai", "naiz", "us", "neg, khoyor, gurav"],
          "fa": ["ساین باینا او", "یو باینا؟", "بایارلالا", "تیم", "اوگوی", "گویا", "بایارتای", "نایز", "اوس", "نِگ، خویور، گوراو"],
          "audio": ("ru", ["Сайн байна у", "Ю байна?", "Баярлала", "Тим", "Угуй", "Гуйя", "Баяртай", "Найз", "Ус", "Нэг, хойор, гурав"])}),
  "id": ("id", "اندونزیایی", "Indonesian", "id-ID", ["Halo", "Apa kabar?", "Terima kasih", "Ya", "Tidak", "Tolong", "Selamat tinggal", "Teman", "Air", "Satu, dua, tiga"]),
  "ms": ("ms", "مالایی", "Malay", "ms-MY", ["Helo", "Apa khabar?", "Terima kasih", "Ya", "Tidak", "Tolong", "Selamat tinggal", "Kawan", "Air", "Satu, dua, tiga"]),
  "ta": ("ta", "تامیلی", "Tamil", "ta-IN", ["வணக்கம்", "எப்படி இருக்கிறீர்கள்?", "நன்றி", "ஆம்", "இல்லை", "தயவுசெய்து", "போய் வருகிறேன்", "நண்பன்", "தண்ணீர்", "ஒன்று, இரண்டு, மூன்று"], {},
         {"rom": ["va-nak-kam", "ep-pa-di i-ruk-ki-reer-gal?", "nan-dri", "aam", "il-lai", "ta-ya-vu-sei-du", "poi va-ru-gi-ren", "nan-ban", "tan-neer", "on-dru, i-ran-du, moon-dru"],
          "fa": ["وَناکّام", "اِپّادی ایروکّیریرگال؟", "نَندری", "آم", "ایلّای", "تایاووسِیدو", "پوی واروگیرِن", "نَنبان", "تَنّیر", "اوندرو، ایراندو، موندرو"]}),
  "th": ("th", "تایلندی", "Thai", "th-TH", ["สวัสดี", "สบายดีไหม", "ขอบคุณ", "ใช่", "ไม่", "กรุณา", "ลาก่อน", "เพื่อน", "น้ำ", "หนึ่ง สอง สาม"], {},
         {"rom": ["sa-wat-dee", "sa-bai dee mai?", "khop khun", "chai", "mai", "ka-ru-na", "laa gon", "phuean", "naam", "nueng, song, saam"],
          "fa": ["ساوات‌دی", "سابای دی مای؟", "خاپ خون", "چای", "مای", "کارونا", "لا کُن", "پوئن", "نام", "نونگ، سونگ، سام"]}),
  "vi": ("vi", "ویتنامی", "Vietnamese", "vi-VN", ["Xin chào", "Bạn khỏe không?", "Cảm ơn", "Vâng", "Không", "Làm ơn", "Tạm biệt", "Bạn", "Nước", "Một, hai, ba"], {},
         {"rom": ["sin chow", "ban khweh khom?", "gahm un", "vung", "khom", "lahm un", "tahm byet", "ban", "nuoc", "moht, hai, ba"],
          "fa": ["سین چائو", "بان خوِه خُم؟", "گام اُن", "وُنگ", "خُم", "لام اُن", "تام بیِت", "بان", "نووک", "موت، های، با"]}),
  "fil": ("id", "فیلیپینی", "Filipino", "fil-PH", ["Kumusta", "Kumusta ka?", "Salamat", "Oo", "Hindi", "Pakiusap", "Paalam", "Kaibigan", "Tubig", "Isa, dalawa, tatlo"], {},
          {"audio": ("id", ["Kumusta", "Kumusta ka?", "Salamat", "Oo", "Hindi", "Paki-usap", "Pa-alam", "Ka-ibigan", "Tubig", "Isa, dalawa, tatlo"])}),
  "my": ("my", "برمه‌ای", "Burmese", "my-MM", ["မင်္ဂလာပါ", "နေကောင်းလား", "ကျေးဇူးတင်ပါတယ်", "ဟုတ်ကဲ့", "မဟုတ်ဘူး", "ကျေးဇူးပြု၍", "သွားပါဦးမယ်", "သူငယ်ချင်း", "ရေ", "တစ်၊ နှစ်၊ သုံး"], {},
         {"rom": ["min-ga-la-ba", "nay kaung la?", "kyay-zu tin-ba-deh", "hoke-kae", "ma-hoke-bu", "kyay-zu pyu-ywe", "thwa-ba-oun-meh", "tha-nge-chin", "yay", "tit, hnit, thoun"],
          "fa": ["مینگالابا", "نِی کائونگ لا؟", "چِی‌زو تین‌با‌دِه", "هوک‌که", "ماهوک‌بو", "چِی‌زو پیو‌یوه", "توا‌با‌اون‌مِه", "تانگه‌چین", "یِی", "تیت، هنیت، تون"]}),
  "km": (None, "خمر", "Khmer", "km-KH", ["សួស្តី", "សុខសប្បាយទេ?", "អរគុណ", "បាទ", "ទេ", "សូម", "លាហើយ", "មិត្តភក្តិ", "ទឹក", "មួយ ពីរ បី"],
         {3: ("زنان به‌جای آن «ចាស» (چا) می‌گویند.", "Women say “ចាស” (chaa) instead.")},
         {"rom": ["suos-dey", "sok sa-bai te?", "aw-kun", "baat", "te", "som", "lea haey", "mit-pheak", "tuek", "muoy, pii, bei"],
          "fa": ["سوئوس‌دِی", "سوک سابای تِه؟", "اُکون", "بات", "تِه", "سوم", "لیا هِی", "میت‌پیک", "توک", "موئی، پی، بِی"],
          "audio": ("id", ["suosdei", "sok sabai te?", "awkun", "baat", "te", "som", "lia hai", "mitpiak", "tuk", "muoi, pii, bei"])}),
  "lo": (None, "لائوسی", "Lao", "lo-LA", ["ສະບາຍດີ", "ສະບາຍດີບໍ?", "ຂອບໃຈ", "ແມ່ນ", "ບໍ່", "ກະລຸນາ", "ລາກ່ອນ", "ໝູ່", "ນ້ຳ", "ໜຶ່ງ ສອງ ສາມ"], {},
         {"rom": ["sa-bai-dee", "sa-bai-dee bor?", "khop jai", "maen", "bor", "ka-lu-na", "laa gon", "moo", "naam", "nueng, song, saam"],
          "fa": ["سابای‌دی", "سابای‌دی بو؟", "خاپ جای", "مِن", "بو", "کالونا", "لا کُن", "مو", "نام", "نونگ، سونگ، سام"],
          "audio": ("id", ["sabaidi", "sabaidi bo?", "khop jai", "men", "bo", "kaluna", "la kon", "mu", "nam", "nung, song, sam"])}),
  "tet": (None, "تتوم", "Tetum", "tet", ["Bondia", "Ita diak ka?", "Obrigadu", "Sin", "Lae", "Favór", "Até logu", "Belun", "Bee", "Ida, rua, tolu"], {},
          {"audio": ("id", ["Bondia", "Ita diak ka?", "Obrigadu", "Sin", "Lae", "Favor", "Ate logu", "Belun", "Be", "Ida, rua, tolu"])}),
  "hi": ("hi", "هندی", "Hindi", "hi-IN", ["नमस्ते", "आप कैसे हैं?", "धन्यवाद", "हाँ", "नहीं", "कृपया", "अलविदा", "दोस्त", "पानी", "एक, दो, तीन"], {},
         {"rom": ["na-mas-te", "aap kai-se hain?", "dhan-ya-vaad", "haan", "na-heen", "kri-pa-ya", "al-vi-da", "dost", "paa-nee", "ek, do, teen"],
          "fa": ["نَمَستِه", "آپ کِیسه هِین؟", "دَنیاواد", "هان", "نَهین", "کریپایا", "اَلویدا", "دوست", "پانی", "اِک، دو، تین"]}),
  "ur": ("ur", "اردو", "Urdu", "ur-PK", ["السلام علیکم", "آپ کیسے ہیں؟", "شکریہ", "جی ہاں", "نہیں", "براہ کرم", "خدا حافظ", "دوست", "پانی", "ایک، دو، تین"], {},
         {"rom": ["as-sa-laa-mu a-lai-kum", "aap kai-se hain?", "shuk-ri-ya", "jee haan", "na-heen", "ba-raa-e ka-ram", "khu-da haa-fiz", "dost", "paa-nee", "ek, do, teen"],
          "fa": ["السلام علیکم", "آپ کِیسه هِین؟", "شکریه", "جی هان", "نَهین", "برای کرم", "خدا حافظ", "دوست", "پانی", "ایک، دو، تین"]}),
  "bn": ("bn", "بنگالی", "Bengali", "bn-BD", ["আসসালামু আলাইকুম", "আপনি কেমন আছেন?", "ধন্যবাদ", "হ্যাঁ", "না", "দয়া করে", "বিদায়", "বন্ধু", "পানি", "এক, দুই, তিন"], {},
         {"rom": ["as-sa-la-mu a-lai-kum", "a-pni ke-mon a-chen?", "dhon-no-bad", "hyan", "na", "do-ya ko-re", "bi-day", "bon-dhu", "pa-ni", "ek, dui, tin"],
          "fa": ["السلام علیکم", "آپنی کِمون آچِن؟", "دونوباد", "هیا", "نا", "دُیا کُرِه", "بیدای", "بوندو", "پانی", "اِک، دوئی، تین"]}),
  "si": ("si", "سینهالی", "Sinhala", "si-LK", ["ආයුබෝවන්", "ඔබට කොහොමද?", "ස්තූතියි", "ඔව්", "නැහැ", "කරුණාකර", "ගිහින් එන්නම්", "යාළුවා", "වතුර", "එක, දෙක, තුන"], {},
         {"rom": ["aa-yu-bo-wan", "o-ba-ta ko-ho-ma-da?", "stoo-ti-yi", "ow", "nae-hae", "ka-ru-naa-ka-ra", "gi-hin en-nam", "yaa-lu-waa", "wa-tu-ra", "e-ka, de-ka, tu-na"],
          "fa": ["آیوبووان", "اُباتا کُهُمادا؟", "ستوتیی", "اُو", "نِهِه", "کاروناکارا", "گیهین اِنام", "یالووا", "واتورا", "اِکا، دِکا، تونا"]}),
  "ne": ("ne", "نپالی", "Nepali", "ne-NP", ["नमस्ते", "तपाईंलाई कस्तो छ?", "धन्यवाद", "हो", "होइन", "कृपया", "फेरि भेटौँला", "साथी", "पानी", "एक, दुई, तीन"], {},
         {"rom": ["na-mas-te", "ta-pai-lai kas-to cha?", "dhan-ya-baad", "ho", "hoi-na", "kri-pa-ya", "phe-ri bhe-taun-la", "saa-thi", "paa-ni", "ek, dui, teen"],
          "fa": ["نَمَستِه", "تاپای‌لای کاستو چا؟", "دانیاباد", "هو", "هوینا", "کریپایا", "فِری بِتاونلا", "ساتی", "پانی", "اِک، دوئی، تین"]}),
  "dz": (None, "زونگخا", "Dzongkha", "dz-BT", ["ཀུ་ཟུ་ཟང་པོ།", "ག་དེ་སྦེ་ཡོད།", "བཀའ་དྲིན་ཆེ།", "ཨིན།", "མེན།", None, "ལོག་འཇལ་གེ།", "ཚ་རོ།", "ཆུ།", "གཅིག། གཉིས། གསུམ།"], {},
         {"rom": ["ku-zu-zang-po", "ga-de be yoe?", "ka-drin-che", "ing", "men", None, "log jay ge", "tsha-ro", "chu", "chi, nyi, sum"],
          "fa": ["کوزوزانگپو", "گادِه بِه یو؟", "کادرینچه", "اینگ", "مِن", None, "لوگ جِی گِه", "تساروُ", "چو", "چی، نیی، سوم"],
          "audio": ("id", ["kuzuzangpo", "gade be yo?", "kadrince", "ing", "men", None, "log jei ge", "tsaro", "cu", "ci, nyi, sum"])}),
  "dv": (None, "دیوهی", "Dhivehi", "dv-MV", ["އައްސަލާމު ޢަލައިކުމް", "ކިހިނެއް؟", "ޝުކުރިއްޔާ", "އާނ", "ނޫން", None, "ދާނަން", None, "ފެން", "އެކެއް، ދޭއް، ތިނެއް"], {},
         {"rom": ["as-sa-laa-mu a-lai-kum", "ki-hi-neh?", "shu-ku-riy-yaa", "aan", "noon", None, "dhaa-nan", None, "fen", "e-keh, dheyh, thi-neh"],
          "fa": ["السلام علیکم", "کیهینِه؟", "شکریّا", "آن", "نون", None, "دانَن", None, "فِن", "اِکِه، دِیه، تینِه"],
          "audio": ("id", ["assalamu alaikum", "kihineh?", "syukuriya", "aan", "nuun", None, "daanan", None, "fen", "ekeh, deih, tineh"])}),
  "ps": (None, "پشتو", "Pashto", "ps-AF", ["سلام", "ته څنګه یې؟", "مننه", "هو", "نه", "مهرباني وکړه", "په مخه دې ښه", "ملګری", "اوبه", "یو، دوه، درې"], {},
         {"rom": ["sa-laam", "ta tsan-ga ye?", "ma-na-na", "ho", "na", "meh-ra-baa-nee wak-ra", "pa ma-kha de kha", "mal-ga-ray", "o-ba", "yaw, dwa, dre"],
          "fa": ["سلام", "تَه تسَنگه یِه؟", "مَنَنه", "هو", "نه", "مهربانی وکړه", "په مخه دې ښه", "ملګری", "اوبه", "یو، دوه، درې"],
          "audio": ("id", ["salam", "ta tsanga ye?", "manana", "ho", "na", "mehrabani wakra", "pa makha de kha", "malgarai", "oba", "yau, dwa, dre"])}),
  "prs": ("fa", "دری", "Dari", "fa-AF", ["سلام", "چطور هستی؟", "تشکر", "بلی", "نه", "لطفاً", "خدا حافظ", "دوست", "آب", "یک، دو، سه"], {},
          {"rom": ["sa-laam", "che-tor has-ti?", "ta-shak-kur", "ba-li", "na", "lut-fan", "khu-daa haa-fiz", "dost", "aab", "yak, du, se"],
           "fa": ["سلام", "چِطور هستی؟", "تشکر", "بَلی", "نَه", "لطفاً", "خدا حافظ", "دوست", "آب", "یک، دو، سه"]}),
  "kk": ("kk", "قزاقی", "Kazakh", "kk-KZ", ["Сәлеметсіз бе", "Қалыңыз қалай?", "Рахмет", "Иә", "Жоқ", "Өтінемін", "Сау болыңыз", "Дос", "Су", "Бір, екі, үш"], {},
         {"rom": ["sa-le-met-siz be", "qa-ly-nyz qa-lai?", "rakh-met", "i-ya", "zhoq", "ö-ti-ne-min", "sau bo-ly-nyz", "dos", "su", "bir, e-ki, üsh"]}),
  "uz": ("uz", "ازبکی", "Uzbek", "uz-UZ", ["Salom", "Qalaysiz?", "Rahmat", "Ha", "Yo'q", "Iltimos", "Xayr", "Do'st", "Suv", "Bir, ikki, uch"], {},
         {"rom": ["sa-lom", "qa-lay-siz?", "rah-mat", "ha", "yoq", "il-ti-mos", "khayr", "dost", "suv", "bir, ik-ki, uch"],
          "fa": ["سالام", "قالایسیز؟", "رحمت", "ها", "یوق", "ایلتیموس", "خِیر", "دوست", "سوو", "بیر، ایکّی، اوچ"]}),
  "tk": ("tk", "ترکمنی", "Turkmen", "tk-TM", ["Salam", "Nähili?", "Sag bol", "Hawa", "Ýok", "Haýyş", "Hoş gal", "Dost", "Suw", "Bir, iki, üç"]),
  "ky": ("ky", "قرقیزی", "Kyrgyz", "ky-KG", ["Салам", "Кандайсыз?", "Рахмат", "Ооба", "Жок", "Сураныч", "Саламатта калыңыз", "Дос", "Суу", "Бир, эки, үч"], {},
         {"rom": ["sa-lam", "kan-day-syz?", "rakh-mat", "oo-ba", "jok", "su-ra-nych", "sa-la-mat-ta ka-ly-nyz", "dos", "suu", "bir, e-ki, üch"],
          "fa": ["سالام", "قاندایسیز؟", "راخمات", "اوبا", "جوق", "سورانیچ", "سالاماتتا قالینیز", "دوس", "سو", "بیر، اِکی، اوچ"]}),
  "tg": (None, "تاجیکی", "Tajik", "tg-TJ", ["Салом", "Чӣ хел шумо?", "Ташаккур", "Ҳа", "Не", "Лутфан", "Хайр", "Дӯст", "Об", "Як, ду, се"], {},
         {"rom": ["sa-lom", "chi khel shu-mo?", "ta-shak-kur", "ha", "ne", "lut-fan", "khayr", "dust", "ob", "yak, du, se"],
          "fa": ["سلام", "چی خِل شُما؟", "تشکر", "ها", "نِه", "لطفاً", "خیر", "دوست", "آب", "یک، دو، سه"],
          "audio": ("fa", ["سلام", "چی خِل شُما؟", "تشکّر", "ها", "نِه", "لطفاً", "خِیر", "دوست", "آب", "یک، دو، سه"])}),
  "ka": ("ka", "گرجی", "Georgian", "ka-GE", ["გამარჯობა", "როგორ ხარ?", "მადლობა", "დიახ", "არა", "გთხოვთ", "ნახვამდის", "მეგობარი", "წყალი", "ერთი, ორი, სამი"], {},
         {"rom": ["ga-mar-jo-ba", "ro-gor khar?", "mad-lo-ba", "di-akh", "a-ra", "gtkhovt", "nakh-vam-dis", "me-go-ba-ri", "tsqa-li", "er-ti, o-ri, sa-mi"]}),
  "hy": ("hy", "ارمنی", "Armenian", "hy-AM", ["Բարև", "Ինչպե՞ս ես", "Շնորհակալություն", "Այո", "Ոչ", "Խնդրում եմ", "Ցտեսություն", "Ընկեր", "Ջուր", "Մեկ, երկու, երեք"], {},
         {"rom": ["ba-rev", "inch-pes es?", "shnor-ha-ka-lu-tyun", "a-yo", "voch", "khn-drum em", "tste-su-tyun", "en-ker", "jur", "mek, yer-ku, ye-rek"]}),
  "az": ("az", "آذربایجانی", "Azerbaijani", "az-AZ", ["Salam", "Necəsən?", "Təşəkkür edirəm", "Bəli", "Xeyr", "Zəhmət olmasa", "Hələlik", "Dost", "Su", "Bir, iki, üç"], {},
         {"rom": ["sa-lam", "ne-je-san?", "te-shek-kür e-di-rem", "be-li", "kheyr", "zeh-met ol-ma-sa", "he-le-lik", "dost", "su", "bir, i-ki, üch"],
          "fa": ["سلام", "نِجه‌سن؟", "تشکّور اِدیرم", "بلی", "خِیر", "زحمت اولماسا", "هله‌لیک", "دوست", "سو", "بیر، ایکی، اوچ"]}),
}
build_words(ASIA, "ASIA_WORDS", "asia_words.js")
files = sorted(x for x in os.listdir(OUT) if x.endswith(".mp3"))
with open(os.path.join(OUT, "list.json"), "w") as f: json.dump(files, f)
print("total audio files:", len(files))
