from typing import Dict, List, Tuple, Optional
from pathlib import Path
import random, math
import re, os, sys

# ----------------------------
# Paths that work in dev & when frozen (PyInstaller --onefile)
# ----------------------------

def app_base_dir() -> Path:
    """Directory to look for external, user-editable files (config, scores)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent

def resource_root() -> Path:
    """
    Directory where bundled resources live.
    In a one-file PyInstaller build, files added via --add-data are unpacked under _MEIPASS.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).parent

APP_BASE = app_base_dir()
RES_ROOT = resource_root()

# External config: default next to the exe/script; allow override with env var
CONFIG_PATH = Path(os.environ.get("MYAPP_CONFIG", str(APP_BASE / "config.txt")))

# Bundled data dir (include with:  pyinstaller --onefile --add-data "vocab:vocab" app.py)
VOCAB_DIR = RES_ROOT / "vocab"

# ----------------------------
# Config parsing
# ----------------------------

def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent

DEFAULT_CONFIG = """player: nihongo jouzu

lesson: meaning
# can be {meaning, onyomi, kunyomi}

levels:
5, 4.1
# N.a means "from ((a-1)*10)-th word to (a*10)-th word of level N"
# N.a-b means "words from N.a up to N.b"

# N5: 80 words   = 5.1-8
# N4: 167 words  = 4.1-17
# N3: 370 words  = 3.1-37
# N2: 374 words  = 2.1-38
# N1: 1504 words = 1.1-151
"""

def ensure_config(path: Path, content: str = DEFAULT_CONFIG) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"Created default config at: {path}")
    else:
        print(f"Config already exists at: {path}")
    return path

