from __future__ import annotations

import re
import unicodedata

_IX = re.IGNORECASE | re.VERBOSE

INTERN_RE = re.compile(
    r"""
    \b(
        intern(?:ship|ships|s)?
        | stagiar(?:e|i)?
        | stagiu(?:l|lui)?
        | practic(?:[aă]|ant(?:[aei])?)
        | trainee
        | internship
        | summer[\s-]?intern
        | winter[\s-]?intern
        | off[\s-]?cycle
        | program(?:ul)?[\s-]+de[\s-]+internship
    )\b
    """,
    _IX,
)

SPRING_WEEK_RE = re.compile(
    r"""
    \b(
        spring[\s-]?week
        | spring[\s-]?insight
        | spring[\s-]?into
        | insight[\s-]?week
        | insight[\s-]?day
        | insight[\s-]?programme
        | insight[\s-]?program
        | exploratory[\s-]?(?:program|programme)
        | first[\s-]?year[\s-]?(?:program|programme|insight|week)?
        | freshman[\s-]?(?:program|programme|insight)
        | sophomore[\s-]?(?:program|programme)
        | student[\s-]?(?:program|programme)
        | university[\s-]?(?:program|programme)
        | early[\s-]?career
        | discovery[\s-]?day
        | invitational
    )\b
    """,
    _IX,
)

# Keep internships even if the title also says junior; drop true senior roles
# unless they are clearly internships.
SENIOR_RE = re.compile(r"(?i)\b(senior|staff|principal|director|head of|vp|vice president)\b")
LEAD_ONLY_RE = re.compile(r"(?i)\b(tech lead|team lead|engineering manager|lead engineer)\b")

EVENT_RE = re.compile(
    r"""
    \b(
        eveniment|conferin[tţ][aă]|career[\s-]?fair|job[\s-]?fair
        | cv[\s-]?clinic|angajatori[\s-]+de[\s-]+top|top[\s-]+talents
        | jumpstart|consiliere[\s-]+in[\s-]+cariera|sesiune[\s-]+inspirational
        | inscrieri[\s-]+gratuite
    )\b
    """,
    _IX,
)

TECH_RE = re.compile(
    r"""
    \b(
        software|developer|engineer|engineering|programator|programare
        | informatic|it\b|data|python|java|javascript|typescript|golang|rust
        | backend|frontend|fullstack|full[\s-]?stack|devops|sre|cloud|cyber
        | security|quant|quantitative|trading|research|machine[\s-]?learning
        | \bml\b|\bai\b|data[\s-]?science|analyst|analytics|database|sql
        | mobile|android|ios|qa|test(?:are|er)?|embedded|firmware|hardware
        | computer[\s-]?science|swe|sde|backend|platform|infrastructure
        | algoritm|algorithms|c\+\+|intern[\s-]?it|internship[\s-]?it
        | stagiu[\s-]+(?:it|software|programare)
    )\b
    """,
    _IX,
)

NON_TECH_RE = re.compile(
    r"""
    \b(
        sales|marketing|employer[\s-]?branding|talent[\s-]?acquisition
        | recruiter|recruitment|hr\b|human[\s-]?resources|auditor|audit
        | milk|collection|hipermarket|retail|contabil|accountant|accounting
        | supply[\s-]?chain|trade[\s-]?marketing|legal|juridic|logistics
        | human[\s-]?resource
    )\b
    """,
    _IX,
)

RO_LOCATION_RE = re.compile(
    r"""
    \b(
        romania|rom[aâ]nia|romaniei|romanian
        | bucharest|bucure[sşș]ti|bucuresti
        | cluj(?:[\s-]?napoca)?
        | ia[sșş]i|iassi
        | timi[sșş]oara|timisoara
        | bra[sșş]ov|brasov
        | sibiu|oradea|craiova
        | constan[tț]a|constanta
        | ploie[sșş]ti|ploiesti
        | arad|gala[tț]i|galati
        | pite[sșş]ti|pitesti
        | t[aâ]rgu[\s-]?mure[sșş]|targu[\s-]?mures
        | baia[\s-]?mare|satu[\s-]?mare|suceava
        | bac[aă]u|bacau|br[aă]ila|braila
        | ilfov|otopeni|voluntari|popesti|popești
        | \bro\b
    )\b
    | ,\s*RO\b
    | \bROM\b
    | /RO/
    """,
    _IX,
)


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch)).lower()


def is_event(title: str) -> bool:
    return bool(EVENT_RE.search(_fold(title)))


def is_internship(title: str, extra: str = "") -> bool:
    blob = f"{title} {extra}"
    if not INTERN_RE.search(blob):
        return False
    if SENIOR_RE.search(blob) and not INTERN_RE.search(title):
        return False
    if LEAD_ONLY_RE.search(title) and not INTERN_RE.search(title):
        return False
    return True


def is_spring_week(title: str, extra: str = "") -> bool:
    return bool(SPRING_WEEK_RE.search(f"{title} {extra}"))


def is_student_entry(title: str, extra: str = "") -> bool:
    return is_internship(title, extra) or is_spring_week(title, extra)


def is_romania(location: str, extra: str = "") -> bool:
    blob = f"{location} {extra}"
    return bool(RO_LOCATION_RE.search(blob) or RO_LOCATION_RE.search(_fold(blob)))


def is_tech_role(title: str, extra: str = "") -> bool:
    blob = f"{title} {extra}"
    folded = _fold(blob)
    if TECH_RE.search(folded):
        return True
    if NON_TECH_RE.search(folded) and not TECH_RE.search(folded):
        return False
    return False


def keep_job(
    *,
    title: str,
    location: str,
    extra: str = "",
    category: str = "",
    from_aggregator: bool = False,
    already_romania: bool = False,
) -> bool:
    if is_event(title):
        return False
    if not is_student_entry(title, extra):
        return False
    quant = (category or "").lower() == "quant"
    if not quant and not already_romania and not is_romania(location, extra):
        return False
    blob = f"{title} {extra}"
    if not quant and NON_TECH_RE.search(_fold(blob)) and not TECH_RE.search(_fold(blob)):
        return False
    if from_aggregator and not quant and not is_tech_role(title, extra):
        return False
    return True
