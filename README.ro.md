<div align="center">

<h1>norma</h1>

<p>
  <strong>Redenumire automata de fisiere cu AI — orice format, orice limba, complet local.</strong><br/>
  Dai un dosar cu fisiere cu nume haotice. Spui ce format vrei. Gata.
</p>

<p>
  <a href="https://www.python.org/downloads/"><img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white"/></a>
  <a href="https://ollama.com"><img alt="Ollama" src="https://img.shields.io/badge/backend-Ollama%20%7C%20LM%20Studio-black?style=flat-square"/></a>
  <img alt="Confidentialitate" src="https://img.shields.io/badge/confidentialitate-100%25%20local-green?style=flat-square"/>
  <a href="LICENCE"><img alt="Licenta" src="https://img.shields.io/badge/licenta-MIT-orange?style=flat-square"/></a>
</p>

<p><a href="README.md">🇬🇧 English</a></p>

<img src="docs/screenshot-dryrun.svg" alt="norma previzualizare" width="800"/>

</div>

---

## Ce face

norma trimite loturi de nume de fisiere catre un model AI local si le redenumeste in formatul pe care il definesti tu — indiferent de limba, conventie de denumire sau domeniu.

```text
harry_potter_jk_rowling.epub            ->  J.K. Rowling - Harry Potter.epub
4.LISA_KLEYPAS_Scandal_in_primavara.pdf ->  Lisa Kleypas - Scandal in primavara.pdf
Haralamb_Zinca_Interpolul_transmite     ->  Haralamb Zinca - Interpolul transmite arestati.epub
1365135809.epub                         ->  Unknown - 1365135809.epub
INV-2024-ACME-CORP-000432.pdf           ->  ACME Corp / Factura / 2024-000432.pdf
smith2019_ml_paper_final_v2.pdf         ->  Smith (2019) - ML Paper Final.pdf
```

Formatul este ales complet de tine. norma se adapteaza la orice sablon `{Camp}` ii dai.

> **Confidentialitate totala:** niciun nume de fisier nu paraseste calculatorul tau. Nu se trimite nimic catre servicii externe.

---

## Caracteristici

