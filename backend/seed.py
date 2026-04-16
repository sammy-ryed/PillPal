"""
Seed script — populates Supabase with medicine names and frequency codes.

Usage:
  cd backend
  cp .env.example .env   # fill in SUPABASE_URL and SUPABASE_KEY
  python seed.py

Run once before starting the server. Safe to re-run (upserts, no duplicates).
"""
import os
import sys
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Set SUPABASE_URL and SUPABASE_KEY in backend/.env first.")
    sys.exit(1)

from supabase import create_client

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Medicine database ──────────────────────────────────────────────────────────
MEDICINES = [
    # ── Analgesics / Antipyretics ────────────────────────────────────────────
    ("Dolo 650",          "Paracetamol",                "Analgesic",        ["650mg"]),
    ("Crocin 500",        "Paracetamol",                "Analgesic",        ["500mg"]),
    ("Crocin 650",        "Paracetamol",                "Analgesic",        ["650mg"]),
    ("Calpol 500",        "Paracetamol",                "Analgesic",        ["500mg"]),
    ("Paracetamol",       "Paracetamol",                "Analgesic",        ["500mg", "650mg"]),
    ("Brufen 400",        "Ibuprofen",                  "NSAID",            ["400mg"]),
    ("Ibuprofen",         "Ibuprofen",                  "NSAID",            ["200mg", "400mg", "600mg"]),
    ("Combiflam",         "Ibuprofen + Paracetamol",    "NSAID Combo",      ["400mg+325mg"]),
    ("Nimulid 100",       "Nimesulide",                 "NSAID",            ["100mg"]),
    ("Nimesulide",        "Nimesulide",                 "NSAID",            ["100mg"]),
    ("Zerodol 100",       "Aceclofenac",                "NSAID",            ["100mg"]),
    ("Voveran 50",        "Diclofenac",                 "NSAID",            ["50mg"]),
    ("Voveran SR 75",     "Diclofenac SR",              "NSAID",            ["75mg"]),
    ("Diclofenac",        "Diclofenac",                 "NSAID",            ["25mg", "50mg", "75mg", "100mg", "500mg"]),
    ("Aceclofenac",       "Aceclofenac",                "NSAID",            ["100mg"]),
    ("Etoricoxib",        "Etoricoxib",                 "COX-2 Inhibitor",  ["60mg", "90mg", "120mg"]),
    ("Arcoxia 90",        "Etoricoxib",                 "COX-2 Inhibitor",  ["90mg"]),
    ("Tramadol",          "Tramadol",                   "Opioid Analgesic", ["50mg"]),
    ("Ultracet",          "Tramadol + Paracetamol",     "Analgesic Combo",  ["37.5mg+325mg"]),
    ("Ketorolac",         "Ketorolac",                  "NSAID",            ["10mg"]),
    ("Mefenamic Acid",    "Mefenamic Acid",             "NSAID",            ["250mg", "500mg"]),
    ("Meftal Spas",       "Mefenamic Acid + Dicyclomine","NSAID Combo",     ["500mg+10mg"]),
    ("Meftal",            "Mefenamic Acid",             "NSAID",            ["500mg"]),
    ("Naproxen",          "Naproxen",                   "NSAID",            ["250mg", "500mg"]),
    ("Naprosyn",          "Naproxen",                   "NSAID",            ["250mg", "500mg"]),
    ("Celecoxib",         "Celecoxib",                  "COX-2 Inhibitor",  ["100mg", "200mg"]),
    ("Piroxicam",         "Piroxicam",                  "NSAID",            ["20mg"]),
    ("Flurbiprofen",      "Flurbiprofen",               "NSAID",            ["50mg", "100mg"]),
    ("Pentazocine",       "Pentazocine",                "Opioid Analgesic", ["25mg", "50mg"]),

    # ── Antibiotics – Penicillins / Cephalosporins ───────────────────────────
    ("Augmentin 625",     "Amoxicillin + Clavulanate",  "Antibiotic",       ["625mg"]),
    ("Augmentin 1g",      "Amoxicillin + Clavulanate",  "Antibiotic",       ["1000mg"]),
    ("Amoxicillin",       "Amoxicillin",                "Antibiotic",       ["250mg", "500mg"]),
    ("Mox 500",           "Amoxicillin",                "Antibiotic",       ["500mg"]),
    ("Amoxil",            "Amoxicillin",                "Antibiotic",       ["250mg", "500mg"]),
    ("Cephalexin",        "Cephalexin",                 "Antibiotic",       ["250mg", "500mg"]),
    ("Cefixime",          "Cefixime",                   "Antibiotic",       ["100mg", "200mg"]),
    ("Zifi 200",          "Cefixime",                   "Antibiotic",       ["200mg"]),
    ("Taxim O 200",       "Cefixime",                   "Antibiotic",       ["200mg"]),
    ("Cefix 200",         "Cefixime",                   "Antibiotic",       ["200mg"]),
    ("Cefpodoxime",       "Cefpodoxime",                "Antibiotic",       ["100mg", "200mg"]),
    ("Cepodem 200",       "Cefpodoxime",                "Antibiotic",       ["200mg"]),
    ("Cefdinir",          "Cefdinir",                   "Antibiotic",       ["300mg"]),
    ("Cefuroxime",        "Cefuroxime",                 "Antibiotic",       ["250mg", "500mg"]),
    ("Cefaclor",          "Cefaclor",                   "Antibiotic",       ["250mg", "500mg"]),
    ("Penicillin V",      "Phenoxymethylpenicillin",    "Antibiotic",       ["250mg", "500mg"]),

    # ── Antibiotics – Macrolides ─────────────────────────────────────────────
    ("Azithromycin",      "Azithromycin",               "Antibiotic",       ["250mg", "500mg"]),
    ("Azee 500",          "Azithromycin",               "Antibiotic",       ["500mg"]),
    ("Azithral 500",      "Azithromycin",               "Antibiotic",       ["500mg"]),
    ("Zithromax",         "Azithromycin",               "Antibiotic",       ["250mg", "500mg"]),
    ("Erythromycin",      "Erythromycin",               "Antibiotic",       ["250mg", "500mg"]),
    ("Clarithromycin",    "Clarithromycin",             "Antibiotic",       ["250mg", "500mg"]),
    ("Klacid 500",        "Clarithromycin",             "Antibiotic",       ["500mg"]),

    # ── Antibiotics – Fluoroquinolones ───────────────────────────────────────
    ("Ciprofloxacin",     "Ciprofloxacin",              "Antibiotic",       ["250mg", "500mg"]),
    ("Cipro 500",         "Ciprofloxacin",              "Antibiotic",       ["500mg"]),
    ("Ciplox 500",        "Ciprofloxacin",              "Antibiotic",       ["500mg"]),
    ("Cifran 500",        "Ciprofloxacin",              "Antibiotic",       ["500mg"]),
    ("Levofloxacin",      "Levofloxacin",               "Antibiotic",       ["250mg", "500mg", "750mg"]),
    ("Levoflox 500",      "Levofloxacin",               "Antibiotic",       ["500mg"]),
    ("Tavanic 500",       "Levofloxacin",               "Antibiotic",       ["500mg"]),
    ("Moxifloxacin",      "Moxifloxacin",               "Antibiotic",       ["400mg"]),
    ("Avelox",            "Moxifloxacin",               "Antibiotic",       ["400mg"]),
    ("Norfloxacin",       "Norfloxacin",                "Antibiotic",       ["400mg"]),
    ("Ofloxacin",         "Ofloxacin",                  "Antibiotic",       ["200mg", "400mg"]),

    # ── Antibiotics – Others ─────────────────────────────────────────────────
    ("Doxycycline",       "Doxycycline",                "Antibiotic",       ["100mg"]),
    ("Doxy 100",          "Doxycycline",                "Antibiotic",       ["100mg"]),
    ("Clindamycin",       "Clindamycin",                "Antibiotic",       ["150mg", "300mg"]),
    ("Metronidazole",     "Metronidazole",              "Antibiotic",       ["200mg", "400mg", "500mg"]),
    ("Flagyl 400",        "Metronidazole",              "Antibiotic",       ["400mg"]),
    ("Tinidazole",        "Tinidazole",                 "Antibiotic",       ["300mg", "500mg"]),
    ("Co-trimoxazole",    "Trimethoprim + Sulfamethoxazole", "Antibiotic",  ["480mg", "960mg"]),
    ("Septran",           "Trimethoprim + Sulfamethoxazole", "Antibiotic",  ["480mg"]),
    ("Bactrim",           "Trimethoprim + Sulfamethoxazole", "Antibiotic",  ["480mg"]),
    ("Rifampicin",        "Rifampicin",                 "Antibiotic",       ["150mg", "300mg", "450mg", "600mg"]),
    ("Isoniazid",         "Isoniazid",                  "Antibiotic",       ["100mg", "300mg"]),
    ("Pyrazinamide",      "Pyrazinamide",               "Antibiotic",       ["500mg", "750mg"]),
    ("Ethambutol",        "Ethambutol",                 "Antibiotic",       ["200mg", "400mg", "800mg"]),
    ("Mupirocin",         "Mupirocin",                  "Topical Antibiotic",["2%"]),
    ("Fusidic Acid",      "Fusidic Acid",               "Topical Antibiotic",["2%"]),
    ("Amikacin",          "Amikacin",                   "Antibiotic",       ["250mg", "500mg"]),
    ("Gentamicin",        "Gentamicin",                 "Antibiotic",       ["80mg"]),

    # ── Antifungals ──────────────────────────────────────────────────────────
    ("Fluconazole",       "Fluconazole",                "Antifungal",       ["50mg", "150mg"]),
    ("Forcan 150",        "Fluconazole",                "Antifungal",       ["150mg"]),
    ("Diflucan",          "Fluconazole",                "Antifungal",       ["150mg"]),
    ("Itraconazole",      "Itraconazole",               "Antifungal",       ["100mg", "200mg"]),
    ("Terbinafine",       "Terbinafine",                "Antifungal",       ["250mg"]),
    ("Lamisil",           "Terbinafine",                "Antifungal",       ["250mg"]),
    ("Clotrimazole",      "Clotrimazole",               "Antifungal",       ["1%"]),
    ("Ketoconazole",      "Ketoconazole",               "Antifungal",       ["200mg"]),
    ("Voriconazole",      "Voriconazole",               "Antifungal",       ["200mg"]),
    ("Nystatin",          "Nystatin",                   "Antifungal",       ["500000 IU"]),

    # ── Antivirals ───────────────────────────────────────────────────────────
    ("Acyclovir",         "Acyclovir",                  "Antiviral",        ["200mg", "400mg", "800mg"]),
    ("Valacyclovir",      "Valacyclovir",               "Antiviral",        ["500mg", "1000mg"]),
    ("Oseltamivir",       "Oseltamivir",                "Antiviral",        ["75mg"]),
    ("Tamiflu",           "Oseltamivir",                "Antiviral",        ["75mg"]),

    # ── Antiparasitics ───────────────────────────────────────────────────────
    ("Albendazole",       "Albendazole",                "Antiparasitic",    ["400mg"]),
    ("Mebendazole",       "Mebendazole",                "Antiparasitic",    ["100mg", "500mg"]),
    ("Ivermectin",        "Ivermectin",                 "Antiparasitic",    ["3mg", "6mg", "12mg"]),
    ("Chloroquine",       "Chloroquine",                "Antimalarial",     ["250mg", "500mg"]),
    ("Hydroxychloroquine","Hydroxychloroquine",          "Immunomodulator",  ["200mg", "400mg"]),
    ("HCQS 200",          "Hydroxychloroquine",         "Immunomodulator",  ["200mg"]),

    # ── Antihypertensives ────────────────────────────────────────────────────
    ("Amlodipine",        "Amlodipine",                 "Antihypertensive", ["2.5mg", "5mg", "10mg"]),
    ("Amlokind 5",        "Amlodipine",                 "Antihypertensive", ["5mg"]),
    ("Telmisartan",       "Telmisartan",                "Antihypertensive", ["20mg", "40mg", "80mg"]),
    ("Telma 40",          "Telmisartan",                "Antihypertensive", ["40mg"]),
    ("Telmikind 40",      "Telmisartan",                "Antihypertensive", ["40mg"]),
    ("Losartan",          "Losartan",                   "Antihypertensive", ["25mg", "50mg", "100mg"]),
    ("Losacar 50",        "Losartan",                   "Antihypertensive", ["50mg"]),
    ("Ramipril",          "Ramipril",                   "Antihypertensive", ["1.25mg", "2.5mg", "5mg", "10mg"]),
    ("Cardace 5",         "Ramipril",                   "Antihypertensive", ["5mg"]),
    ("Olmesartan",        "Olmesartan",                 "Antihypertensive", ["10mg", "20mg", "40mg"]),
    ("Olsar 20",          "Olmesartan",                 "Antihypertensive", ["20mg"]),
    ("Valsartan",         "Valsartan",                  "Antihypertensive", ["40mg", "80mg", "160mg"]),
    ("Atenolol",          "Atenolol",                   "Beta-blocker",     ["25mg", "50mg", "100mg"]),
    ("Tenormin 50",       "Atenolol",                   "Beta-blocker",     ["50mg"]),
    ("Metoprolol",        "Metoprolol",                 "Beta-blocker",     ["25mg", "50mg", "100mg"]),
    ("Metolar 50",        "Metoprolol",                 "Beta-blocker",     ["50mg"]),
    ("Bisoprolol",        "Bisoprolol",                 "Beta-blocker",     ["2.5mg", "5mg", "10mg"]),
    ("Biselect 5",        "Bisoprolol",                 "Beta-blocker",     ["5mg"]),
    ("Carvedilol",        "Carvedilol",                 "Beta-blocker",     ["3.125mg", "6.25mg", "12.5mg", "25mg"]),
    ("Nebivolol",         "Nebivolol",                  "Beta-blocker",     ["2.5mg", "5mg"]),
    ("Nebicard 5",        "Nebivolol",                  "Beta-blocker",     ["5mg"]),
    ("Hydrochlorothiazide","Hydrochlorothiazide",        "Diuretic",         ["12.5mg", "25mg"]),
    ("Furosemide",        "Furosemide",                 "Diuretic",         ["20mg", "40mg"]),
    ("Lasix 40",          "Furosemide",                 "Diuretic",         ["40mg"]),
    ("Spironolactone",    "Spironolactone",             "Diuretic",         ["25mg", "50mg", "100mg"]),
    ("Indapamide",        "Indapamide",                 "Diuretic",         ["1.5mg", "2.5mg"]),
    ("Chlorthalidone",    "Chlorthalidone",             "Diuretic",         ["12.5mg", "25mg"]),
    ("Enalapril",         "Enalapril",                  "Antihypertensive", ["2.5mg", "5mg", "10mg", "20mg"]),
    ("Lisinopril",        "Lisinopril",                 "Antihypertensive", ["2.5mg", "5mg", "10mg", "20mg"]),
    ("Perindopril",       "Perindopril",                "Antihypertensive", ["2mg", "4mg", "8mg"]),
    ("Nifedipine",        "Nifedipine",                 "Antihypertensive", ["10mg", "30mg"]),
    ("Adalat",            "Nifedipine",                 "Antihypertensive", ["10mg", "30mg"]),
    ("Diltiazem",         "Diltiazem",                  "Antihypertensive", ["30mg", "60mg", "90mg", "120mg"]),
    ("Verapamil",         "Verapamil",                  "Antihypertensive", ["40mg", "80mg", "120mg"]),
    ("Isosorbide Mononitrate","Isosorbide Mononitrate", "Nitrate",          ["10mg", "20mg", "40mg"]),
    ("ISMN",              "Isosorbide Mononitrate",     "Nitrate",          ["10mg", "20mg"]),
    ("Isosorbide Dinitrate","Isosorbide Dinitrate",     "Nitrate",          ["5mg", "10mg", "20mg"]),
    ("Nitroglycerin",     "Nitroglycerin",              "Nitrate",          ["0.5mg"]),
    ("Sacubitril Valsartan","Sacubitril + Valsartan",   "Antihypertensive", ["50mg", "100mg", "200mg"]),
    ("Entresto",          "Sacubitril + Valsartan",     "Antihypertensive", ["50mg", "100mg"]),

    # ── Antidiabetics ────────────────────────────────────────────────────────
    ("Metformin",         "Metformin",                  "Antidiabetic",     ["500mg", "850mg", "1000mg"]),
    ("Glycomet 500",      "Metformin",                  "Antidiabetic",     ["500mg"]),
    ("Glycomet SR 500",   "Metformin SR",               "Antidiabetic",     ["500mg"]),
    ("Glucophage",        "Metformin",                  "Antidiabetic",     ["500mg", "850mg", "1000mg"]),
    ("Glimepiride",       "Glimepiride",                "Antidiabetic",     ["1mg", "2mg", "3mg", "4mg"]),
    ("Amaryl 1",          "Glimepiride",                "Antidiabetic",     ["1mg"]),
    ("Amaryl 2",          "Glimepiride",                "Antidiabetic",     ["2mg"]),
    ("Sitagliptin",       "Sitagliptin",                "Antidiabetic",     ["25mg", "50mg", "100mg"]),
    ("Januvia 50",        "Sitagliptin",                "Antidiabetic",     ["50mg"]),
    ("Januvia 100",       "Sitagliptin",                "Antidiabetic",     ["100mg"]),
    ("Vildagliptin",      "Vildagliptin",               "Antidiabetic",     ["50mg"]),
    ("Jalra 50",          "Vildagliptin",               "Antidiabetic",     ["50mg"]),
    ("Galvus 50",         "Vildagliptin",               "Antidiabetic",     ["50mg"]),
    ("Teneligliptin",     "Teneligliptin",              "Antidiabetic",     ["20mg"]),
    ("Tendia 20",         "Teneligliptin",              "Antidiabetic",     ["20mg"]),
    ("Dapagliflozin",     "Dapagliflozin",              "Antidiabetic",     ["5mg", "10mg"]),
    ("Forxiga 10",        "Dapagliflozin",              "Antidiabetic",     ["10mg"]),
    ("Empagliflozin",     "Empagliflozin",              "Antidiabetic",     ["10mg", "25mg"]),
    ("Jardiance 10",      "Empagliflozin",              "Antidiabetic",     ["10mg"]),
    ("Canagliflozin",     "Canagliflozin",              "Antidiabetic",     ["100mg", "300mg"]),
    ("Voglibose",         "Voglibose",                  "Antidiabetic",     ["0.2mg", "0.3mg"]),
    ("Pioglitazone",      "Pioglitazone",               "Antidiabetic",     ["15mg", "30mg", "45mg"]),
    ("Glipizide",         "Glipizide",                  "Antidiabetic",     ["2.5mg", "5mg", "10mg"]),
    ("Glyburide",         "Glibenclamide",              "Antidiabetic",     ["2.5mg", "5mg"]),
    ("Acarbose",          "Acarbose",                   "Antidiabetic",     ["25mg", "50mg", "100mg"]),
    ("Repaglinide",       "Repaglinide",                "Antidiabetic",     ["0.5mg", "1mg", "2mg"]),
    ("Linagliptin",       "Linagliptin",                "Antidiabetic",     ["5mg"]),
    ("Tradjenta 5",       "Linagliptin",                "Antidiabetic",     ["5mg"]),
    ("Saxagliptin",       "Saxagliptin",                "Antidiabetic",     ["2.5mg", "5mg"]),
    ("Liraglutide",       "Liraglutide",                "Antidiabetic",     ["0.6mg", "1.2mg", "1.8mg"]),
    ("Victoza",           "Liraglutide",                "Antidiabetic",     ["1.2mg", "1.8mg"]),
    ("Semaglutide",       "Semaglutide",                "Antidiabetic",     ["0.25mg", "0.5mg", "1mg"]),
    ("Ozempic",           "Semaglutide",                "Antidiabetic",     ["0.5mg", "1mg"]),
    ("Insulin",           "Insulin",                    "Antidiabetic",     ["100 IU/ml"]),
    ("Actrapid",          "Soluble Insulin",            "Antidiabetic",     ["100 IU/ml"]),
    ("Mixtard",           "Biphasic Insulin",           "Antidiabetic",     ["100 IU/ml"]),
    ("Glargine",          "Insulin Glargine",           "Antidiabetic",     ["100 IU/ml"]),
    ("Lantus",            "Insulin Glargine",           "Antidiabetic",     ["100 IU/ml"]),
    ("Huminsulin",        "Human Insulin",              "Antidiabetic",     ["100 IU/ml"]),

    # ── Statins / Lipid-lowering ─────────────────────────────────────────────
    ("Atorvastatin",      "Atorvastatin",               "Statin",           ["10mg", "20mg", "40mg", "80mg"]),
    ("Lipitor",           "Atorvastatin",               "Statin",           ["10mg", "20mg", "40mg"]),
    ("Atorva 10",         "Atorvastatin",               "Statin",           ["10mg"]),
    ("Atorva 20",         "Atorvastatin",               "Statin",           ["20mg"]),
    ("Atorva 40",         "Atorvastatin",               "Statin",           ["40mg"]),
    ("Rosuvastatin",      "Rosuvastatin",               "Statin",           ["5mg", "10mg", "20mg", "40mg"]),
    ("Rozavel 10",        "Rosuvastatin",               "Statin",           ["10mg"]),
    ("Rozavel 20",        "Rosuvastatin",               "Statin",           ["20mg"]),
    ("Rosuvas 10",        "Rosuvastatin",               "Statin",           ["10mg"]),
    ("Crestor 10",        "Rosuvastatin",               "Statin",           ["10mg"]),
    ("Simvastatin",       "Simvastatin",                "Statin",           ["10mg", "20mg", "40mg"]),
    ("Pravastatin",       "Pravastatin",                "Statin",           ["10mg", "20mg", "40mg"]),
    ("Fenofibrate",       "Fenofibrate",                "Fibrate",          ["67mg", "134mg", "160mg"]),
    ("Ezetimibe",         "Ezetimibe",                  "Lipid-lowering",   ["10mg"]),
    ("Zetia",             "Ezetimibe",                  "Lipid-lowering",   ["10mg"]),
    ("Gemfibrozil",       "Gemfibrozil",                "Fibrate",          ["300mg", "600mg"]),

    # ── GI / Acid reducers ───────────────────────────────────────────────────
    ("Pantoprazole",      "Pantoprazole",               "PPI",              ["20mg", "40mg"]),
    ("Pan 40",            "Pantoprazole",               "PPI",              ["40mg"]),
    ("Pantocid 40",       "Pantoprazole",               "PPI",              ["40mg"]),
    ("Omeprazole",        "Omeprazole",                 "PPI",              ["10mg", "20mg", "40mg"]),
    ("Omez 20",           "Omeprazole",                 "PPI",              ["20mg"]),
    ("Prilosec",          "Omeprazole",                 "PPI",              ["20mg"]),
    ("Rabeprazole",       "Rabeprazole",                "PPI",              ["10mg", "20mg"]),
    ("Rabifast 20",       "Rabeprazole",                "PPI",              ["20mg"]),
    ("Esomeprazole",      "Esomeprazole",               "PPI",              ["20mg", "40mg"]),
    ("Nexpro 40",         "Esomeprazole",               "PPI",              ["40mg"]),
    ("Nexium",            "Esomeprazole",               "PPI",              ["20mg", "40mg"]),
    ("Lansoprazole",      "Lansoprazole",               "PPI",              ["15mg", "30mg"]),
    ("Domperidone",       "Domperidone",                "Antiemetic",       ["10mg"]),
    ("Domstal 10",        "Domperidone",                "Antiemetic",       ["10mg"]),
    ("Ondansetron",       "Ondansetron",                "Antiemetic",       ["4mg", "8mg"]),
    ("Vomistar 4",        "Ondansetron",                "Antiemetic",       ["4mg"]),
    ("Ranitidine",        "Ranitidine",                 "H2 Blocker",       ["150mg", "300mg"]),
    ("Rantac 150",        "Ranitidine",                 "H2 Blocker",       ["150mg"]),
    ("Famotidine",        "Famotidine",                 "H2 Blocker",       ["20mg", "40mg"]),
    ("Sucralfate",        "Sucralfate",                 "Antacid",          ["500mg", "1g"]),
    ("Metoclopramide",    "Metoclopramide",             "Antiemetic",       ["10mg"]),
    ("Loperamide",        "Loperamide",                 "Antidiarrheal",    ["2mg"]),
    ("Dicyclomine",       "Dicyclomine",                "Antispasmodic",    ["10mg", "20mg"]),
    ("Mebeverine",        "Mebeverine",                 "Antispasmodic",    ["135mg", "200mg"]),
    ("Drotaverine",       "Drotaverine",                "Antispasmodic",    ["40mg", "80mg"]),
    ("Lactulose",         "Lactulose",                  "Laxative",         ["10g/15ml"]),
    ("Bisacodyl",         "Bisacodyl",                  "Laxative",         ["5mg"]),
    ("Ursodeoxycholic Acid","Ursodeoxycholic Acid",      "Hepatoprotective", ["150mg", "300mg"]),
    ("UDCA 300",          "Ursodeoxycholic Acid",       "Hepatoprotective", ["300mg"]),
    ("Silymarin",         "Silymarin",                  "Hepatoprotective", ["140mg"]),

    # ── Respiratory / Allergy ────────────────────────────────────────────────
    ("Salbutamol",        "Salbutamol",                 "Bronchodilator",   ["2mg", "4mg"]),
    ("Asthalin",          "Salbutamol",                 "Bronchodilator",   ["2mg"]),
    ("Montelukast",       "Montelukast",                "Antileukotriene",  ["4mg", "5mg", "10mg"]),
    ("Montair 10",        "Montelukast",                "Antileukotriene",  ["10mg"]),
    ("Singulair",         "Montelukast",                "Antileukotriene",  ["10mg"]),
    ("Levocetirizine",    "Levocetirizine",             "Antihistamine",    ["2.5mg", "5mg"]),
    ("Levocet 5",         "Levocetirizine",             "Antihistamine",    ["5mg"]),
    ("Cetirizine",        "Cetirizine",                 "Antihistamine",    ["5mg", "10mg"]),
    ("Alerid 10",         "Cetirizine",                 "Antihistamine",    ["10mg"]),
    ("Fexofenadine",      "Fexofenadine",               "Antihistamine",    ["60mg", "120mg", "180mg"]),
    ("Allegra 180",       "Fexofenadine",               "Antihistamine",    ["180mg"]),
    ("Loratadine",        "Loratadine",                 "Antihistamine",    ["10mg"]),
    ("Desloratadine",     "Desloratadine",              "Antihistamine",    ["5mg"]),
    ("Budesonide",        "Budesonide",                 "Corticosteroid",   ["200mcg", "400mcg"]),
    ("Tiotropium",        "Tiotropium",                 "Bronchodilator",   ["18mcg"]),
    ("Tiova",             "Tiotropium",                 "Bronchodilator",   ["18mcg"]),
    ("Theophylline",      "Theophylline",               "Bronchodilator",   ["100mg", "200mg", "300mg"]),
    ("Ambroxol",          "Ambroxol",                   "Mucolytic",        ["30mg", "75mg"]),
    ("Bromhexine",        "Bromhexine",                 "Mucolytic",        ["4mg", "8mg"]),
    ("Acetylcysteine",    "N-Acetylcysteine",           "Mucolytic",        ["200mg", "600mg"]),
    ("Chlorpheniramine",  "Chlorpheniramine",           "Antihistamine",    ["4mg"]),
    ("Diphenhydramine",   "Diphenhydramine",            "Antihistamine",    ["25mg"]),
    ("Promethazine",      "Promethazine",               "Antihistamine",    ["10mg", "25mg"]),
    ("Fluticasone",       "Fluticasone",                "Corticosteroid",   ["50mcg", "100mcg"]),
    ("Mometasone",        "Mometasone",                 "Corticosteroid",   ["50mcg", "100mcg"]),

    # ── Thyroid ──────────────────────────────────────────────────────────────
    ("Levothyroxine",     "Levothyroxine",              "Thyroid",          ["25mcg", "50mcg", "75mcg", "100mcg"]),
    ("Thyronorm 25",      "Levothyroxine",              "Thyroid",          ["25mcg"]),
    ("Thyronorm 50",      "Levothyroxine",              "Thyroid",          ["50mcg"]),
    ("Thyronorm 75",      "Levothyroxine",              "Thyroid",          ["75mcg"]),
    ("Thyronorm 100",     "Levothyroxine",              "Thyroid",          ["100mcg"]),
    ("Methimazole",       "Methimazole",                "Antithyroid",      ["5mg", "10mg", "20mg"]),
    ("Carbimazole",       "Carbimazole",                "Antithyroid",      ["5mg", "10mg", "20mg"]),
    ("Propylthiouracil",  "Propylthiouracil",           "Antithyroid",      ["50mg", "100mg"]),

    # ── Vitamins / Supplements ───────────────────────────────────────────────
    ("Vitamin D3",        "Cholecalciferol",            "Supplement",       ["60000 IU", "1000 IU"]),
    ("Calcirol 60000",    "Cholecalciferol",            "Supplement",       ["60000 IU"]),
    ("Vitamin B12",       "Cyanocobalamin",             "Supplement",       ["500mcg", "1000mcg"]),
    ("Methylcobalamin",   "Methylcobalamin",            "Supplement",       ["500mcg", "1500mcg"]),
    ("Vitamin C",         "Ascorbic Acid",              "Supplement",       ["250mg", "500mg"]),
    ("Celin 500",         "Ascorbic Acid",              "Supplement",       ["500mg"]),
    ("Calcium",           "Calcium Carbonate",          "Supplement",       ["500mg", "1000mg"]),
    ("Shelcal",           "Calcium + Vit D3",           "Supplement",       ["500mg"]),
    ("Iron",              "Ferrous Sulphate",           "Supplement",       ["150mg", "300mg"]),
    ("Folic Acid",        "Folic Acid",                 "Supplement",       ["5mg"]),
    ("Zinc",              "Zinc Sulphate",              "Supplement",       ["20mg", "50mg"]),
    ("Multivitamin",      "Multivitamin",               "Supplement",       ["1 tablet"]),
    ("Supradyn",          "Multivitamin + Minerals",    "Supplement",       ["1 tablet"]),
    ("Revital",           "Multivitamin + Minerals",    "Supplement",       ["1 capsule"]),
    ("Neurobion",         "B-complex",                  "Supplement",       ["1 tablet"]),
    ("Becosules",         "B-complex",                  "Supplement",       ["1 capsule"]),
    ("Omega 3",           "Omega-3 Fatty Acids",        "Supplement",       ["1000mg"]),
    ("Biotin",            "Biotin",                     "Supplement",       ["5000mcg", "10000mcg"]),
    ("Melatonin",         "Melatonin",                  "Supplement",       ["3mg", "5mg"]),
    ("Magnesium",         "Magnesium",                  "Supplement",       ["250mg", "500mg"]),
    ("Coenzyme Q10",      "Ubiquinol",                  "Supplement",       ["100mg", "200mg"]),
    ("L-Carnitine",       "L-Carnitine",                "Supplement",       ["500mg", "1000mg"]),
    ("Vitamin A",         "Retinol",                    "Supplement",       ["25000 IU", "50000 IU"]),
    ("Vitamin E",         "Tocopherol",                 "Supplement",       ["200 IU", "400 IU"]),
    ("Ferrous Ascorbate", "Ferrous Ascorbate",          "Supplement",       ["100mg"]),
    ("Livogen XT",        "Iron + Folic Acid",          "Supplement",       ["150mg+0.5mg"]),

    # ── Psychiatric / Neurological ───────────────────────────────────────────
    ("Alprazolam",        "Alprazolam",                 "Anxiolytic",       ["0.25mg", "0.5mg", "1mg"]),
    ("Alprax",            "Alprazolam",                 "Anxiolytic",       ["0.25mg", "0.5mg"]),
    ("Clonazepam",        "Clonazepam",                 "Anxiolytic",       ["0.25mg", "0.5mg", "1mg", "2mg"]),
    ("Rivotril",          "Clonazepam",                 "Anxiolytic",       ["0.5mg", "1mg"]),
    ("Escitalopram",      "Escitalopram",               "Antidepressant",   ["5mg", "10mg", "20mg"]),
    ("Nexito 5",          "Escitalopram",               "Antidepressant",   ["5mg"]),
    ("Nexito 10",         "Escitalopram",               "Antidepressant",   ["10mg"]),
    ("Sertraline",        "Sertraline",                 "Antidepressant",   ["25mg", "50mg", "100mg"]),
    ("Fluoxetine",        "Fluoxetine",                 "Antidepressant",   ["10mg", "20mg", "40mg"]),
    ("Amitriptyline",     "Amitriptyline",              "Antidepressant",   ["10mg", "25mg", "50mg"]),
    ("Nortriptyline",     "Nortriptyline",              "Antidepressant",   ["10mg", "25mg"]),
    ("Duloxetine",        "Duloxetine",                 "Antidepressant",   ["20mg", "30mg", "60mg"]),
    ("Venlafaxine",       "Venlafaxine",                "Antidepressant",   ["37.5mg", "75mg", "150mg"]),
    ("Mirtazapine",       "Mirtazapine",                "Antidepressant",   ["7.5mg", "15mg", "30mg"]),
    ("Gabapentin",        "Gabapentin",                 "Anticonvulsant",   ["100mg", "300mg", "400mg"]),
    ("Gabantin 300",      "Gabapentin",                 "Anticonvulsant",   ["300mg"]),
    ("Pregabalin",        "Pregabalin",                 "Anticonvulsant",   ["75mg", "150mg", "300mg"]),
    ("Pregalin 75",       "Pregabalin",                 "Anticonvulsant",   ["75mg"]),
    ("Valproate",         "Sodium Valproate",           "Anticonvulsant",   ["200mg", "500mg"]),
    ("Levetiracetam",     "Levetiracetam",              "Anticonvulsant",   ["250mg", "500mg", "1000mg"]),
    ("Olanzapine",        "Olanzapine",                 "Antipsychotic",    ["2.5mg", "5mg", "10mg"]),
    ("Quetiapine",        "Quetiapine",                 "Antipsychotic",    ["25mg", "50mg", "100mg", "200mg"]),
    ("Risperidone",       "Risperidone",                "Antipsychotic",    ["0.5mg", "1mg", "2mg", "3mg"]),
    ("Haloperidol",       "Haloperidol",                "Antipsychotic",    ["0.5mg", "1.5mg", "5mg"]),
    ("Carbamazepine",     "Carbamazepine",              "Anticonvulsant",   ["100mg", "200mg", "400mg"]),
    ("Lamotrigine",       "Lamotrigine",                "Anticonvulsant",   ["25mg", "50mg", "100mg", "200mg"]),
    ("Topiramate",        "Topiramate",                 "Anticonvulsant",   ["25mg", "50mg", "100mg"]),
    ("Diazepam",          "Diazepam",                   "Anxiolytic",       ["2mg", "5mg", "10mg"]),
    ("Lorazepam",         "Lorazepam",                  "Anxiolytic",       ["0.5mg", "1mg", "2mg"]),
    ("Zolpidem",          "Zolpidem",                   "Hypnotic",         ["5mg", "10mg"]),
    ("Donepezil",         "Donepezil",                  "Anticholinesterase",["5mg", "10mg"]),
    ("Memantine",         "Memantine",                  "Anticholinesterase",["5mg", "10mg", "20mg"]),
    ("Lithium",           "Lithium Carbonate",          "Mood Stabilizer",  ["300mg", "400mg"]),

    # ── Blood thinners / Cardiac ─────────────────────────────────────────────
    ("Aspirin",           "Aspirin",                    "Antiplatelet",     ["75mg", "150mg"]),
    ("Ecosprin 75",       "Aspirin",                    "Antiplatelet",     ["75mg"]),
    ("Clopidogrel",       "Clopidogrel",                "Antiplatelet",     ["75mg"]),
    ("Clopilet 75",       "Clopidogrel",                "Antiplatelet",     ["75mg"]),
    ("Warfarin",          "Warfarin",                   "Anticoagulant",    ["1mg", "2mg", "5mg"]),
    ("Warf 2",            "Warfarin",                   "Anticoagulant",    ["2mg"]),
    ("Rivaroxaban",       "Rivaroxaban",                "Anticoagulant",    ["10mg", "15mg", "20mg"]),
    ("Xarelto",           "Rivaroxaban",                "Anticoagulant",    ["10mg", "15mg"]),
    ("Apixaban",          "Apixaban",                   "Anticoagulant",    ["2.5mg", "5mg"]),
    ("Eliquis",           "Apixaban",                   "Anticoagulant",    ["2.5mg", "5mg"]),
    ("Dabigatran",        "Dabigatran",                 "Anticoagulant",    ["75mg", "110mg", "150mg"]),
    ("Digoxin",           "Digoxin",                    "Cardiac Glycoside",["0.25mg"]),
    ("Amiodarone",        "Amiodarone",                 "Antiarrhythmic",   ["100mg", "200mg"]),
    ("Ticagrelor",        "Ticagrelor",                 "Antiplatelet",     ["60mg", "90mg"]),
    ("Brilinta",          "Ticagrelor",                 "Antiplatelet",     ["60mg", "90mg"]),
    ("Enoxaparin",        "Enoxaparin",                 "Anticoagulant",    ["40mg", "60mg", "80mg"]),
    ("Clexane",           "Enoxaparin",                 "Anticoagulant",    ["40mg", "60mg"]),

    # ── Steroids / Immunomodulators ──────────────────────────────────────────
    ("Prednisolone",      "Prednisolone",               "Corticosteroid",   ["5mg", "10mg", "20mg", "40mg"]),
    ("Wysolone 5",        "Prednisolone",               "Corticosteroid",   ["5mg"]),
    ("Wysolone 10",       "Prednisolone",               "Corticosteroid",   ["10mg"]),
    ("Methylprednisolone","Methylprednisolone",          "Corticosteroid",   ["4mg", "8mg", "16mg"]),
    ("Medrol 4",          "Methylprednisolone",         "Corticosteroid",   ["4mg"]),
    ("Dexamethasone",     "Dexamethasone",              "Corticosteroid",   ["0.5mg", "0.75mg", "4mg"]),
    ("Deflazacort",       "Deflazacort",                "Corticosteroid",   ["6mg", "12mg", "24mg"]),
    ("Defcort 6",         "Deflazacort",                "Corticosteroid",   ["6mg"]),
    ("Azathioprine",      "Azathioprine",               "Immunosuppressant",["25mg", "50mg"]),
    ("Methotrexate",      "Methotrexate",               "Immunosuppressant",["2.5mg", "5mg", "7.5mg"]),
    ("Leflunomide",       "Leflunomide",                "Immunosuppressant",["10mg", "20mg"]),
    ("Sulfasalazine",     "Sulfasalazine",              "Immunosuppressant",["500mg"]),
    ("Cyclosporine",      "Cyclosporine",               "Immunosuppressant",["25mg", "50mg", "100mg"]),

    # ── Urology ──────────────────────────────────────────────────────────────
    ("Tamsulosin",        "Tamsulosin",                 "Alpha-blocker",    ["0.4mg"]),
    ("Urimax 0.4",        "Tamsulosin",                 "Alpha-blocker",    ["0.4mg"]),
    ("Finasteride",       "Finasteride",                "5-ARI",            ["1mg", "5mg"]),
    ("Dutasteride",       "Dutasteride",                "5-ARI",            ["0.5mg"]),
    ("Tadalafil",         "Tadalafil",                  "PDE5 Inhibitor",   ["2.5mg", "5mg", "10mg", "20mg"]),
    ("Sildenafil",        "Sildenafil",                 "PDE5 Inhibitor",   ["25mg", "50mg", "100mg"]),
    ("Solifenacin",       "Solifenacin",                "Anticholinergic",  ["5mg", "10mg"]),
    ("Oxybutynin",        "Oxybutynin",                 "Anticholinergic",  ["2.5mg", "5mg"]),

    # ── Gout ─────────────────────────────────────────────────────────────────
    ("Allopurinol",       "Allopurinol",                "Antigout",         ["100mg", "300mg"]),
    ("Zyloric 100",       "Allopurinol",                "Antigout",         ["100mg"]),
    ("Zyloric 300",       "Allopurinol",                "Antigout",         ["300mg"]),
    ("Colchicine",        "Colchicine",                 "Antigout",         ["0.5mg", "1mg"]),
    ("Febuxostat",        "Febuxostat",                 "Antigout",         ["40mg", "80mg", "120mg"]),

    # ── Ophthalmology ────────────────────────────────────────────────────────
    ("Latanoprost",       "Latanoprost",                "Antiglaucoma",     ["0.005%"]),
    ("Timolol Eye",       "Timolol",                    "Antiglaucoma",     ["0.25%", "0.5%"]),
    ("Brimonidine",       "Brimonidine",                "Antiglaucoma",     ["0.15%", "0.2%"]),
    ("Dorzolamide",       "Dorzolamide",                "Antiglaucoma",     ["2%"]),

    # ── Dermatology ──────────────────────────────────────────────────────────
    ("Isotretinoin",      "Isotretinoin",               "Retinoid",         ["5mg", "10mg", "20mg"]),
    ("Tretinoin",         "Tretinoin",                  "Retinoid",         ["0.025%", "0.05%", "0.1%"]),
    ("Adapalene",         "Adapalene",                  "Retinoid",         ["0.1%", "0.3%"]),
    ("Clindamycin Gel",   "Clindamycin",                "Antibiotic",       ["1%"]),
    ("Clobetasol",        "Clobetasol Propionate",      "Corticosteroid",   ["0.05%"]),
    ("Calcipotriol",      "Calcipotriol",               "Vitamin D analogue",["0.005%"]),

    # ── Oncology (oral) ──────────────────────────────────────────────────────
    ("Imatinib",          "Imatinib",                   "Anticancer",       ["100mg", "400mg"]),
    ("Tamoxifen",         "Tamoxifen",                  "Anticancer",       ["10mg", "20mg"]),
    ("Letrozole",         "Letrozole",                  "Anticancer",       ["2.5mg"]),
    ("Anastrozole",       "Anastrozole",                "Anticancer",       ["1mg"]),
    ("Exemestane",        "Exemestane",                 "Anticancer",       ["25mg"]),
    ("Capecitabine",      "Capecitabine",               "Anticancer",       ["500mg"]),
]

