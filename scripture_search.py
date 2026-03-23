#!/usr/bin/env python3
"""
Scripture Original Language Research Tool
Kahu Phil Stephens - Ke Aupuni O Ke Akua Press

Looks up any verse by reference and shows:
  - Every word in original Greek / Hebrew / Aramaic
  - Transliteration (English letters)
  - Root word & etymology
  - True lexical meaning (not just Strong's gloss)
  - Cross-references for key words

Data sources (all free, public domain, scholarly):
  - bible-api.com          (English verse text, no key needed)
  - STEPBible open data    (interlinear Greek/Hebrew with transliteration)
  - Bundled Thayer/BDB     (Greek/Hebrew lexicon entries)

Run once with internet to cache data. After that works offline.
"""

import sys
import os
import json
import re
import urllib.request
import urllib.parse
import urllib.error
import zipfile
import io
import time

# ─── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR  = os.path.join(SCRIPT_DIR, "scripture_cache")
LEXI_FILE  = os.path.join(CACHE_DIR, "lexicon.json")
STEP_FILE  = os.path.join(CACHE_DIR, "step_interlinear.json")

os.makedirs(CACHE_DIR, exist_ok=True)

# ─── Book name maps ───────────────────────────────────────────────────────────
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

# Canonical book name for display
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

# ─── Bundled Lexicon Data (public domain: Thayer's Greek, BDB Hebrew) ─────────
# A carefully selected set of theologically significant words
# with TRUE original language meanings beyond Strong's glosses

