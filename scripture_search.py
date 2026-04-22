#!/usr/bin/env python3
"""
Scripture Mistranslation Finder
Kahu Phil Stephens — Ke Aupuni O Ke Akua Press

For each word in a Bible verse, checks its Strong's number against
lexicon/mistranslations.json and returns every word where the standard
English translation flattens or loses the original meaning.
"""

import os
import json
import re
import urllib.request
import urllib.parse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BIBLE_FILE = os.path.join(SCRIPT_DIR, "data", "bible_words.json")
LEXI_FILE  = os.path.join(SCRIPT_DIR, "lexicon", "mistranslations.json")

# ─── Lazy-loaded data ──────────────────────────────────────────────────────────

_BIBLE   = None
_LEXICON = None

def _load_bible():
    global _BIBLE
    if _BIBLE is None:
        with open(BIBLE_FILE, encoding="utf-8") as f:
            _BIBLE = json.load(f)
    return _BIBLE

def _load_lexicon():
    global _LEXICON
    if _LEXICON is None:
        with open(LEXI_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        # Index only plain Strong's keys (G123 / H456 / A789); skip _meta and _suffix variants
        _LEXICON = {
            k: v for k, v in raw.items()
            if re.match(r"^[GHA]\d+$", k)
        }
    return _LEXICON

# ─── Book maps ────────────────────────────────────────────────────────────────

OT_BOOKS = {
    "genesis":1,"exodus":2,"leviticus":3,"numbers":4,"deuteronomy":5,
    "joshua":6,"judges":7,"ruth":8,"1samuel":9,"2samuel":10,
    "1kings":11,"2kings":12,"1chronicles":13,"2chronicles":14,
    "ezra":15,"nehemiah":16,"esther":17,"job":18,"psalms":19,"psalm":19,
    "proverbs":20,"ecclesiastes":21,"songofsolomon":22,"isaiah":23,
    "jeremiah":24,"lamentations":25,"ezekiel":26,"daniel":27,
    "hosea":28,"joel":29,"amos":30,"obadiah":31,"jonah":32,"micah":33,
    "nahum":34,"habakkuk":35,"zephaniah":36,"haggai":37,"zechariah":38,
    "malachi":39,
}
NT_BOOKS = {
    "matthew":40,"mark":41,"luke":42,"john":43,"acts":44,
    "romans":45,"1corinthians":46,"2corinthians":47,"galatians":48,
    "ephesians":49,"philippians":50,"colossians":51,"1thessalonians":52,
    "2thessalonians":53,"1timothy":54,"2timothy":55,"titus":56,
    "philemon":57,"hebrews":58,"james":59,"1peter":60,"2peter":61,
    "1john":62,"2john":63,"3john":64,"jude":65,"revelation":66,
}
ALL_BOOKS = {**OT_BOOKS, **NT_BOOKS}

BOOK_DISPLAY = {
    1:"Genesis",2:"Exodus",3:"Leviticus",4:"Numbers",5:"Deuteronomy",
    6:"Joshua",7:"Judges",8:"Ruth",9:"1 Samuel",10:"2 Samuel",
    11:"1 Kings",12:"2 Kings",13:"1 Chronicles",14:"2 Chronicles",
    15:"Ezra",16:"Nehemiah",17:"Esther",18:"Job",19:"Psalms",
    20:"Proverbs",21:"Ecclesiastes",22:"Song of Solomon",23:"Isaiah",
    24:"Jeremiah",25:"Lamentations",26:"Ezekiel",27:"Daniel",
    28:"Hosea",29:"Joel",30:"Amos",31:"Obadiah",32:"Jonah",33:"Micah",
    34:"Nahum",35:"Habakkuk",36:"Zephaniah",37:"Haggai",38:"Zechariah",
    39:"Malachi",
    40:"Matthew",41:"Mark",42:"Luke",43:"John",44:"Acts",
    45:"Romans",46:"1 Corinthians",47:"2 Corinthians",48:"Galatians",
    49:"Ephesians",50:"Philippians",51:"Colossians",52:"1 Thessalonians",
    53:"2 Thessalonians",54:"1 Timothy",55:"2 Timothy",56:"Titus",
    57:"Philemon",58:"Hebrews",59:"James",60:"1 Peter",61:"2 Peter",
    62:"1 John",63:"2 John",64:"3 John",65:"Jude",66:"Revelation",
}

# STEPBible key prefix used in bible_words.json
NUM_TO_STEP = {
    1:"Gen",2:"Exo",3:"Lev",4:"Num",5:"Deu",6:"Jos",7:"Jdg",8:"Rut",
    9:"1Sa",10:"2Sa",11:"1Ki",12:"2Ki",13:"1Ch",14:"2Ch",15:"Ezr",
    16:"Neh",17:"Est",18:"Job",19:"Psa",20:"Pro",21:"Ecc",22:"Sng",
    23:"Isa",24:"Jer",25:"Lam",26:"Ezk",27:"Dan",28:"Hos",29:"Jol",
    30:"Amo",31:"Oba",32:"Jon",33:"Mic",34:"Nam",35:"Hab",36:"Zep",
    37:"Hag",38:"Zec",39:"Mal",
    40:"Mat",41:"Mrk",42:"Luk",43:"Jhn",44:"Act",45:"Rom",46:"1Co",
    47:"2Co",48:"Gal",49:"Eph",50:"Php",51:"Col",52:"1Th",53:"2Th",
    54:"1Ti",55:"2Ti",56:"Tit",57:"Phm",58:"Heb",59:"Jas",60:"1Pe",
    61:"2Pe",62:"1Jn",63:"2Jn",64:"3Jn",65:"Jud",66:"Rev",
}

# ─── Reference parsing ────────────────────────────────────────────────────────

def parse_reference(ref_str):
    """Parse 'Matthew 6:33' -> (book_num, chapter, verse, lang).
    Returns (None,None,None,None) on failure."""
    if not ref_str:
        return None, None, None, None
    s = re.sub(r"\s+", " ", ref_str).strip()
    s = re.sub(r"(\d)\s*[.;]\s*(\d)", r"\1:\2", s)
    s = re.sub(r"(:\d+)\s*[-,].*$", r"\1", s)
    for pat, rep in [
        (r"^first\s+","1 "),(r"^second\s+","2 "),(r"^third\s+","3 "),
        (r"^1st\s+","1 "),(r"^2nd\s+","2 "),(r"^3rd\s+","3 "),
        (r"^III\s+","3 "),(r"^II\s+","2 "),(r"^I\s+(?=[A-Za-z])","1 "),
    ]:
        s = re.sub(pat, rep, s, flags=re.IGNORECASE)
    s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)
    s = re.sub(r"\s*:\s*", ":", s)
    m = re.match(r"^(.+?)\s+(\d+):(\d+)\s*$", s)
    if not m:
        return None, None, None, None
    chapter = int(m.group(2))
    verse   = int(m.group(3))
    key = m.group(1).strip().lower().replace(" ", "").replace(".", "")
    abbrevs = {
        "gen":"genesis","ex":"exodus","exo":"exodus","lev":"leviticus",
        "num":"numbers","deut":"deuteronomy","dt":"deuteronomy",
        "josh":"joshua","judg":"judges","jdg":"judges",
        "1sam":"1samuel","1sa":"1samuel","2sam":"2samuel","2sa":"2samuel",
        "1kgs":"1kings","1ki":"1kings","2kgs":"2kings","2ki":"2kings",
        "1chr":"1chronicles","2chr":"2chronicles",
        "neh":"nehemiah","est":"esther","esth":"esther",
        "ps":"psalms","psa":"psalms","pss":"psalms",
        "prov":"proverbs","prv":"proverbs","pr":"proverbs",
        "eccl":"ecclesiastes","ecc":"ecclesiastes",
        "song":"songofsolomon","sos":"songofsolomon","sng":"songofsolomon",
        "isa":"isaiah","is":"isaiah","jer":"jeremiah",
        "lam":"lamentations","ezek":"ezekiel","ez":"ezekiel","eze":"ezekiel",
        "dan":"daniel","hos":"hosea","jl":"joel","am":"amos",
        "ob":"obadiah","obad":"obadiah","jon":"jonah","mic":"micah",
        "nah":"nahum","hab":"habakkuk","zeph":"zephaniah","zep":"zephaniah",
        "hag":"haggai","zech":"zechariah","zec":"zechariah","mal":"malachi",
        "mt":"matthew","matt":"matthew","mat":"matthew","mathew":"matthew",
        "mk":"mark","mrk":"mark","lk":"luke","luk":"luke",
        "jn":"john","jhn":"john","joh":"john",
        "ac":"acts","act":"acts","rom":"romans","ro":"romans",
        "1cor":"1corinthians","1co":"1corinthians",
        "2cor":"2corinthians","2co":"2corinthians",
        "gal":"galatians","eph":"ephesians",
        "phil":"philippians","php":"philippians",
        "col":"colossians",
        "1thess":"1thessalonians","1thes":"1thessalonians","1th":"1thessalonians",
        "2thess":"2thessalonians","2thes":"2thessalonians","2th":"2thessalonians",
        "1tim":"1timothy","1ti":"1timothy","2tim":"2timothy","2ti":"2timothy",
        "tit":"titus","phlm":"philemon","phm":"philemon","philem":"philemon",
        "heb":"hebrews","jas":"james","jm":"james",
        "1pet":"1peter","1pe":"1peter","2pet":"2peter","2pe":"2peter",
        "1jn":"1john","1jhn":"1john","2jn":"2john","3jn":"3john",
        "jud":"jude","rev":"revelation","rv":"revelation",
        "revelations":"revelation",
    }
    book_num = ALL_BOOKS.get(key)
    if book_num is None:
        book_num = ALL_BOOKS.get(abbrevs.get(key, ""))
    if book_num is None:
        hits = [v for k, v in ALL_BOOKS.items() if k.startswith(key) and len(key) >= 3]
        if len(hits) == 1:
            book_num = hits[0]
    if book_num is None:
        return None, None, None, None
    lang = "Hebrew" if book_num <= 39 else "Greek"
    return book_num, chapter, verse, lang

