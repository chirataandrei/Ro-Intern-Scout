#!/usr/bin/env python3
"""Build tools/candidates.json from the five expansion buckets."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "candidates.json"

# (name, category, extra slugs, careers_url)
BUCKETS: list[tuple[str, str, list[str], str]] = []

def add(category: str, names: list[str], slugs: dict[str, list[str]] | None = None, careers: dict[str, str] | None = None) -> None:
    slugs = slugs or {}
    careers = careers or {}
    for name in names:
        BUCKETS.append((name, category, slugs.get(name, []), careers.get(name, "")))


# --- Bucket 1: Romanian startups (product) ---
add("product", [
    "Deepstash", "Planable", "Sessions", "Digitail", "Vatis Tech", "Machinations",
    "Kinderpedia", "Adservio", "Medicai", "XVision", "Ogre AI", "Nestor", "Bookster",
    "Flip.ro", "Frisbo", "Innoship", "Tokinomo", "Cyscale", "CyberSwarm",
    "Instant Factoring", "Filbo", "Salt Edge", "Pago", "Omniconvert", "Creatopy",
    "Squirrly", "Softescu", "Humans.ai", "Aggranda", "Neurolabs", "Safetech Innovations",
    "certSIGN", "Bit Sentinel", "Licenseware", "Genezio", "Symphopay", "MeetGeek",
    "YAROOMS", "Bware Labs", "Questo", "Blackshell", "parol", "Footprints AI",
    "BookVitals", "Dexory", "EntertainM", "Ronin", "Wyliodrin", "SanoPass",
    "Telios Care", "PayByFace", "Lendrise", "Investimental", "TradeVille", "Tokero",
    "Confidas", "Ascendia", "Ringhel", "Elefant.ro", "Vola.ro",
], {
    "Flip.ro": ["flip", "flipro"],
    "Elefant.ro": ["elefant"],
    "Vola.ro": ["vola"],
    "Humans.ai": ["humansai", "humans"],
    "Ogre AI": ["ogreai", "ogre"],
    "Footprints AI": ["footprintsai"],
    "Salt Edge": ["saltedge"],
    "Instant Factoring": ["instantfactoring"],
    "Safetech Innovations": ["safetech"],
    "Bit Sentinel": ["bitsentinel"],
    "Bware Labs": ["bwarelabs"],
    "certSIGN": ["certsign"],
    "YAROOMS": ["yarooms"],
    "PayByFace": ["paybyface"],
    "Telios Care": ["telioscare"],
    "SanoPass": ["sanopass"],
    "TradeVille": ["tradeville"],
    "Vatis Tech": ["vatis"],
    "XVision": ["xvision"],
}, {
    "Deepstash": "https://deepstash.com/careers",
    "Planable": "https://planable.io/careers",
    "Digitail": "https://digitail.io/careers",
    "Kinderpedia": "https://kinderpedia.co/careers",
    "Bookster": "https://www.bookster.ro/careers",
    "Creatopy": "https://www.creatopy.com/careers",
    "MeetGeek": "https://meetgeek.ai/careers",
    "Genezio": "https://genezio.com/careers",
    "Dexory": "https://www.dexory.com/careers",
})

# --- Bucket 2: EU startups with RO office or remote-EU (product) ---
add("product", [
    "Supabase", "Neon", "PlanetScale", "Clerk", "Resend", "Railway", "Render",
    "Fly.io", "Grafana Labs", "n8n", "Weaviate", "Qdrant", "LangChain", "Langfuse",
    "Hugging Face", "Replit", "Sourcegraph", "Tabnine", "Framer", "Aiven", "Mollie",
    "Backbase", "Bird",
    "Mistral AI", "Aleph Alpha", "Synthesia", "ElevenLabs", "Lovable", "DeepL",
    "Photoroom", "Dust", "Poolside", "H Company", "Nabla", "Parloa",
    "Black Forest Labs", "Sana Labs", "Helsing",
    "Payhawk", "Nexo", "Tide", "GoCardless", "Checkout.com", "Rapyd", "Yapily",
    "TrueLayer", "Modulr", "Form3", "Thought Machine", "10x Banking", "Griffin",
    "Zilch", "Zopa", "Marshmallow", "Cleo", "Plum", "Moneybox", "Curve",
    "Wagestream", "Lendable", "Onfido", "ComplyAdvantage", "Quantexa",
    "Featurespace", "Solaris", "Scalable Capital", "Raisin", "Taxfix", "Anyfin",
    "Juni", "Tink", "Trustly", "Qonto", "Swile", "Payfit", "Spendesk", "Pennylane",
    "Alma", "Younited", "Shift Technology",
    "Vinted", "Pipedrive", "Veriff", "Hostinger", "Nord Security", "Kilo Health",
    "Back Market", "Doctolib", "Ankorstore", "Mirakl", "Malt", "Aircall", "Front",
    "Getaround", "Sorare", "Ledger", "Contentsquare", "Dataiku", "Algolia",
    "Picnic", "Otrium", "Swappie", "Oura", "Smartly.io", "Relex Solutions",
    "Truecaller", "Voi", "Mentimeter", "Kry", "Epidemic Sound", "Instabee",
    "Supercell", "Babbel", "Blinkist", "Egym", "Urban Sports Club", "Choco",
    "Grover", "Wefox", "Getsafe", "Clark", "Forto", "sennder", "Enpal", "1Komma5",
    "Einride", "Isar Aerospace", "The Exploration Company", "Volocopter", "Multiverse",
], {
    "Fly.io": ["fly", "flyio"],
    "n8n": ["n8n", "n8nio"],
    "Grafana Labs": ["grafanalabs", "grafana"],
    "Hugging Face": ["huggingface"],
    "Mistral AI": ["mistralai", "mistral"],
    "H Company": ["hcompany", "helloh"],
    "Black Forest Labs": ["blackforestlabs"],
    "Checkout.com": ["checkout", "checkoutcom"],
    "10x Banking": ["10xbanking", "10x"],
    "Thought Machine": ["thoughtmachine"],
    "ComplyAdvantage": ["complyadvantage"],
    "Shift Technology": ["shifttechnology"],
    "Nord Security": ["nordsecurity"],
    "Back Market": ["backmarket"],
    "Relex Solutions": ["relexsolutions", "relex"],
    "Epidemic Sound": ["epidemicsound"],
    "Urban Sports Club": ["urbansportsclub"],
    "1Komma5": ["1komma5"],
    "Isar Aerospace": ["isaraerospace"],
    "The Exploration Company": ["explorationcompany"],
    "Bird": ["messagebird", "bird"],
    "Smartly.io": ["smartly"],
    "Sana Labs": ["sanalabs"],
    "Aleph Alpha": ["alephalpha"],
    "Scalable Capital": ["scalablecapital"],
}, {
    "Supabase": "https://supabase.com/careers",
    "Grafana Labs": "https://grafana.com/about/careers/",
    "Hugging Face": "https://huggingface.co/join",
    "Mistral AI": "https://mistral.ai/careers",
    "ElevenLabs": "https://elevenlabs.io/careers",
    "DeepL": "https://jobs.deepl.com/",
    "Vinted": "https://www.vinted.com/careers",
    "Doctolib": "https://careers.doctolib.com/",
    "Algolia": "https://www.algolia.com/careers/",
    "Payhawk": "https://payhawk.com/careers",
    "Hostinger": "https://www.hostinger.com/careers",
    "Nord Security": "https://nordsecurity.com/careers",
})

# --- Bucket 3: rest of RO market ---
add("ssc", [
    "Yardi Romania", "Levi9", "NetRom Software", "Telenav Romania", "SCC Services Romania",
    "Centric IT Solutions", "Focality", "Signant Health", "Basware", "Modular Services",
    "Red Point Software Solutions", "Nuvei", "Wolfpack Digital", "Halcyon Mobile",
    "Nordlogic", "Zenitech", "Grapefruit", "Maxcode", "RomSoft", "Assist Software",
    "Sparktech Software", "Arnia Software", "Star Storage", "Bittnet Systems", "Dendrio",
    "Simavi", "Wizrom", "Transart", "Class IT", "Reea", "Qubiz", "Recognos",
    "Small Footprint", "Bitstone", "Ropardo", "msg systems", "adesso", "Concentrix",
    "Foundever", "Teleperformance", "Majorel", "Conduent", "TTEC", "WNS", "Inetum",
    "Expleo", "Devoteam", "Sopra Steria", "Akkodis", "N-iX", "ELEKS", "Ciklum",
    "Sigma Software", "Xebia", "Grid Dynamics", "Orange Services",
], {
    "Yardi Romania": ["yardi"],
    "Levi9": ["levi9"],
    "NetRom Software": ["netrom"],
    "Telenav Romania": ["telenav"],
    "Wolfpack Digital": ["wolfpackdigital"],
    "Halcyon Mobile": ["halcyonmobile"],
    "Assist Software": ["assistsoftware", "assist"],
    "Bittnet Systems": ["bittnet"],
    "Small Footprint": ["smallfootprint"],
    "msg systems": ["msgsystems", "msg"],
    "N-iX": ["nix", "n-ix"],
    "Sopra Steria": ["soprasteria"],
    "Grid Dynamics": ["griddynamics"],
    "Sigma Software": ["sigmasoftware"],
    "Signant Health": ["signanthealth"],
    "Red Point Software Solutions": ["redpoint"],
    "SCC Services Romania": ["scc"],
    "Centric IT Solutions": ["centric"],
    "Sparktech Software": ["sparktech"],
    "Arnia Software": ["arnia"],
    "Star Storage": ["starstorage"],
    "Orange Services": ["orangeservices"],
    "Class IT": ["classit"],
})

add("finance", [
    "MSCI", "Finastra", "Mambu", "Worldline", "Nexi", "Paysafe", "FIS", "Fiserv",
    "Global Payments", "SS&C", "FactSet", "Moody's", "S&P Global", "BT Code Crafters",
    "Vista Bank", "Patria Bank", "ProCredit Bank", "Credit Europe Bank",
    "Exim Banca Romaneasca", "Omniasig", "Asirom", "Uniqa", "Grawe", "Signal Iduna",
], {
    "S&P Global": ["spglobal"],
    "SS&C": ["ssctech", "sscinc"],
    "Global Payments": ["globalpayments"],
    "Moody's": ["moodys"],
    "BT Code Crafters": ["btcodecrafters"],
    "Exim Banca Romaneasca": ["eximbank"],
    "Credit Europe Bank": ["crediteurope"],
    "ProCredit Bank": ["procredit"],
    "Patria Bank": ["patriabank"],
    "Vista Bank": ["vistabank"],
    "Signal Iduna": ["signaliduna"],
})

add("product", [
    "SAS Institute", "Temenos", "OpenText", "Wolters Kluwer", "Unit4", "IFS",
    "Sage", "Freshworks", "Odoo", "MathWorks", "Vertiv",
], {
    "SAS Institute": ["sas"],
    "Wolters Kluwer": ["wolterskluwer"],
    "MathWorks": ["mathworks"],
    "Freshworks": ["freshworks"],
})

add("rd", [
    "Synopsys", "Cadence", "Siemens EDA", "AMD", "Texas Instruments", "Melexis",
    "Nordic Semiconductor", "Silicon Labs", "u-blox", "Sensirion", "ams OSRAM",
    "Imagination Technologies", "Skyworks", "Qorvo", "MediaTek", "Ambarella",
    "Semtech", "Lattice", "Rambus", "Synaptics", "Cirrus Logic",
    "Garrett Motion", "Flex", "ZF", "Knorr-Bremse", "Marquardt", "BorgWarner",
    "Adient", "Dana Incorporated", "Pirelli", "Coficab", "SEWS",
    "Kromberg & Schubert", "Prettl", "Zollner", "Webasto", "Eberspächer",
    "Rheinmetall", "thyssenkrupp", "TE Connectivity", "Veoneer", "Plastic Omnium",
    "Sensata", "Littelfuse", "Molex", "Amphenol", "Nexans", "Prysmian", "Legrand",
    "Hager", "Kathrein", "Nidec", "Diehl", "Celestica", "Plexus", "Siemens Energy",
    "Universal Alloy", "Aerostar", "Romaero", "MB Telecom",
    "Roche", "AstraZeneca", "GE HealthCare", "Philips", "Medtronic", "Baxter",
    "Novo Nordisk", "Takeda",
], {
    "Siemens EDA": ["siemenseda"],
    "Texas Instruments": ["texasinstruments", "ti"],
    "Nordic Semiconductor": ["nordicsemi"],
    "Silicon Labs": ["silabs"],
    "u-blox": ["ublox", "u-blox"],
    "ams OSRAM": ["amsosram"],
    "Imagination Technologies": ["imagination", "imgtec"],
    "Cirrus Logic": ["cirruslogic"],
    "Garrett Motion": ["garrettmotion"],
    "Knorr-Bremse": ["knorrbremse"],
    "Dana Incorporated": ["dana"],
    "Kromberg & Schubert": ["kromberg"],
    "TE Connectivity": ["teconnectivity"],
    "Plastic Omnium": ["plasticomnium"],
    "Siemens Energy": ["siemensenergy"],
    "Universal Alloy": ["universalalloy"],
    "MB Telecom": ["mbtelecom"],
    "GE HealthCare": ["gehealthcare"],
    "Novo Nordisk": ["novonordisk"],
    "AstraZeneca": ["astrazeneca"],
})

add("gaming", [
    "Pragmatic Play", "Amusnet", "Sportradar", "Bally's Interactive",
    "Green Horse Games", "Those Awesome Guys", "Fortis Games",
], {
    "Pragmatic Play": ["pragmaticplay"],
    "Bally's Interactive": ["ballys"],
    "Green Horse Games": ["greenhorsegames"],
    "Those Awesome Guys": ["thoseawesomeguys"],
    "Fortis Games": ["fortisgames"],
    "Sportradar": ["sportradar"],
})

add("telecom", ["Wizz Air", "TAROM"], {"Wizz Air": ["wizzair"]})

add("other", [
    "DPD Romania", "Autonom", "Just Eat Takeaway", "eSky", "Dedeman", "Mega Image",
    "Carrefour Romania", "Auchan Romania", "Altex", "Decathlon Romania",
    "IKEA Romania", "MedLife", "Regina Maria", "Electrica", "Hidroelectrica",
    "Nuclearelectrica", "Transgaz", "Transelectrica", "Romgaz", "MOL Romania",
    "Premier Energy",
], {
    "Just Eat Takeaway": ["justeattakeaway"],
    "DPD Romania": ["dpd"],
    "Carrefour Romania": ["carrefour"],
    "Auchan Romania": ["auchan"],
    "Decathlon Romania": ["decathlon"],
    "IKEA Romania": ["ikea"],
    "Regina Maria": ["reginamaria"],
    "MOL Romania": ["mol"],
    "Premier Energy": ["premierenergy"],
    "Nuclearelectrica": ["nuclearelectrica"],
    "Hidroelectrica": ["hidroelectrica"],
    "Transelectrica": ["transelectrica"],
})

# --- Bucket 4: HFT / prop / quant / exchanges ---
add("quant", [
    "Quadrature Capital", "Aspect Capital", "Systematica Investments", "Brevan Howard",
    "Rokos Capital", "Eisler Capital", "BlueCrest Capital", "Cheyne Capital", "CQS",
    "Garda Capital", "Verition", "Symmetry Investments", "Florin Court Capital",
    "Quantica Capital", "GAM Systematic", "H2O Asset Management", "Tudor Investment",
    "Caxton Associates", "Moore Capital", "Sculptor Capital", "Fortress Investment Group",
    "Davidson Kempner", "King Street Capital", "Capital Fund Management",
    "Oxford Asset Management", "Record Financial Group", "Millburn Ridgefield",
    "Transtrend", "Robeco", "APG Asset Management", "Ortec Finance", "Quantitative Brokers",
    "Mako Trading", "Tibra Capital", "Liquid Capital", "OSTC", "Futex", "Amplify Trading",
    "Schneider Trading Group", "Hehmeyer", "Geneva Trading", "XR Trading", "Quantlab",
    "Volant Trading", "Simplex Trading", "Kershner Trading", "Headlands Technologies",
    "Vatic Investments", "Vivienne Court Trading", "All Options", "Webb Traders",
    "Nyenburgh", "Eclipse Trading", "Grasshopper", "Tsuru Capital", "Sunrise Trading",
    "Deep Blue Capital",
    "Auros Global", "Keyrock", "B2C2", "GSR Markets", "Flowdesk", "Wincent",
    "Enigma Securities", "Woorton", "Portofino Technologies", "Amber Group",
    "Nickel Digital", "Hidden Road", "Copper.co", "Elwood Technologies", "Zodia Markets",
    "LMAX Group", "Cboe Europe", "Euronext", "Deutsche Börse", "SIX Group", "Nasdaq",
    "ICE", "CME Group", "Tradeweb", "MarketAxess", "TP ICAP", "BGC Partners",
    "Kepler Cheuvreux",
], {
    "Capital Fund Management": ["cfm"],
    "Oxford Asset Management": ["oxam"],
    "Brevan Howard": ["brevanhoward"],
    "Rokos Capital": ["rokos"],
    "Eisler Capital": ["eisler"],
    "BlueCrest Capital": ["bluecrest"],
    "Garda Capital": ["garda"],
    "Florin Court Capital": ["florincourt"],
    "Davidson Kempner": ["davidsonkempner"],
    "King Street Capital": ["kingstreet"],
    "Fortress Investment Group": ["fortress"],
    "Sculptor Capital": ["sculptor"],
    "Tudor Investment": ["tudor"],
    "Caxton Associates": ["caxton"],
    "Moore Capital": ["moorecapital"],
    "H2O Asset Management": ["h2o"],
    "GAM Systematic": ["gam"],
    "APG Asset Management": ["apg"],
    "Quantitative Brokers": ["quantitativebrokers"],
    "Schneider Trading Group": ["schneidertrading"],
    "Headlands Technologies": ["headlands"],
    "Kershner Trading": ["kershner"],
    "Vivienne Court Trading": ["viviennecourt"],
    "Tsuru Capital": ["tsuru"],
    "Deep Blue Capital": ["deepbluecapital"],
    "Auros Global": ["auros"],
    "GSR Markets": ["gsr"],
    "B2C2": ["b2c2"],
    "Portofino Technologies": ["portofino"],
    "Amber Group": ["ambergroup"],
    "Hidden Road": ["hiddenroad"],
    "Copper.co": ["copper", "copperco"],
    "Elwood Technologies": ["elwood"],
    "Zodia Markets": ["zodia"],
    "LMAX Group": ["lmax"],
    "Cboe Europe": ["cboe"],
    "Deutsche Börse": ["deutscheboerse"],
    "SIX Group": ["six-group", "sixgroup"],
    "CME Group": ["cmegroup", "cme"],
    "ICE": ["theice"],
    "TP ICAP": ["tpicap"],
    "BGC Partners": ["bgcpartners"],
    "Kepler Cheuvreux": ["keplercheuvreux"],
    "Enigma Securities": ["enigma"],
    "Nickel Digital": ["nickeldigital"],
})

# --- Bucket 5: spring weeks ---
add("finance", [
    "Jefferies", "Blackstone", "Evercore", "Lazard", "Rothschild & Co", "Houlihan Lokey",
    "Moelis", "PJT Partners", "Centerview", "Perella Weinberg", "Piper Sandler",
    "William Blair", "Baird", "RBC Capital Markets", "Wells Fargo", "Mizuho", "MUFG",
    "SMBC", "Santander CIB", "Rabobank", "ABN AMRO", "Commerzbank", "Nordea", "SEB",
    "Danske Bank", "Investec", "Cantor Fitzgerald", "Stifel", "Canaccord Genuity",
    "Peel Hunt", "Panmure Liberum", "Erste Group", "KBC", "Crédit Agricole CIB", "Natixis",
    "Julius Baer", "Pictet", "Vontobel", "Lombard Odier", "Baillie Gifford",
    "Legal & General", "M&G", "abrdn", "Janus Henderson", "Insight Investment",
    "PIMCO Europe", "Amundi", "Invesco", "Franklin Templeton", "T. Rowe Price",
    "Wellington Management", "Capital Group", "Barings", "Columbia Threadneedle",
    "Jupiter", "Ninety One", "Ruffer", "Rathbones", "Quilter", "St James's Place",
    "Hargreaves Lansdown", "AJ Bell",
    "IG Group", "CMC Markets", "Plus500", "eToro", "Interactive Brokers", "Saxo Bank",
    "Freetrade",
    "Lloyd's of London", "Beazley", "Hiscox", "Chubb", "AIG", "Zurich Insurance",
    "Swiss Re", "Munich Re", "SCOR", "Aon", "WTW", "Marsh McLennan", "Gallagher",
    "Howden",
    "Grant Thornton", "BDO", "Forvis Mazars", "RSM", "Alvarez & Marsal",
    "FTI Consulting", "AlixPartners", "Teneo", "L.E.K. Consulting", "OC&C",
    "Frontier Economics", "Charles River Associates", "NERA", "Analysis Group",
], {
    "Rothschild & Co": ["rothschild", "rothschildandco"],
    "Houlihan Lokey": ["houlihanlokey"],
    "PJT Partners": ["pjtpartners"],
    "Perella Weinberg": ["pwpartners", "perellaweinberg"],
    "Piper Sandler": ["pipersandler"],
    "William Blair": ["williamblair"],
    "RBC Capital Markets": ["rbc", "rbccm"],
    "Wells Fargo": ["wellsfargo"],
    "Santander CIB": ["santander"],
    "ABN AMRO": ["abnamro"],
    "Canaccord Genuity": ["canaccord"],
    "Peel Hunt": ["peelhunt"],
    "Panmure Liberum": ["panmureliberum"],
    "Erste Group": ["erstegroup"],
    "Crédit Agricole CIB": ["creditagricole", "cacib"],
    "Julius Baer": ["juliusbaer"],
    "Lombard Odier": ["lombardodier"],
    "Baillie Gifford": ["bailliegifford"],
    "Legal & General": ["legalandgeneral", "landg"],
    "M&G": ["mandg"],
    "Janus Henderson": ["janushenderson"],
    "Insight Investment": ["insightinvestment"],
    "PIMCO Europe": ["pimco"],
    "Franklin Templeton": ["franklintempleton"],
    "T. Rowe Price": ["troweprice"],
    "Wellington Management": ["wellington"],
    "Capital Group": ["capitalgroup"],
    "Columbia Threadneedle": ["columbiathreadneedle"],
    "Ninety One": ["ninetyone"],
    "St James's Place": ["sjp", "stjamessplace"],
    "Hargreaves Lansdown": ["hargreaveslansdown"],
    "AJ Bell": ["ajbell"],
    "IG Group": ["iggroup"],
    "CMC Markets": ["cmcmarkets"],
    "Interactive Brokers": ["interactivebrokers"],
    "Saxo Bank": ["saxobank"],
    "Lloyd's of London": ["lloyds"],
    "Zurich Insurance": ["zurich"],
    "Swiss Re": ["swissre"],
    "Munich Re": ["munichre"],
    "Marsh McLennan": ["mmc", "marshmclennan"],
    "WTW": ["willistowerswatson", "wtw"],
    "Forvis Mazars": ["mazars", "forvismazars"],
    "Alvarez & Marsal": ["alvarezmarsal"],
    "FTI Consulting": ["fticonsulting"],
    "L.E.K. Consulting": ["lek", "lekconsulting"],
    "OC&C": ["occstrategy"],
    "Frontier Economics": ["frontiereconomics"],
    "Charles River Associates": ["crai"],
    "Analysis Group": ["analysisgroup"],
    "Cantor Fitzgerald": ["cantor"],
})


def main() -> None:
    seen: set[str] = set()
    candidates: list[dict] = []
    for name, category, slugs, careers_url in BUCKETS:
        key = name.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        row = {"name": name, "category": category, "slugs": slugs}
        if careers_url:
            row["careers_url"] = careers_url
        candidates.append(row)
    OUT.write_text(json.dumps({"candidates": candidates}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(candidates)} candidates → {OUT}")


if __name__ == "__main__":
    main()