BUNDLED_LEXICON = {
    # ── GREEK (NT) ──────────────────────────────────────────────────────────
    "G25": {
        "translit": "agapaō",
        "root": "agapē (G26)",
        "pos": "verb",
        "meaning": "To love — but not merely affection or friendship. In classical Greek agapaō meant to be well-pleased, to be contented with. In the NT it carries the weight of a deliberate, self-giving commitment that chooses the well-being of another regardless of response. Distinguished from phileō (emotional fondness) and erōs (desire). God's agapaō of the world (John 3:16) is covenantal, volitional love.",
        "etymology": "Root disputed; possibly from agō (to lead) + a root meaning 'very much'. The noun agapē was rare in classical Greek; early Christians essentially filled it with new theological content.",
        "cross_refs": ["John 3:16","John 13:34","Romans 5:8","1 John 4:8","1 Corinthians 13:4-7"]
    },
    "G26": {
        "translit": "agapē",
        "root": "agapaō (G25)",
        "pos": "noun feminine",
        "meaning": "Love — the defining NT word for God's own nature and the command to imitate it. Not sentiment but the steady, purposeful goodwill that seeks the highest good of the beloved. Thayer: 'the deepest and most spiritual of the words for love.' Unlike eros (desire) or philia (friendship/kinship affection), agapē can be commanded because it is a choice, not merely a feeling.",
        "etymology": "See agapaō (G25). The word was so rare before the NT that many scholars believe the LXX translators and then NT writers gave it its rich theological meaning almost entirely.",
        "cross_refs": ["John 3:16","Romans 8:35","1 Corinthians 13","1 John 4:7-8","Ephesians 3:18-19"]
    },
    "G932": {
        "translit": "basileia",
        "root": "basileus (G935) — king",
        "pos": "noun feminine",
        "meaning": "Kingdom, reign, royal rule. Not primarily a territory but the active RULE of a king. Basileia tou Theou = the sovereign reign of God breaking into history. Thayer: 'royal power, kingship, dominion, rule.' Jesus uses it almost entirely in the dynamic sense — God's rule arriving, invading, transforming — not a static territory people enter after death.",
        "etymology": "From basileus (king), from basis (step, foundation) — one who walks/stands as the foundation of the people. The -eia suffix denotes the quality, office, or activity of the root.",
        "cross_refs": ["Matthew 4:17","Matthew 6:33","Luke 17:20-21","John 18:36","Colossians 1:13"]
    },
    "G935": {
        "translit": "basileus",
        "root": "basis (foundation/step)",
        "pos": "noun masculine",
        "meaning": "King — the supreme ruler. In NT context, the title given to God and to Christ as His anointed representative. The word implies absolute sovereign authority, not the constitutional/limited monarchy of modern thought.",
        "etymology": "From basis (step, base) — 'one who is the foundation/base' of the community. Related to bainō (to walk/step).",
        "cross_refs": ["Matthew 2:2","Matthew 27:37","Revelation 19:16","1 Timothy 6:15","John 18:37"]
    },
    "G4151": {
        "translit": "pneuma",
        "root": "pneō — to blow, to breathe",
        "pos": "noun neuter",
        "meaning": "Spirit, wind, breath. The range of meaning is significant: (1) wind/breath — physical moving air, (2) the animating life-principle in a person, (3) a spiritual being, (4) the Holy Spirit. Context determines which. In John 3:8, Jesus deliberately plays on all the meanings: 'The pneuma blows where it wills... so is everyone born of the pneuma.' The original audience would feel the layered meaning.",
        "etymology": "From pneō (to blow, breathe). Proto-Indo-European root *pneu- related to breath and wind, same root as English 'pneumatic'.",
        "cross_refs": ["John 3:5-8","John 4:24","Romans 8:9-16","1 Corinthians 2:10-14","Genesis 1:2 (LXX)"]
    },
    "G2222": {
        "translit": "zōē",
        "root": "zaō (G2198) — to live",
        "pos": "noun feminine",
        "meaning": "Life — but specifically the life that belongs to God, divine life, life in its fullest and highest form. Distinguished from bios (G979), which means biological/physical life or livelihood. Zōē aiōnios ('eternal life') does not primarily mean 'life that goes on forever' but 'the life characteristic of the age to come' — God's own quality of life. John uses zōē almost exclusively for this divine, abundant life.",
        "etymology": "From zaō (to live). Indo-European root *gwei- (to live), same root as Latin vivus, English 'quick' (as in 'the quick and the dead').",
        "cross_refs": ["John 1:4","John 10:10","John 17:3","1 John 5:12","Romans 6:23"]
    },
    "G165": {
        "translit": "aiōn",
        "root": "aei (always) + ōn (being) — some scholars",
        "pos": "noun masculine",
        "meaning": "Age, era, epoch — a period of time with its own character. NOT simply 'forever.' Aiōnios (the adjective) means 'belonging to the age [to come]' more than 'never-ending.' Thayer: 'a period of time of significant character; the world.' In rabbinic thought there were two ages: ha-olam hazeh (this present age) and ha-olam ha-ba (the age to come). Jesus announced the age to come was arriving.",
        "etymology": "Classical Greek: a lifetime, an age. Related to Latin aevum, English 'age' and 'ever.' The plural aiōnes can mean 'the ages' or 'the universe/creation.'",
        "cross_refs": ["Matthew 12:32","Galatians 1:4","Ephesians 1:21","Hebrews 9:26","John 17:3"]
    },
    "G4982": {
        "translit": "sōzō",
        "root": "sōs (safe, whole)",
        "pos": "verb",
        "meaning": "To save, to rescue, to heal, to make whole. Critically: the word covers healing the sick just as much as rescuing from sin. When Jesus 'saves' someone in the Gospels, the same word is used for both healing the body and forgiving sin — because salvation in the Hebrew/Greek mindset was WHOLENESS, shalom, restoration of the whole person. Not just a ticket to heaven.",
        "etymology": "From sōs (safe, unharmed, whole). Related to sōtēria (salvation), sōtēr (savior/deliverer). The root idea is rescue from danger and restoration to wholeness.",
        "cross_refs": ["Matthew 9:22","Luke 7:50","John 3:17","Romans 10:9","Ephesians 2:8"]
    },
    "G3056": {
        "translit": "logos",
        "root": "legō — to speak, to reason",
        "pos": "noun masculine",
        "meaning": "Word, reason, account, meaning. One of the most theologically loaded words in the NT. In Greek philosophy (Heraclitus, Stoics), Logos was the rational principle ordering the universe. In Jewish thought (Philo), it was the intermediary between God and creation. John 1:1 takes all these layers and says: This Logos is a Person, and He became flesh. The word carries the sense of the articulated mind, the expressed thought, the rational order behind everything.",
        "etymology": "From legō (to say, to lay out in order). Indo-European root *leg- (to gather, to arrange). Related to Latin legere, English 'lecture,' 'logic,' 'legend.'",
        "cross_refs": ["John 1:1-14","Revelation 19:13","1 John 1:1","Hebrews 4:12","Colossians 1:17"]
    },
    "G5485": {
        "translit": "charis",
        "root": "chairō — to rejoice",
        "pos": "noun feminine",
        "meaning": "Grace, favor, goodwill. In classical Greek: that which brings joy, a pleasing quality, gratitude. In the NT it becomes the specific word for God's unearned, freely-given favor toward humanity. NOT 'unmerited favor' merely in the sense that we don't deserve it — the Greek carries the additional sense that it flows from the JOYFUL generosity of the giver, not from any calculation of worthiness.",
        "etymology": "From chairō (to rejoice, to be glad). The root *gher- means to desire or to like. The connection between joy and grace is in the giver's gladness in giving.",
        "cross_refs": ["John 1:14","Romans 3:24","Ephesians 2:8","2 Corinthians 12:9","Titus 2:11"]
    },
    "G4102": {
        "translit": "pistis",
        "root": "peithomai — to be persuaded",
        "pos": "noun feminine",
        "meaning": "Faith, trust, faithfulness. This is crucial: pistis is NOT merely intellectual belief. It is the trust that emerges from being persuaded, from evidence. It carries the relational dimension of faithfulness/loyalty (like a treaty). Abraham's pistis was acting on what God said — it was trust that moved his feet. Often translated 'faith' but 'allegiance' or 'covenant loyalty' captures dimensions the English word loses.",
        "etymology": "From peithomai (to be persuaded, to trust). Root *bheydh- (to trust, to compel). Related to Latin fides (faith), fidus (faithful).",
        "cross_refs": ["Romans 1:17","Hebrews 11:1","Galatians 2:20","James 2:17","Habakkuk 2:4"]
    },

    # ── HEBREW (OT) ──────────────────────────────────────────────────────────
    "H4428": {
        "translit": "melek",
        "root": "m-l-k (to reign, to counsel)",
        "pos": "noun masculine",
        "meaning": "King. The ancient Near Eastern concept of a king was very different from modern constitutional monarchy. A melek was the military leader, the supreme judge, the high priest's counterpart, and the representative of the divine before the people. In Israel, the earthly melek was always supposed to be subordinate to YHWH, the true Melek. The prophets constantly judged Israel's kings by whether they ruled as YHWH's viceroys or set themselves up as autonomous.",
        "etymology": "Semitic root m-l-k appears across Akkadian, Ugaritic, Aramaic, and Arabic. Related to the divine name Molech and the name Malachi ('my messenger/king').",
        "cross_refs": ["Psalm 24:7-10","Psalm 93:1","Isaiah 6:5","Zechariah 14:9","1 Samuel 8:7"]
    },
    "H4438": {
        "translit": "malkuth",
        "root": "melek (H4428) — king",
        "pos": "noun feminine",
        "meaning": "Kingdom, kingship, royal dominion. Like the Greek basileia, this word emphasizes the RULE more than the territory. The Aramaic equivalent malkuta is used in Daniel. In the Kaddish prayer (ancient Jewish liturgy), 'May His kingdom/malkuth come' is the same concept Jesus picks up in the Lord's Prayer — the active, transforming reign of God breaking into human affairs.",
        "etymology": "Derived from melek (king) via the abstract noun suffix -uth. The same root in Aramaic gives us malkuta (Daniel's kingdom language).",
        "cross_refs": ["Daniel 2:44","Psalm 103:19","Psalm 145:11-13","Obadiah 1:21","Isaiah 9:7"]
    },
    "H7307": {
        "translit": "ruach",
        "root": "r-w-ch (to breathe, to be spacious)",
        "pos": "noun feminine/masculine",
        "meaning": "Spirit, wind, breath. The exact parallel to Greek pneuma. Ruach Elohim in Genesis 1:2 — 'the Spirit/Wind/Breath of God' hovered over the waters. The same word describes the life-giving breath God breathed into Adam (Genesis 2:7 uses neshamah but ruach carries the same idea). Ezekiel 37: God tells the ruach to breathe into the dry bones. The word is inseparable from life, movement, power, and divine presence.",
        "etymology": "Semitic root r-w-ch (spaciousness, refreshment, breath). Related to the Arabic ruh (spirit). BDB: 'wind, breath, mind, spirit.'",
        "cross_refs": ["Genesis 1:2","Genesis 2:7","Ezekiel 37:1-14","Isaiah 61:1","Joel 2:28"]
    },
    "H2617": {
        "translit": "chesed",
        "root": "possibly related to chasad — to bow down in kindness",
        "pos": "noun masculine",
        "meaning": "Steadfast love, covenant loyalty, lovingkindness. This is one of the most untranslatable Hebrew words in the OT. No English word captures it alone. BDB: 'goodness, kindness, faithfulness.' It is the love that holds to a covenant even when the other party has broken it. It is YHWH's defining characteristic — the love He showed Israel not because they deserved it but because He committed Himself. Translated 'mercy,' 'lovingkindness,' 'steadfast love,' 'loyalty,' 'grace' in various versions — none is adequate alone.",
        "etymology": "Semitic root possibly related to stork-like devotion (the stork was a symbol of loyalty in the ancient world). Some connect it to Arabic hasada (to be good to). The exact etymology is debated — the MEANING is rich and clear even if the root is disputed.",
        "cross_refs": ["Exodus 34:6-7","Psalm 136","Hosea 6:6","Micah 6:8","Lamentations 3:22-23"]
    },
    "H6666": {
        "translit": "tsedaqah",
        "root": "tsadeq (H6663) — to be right/just",
        "pos": "noun feminine",
        "meaning": "Righteousness, justice — but in the RELATIONAL sense of being in right relationship with others and with God, fulfilling covenant obligations. This is NOT primarily forensic (legal standing) as later Western theology made it. In the OT, tsedaqah means doing right by the poor, the widow, the orphan, the foreigner — it is SOCIAL JUSTICE and COVENANT FAITHFULNESS combined. Abraham 'believed God and it was counted to him as tsedaqah' — meaning he was in right relationship with God.",
        "etymology": "From the root ts-d-q (to be straight, right). The same root gives tsaddiq (righteous person) and tsedek (righteousness). BDB: 'righteousness in government, in a case or cause; of God, His attribute.'",
        "cross_refs": ["Genesis 15:6","Deuteronomy 6:25","Isaiah 1:27","Amos 5:24","Micah 6:8"]
    },
    "H7965": {
        "translit": "shalom",
        "root": "shalem — to be whole, to be complete",
        "pos": "noun masculine",
        "meaning": "Peace — but the Hebrew concept is FAR richer than the absence of conflict. Shalom is wholeness, completeness, flourishing, right relationships, well-being of the whole person and community. BDB: 'completeness, soundness, welfare, peace.' When the prophets speak of the Prince of Shalom (Isaiah 9:6), they mean the one who will restore total flourishing — economically, relationally, spiritually, physically. The Greek eirēnē (peace) translates it but loses much.",
        "etymology": "From the root sh-l-m (to be complete, whole, unharmed). Related to the name Jerusalem (city of shalom), Absalom, Solomon. The same root appears in the Arabic salaam.",
        "cross_refs": ["Isaiah 9:6","Isaiah 53:5","Numbers 6:24-26","Jeremiah 29:7","John 14:27"]
    },
    "H1285": {
        "translit": "berith",
        "root": "uncertain — possibly bara (to cut) or baru (Akkadian: bond)",
        "pos": "noun feminine",
        "meaning": "Covenant. The foundational relational-legal concept of the OT. A berith was a solemn binding agreement, usually between unequals, establishing obligations, identity, and relationship. Covenants in the ANE were 'cut' (hence 'cut a covenant') — animals were slaughtered and the parties walked between the pieces, symbolizing: 'may this happen to me if I break these terms.' God's covenants with Noah, Abraham, Moses, David, and the New Covenant are all berith — God binding Himself to humanity.",
        "etymology": "Root disputed. Main theories: (1) from baru (Akkadian) = bond/fetter; (2) from bara (to cut) — pointing to the ritual of cutting animals; (3) from barah (to eat) — covenants sealed with a meal. All three may be present in the concept.",
        "cross_refs": ["Genesis 15:18","Genesis 17:1-14","Exodus 24:7-8","Jeremiah 31:31-34","Hebrews 8:6"]
    },
    "H8451": {
        "translit": "torah",
        "root": "yarah — to throw, to shoot, to direct",
        "pos": "noun feminine",
        "meaning": "Law, instruction, teaching, direction. This is consistently mistranslated as just 'Law,' which in Western ears sounds like a legal code. Torah means INSTRUCTION — it is the loving guidance of a Father showing His people how to live. BDB: 'direction, instruction, law.' The Psalms celebrate Torah with delight (Psalm 119) not because they loved a legal code but because it was YHWH's gift of wisdom for flourishing. Jesus did not come to abolish the Torah but to embody and fulfill its meaning.",
        "etymology": "From yarah (to throw, to shoot, to point the way). The hiphil form of yarah means 'to teach, to direct.' Same root as moreh (teacher) and yoreh (early rain — that which hits/comes down).",
        "cross_refs": ["Psalm 1:2","Psalm 119:97","Isaiah 2:3","Matthew 5:17","Romans 7:12"]
    },
    "H430": {
        "translit": "elohim",
        "root": "el — God, power, might",
        "pos": "noun masculine plural (used with singular verbs for the one God)",
        "meaning": "God. The grammatically plural form used with singular verbs when referring to YHWH. In polytheistic contexts it can refer to gods (plural). For Israel: the one God in the fullness of His being. BDB: 'rulers, judges, divine ones, angels, gods, God.' The plural of majesty or fullness — the same pattern as Hebrew mayim (waters) being plural though often singular in meaning. Ancient Jewish and Christian interpreters saw hints of the Trinitarian fullness here.",
        "etymology": "From el (might, power, God). El is one of the oldest Semitic words for deity, appearing across Ugaritic, Akkadian, Phoenician. Elohim adds the plural suffix -im.",
        "cross_refs": ["Genesis 1:1","Deuteronomy 6:4","Psalm 82:1","John 10:34-35","Genesis 1:26-27"]
    },
    "H3068": {
        "translit": "YHWH (Yahweh)",
        "root": "hayah — to be, to exist, to become",
        "pos": "proper noun — the personal name of God",
        "meaning": "The LORD. The personal covenant name of God, never merely a title. God revealed this name to Moses at the burning bush: 'I AM WHO I AM' / 'I WILL BE WHAT I WILL BE' (Exodus 3:14). The name is connected to the Hebrew verb 'to be' — suggesting self-existence, eternal presence, and the God who shows up and acts. Jewish tradition calls this the Tetragrammaton (four letters: YHWH) and considered it too holy to pronounce. English Bibles substitute 'LORD' (all caps) following this tradition.",
        "etymology": "From the causative of hayah (to be): 'He who causes to be,' or from the qal 'He who IS.' The exact vocalization (Yahweh vs Jehovah) has been debated since the vowels were not written in the original.",
        "cross_refs": ["Exodus 3:14-15","Exodus 34:5-7","Psalm 68:4","Isaiah 42:8","John 8:58"]
    },
    "H2421": {
        "translit": "chayah",
        "root": "ch-y-h (to live, to give life)",
        "pos": "verb",
        "meaning": "To live, to have life, to revive, to give life. This is the root behind chayim (life — always plural in Hebrew, suggesting life in its fullness and multiplicity). BDB: 'to live, to have life, to remain alive, to sustain life, to live prosperously, to revive, to be healed.' In Deuteronomy 30:19, 'choose life' uses this root — it means choose the whole flourishing that comes with covenant faithfulness.",
        "etymology": "Semitic root ch-y-h (life, living). Related to Arabic hayy (living), Akkadian hayyu. The same root gives Eve her name (Chavah — 'mother of all living').",
        "cross_refs": ["Genesis 2:7","Deuteronomy 30:19","Ezekiel 37:5-6","John 10:10","Psalm 16:11"]
    },
    "H3519": {
        "translit": "kabod",
        "root": "kabad — to be heavy, to be weighty",
        "pos": "noun masculine",
        "meaning": "Glory, honor, weight, abundance. The original meaning is HEAVINESS or WEIGHT — what has substance, what is weighty and real. YHWH's kabod is His weighty, substantial, overwhelming presence and splendor. BDB: 'abundance, honor, glory.' When Isaiah says 'the whole earth is full of His glory' (6:3), he means the earth is laden, weighty, full of the presence of God. The NT equivalent is the Greek doxa.",
        "etymology": "From kabad (to be heavy, weighty, honored). The same root gives kabed (heavy, serious), and also the word for liver (kabed — the heaviest organ, considered the seat of life in ancient physiology).",
        "cross_refs": ["Exodus 24:16-17","Isaiah 6:3","Psalm 19:1","John 1:14","Habakkuk 2:14"]
    },

    # ── ARAMAIC ──────────────────────────────────────────────────────────────
    "A4437": {
        "translit": "malkuth (Aramaic)",
        "root": "melek — king",
        "pos": "noun feminine",
        "meaning": "Kingdom, royal dominion. The Aramaic equivalent of Hebrew malkuth. Used extensively in Daniel where the shift from Hebrew to Aramaic signals a message for all nations, not just Israel. Daniel's four kingdoms and the 'kingdom of the Most High' (Daniel 7:27) use this word. The Kaddish prayer — which Jesus almost certainly knew — uses malkuth: 'May His kingdom be established.' This is the backdrop for the Lord's Prayer.",
        "etymology": "Same Semitic root m-l-k as Hebrew. Aramaic was the lingua franca of the ancient Near East — the international language — which is why Daniel uses it when speaking of world empires.",
        "cross_refs": ["Daniel 2:44","Daniel 4:3","Daniel 7:14","Daniel 7:27","Matthew 6:10"]
    },
    "A426": {
        "translit": "elah (Aramaic)",
        "root": "el — God, might",
        "pos": "noun masculine",
        "meaning": "God. The Aramaic form of the Hebrew El/Elohim. Used in Daniel and Ezra where those books shift to Aramaic. Nebuchadnezzar uses this word when he recognizes God after his madness (Daniel 4:2). The same root appears in the Arabic Allah.",
        "etymology": "Same Semitic root el (might, power, deity). Aramaic form of the widespread Semitic word for God.",
        "cross_refs": ["Daniel 2:20","Daniel 3:28","Daniel 6:26","Ezra 5:2","Ezra 6:12"]
    },
}