- **Format universal** — definesti orice sablon cu tokeni `{Camp}`: `{Autor} - {Titlu}`, `{Client} / Factura / {Data}`, `{Artist} - {Album} ({An})`, orice
- **Orice limba** — gestioneaza romana, engleza, spaniola, japoneza, caractere mixte; pastreaza diacriticele
- **Procesare in loturi** — trimite 100 de fisiere per apel AI in loc de unul; de ~10x mai rapid
- **Executie paralela** — 16 fire de executie trimit loturi simultan, saturand coada GPU
- **Reincercare automata** — fisierele esuate sunt reincercate automat de pana la 3 ori
- **Mod previzualizare** — vezi toate redenumirile intr-un tabel inainte sa atingi vreun fisier
- **Doua backend-uri** — functioneaza cu [Ollama](https://ollama.com) sau [LM Studio](https://lmstudio.ai)
- **Siguranta la coliziuni** — numele duplicate primesc sufixe `(2)`, `(3)` automat
- **Biblioteci mari** — imparte automat dosarele cu >3000 de fisiere in subdosare inainte de procesare

---

## Cerinte

- Python 3.10+
- [Ollama](https://ollama.com) **sau** [LM Studio](https://lmstudio.ai) rulând local

**Model recomandat (Ollama):**

```bash
ollama pull qwen2.5:3b
```

**LM Studio:** incarca `qwen2.5-3b-instruct` in tab-ul Developer si porneste serverul local.

---

## Instalare

```bash
# Instalare izolata (recomandat)
pipx install .

# Instalare pentru dezvoltare
pip install -e .
```

---

## Utilizare

### Previzualizeaza redenumirile inainte de aplicare

```bash
norma run ./carti --format "{Autor} - {Titlu}" --dry-run
```

<img src="docs/screenshot-dryrun.svg" alt="previzualizare dry-run" width="750"/>

### Redenumeste un dosar

```bash
norma run ./carti --format "{Autor} - {Titlu}"
```

<img src="docs/screenshot-run.svg" alt="rezumat executie" width="600"/>

### Verifica conectivitatea backend-ului

```bash
norma status
norma status --backend lmstudio
```

<img src="docs/screenshot-status.svg" alt="iesire status" width="550"/>

---

## Exemple de formate

```bash
# Facturi
norma run ./facturi --format "{Client} / Factura / {Data}"

# Articole de cercetare
norma run ./articole --format "{Autor} ({An}) - {Titlu}"

# Albume muzicale
norma run ./albume --format "{Artist} - {Album} ({An})"

# Documente juridice
norma run ./contracte --format "{Companie} - {Tip} - {Data}"

# Redenumire intr-un alt dosar
norma run ./sursa --format "{Autor} - {Titlu}" --output ./redenumite
```

norma deduce ce inseamna fiecare `{Camp}` din numele sau. Nu trebuie sa configurezi definitii de campuri.

---

## Backend LM Studio

```bash
# Verifica conectivitatea LM Studio
norma status --backend lmstudio

# Ruleaza cu LM Studio
norma run ./carti --format "{Autor} - {Titlu}" --backend lmstudio
```

LM Studio ignora optiunea `--model` — foloseste modelul incarcat curent in tab-ul Developer.

---

## Toate optiunile

```text
norma run <dosar> [optiuni]

  --format    -f   Sablon de redenumire              implicit: "{Autor} - {Titlu}"
  --output    -o   Dosar destinatie                  implicit: <intrare>/../norma-output
  --model     -m   Nume model                        implicit: qwen2.5:3b
  --workers   -w   Fire de executie paralele         implicit: 16
  --batch-size -b  Fisiere per apel AI               implicit: 100
  --dry-run   -n   Previzualizeaza, nu copiaza nimic implicit: false
  --backend        ollama sau lmstudio               implicit: ollama
  --api-url        Suprascrie URL-ul API
  --max-retries -r Reincearca fisierele esuate de N  implicit: 3
```

---

## Performanta

norma obtine un debit ridicat prin gruparea numelor de fisiere (100 per apel) si trimiterea lor paralela. Aceasta amortizeaza costul prompt-ului de sistem pe mai multe fisiere si mentine GPU-ul ocupat.

| Configuratie | Debit |
| ------------ | ----- |
| `qwen2.5:3b`, lot 100, 16 fire | **~870 fisiere/min** |
| `qwen2.5:3b`, lot 15, 8 fire (implicit vechi) | ~590 fisiere/min |
| `qwen2.5:7b`, lot 100, 16 fire | ~300-450 fisiere/min |

Testat pe 1 000 de fisiere diverse (multilingv, haotice, numerice, articole de cercetare). Rezultatele variaza in functie de hardware.

> Benchmarkul in 10 iteratii care a produs aceste cifre se afla in [`benchmark/`](benchmark/).

---

## Structura output-ului

```text
norma-output/
+-- J.K. Rowling - Harry Potter.epub
+-- Lisa Kleypas - Scandal in primavara.pdf
+-- Isaac Asimov - Foundation.pdf
+-- ...
+-- _errors/          <- fisiere pe care norma nu a putut sa le redenumeasca
+-- processed.log     <- jurnal cu toate redenumirile
+-- norma.log         <- jurnal detaliat al executiei
```

Fisierele care nu au putut fi redenumite (ex: ID-uri numerice fara context) ajung in `_errors/`. Ruleaza-le din nou cu un model diferit sau un alt format:

```bash
norma retry ./norma-output/_errors --format "{Autor} - {Titlu}" --model qwen2.5:7b
```

---

## Cum functioneaza

```text
CLI (cli.py)
  +- construieste dataclass-ul Config
  +- apeleaza run_pipeline()

pipeline.py
  +- imparte automat dosarele cu > 3 000 fisiere
  +- colecteaza toate fisierele
  +- imparte in loturi de 100
  +- trimite la ThreadPoolExecutor (16 fire)
        |
        v
processor.py (per lot)
  +- trimite lista numerotata de nume la AI
  +- parseaza raspunsul numerotat
  +- revine la apeluri individuale la nepotrivire de numar
  +- valideaza ca output-ul corespunde formatului
  +- copiaza fisierul in dosarul output, gestioneaza coliziunile

dedup.py
  +- elimina fisierele sursa deja prezente in output
```

Toata configuratia trece printr-un singur dataclass `Config` — fara stare globala, fara cai hardcodate.

---

## Licenta

[MIT](LICENCE)