def _merge_ranges(ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Merge overlapping/adjacent [start, end) ranges."""
    if not ranges:
        return []
    ranges = sorted(ranges)
    merged = [ranges[0]]
    for s, e in ranges[1:]:
        ps, pe = merged[-1]
        if s <= pe:  # overlap/adjacent
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged

def _parse_levels_spec(spec: str) -> Dict[int, Optional[List[Tuple[int, int]]]]:
    """
    Parse a levels spec like:
      "5.1-5, 4.1, 4.2, 4.12-13, 3.5-17, 2"
    Returns:
      { level: None } for whole level,
      or { level: [(start_idx, end_idx_exclusive), ...] } for selected 10-word blocks.
      Block a means words [ (a-1)*10 , a*10 ).
    """
    out: Dict[int, Optional[List[Tuple[int, int]]]] = {}

    for token in [t.strip() for t in spec.split(",") if t.strip()]:
        m = re.fullmatch(r"(\d+)(?:\.(\d+)(?:-(\d+))?)?$", token)
        if not m:
            continue  # skip unparseable token
        lvl = int(m.group(1))
        a = m.group(2)
        b = m.group(3)

        # Whole level
        if a is None:
            out[lvl] = None
            continue

        a_i = int(a)
        b_i = int(b) if b is not None else a_i

        # Build block ranges (10 words per block)
        ranges = out.get(lvl, [])
        if ranges is None:
            # already whole-level; nothing to do
            continue
        for blk in range(a_i, b_i + 1):
            start = (blk - 1) * 10
            end = blk * 10
            ranges.append((start, end))
        out[lvl] = _merge_ranges(ranges)

    return out

def _strip_comment(line: str) -> str:
    return line.strip()

def load_config(path: Path) -> Tuple[str, List[str], Dict[int, Optional[List[Tuple[int, int]]]]]:
    """
    Reads config.txt and returns:
      PLAYER: str
      LESSONS: list like ["meaning"] or ["onyomi_en"] or ["kunyomi_en"]
      SELECTED: dict level -> None (all) or list of [start,end) ranges
    Ignores blank lines and lines whose first non-space char is '#'.
    Supports value on the same line or next non-comment line.
    """
    player_raw = None
    lessons_raw = None
    levels_raw = None
    expect_player = False
    expect_lessons = False
    expect_levels = False

    if not path.exists():
        # Sensible defaults if no config file is present
        return "default", ["meaning"], {5: None}

    with path.open("r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]

    def is_comment_or_blank(ln: str) -> bool:
        stripped = ln.strip()
        return (not stripped) or stripped.startswith("#")

    for i, ln in enumerate(lines):
        if is_comment_or_blank(ln):
            continue

        if expect_player and player_raw is None:
            if not is_comment_or_blank(ln):
                player_raw = ln.strip()
                expect_player = False
                continue

        if expect_lessons and lessons_raw is None:
            if not is_comment_or_blank(ln):
                lessons_raw = ln.strip()
                expect_lessons = False
                continue

        if expect_levels and levels_raw is None:
            if not is_comment_or_blank(ln):
                levels_raw = ln.strip()
                expect_levels = False
                continue

        # key: value on same line
        if re.match(r"^\s*player\s*:", ln, flags=re.I):
            after = ln.split(":", 1)[1].strip()
            if after:
                player_raw = after
            else:
                expect_player = True
            continue

        if re.match(r"^\s*lesson\s*:", ln, flags=re.I):
            after = ln.split(":", 1)[1].strip()
            if after:
                lessons_raw = after
            else:
                expect_lessons = True
            continue

        if re.match(r"^\s*levels\s*:", ln, flags=re.I):
            after = ln.split(":", 1)[1].strip()
            if after:
                levels_raw = after
            else:
                expect_levels = True
            continue

    # Defaults
    if player_raw is None:
        player_raw = "default"
    if lessons_raw is None:
        lessons_raw = "meaning"
    if levels_raw is None:
        levels_raw = "5"

    # Normalize lessons
    # Accept comma/space separated values, e.g. "meaning, onyomi"
    lesson_tokens = [t.strip().lower() for t in re.split(r"[,\s]+", lessons_raw) if t.strip()]
    LESSONS: List[str] = []
    for tk in lesson_tokens:
        if tk == "meaning":
            LESSONS.append("meaning")
        elif tk == "onyomi":
            LESSONS.append("onyomi_en")
        elif tk == "kunyomi":
            LESSONS.append("kunyomi_en")
        else:
            # fallback: accept raw field name if user knows internal keys
            LESSONS.append(tk)
    PLAYER = player_raw
    SELECTED = _parse_levels_spec(levels_raw)
    if not SELECTED:
        SELECTED = {5: None}  # default whole N5
    return PLAYER, LESSONS, SELECTED

# ----------------------------
# App (with selection support)
# ----------------------------

LEVEL_LIMITS: Dict[int, float] = {}

# Load config (now robust to frozen builds)
ensure_config(CONFIG_PATH)
PLAYER, LESSONS, SELECTED = load_config(CONFIG_PATH)

# Convert SELECTED into LEVEL_LIMITS (upper bound) for fast file reads
for lvl, ranges in SELECTED.items():
    if ranges is None:
        LEVEL_LIMITS[lvl] = float('inf')  # whole level
    else:
        # Limit read to the end of the furthest selected slice
        LEVEL_LIMITS[lvl] = max(e for _, e in ranges)

def _iline_selected(level: int, iline: int) -> bool:
    """
    Check if a zero-based line index 'iline' within a level belongs to the selected slices.
    If level is whole-level (None), always True.
    """
    ranges = SELECTED.get(level, None)
    if ranges is None:
        return True
    for s, e in ranges:
        if s <= iline < e:
            return True
    return False

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def main():
    # Prepare score file in a writable location next to the exe/script
    scores_dir = APP_BASE / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    score_file = scores_dir / PLAYER.lower()
    global SCORE_FILE
    SCORE_FILE = str(score_file)

    # Ensure file exists
    with open(SCORE_FILE, "a", encoding="utf-8") as file:
        file.write("")

    vocab: List[List[Dict[str, str]]] = [[], [], [], [], [], []]  # vocab[0] is unused

    for level in [1, 2, 3, 4, 5]:
        if level not in LEVEL_LIMITS:
            continue
        try:
            vocab_path = VOCAB_DIR / f"jlpt_kanji_list_N{level}.csv"
            with vocab_path.open("r", encoding="utf-8") as file:
                lines = file.readlines()[1:]  # Skip header
                limit = LEVEL_LIMITS[level]

                for iline, line in enumerate(lines):
                    if iline >= limit:
                        break
                    if not _iline_selected(level, iline):
                        continue
                    line = (line.replace("\n", "")
                                 .replace("\"", "")
                                 .replace("%@,", "+++")
                                 .replace("%@", "")
                                 .replace("-", ""))
                    parts = line.split("+++")
                    if len(parts) != 4:
                        # Skip malformed line rather than crash
                        continue
                    kanji, onyomi, kunyomi, meaning = parts

                    onyomi_en, onyomi_jp = en_jp_split(onyomi)
                    kunyomi_en, kunyomi_jp = en_jp_split(kunyomi)

                    vocab[level].append({
                        "kanji": kanji,
                        "onyomi_en": onyomi_en,
                        "onyomi_jp": onyomi_jp,
                        "kunyomi_en": kunyomi_en,
                        "kunyomi_jp": kunyomi_jp,
                        "meaning": meaning
                    })
                # tighten LEVEL_LIMITS to the actual included words for nicer UI
                if LEVEL_LIMITS[level] != float('inf') and LEVEL_LIMITS[level] > len(vocab[level]):
                    LEVEL_LIMITS[level] = len(vocab[level])
        except FileNotFoundError:
            print(f"Warning: File for level N{level} not found at {vocab_path}.")

    levels = list(LEVEL_LIMITS.keys())
    words = sum([vocab[level] for level in levels], [])
    session_wins = 0
    session_loses = 0
    dialogues: List[List[str]] = []

    word_counts = {level: len(vocab[level]) for level in levels}

    if not words:
        print(f"\n   No words found from your config selection."
              f"\n   Looked for CSVs under: {VOCAB_DIR}"
              f"\n   Config path: {CONFIG_PATH}\n")
        return

    while True:
        session_score = score_fn(session_wins, session_loses)
        scores = load_scores()
        print_dialogues(dialogues, session_score, scores, word_counts)

        cat2_list = []
        weight_list = []

        for word in words:
            for cat2 in LESSONS:
                key = (word["kanji"], cat2)
                correct, incorrect = scores.get(key, [0, 0])
                score = score_fn(correct, incorrect) if (correct + incorrect) > 0 else 0
                weight = (1 - score) ** 4
                cat2_list.append((word, cat2))
                weight_list.append(weight)

        if all(w == 0 for w in weight_list):
            idx = random.randrange(len(cat2_list))
        else:
            idx = random.choices(range(len(cat2_list)), weights=weight_list, k=1)[0]


        word, cat2 = cat2_list[idx]
        cat1 = "kanji"
        difficulty = str(int(math.floor(10 * weight_list[idx]))) + "/10"

        preposition = "for" if cat2 != "meaning" else "of"
        answers = expand_items(word[cat2])

        question = "\n"
        question += f"   What's the {cat2.replace('_en', '')} {preposition} {word[cat1]}\n"
        question += f"   (dynamic difficulty: {difficulty})\n"

        print(question, end="")
        raw = ""
        while raw.strip() == "" :
            raw = input("    >> ")
            if raw.strip() == "" :
                print("\033[A\033[A")

        if "-x" == raw.strip() :
            print()
            sys.exit(1)

        response = raw.lower().replace("\t","").strip()
        key = (word[cat1], cat2)

        answer = ""
        if isin(response, answers) and len(response) > 0:
            answer += f"    ✅ meaning: {word['meaning']}\n"
            answer += f"        onyomi: {word['onyomi_en']}\n"
            answer += f"       kunyomi: {word['kunyomi_en']}\n"
            correct, incorrect = scores.get(key, [0, 0])
            scores[key] = [correct + 1, incorrect]
            session_wins += 1
        else:
            answer += f"    ❌ meaning: {word['meaning']}\n"
            answer += f"        onyomi: {word['onyomi_en']}\n"
            answer += f"       kunyomi: {word['kunyomi_en']}\n"
            correct, incorrect = scores.get(key, [0, 0])
            scores[key] = [correct, incorrect + 1]
            session_loses += 1
        #print(answer, end="")
        save_scores(scores)
        dialogues.append([question, raw, answer])

def print_dialogues(dialogues, score, score_all, word_counts):
    attempts = 0
    for key in score_all.keys():
        wins, loses = score_all[key]
        attempts += wins + loses

    # simple safe padding
    def pad(s: str, width: int) -> str:
        s = str(s)
        if len(s) >= width:
            return s[:width]
        return s + " " * (width - len(s))

    score_str = (str(score) + " " * 5)[:5]
    score_str = pad(score_str, 44)
    level_str = ", ".join([f"N{n} ({word_counts[n]} words)" for n in word_counts.keys()])
    level_str = level_str.replace(" (inf words)","")
    level_str = pad(level_str, 44)
    attpt_str = pad(str(attempts), 44)
    player_str = pad(PLAYER, 44)

    clear_screen()
    print()
    print(f" ╭───────────┬{'─'*60}╮")
    print(f" │           │        player: {player_str}│")
    print(f" │ ii-KANJi™ │      attempts: {attpt_str}│")
    print(f" │ ʙy ᴅɪᴩᴛɪᴩ │         level: {level_str}│")
    print(f" │           │ session score: {score_str}│")
    print(f" ╰───────────┴{'─'*60}╯")
    trunc_len = 2
    trunc = -trunc_len if len(dialogues) > trunc_len else 0
    for question, raw, answer in dialogues[trunc:]:
        print(question, end="")
        print("    >>",raw)
        print(answer, end="")

    # print the remarks
    print("\n                                    "*4)
    print(" ╭"+"─"*72+"╮")
    print(" │ type -x to close the program"+" "*43+"│")
    print(" ╰"+"─"*72+"╯")
    print("\033[A"*9)

def expand_items(s):
    items = [item.strip() for item in s.replace("-", "").split(',')]
    result = []
    for item in items:
        match = re.fullmatch(r'(\w+)\((\w+)\)', item)
        if match:
            base, inner = match.groups()
            result.extend([base, base + inner])
        else:
            result.append(item)
    return result

def en_jp_split(text):
    split_loc = 0
    for ichar, char in enumerate(text):
        if char in furigana:
            split_loc = ichar
            break
    return text[:split_loc], text[split_loc:]

def score_fn(wins, loses):
    return wins / (2 + wins + loses)

def load_scores():
    scores = {}
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                kanji, cat2, correct, incorrect = line.split(",")
                scores[(kanji, cat2)] = [int(correct), int(incorrect)]
    return scores

def save_scores(scores):
    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        for (kanji, cat2), (correct, incorrect) in scores.items():
            f.write(f"{kanji},{cat2},{correct},{incorrect}\n")

def isin(item, the_list):
    if item in the_list:
        return True
    for other in the_list:
        if item in other:
            return True
    return False

hiragana = [
    'あ', 'い', 'う', 'え', 'お',
    'か', 'き', 'く', 'け', 'こ',
    'さ', 'し', 'す', 'せ', 'そ',
    'た', 'ち', 'つ', 'て', 'と',
    'な', 'に', 'ぬ', 'ね', 'の',
    'は', 'ひ', 'ふ', 'へ', 'ほ',
    'ま', 'み', 'む', 'め', 'も',
    'や',       'ゆ',       'よ',
    'ら', 'り', 'る', 'れ', 'ろ',
    'わ',                   'を',
    'ん',
    'が', 'ぎ', 'ぐ', 'げ', 'ご',
    'ざ', 'じ', 'ず', 'ぜ', 'ぞ',
    'だ', 'ぢ', 'づ', 'で', 'ど',
    'ば', 'び', 'ぶ', 'べ', 'ぼ',
    'ぱ', 'ぴ', 'ぷ', 'ぺ', 'ぽ',
    'ぁ', 'ぃ', 'ぅ', 'ぇ', 'ぉ',
    'ゃ', 'ゅ', 'ょ', 'っ',
    'ゔ'
]

katakana = [
    'ア', 'イ', 'ウ', 'エ', 'オ',
    'カ', 'キ', 'ク', 'ケ', 'コ',
    'サ', 'シ', 'ス', 'セ', 'ソ',
    'タ', 'チ', 'ツ', 'テ', 'ト',
    'ナ', 'ニ', 'ヌ', 'ネ', 'ノ',
    'ハ', 'ヒ', 'フ', 'ヘ', 'ホ',
    'マ', 'ミ', 'ム', 'メ', 'モ',
    'ヤ',       'ユ',       'ヨ',
    'ラ', 'リ', 'ル', 'レ', 'ロ',
    'ワ',                   'ヲ',
    'ン',
    'ガ', 'ギ', 'グ', 'ゲ', 'ゴ',
    'ザ', 'ジ', 'ズ', 'ゼ', 'ゾ',
    'ダ', 'ヂ', 'ヅ', 'デ', 'ド',
    'バ', 'ビ', 'ブ', 'ベ', 'ボ',
    'パ', 'ピ', 'プ', 'ペ', 'ポ',
    'ァ', 'ィ', 'ゥ', 'ェ', 'ォ',
    'ャ', 'ュ', 'ョ', 'ッ',
    'ヴ', 'ー'
]

furigana = hiragana + katakana

# SCORE_FILE is set inside main() after PLAYER is known
SCORE_FILE = str(APP_BASE / "scores" / "default")  # placeholder

if __name__ == "__main__":
    main()