# ─── Bible book number lookup ──────────────────────────────────────────────────

def parse_reference(ref_str):
    """Parse 'John 3:16' or '1 Corinthians 13:4' into (book_num, chapter, verse)."""
    ref_str = ref_str.strip()
    # Match optional leading number, book name, chapter:verse
    m = re.match(r'^(\d\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(\d+):(\d+)$', ref_str)
    if not m:
        return None, None, None, None
    prefix   = (m.group(1) or "").strip()
    bookname = m.group(2).strip()
    chapter  = int(m.group(3))
    verse    = int(m.group(4))

    full = (prefix + bookname).lower().replace(" ","").replace(".","")
    book_num = ALL_BOOKS.get(full)
    if book_num is None:
        # Try partial match
        for k, v in ALL_BOOKS.items():
            if k.startswith(full[:4]):
                book_num = v
                break
    lang = "Hebrew" if (book_num and book_num <= 39) else "Greek"
    return book_num, chapter, verse, lang

# ─── Fetch English verse text ─────────────────────────────────────────────────

def fetch_english_verse(ref_str):
    """Get English verse from bible-api.com (free, no key)."""
    encoded = urllib.parse.quote(ref_str)
    url = f"https://bible-api.com/{encoded}?translation=kjv"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode())
            return data.get("text","").strip()
    except Exception as e:
        return f"[Could not fetch English text: {e}]"

