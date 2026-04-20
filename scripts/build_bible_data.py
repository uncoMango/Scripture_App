#!/usr/bin/env python3
"""Parse STEPBible TAGNT (Koine Greek NT) + TAHOT (Biblical Hebrew OT)
into a single compact JSON lookup. CC BY 4.0 — Tyndale House / STEPBible.org.
Run once on a dev machine; the resulting JSON ships with the app."""

import os, re, json, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
STEP_DIR   = os.environ.get("STEPBIBLE_DIR",
    os.path.abspath(os.path.join(REPO_ROOT, "..", "STEPBible-Data")))
OUT_PATH   = os.path.join(REPO_ROOT, "data", "bible_words.json")

STEP_TO_NUM = {
    "Gen":1,"Exo":2,"Lev":3,"Num":4,"Deu":5,"Jos":6,"Jdg":7,"Rut":8,
    "1Sa":9,"2Sa":10,"1Ki":11,"2Ki":12,"1Ch":13,"2Ch":14,"Ezr":15,
    "Neh":16,"Est":17,"Job":18,"Psa":19,"Pro":20,"Ecc":21,"Sng":22,
    "Isa":23,"Jer":24,"Lam":25,"Ezk":26,"Dan":27,"Hos":28,"Jol":29,
    "Amo":30,"Oba":31,"Jon":32,"Mic":33,"Nam":34,"Hab":35,"Zep":36,
    "Hag":37,"Zec":38,"Mal":39,
    "Mat":40,"Mrk":41,"Luk":42,"Jhn":43,"Act":44,"Rom":45,"1Co":46,
    "2Co":47,"Gal":48,"Eph":49,"Php":50,"Col":51,"1Th":52,"2Th":53,
    "1Ti":54,"2Ti":55,"Tit":56,"Phm":57,"Heb":58,"Jas":59,"1Pe":60,
    "2Pe":61,"1Jn":62,"2Jn":63,"3Jn":64,"Jud":65,"Rev":66,
}
STEP_ALT = {
    "Josh":"Jos","Judg":"Jdg","Ruth":"Rut","1Sam":"1Sa","2Sam":"2Sa",
    "1Kgs":"1Ki","2Kgs":"2Ki","1Chr":"1Ch","2Chr":"2Ch","Ezra":"Ezr",
    "Esth":"Est","Ps":"Psa","Prov":"Pro","Eccl":"Ecc","Song":"Sng",
    "Ezek":"Ezk","Joel":"Jol","Amos":"Amo","Obad":"Oba","Jonah":"Jon",
    "Nah":"Nam","Zeph":"Zep","Zech":"Zec","Matt":"Mat","Mark":"Mrk",
    "Luke":"Luk","John":"Jhn","Acts":"Act","Phil":"Php","Phlm":"Phm",
    "James":"Jas","1Pet":"1Pe","2Pet":"2Pe","1John":"1Jn","2John":"2Jn",
    "3John":"3Jn","Jude":"Jud",
}

REF_LINE_RE        = re.compile(r'^([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)#\d+')
GREEK_TRANSLIT_RE  = re.compile(r'^(.+?)\s*\(([^)]+)\)\s*$')
STRONG_MORPH_RE    = re.compile(r'^([GH]\d+\w?)=([^\t]*)$')
LEMMA_GLOSS_RE     = re.compile(r'^([^=]+?)=:?\s*(.*)$')

def canonical_book(raw):
    if raw in STEP_TO_NUM: return raw
    return STEP_ALT.get(raw)

def normalize_strong(s):
    if not s: return ""
    m = re.match(r'^([GH])0*(\d+)', s)
    return (m.group(1) + m.group(2)) if m else ""

def parse_word_line(line, lang):
    m = REF_LINE_RE.match(line)
    if not m: return None
    book_code = canonical_book(m.group(1))
    if book_code is None: return None
    ch, vs = int(m.group(2)), int(m.group(3))
    parts = line.split("\t")
    if len(parts) < 5: return None

    if lang == "Greek":
        form, english = parts[1].strip(), parts[2].strip()
        strong_morph  = parts[3].strip()
        lemma_gloss   = parts[4].strip()
        original, translit = form, ""
        fm = GREEK_TRANSLIT_RE.match(form)
        if fm: original, translit = fm.group(1).strip(), fm.group(2).strip()
        strong, morph = "", ""
        sm = STRONG_MORPH_RE.match(strong_morph)
        if sm: strong, morph = sm.group(1), sm.group(2)
        lemma, gloss = "", ""
        lg = LEMMA_GLOSS_RE.match(lemma_gloss)
        if lg: lemma, gloss = lg.group(1).strip(), lg.group(2).strip()
    else:  # Hebrew
        original = parts[1].strip()
        translit = parts[2].strip()
        english  = parts[3].strip()
        strong_raw = parts[4].strip() if len(parts)>4 else ""
        morph      = parts[5].strip() if len(parts)>5 else ""
        canonical_s= parts[8].strip() if len(parts)>8 else ""
        lemma_gloss= parts[11].strip() if len(parts)>11 else ""
        strong = canonical_s
        if not strong and strong_raw:
            tokens = re.findall(r'[GH]\d+\w?', strong_raw)
            if tokens: strong = tokens[-1]
        lemma, gloss = "", ""
        if lemma_gloss:
            inner = re.search(r'\{([^{}]+)\}', lemma_gloss)
            target = inner.group(1) if inner else lemma_gloss
            segs = target.split("=")
            if len(segs) >= 3:
                lemma = segs[1].strip()
                raw = "=".join(segs[2:]).lstrip(": ").strip()
                gloss = re.split(r'[»:]', raw, maxsplit=1)[0].strip()
            elif len(segs) == 2:
                gloss = segs[1].strip().lstrip(": ").strip()

    return book_code, ch, vs, {
        "orig": original, "translit": translit, "eng": english,
        "strong": normalize_strong(strong), "morph": morph,
        "lemma": lemma, "gloss": gloss,
    }

def build():
    src = os.path.join(STEP_DIR, "Translators Amalgamated OT+NT")
    if not os.path.isdir(src):
        sys.exit(f"[FATAL] Not found: {src}")
    bible, count = {}, 0
    for fname in sorted(os.listdir(src)):
        if not fname.endswith(".txt"): continue
        lang = "Greek" if fname.startswith("TAGNT") else ("Hebrew" if fname.startswith("TAHOT") else None)
        if lang is None: continue
        print(f"  parsing {fname}")
        with open(os.path.join(src, fname), encoding="utf-8-sig") as f:
            for raw in f:
                line = raw.rstrip("\r\n")
                if not line or line.startswith("#") or line.startswith("\t"): continue
                r = parse_word_line(line, lang)
                if r:
                    book, c, v, w = r
                    bible.setdefault(f"{book}.{c}.{v}", []).append(w)
                    count += 1
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(bible, f, ensure_ascii=False, separators=(",", ":"))
    mb = os.path.getsize(OUT_PATH)/1024/1024
    print(f"\n  Wrote {OUT_PATH}: {len(bible):,} verses, {count:,} words, {mb:.1f} MB")

if __name__ == "__main__":
    build()
