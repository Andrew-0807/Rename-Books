import re

# Known field names → human-readable semantic descriptions
_FIELD_SEMANTICS: dict[str, str] = {
    "author":   "the person who created or wrote the work",
    "writer":   "the person who created or wrote the work",
    "creator":  "the person who created or wrote the work",
    "title":    "the name or title of the work",
    "name":     "the name or title of the work",
    "date":     "a date associated with the file (use YYYY-MM-DD if possible)",
    "year":     "a year associated with the file",
    "client":   "an organization or client name",
    "company":  "an organization or company name",
    "genre":    "the genre or category of the work",
    "series":   "the series name if part of a series",
    "volume":   "the volume or part number",
    "language": "the language of the work",
    "type":     "the document type or category",
    "version":  "the version or edition number",
}

# Hardcoded few-shot examples for the default format — covers multilingual, messy filenames
_EXAMPLES_AUTHOR_TITLE = [
    ("harry_potter_jk_rowling",                     "J.K. Rowling - Harry Potter"),
    ("4.LISA_KLEYPAS_Scandal_in_primavara",         "Lisa Kleypas - Scandal in primavara"),
    ("Haralamb_Zinca_Interpolul_transmite_arestati","Haralamb Zincă - Interpolul transmite arestaţi"),
    ("1365135809",                                   "Unknown - 1365135809"),
    ("Jean_de_la_Hire_Cei_Trei_Cercetasi_V23",      "Jean de la Hire - Cei Trei Cercetaşi V23"),
]


def parse_fields(format_string: str) -> list[str]:
    """Extract field names from a format string like '{Author} - {Title}'."""
    return re.findall(r'\{(\w+)\}', format_string)


def get_format_literals(format_string: str) -> list[str]:
    """
    Extract the literal separator text between {Field} tokens.

    '{Author} - {Title}'          → [' - ']
    '{Client} / Invoice / {Date}' → [' / Invoice / ']
    '{Author} ({Year}) - {Title}' → [' (', ') - ']
    """
    parts = re.split(r'\{[^}]+\}', format_string)
    return [p for p in parts if p.strip()]


def build_system_prompt(format_string: str) -> str:
    """
    Build the LLM system prompt for a given format string.

    Uses a terse prompt by default — benchmark confirmed it gives better
    throughput and lower error rate than the verbose version.
    """
    fields = parse_fields(format_string)
    field_block = ", ".join(f"{{{f}}}" for f in fields)
    examples = _get_examples(format_string, fields)
    # One compact example line keeps token count low
    example_line = f"{examples[0][0]} -> {examples[0][1]}" if examples else ""

    return (
        f"Format each filename as: {format_string}\n"
        f"Fields: {field_block}\n"
        "Rules: output only the formatted name, preserve original language, "
        "use Unknown for missing fields, strip underscores/dots/noise.\n"
        "For numbered lists: return same count in same order, one result per line.\n"
        f"Example: {example_line}"
    )


def _get_examples(format_string: str, fields: list[str]) -> list[tuple[str, str]]:
    """Return few-shot examples appropriate for the format."""
    # Use curated examples for the default format
    if format_string.strip() == "{Author} - {Title}":
        return _EXAMPLES_AUTHOR_TITLE

    # Generate illustrative placeholders for other formats
    example_a_values = {f: f"Sample{f}" for f in fields}
    example_b_values = {f: "Unknown" for f in fields}

    def fill(values: dict[str, str]) -> str:
        result = format_string
        for k, v in values.items():
            result = result.replace(f"{{{k}}}", v)
        return result

    return [
        ("messy_sample_filename_v2",  fill(example_a_values)),
        ("20240315_untitled_doc",     fill(example_b_values)),
    ]