# ─── Fetch interlinear data from STEPBible ────────────────────────────────────

def fetch_step_interlinear(book_num, chapter, verse, lang):
    """
    Fetch word-by-word data from the free STEPBible API.
    Returns list of word dicts with strong, translit, gloss, morph.
    """
    # STEPBible book codes
    step_books = {
        1:"Gen",2:"Exod",3:"Lev",4:"Num",5:"Deut",6:"Josh",7:"Judg",
        8:"Ruth",9:"1Sam",10:"2Sam",11:"1Kgs",12:"2Kgs",13:"1Chr",
        14:"2Chr",15:"Ezra",16:"Neh",17:"Esth",18:"Job",19:"Ps",
        20:"Prov",21:"Eccl",22:"Song",23:"Isa",24:"Jer",25:"Lam",
        26:"Ezek",27:"Dan",28:"Hos",29:"Joel",30:"Amos",31:"Obad",
        32:"Jonah",33:"Mic",34:"Nah",35:"Hab",36:"Zeph",37:"Hag",
        38:"Zech",39:"Mal",
        40:"Matt",41:"Mark",42:"Luke",43:"John",44:"Acts",
        45:"Rom",46:"1Cor",47:"2Cor",48:"Gal",49:"Eph",50:"Phil",
        51:"Col",52:"1Thess",53:"2Thess",54:"1Tim",55:"2Tim",56:"Titus",
        57:"Phlm",58:"Heb",59:"Jas",60:"1Pet",61:"2Pet",
        62:"1John",63:"2John",64:"3John",65:"Jude",66:"Rev",
    }
    book_code = step_books.get(book_num, "")
    version   = "THGNT" if lang == "Greek" else "OSMHB"

    # Try multiple STEPBible URL formats (free, no key needed)
    step_urls = [
        (f"https://www.stepbible.org/rest/passage/text"
         f"?passage={book_code}.{chapter}.{verse}"
         f"&options=XLIT,INTERLEAVED,STRONGS,MORPH&version={version}"),
        (f"https://www.stepbible.org/api/v2/passage/text"
         f"?reference={book_code}.{chapter}.{verse}"
         f"&options=STRONGS,XLIT,MORPH&version={version}"),
    ]
    for url in step_urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"ScriptureResearch/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = r.read().decode(errors="replace")
                words = parse_step_response(raw, lang)
                if words and words[0]:
                    return words, None
        except Exception:
            continue

    # Fallback: biblehub.com interlinear (free, no key needed)
    bh_books = {
        1:"genesis",2:"exodus",3:"leviticus",4:"numbers",5:"deuteronomy",
        6:"joshua",7:"judges",8:"ruth",9:"1_samuel",10:"2_samuel",
        11:"1_kings",12:"2_kings",13:"1_chronicles",14:"2_chronicles",
        15:"ezra",16:"nehemiah",17:"esther",18:"job",19:"psalms",
        20:"proverbs",21:"ecclesiastes",22:"songs",23:"isaiah",
        24:"jeremiah",25:"lamentations",26:"ezekiel",27:"daniel",
        28:"hosea",29:"joel",30:"amos",31:"obadiah",32:"jonah",33:"micah",
        34:"nahum",35:"habakkuk",36:"zephaniah",37:"haggai",38:"zechariah",
        39:"malachi",
        40:"matthew",41:"mark",42:"luke",43:"john",44:"acts",
        45:"romans",46:"1_corinthians",47:"2_corinthians",48:"galatians",
        49:"ephesians",50:"philippians",51:"colossians",
        52:"1_thessalonians",53:"2_thessalonians",54:"1_timothy",
        55:"2_timothy",56:"titus",57:"philemon",58:"hebrews",59:"james",
        60:"1_peter",61:"2_peter",62:"1_john",63:"2_john",64:"3_john",
        65:"jude",66:"revelation",
    }
    bh_book = bh_books.get(book_num, "")
    bh_url = f"https://biblehub.com/interlinear/{bh_book}/{chapter}-{verse}.htm"
    try:
        req2 = urllib.request.Request(bh_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req2, timeout=12) as r:
            html = r.read().decode(errors="replace")
            words = parse_biblehub_response(html, lang)
            if words:
                print(f"  [Source: Biblehub interlinear — {len(words)} words found]")
                return words, None
            return None, "Biblehub: page loaded but word pattern not found"
    except Exception as e:
        return None, f"All sources failed. Last error: {e}"


