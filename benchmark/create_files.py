"""
Generate 1000 benchmark test files covering every naming pattern norma might encounter.
Also writes ground_truth.json: {stem: expected_has_separator} for format-validity scoring.
"""
import json
import random
from pathlib import Path

random.seed(42)

OUT = Path(__file__).parent / "files"
OUT.mkdir(exist_ok=True)

EXTENSIONS = [".epub", ".pdf", ".mobi", ".epub", ".epub", ".pdf"]  # epub-heavy like real usage

# ---------------------------------------------------------------------------
# Pattern generators — each returns (stem, is_already_valid)
# ---------------------------------------------------------------------------

def english_clean():
    authors = ["J.K. Rowling","George Orwell","Stephen King","Agatha Christie",
                "Ernest Hemingway","F. Scott Fitzgerald","Mark Twain","John Steinbeck",
                "Ray Bradbury","Isaac Asimov","Arthur C. Clarke","Philip K. Dick",
                "Ursula K. Le Guin","Kurt Vonnegut","Aldous Huxley"]
    titles  = ["The Great Adventure","Dark Horizons","Whispers of Time","Iron Kingdom",
                "Frozen Memories","The Last Signal","Silent Echoes","Burning Bridges",
                "The Hidden Path","Distant Stars","Shadow Protocol","The Forgotten Gate",
                "New Dawn","Broken Compass","The Final Chapter"]
    a, t = random.choice(authors), random.choice(titles)
    # Already correctly formatted — should pass through
    return f"{a} - {t}", True

def english_messy_underscore():
    first = random.choice(["john","mary","james","anna","robert","linda","william"])
    last  = random.choice(["smith","jones","brown","wilson","taylor","anderson"])
    title = random.choice(["the_big_secret","lost_in_time","rise_of_shadows",
                            "the_last_hope","forgotten_world","dark_prophecy"])
    return f"{first}_{last}_{title}", False

def english_numeric_prefix():
    n = random.randint(1, 99)
    author = random.choice(["tolkien","hemingway","orwell","dickens","austen"])
    title  = random.choice(["fellowship","the_sun","dark_tower","pride","great_expectations"])
    return f"{n:02d}_{author}_{title}", False

def english_title_first():
    title  = random.choice(["dune","neuromancer","foundation","the_hobbit",
                             "enders_game","fahrenheit_451","brave_new_world"])
    author = random.choice(["frank_herbert","william_gibson","isaac_asimov",
                             "j_r_r_tolkien","orson_scott_card","ray_bradbury","aldous_huxley"])
    return f"{title}_{author}", False

def english_parens_noise():
    author = random.choice(["lisa_kleypas","nora_roberts","danielle_steel","james_patterson"])
    title  = random.choice(["the_risk","silent_night","blue_moon","cross_fire"])
    noise  = random.choice(["(biblioteca noastra)","(v2)","(HQ)","(scan)","[OCR]","(draft)"])
    return f"{author}_{title}_{noise}", False

def english_series():
    series = random.choice(["Mindf_ck Series","Dark Tower","Wheel of Time",
                             "Discworld","Foundation Series","Dune Chronicles"])
    n      = random.randint(1, 7)
    author = random.choice(["S.T. Abby","Stephen King","Robert Jordan",
                             "Terry Pratchett","Isaac Asimov","Frank Herbert"])
    title  = random.choice(["The Risk","The Stand","Eye of the World",
                             "The Colour of Magic","Foundation","Dune"])
    return f"({series} {n}) {author} - {title}", False

def romanian():
    authors = ["Haralamb Zinca","Jean de la Hire","Ion Creanga","Mihail Sadoveanu",
                "Liviu Rebreanu","Tudor Arghezi","Camil Petrescu","Marin Preda",
                "Mircea Eliade","Emil Cioran","Nichita Stanescu","Ana Blandiana"]
    titles  = ["Interpolul transmite arestati","Cei Trei Cercetasi","Amintiri din copilarie",
                "Baltagul","Ion","Ultima noapte","Morometii","Noaptea de Sanziene",
                "Tratatul de ontologie","Pe culmile disperarii","Laus Ptolemaei","Orologiul de nisip"]
    a = random.choice(authors)
    t = random.choice(titles)
    return f"{a.replace(' ','_')}_{t.replace(' ','_')}", False

def romanian_already_formatted():
    authors = ["CNSAS","Dan Puric","Petre Tutea","Nicolae Iorga"]
    titles  = ["Romanii in Epoca de Aur","Omul frumos","Omul","Istoria romanilor"]
    a, t = random.choice(authors), random.choice(titles)
    return f"{a} - {t}", True

