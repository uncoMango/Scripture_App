# -*- coding: utf-8 -*-
"""Scripture search backend — offline interlinear via bundled STEPBible data.
CC BY 4.0 — Tyndale House / STEPBible.org  (data/bible_words.json)
"""

import json
import os
import re

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_PATH = os.path.join(_HERE, "data", "bible_words.json")

_bible: dict | None = None

def _load_bible() -> dict:
    global _bible
    if _bible is None:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _bible = json.load(f)
    return _bible

# ---------------------------------------------------------------------------
# Book-name → STEPBible abbreviation
# ---------------------------------------------------------------------------
_BOOK_MAP: dict[str, str] = {
    # OT
    "genesis": "Gen", "gen": "Gen",
    "exodus": "Exo", "exo": "Exo", "exod": "Exo",
    "leviticus": "Lev", "lev": "Lev",
    "numbers": "Num", "num": "Num",
    "deuteronomy": "Deu", "deut": "Deu", "deu": "Deu",
    "joshua": "Jos", "josh": "Jos", "jos": "Jos",
    "judges": "Jdg", "judg": "Jdg", "jdg": "Jdg",
    "ruth": "Rut", "rut": "Rut",
    "1 samuel": "1Sa", "1samuel": "1Sa", "1sa": "1Sa", "1sam": "1Sa",
    "2 samuel": "2Sa", "2samuel": "2Sa", "2sa": "2Sa", "2sam": "2Sa",
    "1 kings": "1Ki", "1kings": "1Ki", "1ki": "1Ki", "1kgs": "1Ki",
    "2 kings": "2Ki", "2kings": "2Ki", "2ki": "2Ki", "2kgs": "2Ki",
    "1 chronicles": "1Ch", "1chronicles": "1Ch", "1ch": "1Ch", "1chr": "1Ch",
    "2 chronicles": "2Ch", "2chronicles": "2Ch", "2ch": "2Ch", "2chr": "2Ch",
    "ezra": "Ezr", "ezr": "Ezr",
    "nehemiah": "Neh", "neh": "Neh",
    "esther": "Est", "esth": "Est", "est": "Est",
    "job": "Job",
    "psalms": "Psa", "psalm": "Psa", "ps": "Psa", "psa": "Psa",
    "proverbs": "Pro", "prov": "Pro", "pro": "Pro",
    "ecclesiastes": "Ecc", "eccl": "Ecc", "ecc": "Ecc",
    "song of solomon": "Sng", "song of songs": "Sng", "song": "Sng", "sng": "Sng",
    "isaiah": "Isa", "isa": "Isa",
    "jeremiah": "Jer", "jer": "Jer",
    "lamentations": "Lam", "lam": "Lam",
    "ezekiel": "Ezk", "ezek": "Ezk", "ezk": "Ezk",
    "daniel": "Dan", "dan": "Dan",
    "hosea": "Hos", "hos": "Hos",
    "joel": "Jol", "jol": "Jol",
    "amos": "Amo", "amo": "Amo",
    "obadiah": "Oba", "obad": "Oba", "oba": "Oba",
    "jonah": "Jon", "jon": "Jon",
    "micah": "Mic", "mic": "Mic",
    "nahum": "Nam", "nah": "Nam", "nam": "Nam",
    "habakkuk": "Hab", "hab": "Hab",
    "zephaniah": "Zep", "zeph": "Zep", "zep": "Zep",
    "haggai": "Hag", "hag": "Hag",
    "zechariah": "Zec", "zech": "Zec", "zec": "Zec",
    "malachi": "Mal", "mal": "Mal",
    # NT
    "matthew": "Mat", "matt": "Mat", "mat": "Mat",
    "mark": "Mrk", "mrk": "Mrk",
    "luke": "Luk", "luk": "Luk",
    "john": "Jhn", "jhn": "Jhn",
    "acts": "Act", "act": "Act",
    "romans": "Rom", "rom": "Rom",
    "1 corinthians": "1Co", "1corinthians": "1Co", "1co": "1Co", "1cor": "1Co",
    "2 corinthians": "2Co", "2corinthians": "2Co", "2co": "2Co", "2cor": "2Co",
    "galatians": "Gal", "gal": "Gal",
    "ephesians": "Eph", "eph": "Eph",
    "philippians": "Php", "phil": "Php", "php": "Php",
    "colossians": "Col", "col": "Col",
    "1 thessalonians": "1Th", "1thessalonians": "1Th", "1th": "1Th", "1thess": "1Th",
    "2 thessalonians": "2Th", "2thessalonians": "2Th", "2th": "2Th", "2thess": "2Th",
    "1 timothy": "1Ti", "1timothy": "1Ti", "1ti": "1Ti", "1tim": "1Ti",
    "2 timothy": "2Ti", "2timothy": "2Ti", "2ti": "2Ti", "2tim": "2Ti",
    "titus": "Tit", "tit": "Tit",
    "philemon": "Phm", "phlm": "Phm", "phm": "Phm",
    "hebrews": "Heb", "heb": "Heb",
    "james": "Jas", "jas": "Jas",
    "1 peter": "1Pe", "1peter": "1Pe", "1pe": "1Pe", "1pet": "1Pe",
    "2 peter": "2Pe", "2peter": "2Pe", "2pe": "2Pe", "2pet": "2Pe",
    "1 john": "1Jn", "1john": "1Jn", "1jn": "1Jn",
    "2 john": "2Jn", "2john": "2Jn", "2jn": "2Jn",
    "3 john": "3Jn", "3john": "3Jn", "3jn": "3Jn",
    "jude": "Jud", "jud": "Jud",
    "revelation": "Rev", "rev": "Rev",
}