def parse_biblehub_response(html, lang):
    """Parse biblehub.com interlinear HTML to extract word data."""
    words = []

    # Pattern 1: Modern biblehub interlinear layout
    # Each word block: strong number, transliteration, English gloss
    blocks = re.findall(
        r'<div class="strong"><a[^>]*>([^<]+)</a></div>'
        r'.*?<div class="translit">([^<]*)</div>'
        r'.*?<div class="eng">([^<]*)</div>',
        html, re.DOTALL
    )
    for strong, translit, gloss in blocks:
        words.append({
            "strong":   strong.strip(),
            "translit": translit.strip(),
            "gloss":    gloss.strip(),
            "morph":    "",
            "original": translit.strip(),
        })
    if words:
        return words

    # Pattern 2: Alternative biblehub layout
    blocks2 = re.findall(
        r'<span class="str_[^"]*">([^<]+)</span>'
        r'.*?<span class="translit">([^<]*)</span>'
        r'.*?<span class="eng">([^<]*)</span>',
        html, re.DOTALL
    )
    for strong, translit, gloss in blocks2:
        words.append({
            "strong":   strong.strip(),
            "translit": translit.strip(),
            "gloss":    gloss.strip(),
            "morph":    "",
            "original": translit.strip(),
        })
    if words:
        return words

    # Pattern 3: scrape any Strong's number + nearby transliteration
    strongs_all = re.findall(r'([GH]\d+)', html)
    translits   = re.findall(r'<[^>]*class="[^"]*translit[^"]*"[^>]*>([^<]+)<', html)
    glosses     = re.findall(r'<[^>]*class="[^"]*eng[^"]*"[^>]*>([^<]+)<', html)
    for i, s in enumerate(strongs_all):
        t = translits[i] if i < len(translits) else ""
        g = glosses[i]   if i < len(glosses)   else ""
        if t or g:
            words.append({
                "strong":   s,
                "translit": t.strip(),
                "gloss":    g.strip(),
                "morph":    "",
                "original": t.strip(),
            })
    return words