# ── Frequency codes ────────────────────────────────────────────────────────────
FREQUENCY_CODES = [
    ("OD",     "Once Daily",        1,  ["08:00"]),
    ("QD",     "Once Daily",        1,  ["08:00"]),
    ("BD",     "Twice Daily",       2,  ["08:00", "20:00"]),
    ("BID",    "Twice Daily",       2,  ["08:00", "20:00"]),
    ("TDS",    "Thrice Daily",      3,  ["08:00", "13:00", "20:00"]),
    ("TID",    "Thrice Daily",      3,  ["08:00", "13:00", "20:00"]),
    ("QID",    "Four Times Daily",  4,  ["08:00", "12:00", "16:00", "20:00"]),
    ("HS",     "At Bedtime",        1,  ["22:00"]),
    ("SOS",    "As Needed",         0,  []),
    ("PRN",    "As Needed",         0,  []),
    ("STAT",   "Immediately",       1,  []),
    ("AC",     "Before Meals",      3,  ["07:30", "12:30", "19:30"]),
    ("PC",     "After Meals",       3,  ["09:00", "14:00", "21:00"]),
    ("AM",     "Morning",           1,  ["08:00"]),
    ("PM",     "Evening",           1,  ["18:00"]),
    ("Q4H",    "Every 4 Hours",     6,  ["06:00", "10:00", "14:00", "18:00", "22:00", "02:00"]),
    ("Q6H",    "Every 6 Hours",     4,  ["06:00", "12:00", "18:00", "00:00"]),
    ("Q8H",    "Every 8 Hours",     3,  ["06:00", "14:00", "22:00"]),
    ("Q12H",   "Every 12 Hours",    2,  ["08:00", "20:00"]),
    ("WEEKLY", "Once Weekly",       0,  ["09:00"]),
]


def seed_medicines():
    print(f"Seeding {len(MEDICINES)} medicines…")
    batch = [
        {
            "name": name,
            "generic_name": generic,
            "category": category,
            "common_dosages": dosages,
        }
        for name, generic, category, dosages in MEDICINES
    ]
    # Upsert in chunks of 100
    for i in range(0, len(batch), 100):
        chunk = batch[i:i+100]
        client.table("medicines_db").upsert(chunk, on_conflict="name").execute()
        print(f"  Inserted chunk {i//100 + 1} ({len(chunk)} records)")
    print("Medicines seeded.")


def seed_frequency_codes():
    print(f"Seeding {len(FREQUENCY_CODES)} frequency codes…")
    batch = [
        {"code": code, "full_name": full, "times_per_day": times, "default_times": def_times}
        for code, full, times, def_times in FREQUENCY_CODES
    ]
    client.table("frequency_codes").upsert(batch, on_conflict="code").execute()
    print("Frequency codes seeded.")


if __name__ == "__main__":
    seed_medicines()
    seed_frequency_codes()
    print("\nDone. Your Supabase DB is ready.")