# ─── English verse ────────────────────────────────────────────────────────────

def fetch_english_verse(ref_str):
    try:
        url = f"https://bible-api.com/{urllib.parse.quote(ref_str)}?translation=kjv"
        with urllib.request.urlopen(url, timeout=8) as r:
            return json.loads(r.read().decode()).get("text", "").strip()
    except Exception:
        return None

# ─── Main API ─────────────────────────────────────────────────────────────────

def get_web_result(ref_str, show_all=False):
    """
    Look up a verse and return flagged_words — words whose Strong's number
    appears in lexicon/mistranslations.json.

    Each flagged word has:
      original        — Greek/Hebrew word as written in the manuscript
      translit        — romanised transliteration
      strong          — Strong's number (e.g. G932)
      morph           — grammatical form code
      gloss           — brief English gloss from the STEPBible dataset
      mistranslation  — full entry from mistranslations.json, including
                        english_flattened, actual_meaning, why_mistranslated,
                        cross_refs, author

    Pass show_all=True to also receive all_words (every word in the verse,
    flagged and unflagged alike).
    """
    result = {
        "query":         ref_str,
        "reference":     ref_str,
        "book":          None,
        "language":      None,
        "chapter":       None,
        "verse":         None,
        "english_kjv":   None,
        "flagged_words": [],
        "flagged_count": 0,
        "error":         None,
    }

    book_num, chapter, verse, lang = parse_reference(ref_str)
    if book_num is None:
        result["error"] = (
            f"Could not parse '{ref_str}'. "
            "Format: Matthew 6:33 | John 3:16 | Genesis 1:1"
        )
        return result

    result["book"]      = BOOK_DISPLAY.get(book_num, "Unknown")
    result["language"]  = lang
    result["chapter"]   = chapter
    result["verse"]     = verse
    result["reference"] = f"{result['book']} {chapter}:{verse}"
    result["english_kjv"] = fetch_english_verse(result["reference"])

    step_code = NUM_TO_STEP.get(book_num)
    if not step_code:
        result["error"] = f"No data code for book #{book_num}"
        return result

    verse_data = _load_bible().get(f"{step_code}.{chapter}.{verse}")
    if not verse_data:
        result["error"] = (
            f"'{result['reference']}' not found in bundled data. "
            "Check that data/bible_words.json is present."
        )
        return result

    lexicon  = _load_lexicon()
    flagged  = []
    all_words = []

    for wd in verse_data:
        strong = (wd.get("strong") or "").upper()
        entry = {
            "original": wd.get("orig", ""),
            "translit": wd.get("translit", ""),
            "strong":   strong,
            "morph":    wd.get("morph", ""),
            "gloss":    wd.get("eng", "") or wd.get("gloss", ""),
        }
        if strong in lexicon:
            entry["mistranslation"] = lexicon[strong]
            flagged.append(entry)
        if show_all:
            all_words.append(entry)

    result["flagged_words"] = flagged
    result["flagged_count"] = len(flagged)
    if show_all:
        result["all_words"] = all_words

    return result


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    ref = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else "Matthew 6:33"
    r = get_web_result(ref, show_all=True)
    print(f"\n{r['reference']}  ({r['language']})")
    if r.get("english_kjv"):
        print(f"KJV: {r['english_kjv']}\n")
    if r.get("error"):
        print(f"Error: {r['error']}")
        raise SystemExit(1)
    print(f"Flagged: {r['flagged_count']}")
    for w in r["flagged_words"]:
        mt = w["mistranslation"]
        print(f"  {w['original']} ({w['translit']}) [{w['strong']}]")
        print(f"    EN flattens to : {mt.get('english_flattened', '')}")
        print(f"    Actual meaning : {mt.get('actual_meaning', '')[:100]}...")
        print()