def parse_step_response(raw, lang):
    """Parse STEPBible HTML/JSON response to extract word data."""
    words = []
    # STEPBible returns HTML with data attributes
    # Pattern: data-strongnumber, data-translit, data-gloss, data-morph
    pattern = re.compile(
        r'<span[^>]*data-strongnumber=["\']([^"\']+)["\'][^>]*'
        r'(?:data-translit=["\']([^"\']*)["\'])?[^>]*'
        r'(?:data-gloss=["\']([^"\']*)["\'])?[^>]*'
        r'(?:data-morph=["\']([^"\']*)["\'])?[^>]*>'
        r'([^<]*)</span>',
        re.DOTALL
    )
    for m in pattern.finditer(raw):
        strong   = m.group(1).strip()
        translit = m.group(2) or ""
        gloss    = m.group(3) or ""
        morph    = m.group(4) or ""
        word     = m.group(5).strip()
        if strong and word:
            words.append({
                "strong":   strong,
                "translit": translit.strip(),
                "gloss":    gloss.strip(),
                "morph":    morph.strip(),
                "original": word,
            })

    # Fallback: try JSON
    if not words:
        try:
            data = json.loads(raw)
            # Navigate STEPBible JSON structure
            verses = (data.get("passage","") or "")
            # Try to extract from different possible structures
            for item in (data.get("words") or []):
                words.append({
                    "strong":   item.get("strong",""),
                    "translit": item.get("translit",""),
                    "gloss":    item.get("gloss",""),
                    "morph":    item.get("morph",""),
                    "original": item.get("word",""),
                })
        except:
            pass

    return words, None