_OT_BOOKS = {
    "Gen","Exo","Lev","Num","Deu","Jos","Jdg","Rut","1Sa","2Sa",
    "1Ki","2Ki","1Ch","2Ch","Ezr","Neh","Est","Job","Psa","Pro",
    "Ecc","Sng","Isa","Jer","Lam","Ezk","Dan","Hos","Jol","Amo",
    "Oba","Jon","Mic","Nam","Hab","Zep","Hag","Zec","Mal",
}

# ---------------------------------------------------------------------------
# 25 hand-written lexicon entries
# ---------------------------------------------------------------------------
LEXICON: dict[str, dict] = {
    # ── Greek (NT) ─────────────────────────────────────────────────────────
    "G26": {
        "lemma": "ἀγάπη", "translit": "agapē", "pos": "noun",
        "gloss": "love",
        "definition": (
            "Unconditional, self-giving love — the characteristic love of God "
            "poured out for humanity regardless of merit (Rom 5:8; 1 Jn 4:8). "
            "Distinct from philía (friendship) and érōs (desire); agapē chooses "
            "the good of the other at personal cost."
        ),
        "usage_note": "Used 116× in NT; central to Pauline ethics (1 Cor 13) and Johannine theology.",
        "cross_refs": ["1 Cor 13:4–7", "Rom 5:8", "1 Jn 4:8", "Jn 3:16"],
    },
    "G27": {
        "lemma": "ἀγαπητός", "translit": "agapētos", "pos": "adjective",
        "gloss": "beloved",
        "definition": "Dearly loved; used of Jesus as the Father's beloved Son (Mt 3:17) and of fellow believers.",
        "usage_note": "Often a term of address in epistles ('dear friends').",
        "cross_refs": ["Mt 3:17", "Rom 1:7", "1 Jn 3:2"],
    },
    "G40": {
        "lemma": "ἅγιος", "translit": "hagios", "pos": "adjective/noun",
        "gloss": "holy, saint",
        "definition": (
            "Set apart for God; morally pure; consecrated. As a noun (οἱ ἅγιοι) "
            "it designates the people of God — 'the saints.' The Holy Spirit is "
            "the πνεῦμα ἅγιον, the Spirit who is wholly other and who sanctifies."
        ),
        "usage_note": "One of the most frequent theological adjectives in the NT (233×).",
        "cross_refs": ["1 Pet 1:16", "Rev 4:8", "Rom 1:7"],
    },
    "G166": {
        "lemma": "αἰώνιος", "translit": "aiōnios", "pos": "adjective",
        "gloss": "eternal, everlasting",
        "definition": (
            "Of or belonging to the age (αἰών) to come; having the quality of "
            "divine life that neither began nor ends. 'Eternal life' (ζωὴ αἰώνιος) "
            "in John is not merely unending existence but the life of the age — "
            "participation in God's own life beginning now."
        ),
        "usage_note": "71× in NT; 43 of those in John + 1 John.",
        "cross_refs": ["Jn 17:3", "Rom 6:23", "1 Jn 5:11"],
    },
    "G575": {
        "lemma": "ἀπό", "translit": "apo", "pos": "preposition",
        "gloss": "from, away from",
        "definition": "Separation or origin; used with genitive to indicate source, cause, or partitive sense.",
        "usage_note": "Distinguishable from ἐκ (out from within) — ἀπό stresses departure from a point.",
        "cross_refs": ["Mt 3:16", "Jn 1:44"],
    },
    "G932": {
        "lemma": "βασιλεία", "translit": "basileia", "pos": "noun",
        "gloss": "kingdom, reign",
        "definition": (
            "The sovereign rule of God, not merely a territory but the dynamic "
            "exercise of kingly authority. In the Synoptics Jesus announces that "
            "this reign has drawn near (ἤγγικεν) and invades the present age through "
            "his ministry, while its fullness remains future (Mt 6:10). Seeking it "
            "first (Mt 6:33) means ordering all of life under God's reign."
        ),
        "usage_note": "162× in NT; 'kingdom of heaven' (βασιλεία τῶν οὐρανῶν) is Matthew's preferred form.",
        "cross_refs": ["Mt 6:33", "Mk 1:15", "Lk 17:21", "Jn 3:3", "Rom 14:17"],
    },
    "G1343": {
        "lemma": "δικαιοσύνη", "translit": "dikaiosynē", "pos": "noun",
        "gloss": "righteousness, justice",
        "definition": (
            "Conformity to God's standard; the state of being in right relationship "
            "with God and others. Paul uses it forensically (imputed righteousness "
            "through faith, Rom 3:22) while Matthew emphasises ethical conduct that "
            "exceeds that of the scribes (Mt 5:20)."
        ),
        "usage_note": "92× in NT; pivotal in Romans and Galatians.",
        "cross_refs": ["Rom 3:22", "Mt 5:6", "Mt 6:33", "Phil 3:9"],
    },
    "G1411": {
        "lemma": "δύναμις", "translit": "dynamis", "pos": "noun",
        "gloss": "power, miracle",
        "definition": (
            "Inherent power or ability; miraculous deeds ('mighty works'). "
            "Distinguishable from ἐξουσία (authority/right to act) — δύναμις "
            "is the energy itself. The Spirit provides δύναμις for witness (Acts 1:8)."
        ),
        "usage_note": "119× in NT; also the root of 'dynamite.'",
        "cross_refs": ["Acts 1:8", "Rom 1:16", "1 Cor 1:18"],
    },
    "G1515": {
        "lemma": "εἰρήνη", "translit": "eirēnē", "pos": "noun",
        "gloss": "peace",
        "definition": (
            "Wholeness, well-being, harmony — the Greek equivalent of Hebrew שָׁלוֹם. "
            "More than the absence of conflict; it is positive flourishing in right "
            "relationship with God and neighbour. Christ is our peace (Eph 2:14)."
        ),
        "usage_note": "92× in NT; standard greeting in Pauline letters.",
        "cross_refs": ["Jn 14:27", "Phil 4:7", "Eph 2:14", "Rom 5:1"],
    },
    "G1680": {
        "lemma": "ἐλπίς", "translit": "elpis", "pos": "noun",
        "gloss": "hope",
        "definition": (
            "Confident expectation of future good, grounded in God's promises and "
            "resurrection of Christ — not wishful thinking but assured trust. "
            "One of Paul's triad: faith, hope, love (1 Cor 13:13)."
        ),
        "usage_note": "53× in NT; frequently eschatological in Paul.",
        "cross_refs": ["Rom 8:24", "1 Cor 13:13", "Heb 11:1", "1 Pet 1:3"],
    },
    "G2222": {
        "lemma": "ζωή", "translit": "zōē", "pos": "noun",
        "gloss": "life",
        "definition": (
            "Life in its fullest sense — physical, spiritual, and eternal. John "
            "distinguishes ζωή (divine/spiritual life) from βίος (biological life). "
            "'I am the way, the truth, and the life' (Jn 14:6)."
        ),
        "usage_note": "135× in NT; 36 in John alone.",
        "cross_refs": ["Jn 1:4", "Jn 10:10", "Jn 14:6", "Rom 6:23"],
    },
    "G2316": {
        "lemma": "θεός", "translit": "theos", "pos": "noun",
        "gloss": "God",
        "definition": (
            "The one true God of Israel, Father of Jesus Christ. Occasionally "
            "used of false gods (1 Cor 8:5) or of powerful beings (Jn 10:34). "
            "The NT develops a Trinitarian understanding while maintaining "
            "monotheism — there is one θεός, revealed in three persons."
        ),
        "usage_note": "Occurs ~1,300× in NT — the most common theological noun.",
        "cross_refs": ["Jn 1:1", "Jn 4:24", "1 Jn 4:8", "Rom 11:33"],
    },
    "G2424": {
        "lemma": "Ἰησοῦς", "translit": "Iēsous", "pos": "noun (proper)",
        "gloss": "Jesus",
        "definition": (
            "Greek form of Hebrew יֵשׁוּעַ (Yeshua), meaning 'YHWH saves.' "
            "The personal name of the Messiah, Son of God. Matthew 1:21 gives "
            "the theological etymology: 'he will save his people from their sins.'"
        ),
        "usage_note": "917× in NT.",
        "cross_refs": ["Mt 1:21", "Acts 4:12", "Phil 2:10"],
    },
    "G3056": {
        "lemma": "λόγος", "translit": "logos", "pos": "noun",
        "gloss": "word, reason",
        "definition": (
            "Word, speech, message, or reason. In John 1:1 the Logos is the "
            "pre-existent divine Word through whom all things were made and who "
            "became flesh (1:14). In general NT usage it often means the 'word' "
            "of God — the gospel message proclaimed."
        ),
        "usage_note": "330× in NT; 40 in John.",
        "cross_refs": ["Jn 1:1–14", "Heb 4:12", "Rev 19:13"],
    },
    "G3341": {
        "lemma": "μετάνοια", "translit": "metanoia", "pos": "noun",
        "gloss": "repentance",
        "definition": (
            "A change of mind, direction, and heart — turning from sin toward God. "
            "Not mere remorse (λύπη) but a transformative reorientation. "
            "John the Baptist and Jesus both open with a call to μετάνοια (Mt 3:2; 4:17)."
        ),
        "usage_note": "22× in NT; foundational to apostolic preaching (Acts 2:38).",
        "cross_refs": ["Mt 3:2", "Acts 2:38", "2 Cor 7:10", "Lk 15:7"],
    },
    "G3952": {
        "lemma": "παρουσία", "translit": "parousia", "pos": "noun",
        "gloss": "coming, presence",
        "definition": (
            "Arrival, presence, or official visit — used in Greek culture for a "
            "royal visit. In NT eschatology, the parousia is the visible return of "
            "Christ in glory (Mt 24:3; 1 Thess 4:15)."
        ),
        "usage_note": "24× in NT; major eschatological term.",
        "cross_refs": ["Mt 24:3", "1 Thess 4:15–17", "2 Pet 3:4"],
    },
    "G3962": {
        "lemma": "πατήρ", "translit": "patēr", "pos": "noun",
        "gloss": "father",
        "definition": (
            "Father — biological, ancestral, or the divine Father. Jesus's "
            "distinctive address Ἀββά (Mk 14:36) reveals intimacy with God as "
            "Father. Believers share this sonship by adoption (υἱοθεσία, Rom 8:15)."
        ),
        "usage_note": "413× in NT; 122 in John.",
        "cross_refs": ["Mt 6:9", "Jn 1:14", "Rom 8:15", "Gal 4:6"],
    },
    "G4102": {
        "lemma": "πίστις", "translit": "pistis", "pos": "noun",
        "gloss": "faith, trust",
        "definition": (
            "Trust, reliance, faithfulness. In Paul, saving faith (πίστις) is the "
            "means by which righteousness is received — not a human work but a "
            "response of trust in Christ's faithfulness (πίστις Χριστοῦ). "
            "In Heb 11:1 it is 'the assurance of things hoped for.'"
        ),
        "usage_note": "243× in NT; cornerstone of Pauline soteriology.",
        "cross_refs": ["Rom 1:17", "Gal 2:20", "Heb 11:1", "Jas 2:17"],
    },
    "G4151": {
        "lemma": "πνεῦμα", "translit": "pneuma", "pos": "noun",
        "gloss": "spirit, wind, breath",
        "definition": (
            "Spirit, wind, or breath. Referring to the Holy Spirit (πνεῦμα ἅγιον), "
            "the third person of the Trinity — the divine presence given to believers "
            "at Pentecost (Acts 2) who indwells, empowers, and sanctifies."
        ),
        "usage_note": "379× in NT; 'Holy Spirit' combination 93×.",
        "cross_refs": ["Jn 3:8", "Acts 2:1–4", "Rom 8:9–16", "Gal 5:22"],
    },
    "G4561": {
        "lemma": "σάρξ", "translit": "sarx", "pos": "noun",
        "gloss": "flesh",
        "definition": (
            "Physical body, human nature, or the fallen sinful nature. Context "
            "determines meaning: in Jn 1:14 ('the Word became flesh') it affirms "
            "real incarnation; in Rom 8 σάρξ denotes the rebellious human nature "
            "opposed to the Spirit."
        ),
        "usage_note": "147× in NT; rich theological range from neutral to deeply ethical.",
        "cross_refs": ["Jn 1:14", "Rom 8:3–8", "Gal 5:16–17"],
    },
    "G4991": {
        "lemma": "σωτηρία", "translit": "sōtēria", "pos": "noun",
        "gloss": "salvation",
        "definition": (
            "Deliverance, rescue, preservation — from sin, death, and judgment. "
            "Encompasses justification (past), sanctification (present), and "
            "glorification (future). 'There is salvation in no one else' (Acts 4:12)."
        ),
        "usage_note": "46× in NT.",
        "cross_refs": ["Acts 4:12", "Rom 1:16", "Eph 2:8", "Heb 2:3"],
    },
    "G5207": {
        "lemma": "υἱός", "translit": "huios", "pos": "noun",
        "gloss": "son",
        "definition": (
            "Son — biological or metaphorical. 'Son of God' (υἱὸς θεοῦ) identifies "
            "Jesus's unique divine relationship. 'Son of Man' (υἱὸς τοῦ ἀνθρώπου) "
            "is Jesus's self-designation, evoking Dan 7:13."
        ),
        "usage_note": "377× in NT.",
        "cross_refs": ["Mt 16:16", "Mk 14:62", "Jn 3:16", "Dan 7:13"],
    },
    "G5485": {
        "lemma": "χάρις", "translit": "charis", "pos": "noun",
        "gloss": "grace",
        "definition": (
            "Unmerited favour, gift freely given. God's grace is the source of "
            "salvation (Eph 2:8), apostolic calling (Gal 1:15), and spiritual gifts "
            "χαρίσματα. The standard NT greeting 'grace and peace' (χάρις καὶ εἰρήνη) "
            "fuses Greek and Hebrew idioms."
        ),
        "usage_note": "155× in NT; 100 of those in Paul.",
        "cross_refs": ["Eph 2:8", "Jn 1:14", "2 Cor 12:9", "Tit 2:11"],
    },
    "G5547": {
        "lemma": "Χριστός", "translit": "Christos", "pos": "noun (proper)",
        "gloss": "Christ, Anointed One",
        "definition": (
            "Greek translation of Hebrew מָשִׁיחַ (Mashiach), the Anointed One. "
            "Originally a title, by Paul's letters it functions almost as a proper "
            "name. Jesus is the long-awaited royal and priestly Messiah of Israel."
        ),
        "usage_note": "531× in NT.",
        "cross_refs": ["Mt 16:16", "Jn 1:41", "Acts 2:36", "Phil 2:11"],
    },

    # ── Hebrew (OT) ────────────────────────────────────────────────────────
    "H539": {
        "lemma": "אָמַן", "translit": "ʾāman", "pos": "verb",
        "gloss": "to believe, be faithful, confirm",
        "definition": (
            "Root of אֱמוּנָה (faithfulness) and אָמֵן (amen). In the Hiphil, "
            "'to believe/trust' (Gen 15:6 — Abraham believed God). Conveys "
            "stability and reliability — faith as firm trust in a trustworthy God."
        ),
        "usage_note": "Gen 15:6 is the foundational OT text Paul cites in Rom 4 and Gal 3.",
        "cross_refs": ["Gen 15:6", "Isa 7:9", "Hab 2:4"],
    },
    "H571": {
        "lemma": "אֱמֶת", "translit": "ʾemet", "pos": "noun",
        "gloss": "truth, faithfulness, reliability",
        "definition": (
            "Derived from אָמַן; denotes that which is firm, reliable, and trustworthy. "
            "God's truth is a covenant reality — his word and ways are dependable. "
            "Often paired with חֶסֶד (steadfast love): 'truth and love' (Ps 117:2)."
        ),
        "usage_note": "127× in OT.",
        "cross_refs": ["Ps 117:2", "Ps 119:160", "Jn 14:6"],
    },
    "H1285": {
        "lemma": "בְּרִית", "translit": "bĕrît", "pos": "noun",
        "gloss": "covenant",
        "definition": (
            "A binding agreement, often sealed with blood or oath. God's covenants "
            "with Noah, Abraham, Moses, David, and the New Covenant (Jer 31:31) "
            "are the backbone of biblical theology. They are God's sovereign "
            "commitments that drive the whole redemptive story."
        ),
        "usage_note": "287× in OT.",
        "cross_refs": ["Gen 15:18", "Ex 24:8", "Jer 31:31", "Heb 8:6"],
    },
    "H1288": {
        "lemma": "בָּרַךְ", "translit": "bārak", "pos": "verb",
        "gloss": "to bless",
        "definition": (
            "To bestow favour, prosperity, and life — used both of God blessing "
            "humans and humans blessing God (praise). The Abrahamic blessing "
            "(Gen 12:2–3) is the channel through which all nations receive blessing."
        ),
        "usage_note": "330× in OT in various stems.",
        "cross_refs": ["Gen 1:22", "Gen 12:2", "Num 6:24", "Ps 103:1"],
    },
    "H2617": {
        "lemma": "חֶסֶד", "translit": "ḥesed", "pos": "noun",
        "gloss": "steadfast love, lovingkindness, covenant loyalty",
        "definition": (
            "One of the richest Hebrew words — denotes loyal love that goes beyond "
            "obligation, the covenant faithfulness of God who does not abandon his "
            "people. Translated variously as 'steadfast love' (ESV), 'lovingkindness' "
            "(KJV/NASB), or 'mercy.' Ps 136 repeats 'his חֶסֶד endures forever' 26×."
        ),
        "usage_note": "245× in OT; 127 in Psalms.",
        "cross_refs": ["Ex 34:6–7", "Ps 136", "Lam 3:22", "Mic 6:8"],
    },
    "H3068": {
        "lemma": "יהוה", "translit": "YHWH", "pos": "noun (proper)",
        "gloss": "LORD (the personal name of Israel's God)",
        "definition": (
            "The divine name revealed to Moses (Ex 3:14–15): 'I AM WHO I AM' "
            "(אֶהְיֶה אֲשֶׁר אֶהְיֶה). Expresses God's self-existent, eternal being. "
            "Traditionally read as Adonai ('Lord') out of reverence. "
            "Rendered LORD (small caps) in most English translations."
        ),
        "usage_note": "~6,828× in OT — the most frequent noun in the Hebrew Bible.",
        "cross_refs": ["Ex 3:14", "Ex 34:6", "Ps 23:1", "Isa 40:28"],
    },
    "H3820": {
        "lemma": "לֵב", "translit": "lēb", "pos": "noun",
        "gloss": "heart, mind, will",
        "definition": (
            "The centre of inner life — not primarily emotion (as in modern usage) "
            "but the seat of thought, will, and moral decision. The Shema calls "
            "for love with all one's לֵב (Deut 6:5). God looks at the heart (1 Sam 16:7)."
        ),
        "usage_note": "850× in OT (also לֵבָב, the longer form).",
        "cross_refs": ["Deut 6:5", "1 Sam 16:7", "Ps 51:10", "Prov 4:23"],
    },
    "H430": {
        "lemma": "אֱלֹהִים", "translit": "ʾĕlōhîm", "pos": "noun",
        "gloss": "God, gods",
        "definition": (
            "The standard Hebrew word for God — morphologically plural but "
            "overwhelmingly used with singular verbs when referring to Israel's God, "
            "often explained as a 'plural of majesty' or fullness. The first word "
            "used for God in Scripture (Gen 1:1). Also used for the gods of the nations "
            "and occasionally for human judges or heavenly beings."
        ),
        "usage_note": "2,602× in OT; 32× in Genesis 1 alone.",
        "cross_refs": ["Gen 1:1", "Deut 6:4", "Ps 82:1", "Jn 1:1"],
    },
    "H5315": {
        "lemma": "נֶפֶשׁ", "translit": "nepeš", "pos": "noun",
        "gloss": "soul, life, person, desire",
        "definition": (
            "The living being as a whole — not an immortal soul imprisoned in a "
            "body (Greek dualism) but the whole person animated by God's breath. "
            "'God breathed into his nostrils the breath of life and man became "
            "a living נֶפֶשׁ' (Gen 2:7). Also means appetite, desire, or throat."
        ),
        "usage_note": "754× in OT; often translated 'soul' but 'person' or 'life' is frequently more accurate.",
        "cross_refs": ["Gen 2:7", "Deut 6:5", "Ps 103:1", "Isa 53:10–12"],
    },
    "H7307": {
        "lemma": "רוּחַ", "translit": "rûaḥ", "pos": "noun",
        "gloss": "spirit, wind, breath",
        "definition": (
            "Wind, breath, or spirit — the animating force of life and the presence "
            "of God. The רוּחַ of God hovers over the waters (Gen 1:2), empowers "
            "judges and prophets, and in the new covenant promise will be poured "
            "out on all flesh (Joel 2:28)."
        ),
        "usage_note": "389× in OT.",
        "cross_refs": ["Gen 1:2", "Ezek 37:1–14", "Joel 2:28", "Isa 61:1"],
    },
    "H7965": {
        "lemma": "שָׁלוֹם", "translit": "šālôm", "pos": "noun",
        "gloss": "peace, wholeness, well-being",
        "definition": (
            "Far richer than the absence of war — שָׁלוֹם encompasses completeness, "
            "prosperity, health, and right relationship. The Aaronic blessing "
            "(Num 6:26) asks God to give שָׁלוֹם. The messianic prince is 'Prince of "
            "Peace' (שַׂר שָׁלוֹם, Isa 9:6)."
        ),
        "usage_note": "237× in OT.",
        "cross_refs": ["Num 6:24–26", "Isa 9:6", "Isa 53:5", "Ps 29:11"],
    },
    "H8199": {
        "lemma": "שָׁפַט", "translit": "šāpaṭ", "pos": "verb",
        "gloss": "to judge, govern, vindicate",
        "definition": (
            "To act as ruler-judge, executing justice and delivering the oppressed. "
            "The 'judges' (שֹׁפְטִים) of Israel were military deliverers. God as judge "
            "both punishes evil and vindicates the righteous — his judgment is "
            "ultimately good news for the poor (Ps 82:3)."
        ),
        "usage_note": "203× in OT.",
        "cross_refs": ["Gen 18:25", "Ps 82:3", "Isa 11:4", "Mic 6:8"],
    },
}

