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

# Abroad we only keep true spring / insight weeks — not internships
# and not generic "student programme" / "early career" titles.
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
        | first[\s-]?year[\s-]?(?:program|programme|insight|week)
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
        | inscrieri[\s-]+gratuite|career[\s-]?hub
    )\b
    """,
    _IX,
)

JUNK_COMPANY_RE = re.compile(
    r"""
    \b(
        jumpstart
        | genz[\s-]?career
        | career[\s-]?hub
    )\b
    | ^ejobs$
    | ^hipo$
    | ^bestjobs$
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
        | transilvania|transylvania
        | odorhei(?:u)?(?:[\s-]?secuiesc)?
        | mures|alba[\s-]?iulia|zalau|zalău
        | sf[aâ]ntu[\s-]?gheorghe|resita|reșița|deva|hunedoara
        | \bro\b
    )\b
    | ,\s*RO\b
    | \bROM\b
    | /RO/
    """,
    _IX,
)

# US + Canada only. UK / EU spring weeks stay in.
AMERICA_RE = re.compile(
    r"""
    \b(
        united[\s-]?states
        | u\.?s\.?a\.?
        | u\.s\.
        | chicago
        | nyc
        | new[\s-]?york
        | boston
        | san[\s-]?francisco
        | palo[\s-]?alto
        | mountain[\s-]?view
        | menlo[\s-]?park
        | seattle
        | redmond
        | austin
        | dallas
        | houston
        | miami
        | denver
        | atlanta
        | los[\s-]?angeles
        | san[\s-]?jose
        | california
        | texas
        | florida
        | massachusetts
        | illinois
        | connecticut
        | princeton
        | jersey[\s-]?city
        | hoboken
        | philadelphia
        | greenwich
        | stamford
        | washington[\s,]?\s*d\.?c
        | canada
        | toronto
        | vancouver
        | montreal
        | calgary
        | ontario
        | remote[\s-]*(?:[-,/]|\s+in\s+)?(?:the\s+)?(?:us|usa|u\.s|united[\s-]?states|canada)
    )\b
    | ,\s*(NY|IL|CA|MA|TX|WA|FL|NJ|CT|CO|GA|PA|DC|ON)\b
    | \bUSA\b
    | \bUS\b
    """,
    _IX,
)

FOREIGN_HINT_RE = re.compile(
    r"""
    \b(
        strainatate|străinătate|abroad
        | london|londra|amsterdam|paris|berlin|dublin|madrid
        | zurich|zürich|singapore|hong[\s-]?kong|tokyo
        | united[\s-]?kingdom|\buk\b|england|germany|france|netherlands
    )\b
    """,
    _IX,
)


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch)).lower()


def is_event(title: str) -> bool:
    return bool(EVENT_RE.search(_fold(title)))


def is_junk_company(company: str) -> bool:
    folded = _fold(company)
    if not folded:
        return False
    return bool(JUNK_COMPANY_RE.search(folded) or EVENT_RE.search(folded))


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


def is_america(location: str, extra: str = "") -> bool:
    blob = f"{location} {extra}"
    return bool(AMERICA_RE.search(blob) or AMERICA_RE.search(_fold(blob)))


def is_foreign_hint(location: str, extra: str = "") -> bool:
    blob = f"{location} {extra}"
    return bool(FOREIGN_HINT_RE.search(blob) or FOREIGN_HINT_RE.search(_fold(blob)))


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
    company: str = "",
    from_aggregator: bool = False,
    already_romania: bool = False,
) -> bool:
    if is_event(title) or is_event(company) or is_junk_company(company):
        return False
    intern = is_internship(title, extra)
    spring = is_spring_week(title, extra)
    if not intern and not spring:
        return False

    romania = already_romania or is_romania(location, extra)
    if from_aggregator and not romania and not is_america(location) and not is_foreign_hint(location):
        # Hipo / eJobs / BestJobs are Romanian boards; missing city still means RO.
        romania = True

    if is_america(location) and not romania:
        return False

    if not romania:
        return spring

    blob = f"{title} {extra} {company}"
    if NON_TECH_RE.search(_fold(blob)) and not TECH_RE.search(_fold(blob)):
        return False
    if from_aggregator and not is_tech_role(title, extra):
        return False
    return True