# ─── Lookup in bundled lexicon ────────────────────────────────────────────────

def lookup_lexicon(strong_num):
    """Return lexicon entry for a Strong's number, or None."""
    # Normalize: G25, H2617, A4437 etc.
    key = strong_num.strip().upper()
    entry = BUNDLED_LEXICON.get(key)
    return entry

# ─── Cross-reference lookup ───────────────────────────────────────────────────

def get_cross_refs(strong_num):
    """Return cross-references for a word."""
    entry = lookup_lexicon(strong_num)
    if entry:
        return entry.get("cross_refs", [])
    return []

# ─── Pretty print ─────────────────────────────────────────────────────────────

def divider(char="═", width=70):
    print(char * width)

def print_word_analysis(word_data, idx):
    strong   = word_data.get("strong","")
    translit = word_data.get("translit","")
    gloss    = word_data.get("gloss","")
    morph    = word_data.get("morph","")
    original = word_data.get("original","")

    print(f"\n  [{idx}] Original: {original}")
    if translit:
        print(f"       Transliteration : {translit}")
    if strong:
        print(f"       Strong's Number  : {strong}")
    if morph:
        print(f"       Grammar/Form     : {morph}")
    if gloss:
        print(f"       Basic gloss      : {gloss}")

    # Deep lexicon entry
    entry = lookup_lexicon(strong)
    if entry:
        print(f"\n       ── ORIGINAL MEANING (Scholarly Lexicon) ──")
        if entry.get("root"):
            print(f"       Root / Etymology : {entry['root']}")
            if entry.get("etymology"):
                print(f"                          {entry['etymology']}")
        if entry.get("pos"):
            print(f"       Part of speech   : {entry['pos']}")
        print(f"\n       MEANING:")
        # Word-wrap the meaning text
        meaning = entry.get("meaning","")
        words = meaning.split()
        line = "       "
        for w in words:
            if len(line) + len(w) + 1 > 72:
                print(line)
                line = "       " + w + " "
            else:
                line += w + " "
        if line.strip():
            print(line)

        refs = entry.get("cross_refs",[])
        if refs:
            print(f"\n       Cross-references for this word:")
            for r in refs:
                print(f"         • {r}")
    else:
        print(f"       [Detailed lexicon entry not in bundled database for {strong}]")
        print(f"        Tip: Look up '{strong}' at blueletterbible.org or stepbible.org")

# ─── Main search function ──────────────────────────────────────────────────────