def gibberish():
    # Pure numeric or hash — should become Unknown - X
    patterns = [
        str(random.randint(1000000000, 9999999999)),
        f"scan_{random.randint(1000,9999)}",
        f"IMG_{random.randint(10000,99999)}",
        f"DOC{random.randint(100,999)}",
        f"file_{random.randint(1,999):03d}",
    ]
    return random.choice(patterns), False

def invoice_style():
    client = random.choice(["ACME-CORP","TechSolutions","GlobalTrade",
                             "FastLogistics","MegaRetail","DataSystems"])
    year   = random.randint(2020, 2024)
    num    = random.randint(1000, 99999)
    return f"INV-{year}-{client}-{num:05d}", False

def research_paper():
    author = random.choice(["smith","johnson","chen","kim","garcia","mueller","tanaka"])
    year   = random.randint(2015, 2024)
    topic  = random.choice(["ml_survey","deep_learning","transformer_arch",
                             "attention_mechanism","graph_neural","diffusion_models"])
    return f"{author}{year}_{topic}_final_v2", False

def dot_separated():
    last  = random.choice(["King","Martin","Tolkien","Rowling","Pratchett"])
    first = random.choice(["S","G.R.R","J.R.R","J.K","T"])
    title = random.choice(["Dune","A Game of Thrones","The Fellowship",
                            "Harry Potter","The Colour of Magic"])
    return f"{last}.{first}.{title.replace(' ','.')}".replace(" ",""), False

def dash_separated():
    author = random.choice(["khalil-gibran","paulo-coelho","gabriel-garcia-marquez",
                             "jorge-luis-borges","umberto-eco"])
    title  = random.choice(["the-prophet","the-alchemist","one-hundred-years",
                             "labyrinths","the-name-of-the-rose"])
    return f"{author}-{title}", False

def comma_last_first():
    last  = random.choice(["Hategan","Popescu","Ionescu","Georgescu","Dumitrescu"])
    first = random.choice(["Ioan","Mihai","Andrei","Bogdan","Stefan"])
    title = random.choice(["Filippo Scolari","Istoria","Memorii","Cronici","Studii"])
    return f"{last}, {first} - {title}", True  # already has valid separator

def mixed_lang():
    combos = [
        ("Jack_L_Chalker", "The_Red_Tape_War"),
        ("Harwey_Rex", "Canionul_Blestemat"),
        ("Lisa_Kleypas", "Scandal_in_primavara"),
        ("4.LISA_KLEYPAS", "Scandal_in_primavara"),
        ("j_k_rowling", "harry_potter_chamber_of_secrets"),
        ("tolkien", "lord_of_the_rings_fellowship"),
        ("George_Orwell", "Animal_Farm"),
        ("George_Orwell", "Nineteen_Eighty_Four"),
    ]
    a, t = random.choice(combos)
    return f"{a}_{t}", False

# ---------------------------------------------------------------------------
# Generate 1000 files across all patterns
# ---------------------------------------------------------------------------

GENERATORS = [
    (english_clean,           80),   # already valid — speed test (pass-through)
    (english_messy_underscore,120),
    (english_numeric_prefix,   80),
    (english_title_first,     100),
    (english_parens_noise,     80),
    (english_series,           60),
    (romanian,                120),
    (romanian_already_formatted, 40),
    (gibberish,                60),
    (invoice_style,            60),
    (research_paper,           60),
    (dot_separated,            40),
    (dash_separated,           40),
    (comma_last_first,         30),
    (mixed_lang,               30),
]

assert sum(n for _, n in GENERATORS) == 1000

stems_used: set[str] = set()
ground_truth: dict[str, bool] = {}
created = 0

for gen_fn, count in GENERATORS:
    for _ in range(count):
        for attempt in range(20):
            stem, already_valid = gen_fn()
            # Deduplicate
            unique_stem = stem if stem not in stems_used else f"{stem}_{created}"
            stems_used.add(unique_stem)
            ext  = random.choice(EXTENSIONS)
            path = OUT / (unique_stem + ext)
            path.write_bytes(b"dummy")  # non-empty so norma doesn't skip it
            ground_truth[unique_stem] = already_valid
            created += 1
            break

# Write ground truth
(Path(__file__).parent / "ground_truth.json").write_text(
    json.dumps(ground_truth, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"Created {created} files in {OUT}")
print(f"  Already-valid: {sum(ground_truth.values())}")
print(f"  Needs renaming: {sum(not v for v in ground_truth.values())}")
