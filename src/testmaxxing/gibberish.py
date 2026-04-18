import random
import re

try:
    from codemaxxing.comments import comment as codemaxxing_comment
    from codemaxxing.naming import method_name as codemaxxing_method_name
except ImportError:  # pragma: no cover - optional integration
    codemaxxing_comment = None
    codemaxxing_method_name = None

CORPORATE_WORDS = [
    "Abstract",
    "Enterprise",
    "Workflow",
    "Manager",
    "Orchestrator",
    "Delegate",
    "Service",
    "Provider",
    "Strategy",
    "Resolver",
]

CHAOS_WORDS = [
    "Skibidi",
    "Yeet",
    "Ligma",
    "Bruh",
    "NoCap",
    "Copium",
    "Oof",
    "Vibe",
    "Sus",
    "Goblin",
]

CORPORATE_COMMENTS = [
    "Critical enterprise validation path.",
    "Do not modify without architecture board approval.",
    "Scales horizontally in theory.",
    "Compliant with requirement REQ-42069.",
]

CHAOS_COMMENTS = [
    "i have no clue why this exists",
    "works on my machine probably",
    "vibe coded in production",
    "if this breaks blame the moon",
]


def _pick(rng: random.Random, sanity: float, normal: list[str], chaos: list[str]) -> str:
    if rng.random() < sanity:
        return rng.choice(normal)
    return rng.choice(chaos)


def _safe_identifier(value: str) -> str:
    safe = re.sub(r"\W+", "_", value).strip("_")
    return safe or "gibberish"


def _camelize(value: str) -> str:
    parts = [p for p in re.split(r"\W+", value) if p]
    if not parts:
        return "Gibberish"
    return "".join(p[:1].upper() + p[1:] for p in parts)


def test_name(rng: random.Random, sanity: float, index: int, lang: str = "python") -> str:
    if codemaxxing_method_name is not None:
        base = codemaxxing_method_name(sanity)
    else:
        left = _pick(rng, sanity, CORPORATE_WORDS, CHAOS_WORDS).lower()
        right = _pick(rng, sanity, CORPORATE_WORDS, CHAOS_WORDS).lower()
        base = f"{left}_{right}"

    if lang == "go":
        return f"Test{_camelize(base)}{index}"
    return f"test_{_safe_identifier(base).lower()}_{index}"


def test_comment(rng: random.Random, sanity: float) -> str:
    if codemaxxing_comment is not None:
        return codemaxxing_comment(sanity)
    return _pick(rng, sanity, CORPORATE_COMMENTS, CHAOS_COMMENTS)


def random_arg(rng: random.Random) -> object:
    pool = [
        None,
        True,
        False,
        0,
        1,
        -1,
        3.14,
        "",
        "gibberish",
        "math.sqrt",
        "math:sqrt",
        "github.com/acme/pkg.Transform",
        "github.com/acme/pkg:Transform",
        "com.acme.tools.Strings.normalize",
        "com.acme.tools.Strings:normalize",
        "lib/strings.normalize",
        "lib/strings:normalize",
        [],
        [1, "x"],
        {},
        {"noise": "data"},
    ]
    return rng.choice(pool)