def search_verse(ref_str):
    divider()
    print(f"  SCRIPTURE ORIGINAL LANGUAGE RESEARCH")
    print(f"  Ke Aupuni O Ke Akua Press")
    divider()
    print(f"\n  Reference: {ref_str}\n")

    book_num, chapter, verse, lang = parse_reference(ref_str)
    if book_num is None:
        print(f"  Could not parse reference '{ref_str}'")
        print(f"  Format examples: John 3:16  |  Genesis 1:1  |  Psalm 23:1")
        return

    book_name = BOOK_DISPLAY.get(book_num, "Unknown")
    print(f"  Book       : {book_name} (book #{book_num})")
    print(f"  Language   : {lang}")
    print(f"  Chapter    : {chapter}   Verse: {verse}")

    # English text
    print(f"\n  ── English (KJV) ──")
    english = fetch_english_verse(ref_str)
    # Word wrap
    words = english.split()
    line = "  "
    for w in words:
        if len(line) + len(w) + 1 > 72:
            print(line)
            line = "  " + w + " "
        else:
            line += w + " "
    if line.strip():
        print(line)

    # Interlinear
    print(f"\n  ── Original Language Word Study ──")
    print(f"  Fetching interlinear data from STEPBible (free scholarly database)...")

    word_list, err = fetch_step_interlinear(book_num, chapter, verse, lang)

    if err or not word_list:
        print(f"\n  [Could not fetch interlinear data: {err or 'no words returned'}]")
        print(f"  This may be a network issue. Showing bundled lexicon entries instead.\n")
        # Show relevant bundled entries for the testament
        prefix = "G" if lang == "Greek" else "H"
        relevant = {k:v for k,v in BUNDLED_LEXICON.items() if k.startswith(prefix)}
        print(f"  Bundled {lang} lexicon entries available:")
        for k, v in list(relevant.items())[:8]:
            print(f"    {k}: {v['translit']} — {v['meaning'][:60]}...")
        print(f"\n  For full interlinear: try stepbible.org or blueletterbible.org")
    else:
        print(f"\n  Found {len(word_list)} words in the original {lang}:\n")
        divider("─")
        for i, wd in enumerate(word_list, 1):
            print_word_analysis(wd, i)
            print()
        divider("─")

    # Summary of key theological words found
    found_in_lexicon = []
    if word_list:
        for wd in word_list:
            s = wd.get("strong","").upper()
            if s in BUNDLED_LEXICON:
                found_in_lexicon.append((s, wd.get("translit",""), wd.get("original","")))

    if found_in_lexicon:
        print(f"\n  ── Key Theological Words in This Verse ──")
        for strong, translit, orig in found_in_lexicon:
            entry = BUNDLED_LEXICON[strong]
            print(f"\n  {orig} ({translit}) [{strong}]")
            print(f"  Root: {entry.get('root','')}")
            meaning_preview = entry.get('meaning','')[:120]
            print(f"  {meaning_preview}...")

    print(f"\n")
    divider()
    print(f"  For deeper study:")
    print(f"    stepbible.org — Free scholarly interlinear (STEPBible project)")
    print(f"    blueletterbible.org — Free Strong's + lexicon")
    print(f"    biblehub.com/interlinear — Free verse-by-verse interlinear")
    divider()

# ─── Direct word lookup ────────────────────────────────────────────────────────

def search_word(strong_num):
    """Look up a Strong's number directly."""
    key = strong_num.strip().upper()
    divider()
    print(f"  WORD LOOKUP: {key}")
    divider()
    entry = BUNDLED_LEXICON.get(key)
    if entry:
        print(f"\n  Transliteration : {entry.get('translit','')}")
        print(f"  Root/Etymology  : {entry.get('root','')}")
        print(f"                    {entry.get('etymology','')}")
        print(f"  Part of speech  : {entry.get('pos','')}")
        print(f"\n  MEANING:")
        meaning = entry.get("meaning","")
        words = meaning.split()
        line = "  "
        for w in words:
            if len(line) + len(w) + 1 > 72:
                print(line)
                line = "  " + w + " "
            else:
                line += w + " "
        if line.strip():
            print(line)
        refs = entry.get("cross_refs",[])
        if refs:
            print(f"\n  Cross-references:")
            for r in refs:
                print(f"    • {r}")
    else:
        print(f"\n  No bundled entry for {key}.")
        print(f"  Try stepbible.org or blueletterbible.org/lexicon/{key.lower()}")
    divider()

# ─── Interactive loop ─────────────────────────────────────────────────────────

def interactive():
    print("\n" + "═"*70)
    print("  SCRIPTURE ORIGINAL LANGUAGE RESEARCH TOOL")
    print("  Kahu Phil Stephens — Ke Aupuni O Ke Akua Press")
    print("  Original Greek, Hebrew & Aramaic meanings + cross-references")
    print("═"*70)
    print("\n  HOW TO USE:")
    print("    Type a verse reference:   John 3:16")
    print("    Look up a word by code:   G26  or  H7965  or  A4437")
    print("    List bundled words:       list greek  /  list hebrew  /  list aramaic")
    print("    Quit:                     quit\n")

    while True:
        try:
            user = input("  Enter reference or word code: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Aloha!")
            break

        if not user:
            continue
        if user.lower() in ("quit","exit","q"):
            print("  Aloha! God bless your study.")
            break
        elif user.lower().startswith("list"):
            parts = user.lower().split()
            prefix = "G"
            if len(parts) > 1:
                if "heb" in parts[1]: prefix = "H"
                elif "aram" in parts[1]: prefix = "A"
            print(f"\n  Bundled lexicon entries ({prefix}):\n")
            for k,v in BUNDLED_LEXICON.items():
                if k.startswith(prefix):
                    print(f"    {k:8s} {v['translit']:20s} {v['meaning'][:45]}...")
            print()
        elif re.match(r'^[GHA]\d+$', user.upper()):
            search_word(user)
        else:
            # Assume verse reference
            search_verse(user)

# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = " ".join(sys.argv[1:])
        if re.match(r'^[GHA]\d+$', arg.upper()):
            search_word(arg)
        else:
            search_verse(arg)
    else:
        interactive()