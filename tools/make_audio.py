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

eu_js = {}
for code, (voice, nfa, nen, tts, words, *notes) in EU.items():
    notes = notes[0] if notes else {}
    prs = [PRON_FIX.get(code, {}).get(i) or pron(voice, w) for i, w in enumerate(words)]
    for i, w in enumerate(words):
        v, txt = AUDIO_FIX.get((code, i), (voice, w))
        synth(v, txt, os.path.join(OUT, f"{code}-{i}.mp3"))
    eu_js[code] = {"name": [nfa, nen], "tts": tts, "w": words, "fa": [p[0] for p in prs], "en": [p[1] for p in prs],
                   "notes": {str(k): v for k, v in notes.items()}}
with open(os.path.join(ROOT, "src", "europe_words.js"), "w", encoding="utf-8") as f:
    f.write("// Generated by tools/make_audio.py — words, pronunciations (Persian/Latin letters) for European languages\n")
    f.write("const EU_WORDS = " + json.dumps(eu_js, ensure_ascii=False, indent=1) + ";\n")
files = sorted(x for x in os.listdir(OUT) if x.endswith(".mp3"))
with open(os.path.join(OUT, "list.json"), "w") as f: json.dump(files, f)
print("europe:", len(EU), "languages;", len(files), "audio files")