# ---------------------------------------------------------------------------
# Reference parsing
# ---------------------------------------------------------------------------
_REF_RE = re.compile(
    r'^([1-3]?\s*[A-Za-z ]+?)\s+(\d+)[:\.](\d+)$',
    re.IGNORECASE,
)

def _parse_reference(ref: str) -> tuple[str, int, int] | None:
    """Return (step_book_code, chapter, verse) or None."""
    ref = ref.strip()
    m = _REF_RE.match(ref)
    if not m:
        return None
    book_raw = m.group(1).strip().lower()
    chapter  = int(m.group(2))
    verse    = int(m.group(3))
    code = _BOOK_MAP.get(book_raw)
    if code is None:
        # try removing internal spaces
        code = _BOOK_MAP.get(book_raw.replace(" ", ""))
    return (code, chapter, verse) if code else None

# ---------------------------------------------------------------------------
# Core lookup
# ---------------------------------------------------------------------------
def get_web_result(reference: str) -> dict:
    """Return interlinear word list for a Bible verse from bundled STEPBible data."""
    parsed = _parse_reference(reference)
    if not parsed:
        return {"error": f"Could not parse reference: {reference!r}"}

    book, chapter, verse = parsed
    key = f"{book}.{chapter}.{verse}"

    bible = _load_bible()
    raw_words = bible.get(key)
    if raw_words is None:
        return {
            "reference": reference,
            "key": key,
            "data_source": "bundled_stepbible",
            "error": f"Verse not found in bundled data: {key}",
        }

    lang = "Hebrew" if book in _OT_BOOKS else "Greek"
    words = []
    for w in raw_words:
        entry: dict = {
            "original":  w.get("orig", ""),
            "translit":  w.get("translit", ""),
            "english":   w.get("eng", ""),
            "strong":    w.get("strong", ""),
            "morph":     w.get("morph", ""),
            "lemma":     w.get("lemma", ""),
            "gloss":     w.get("gloss", ""),
            "language":  lang,
        }
        # Attach full lexicon entry if we have one
        lex = LEXICON.get(w.get("strong", ""))
        if lex:
            entry["lexicon"] = lex
        words.append(entry)

    return {
        "reference":   reference,
        "key":         key,
        "language":    lang,
        "data_source": "bundled_stepbible",
        "word_count":  len(words),
        "words":       words,
    }

# ---------------------------------------------------------------------------
# Simple word search across entire Bible
# ---------------------------------------------------------------------------
def search_strong(strong_id: str) -> list[dict]:
    """Return all verses containing a given Strong's number."""
    strong_id = strong_id.upper()
    bible = _load_bible()
    results = []
    for key, words in bible.items():
        for w in words:
            if w.get("strong") == strong_id:
                results.append({"verse": key, "word": w})
                break
    return results

def get_lexicon_entry(strong_id: str) -> dict | None:
    return LEXICON.get(strong_id.upper())
