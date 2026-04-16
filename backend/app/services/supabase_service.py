"""
Supabase data access layer.

All DB operations are wrapped in try/except so the OCR pipeline
never crashes because of a missing or misconfigured database.

If SUPABASE_URL / SUPABASE_KEY are not set, the service falls back to
a bundled in-memory dataset of ~200 common Indian medicines plus the
full frequency code table — enough for a working demo.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from app.config import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Fallback in-memory medicine list ─────────────────────────────────────────
# Used when Supabase is not configured. Covers the most-prescribed Indian brands.
_FALLBACK_MEDICINES: List[str] = [
    # ── Analgesics / Antipyretics ─────────────────────────────────────────────
    "Dolo 650", "Crocin 500", "Crocin 650", "Calpol 500", "Tylenol",
    "Paracetamol", "Brufen 400", "Combiflam", "Ibugesic 400", "Ibuprofen",
    "Nimulid 100", "Zerodol 100", "Voveran 50", "Diclofenac",
    "Aceclofenac", "Etoricoxib", "Tramadol", "Ultracet",
    "Ketorolac", "Mefenamic Acid", "Meftal Spas", "Meftal",
    "Naprosyn", "Naproxen", "Celecoxib", "Celebrex",
    "Flurbiprofen", "Piroxicam", "Oxaprozin",

    # ── Antibiotics ───────────────────────────────────────────────────────────
    "Augmentin 625", "Augmentin 1g", "Amoxicillin", "Mox 500", "Amoxil",
    "Azithromycin", "Azee 500", "Azithral 500", "Zithromax",
    "Ciprofloxacin", "Cipro 500", "Ciplox 500", "Cifran 500",
    "Levofloxacin", "Levoflox 500", "Tavanic 500", "Levo 500",
    "Moxifloxacin", "Avelox", "Doxycycline", "Doxy 100",
    "Clindamycin", "Dalacin", "Metronidazole", "Flagyl 400", "Metro",
    "Cefixime", "Zifi 200", "Taxim O 200", "Cefix 200",
    "Cephalexin", "Ciplox", "Norfloxacin", "Ofloxacin", "Tinidazole",
    "Co-trimoxazole", "Bactrim", "Septran",
    "Fluconazole", "Forcan 150", "Diflucan",
    "Itraconazole", "Itrafungol", "Voriconazole",
    "Amikacin", "Gentamicin", "Tobramycin",
    "Cefpodoxime", "Cefpodox 200", "Cepodem", "Ceftriaxone",
    "Cefuroxime", "Cefaclor", "Cefdinir",
    "Piperacillin", "Tazobactam", "Penicillin",
    "Erythromycin", "Clarithromycin", "Klacid",
    "Rifampicin", "Isoniazid", "Pyrazinamide", "Ethambutol",
    "Mupirocin", "Fusidic Acid",

    # ── Antifungals ───────────────────────────────────────────────────────────
    "Clotrimazole", "Miconazole", "Terbinafine", "Lamisil",
    "Nystatin", "Griseofulvin", "Ketoconazole",

    # ── Antivirals ────────────────────────────────────────────────────────────
    "Acyclovir", "Valacyclovir", "Famciclovir",
    "Oseltamivir", "Tamiflu", "Remdesivir",

    # ── Antiparasitics ────────────────────────────────────────────────────────
    "Albendazole", "Mebendazole", "Ivermectin",
    "Chloroquine", "Artemether", "Lumefantrine",

    # ── Antihypertensives ─────────────────────────────────────────────────────
    "Amlodipine", "Amlokind 5", "Telmisartan", "Telma 40",
    "Telmikind 40", "Losartan", "Losacar 50", "Cozaar",
    "Ramipril", "Cardace 5", "Altace",
    "Olmesartan", "Olsar 20", "Benicar",
    "Valsartan", "Diovan", "Atenolol", "Tenormin 50",
    "Metoprolol", "Metolar 50", "Lopressor",
    "Bisoprolol", "Biselect 5", "Carvedilol",
    "Nebivolol", "Nebicard 5", "Bystolic",
    "Hydrochlorothiazide", "Furosemide", "Lasix",
    "Spironolactone", "Aldactone", "Indapamide", "Chlorthalidone",
    "Nifedipine", "Adalat", "Diltiazem", "Cardizem",
    "Verapamil", "Isradipine", "Felodipine",
    "Prazosin", "Doxazosin", "Hydralazine",
    "Nitroglycerine", "Isosorbide Mononitrate", "ISMN",
    "Isosorbide Dinitrate", "ISDN",
    "Perindopril", "Enalapril", "Lisinopril", "Benazepril",
    "Sacubitril", "Entresto",

    # ── Antidiabetics ─────────────────────────────────────────────────────────
    "Metformin", "Glycomet 500", "Glycomet SR 500", "Glucophage",
    "Glimepiride", "Amaryl 1", "Amaryl 2", "Miniglim",
    "Sitagliptin", "Januvia 50", "Januvia 100",
    "Vildagliptin", "Jalra 50", "Galvus",
    "Teneligliptin", "Tendia 20", "Tenepure",
    "Dapagliflozin", "Forxiga 10", "Farxiga",
    "Empagliflozin", "Jardiance 10",
    "Canagliflozin", "Invokana",
    "Voglibose", "Pioglitazone", "Glipizide", "Glyburide",
    "Acarbose", "Repaglinide", "Nateglinide",
    "Linagliptin", "Tradjenta", "Saxagliptin", "Onglyza",
    "Alogliptin", "Nesina",
    "Dulaglutide", "Trulicity", "Semaglutide", "Ozempic",
    "Liraglutide", "Victoza", "Exenatide", "Byetta",

    # ── Insulin ───────────────────────────────────────────────────────────────
    "Insulin", "Actrapid", "Mixtard", "Glargine", "Detemir",
    "Degludec", "Lispro", "Aspart", "Glulisine",
    "Basaglar", "Lantus", "Toujeo", "Tresiba",
    "Huminsulin", "Wosulin",

    # ── Statins / Lipid-lowering ──────────────────────────────────────────────
    "Atorvastatin", "Lipitor", "Atorva 10", "Atorva 20", "Atorva 40",
    "Rosuvastatin", "Rozavel 10", "Rozavel 20", "Rosuvas 10", "Crestor",
    "Simvastatin", "Zocor", "Pravastatin", "Lovastatin",
    "Fenofibrate", "Tricor", "Gemfibrozil", "Lopid",
    "Ezetimibe", "Zetia", "Ezetrol",
    "Evolocumab", "Repatha", "Alirocumab", "Praluent",

    # ── GI / Acid Reducers ────────────────────────────────────────────────────
    "Pantoprazole", "Pan 40", "Pantocid 40", "Protonix",
    "Omeprazole", "Omez 20", "Prilosec", "Losec",
    "Rabeprazole", "Rabifast 20", "Aciphex",
    "Esomeprazole", "Nexpro 40", "Nexium",
    "Lansoprazole", "Lafutidine",
    "Domperidone", "Domstal 10", "Motilium",
    "Ondansetron", "Vomistar 4", "Zofran",
    "Ranitidine", "Rantac 150", "Zantac",
    "Famotidine", "Pepcid", "Cimetidine",
    "Sucralfate", "Metoclopramide", "Reglan",
    "Bisacodyl", "Laxative", "Lactulose",
    "Loperamide", "Imodium", "ORS",
    "Dicyclomine", "Mebeverine", "Drotaverine",
    "Ursodeoxycholic Acid", "UDCA", "Livogen",

    # ── Respiratory / Allergy ─────────────────────────────────────────────────
    "Salbutamol", "Asthalin", "Ventolin", "Albuterol",
    "Montelukast", "Montair 10", "Singulair",
    "Levocetirizine", "Levocet 5", "Xyzal",
    "Cetirizine", "Alerid 10", "Zyrtec",
    "Fexofenadine", "Allegra", "Telfast",
    "Loratadine", "Claritin", "Desloratadine",
    "Budesonide", "Pulmicort", "Tiotropium", "Tiova", "Spiriva",
    "Salmeterol", "Formoterol", "Indacaterol",
    "Ipratropium", "Atrovent", "Theophylline",
    "Dextromethorphan", "Guaifenesin", "Bromhexine",
    "Ambroxol", "Ambrodil", "Mucaine", "Benadryl",
    "Diphenhydramine", "Chlorpheniramine", "Promethazine",
    "Fluticasone", "Mometasone", "Beclomethasone",
    "Zafirlukast", "Acetylcysteine",

    # ── Thyroid / Endocrine ───────────────────────────────────────────────────
    "Levothyroxine", "Thyronorm 25", "Thyronorm 50",
    "Thyronorm 75", "Thyronorm 100", "Synthroid",
    "Methimazole", "Propylthiouracil", "PTU",
    "Carbimazole", "Neo-Mercazole",

    # ── Vitamins / Supplements ────────────────────────────────────────────────
    "Vitamin D3", "Calcirol 60000", "Vitamin B12", "Cyanocobalamin",
    "Vitamin C", "Calcium", "Shelcal", "Iron", "Folic Acid",
    "Zinc", "Multivitamin", "Supradyn", "Revital",
    "Omega 3", "Biotin", "Methylcobalamin", "Melatonin",
    "Vitamin A", "Vitamin E", "Vitamin K",
    "B-complex", "Neurobion", "Becosules",
    "Magnesium", "Potassium Chloride", "Ferrous Sulphate",
    "Ferrous Ascorbate", "Livogen XT", "Ferium XT",
    "Calcium Carbonate", "Calcium Citrate",
    "Cholecalciferol", "Ergocalciferol",
    "Coenzyme Q10", "L-Arginine", "L-Carnitine",

    # ── Psychiatric / Neurological ────────────────────────────────────────────
    "Alprazolam", "Alprax", "Clonazepam", "Rivotril",
    "Escitalopram", "Nexito 5", "Nexito 10", "Lexapro",
    "Sertraline", "Zoloft", "Fluoxetine", "Prozac",
    "Amitriptyline", "Nortriptyline",
    "Gabapentin", "Gabantin 300", "Neurontin",
    "Pregabalin", "Pregalin 75", "Lyrica",
    "Valproate", "Depakote", "Levetiracetam", "Keppra",
    "Olanzapine", "Quetiapine", "Seroquel",
    "Risperidone", "Risperdal", "Haloperidol",
    "Lithium", "Carbamazepine", "Tegretol",
    "Lamotrigine", "Lamictal", "Topiramate", "Topamax",
    "Diazepam", "Lorazepam", "Midazolam",
    "Zolpidem", "Nitrazepam", "Clobazam",
    "Donepezil", "Rivastigmine", "Memantine",
    "Duloxetine", "Venlafaxine", "Mirtazapine",
    "Bupropion", "Citalopram", "Paroxetine",

    # ── Blood Thinners / Cardiac ──────────────────────────────────────────────
    "Aspirin", "Ecosprin 75", "Clopidogrel", "Clopilet 75", "Plavix",
    "Warfarin", "Warf 2", "Rivaroxaban", "Xarelto",
    "Apixaban", "Eliquis", "Dabigatran", "Pradaxa",
    "Digoxin", "Lanoxin", "Amiodarone", "Cordarone",
    "Ticagrelor", "Brilinta", "Prasugrel",
    "Heparin", "Enoxaparin", "Clexane", "Dalteparin",

    # ── Steroids / Immunomodulators ───────────────────────────────────────────
    "Prednisolone", "Wysolone 5", "Wysolone 10",
    "Methylprednisolone", "Medrol 4",
    "Deflazacort", "Defcort 6",
    "Hydroxychloroquine", "HCQS 200", "Plaquenil",
    "Dexamethasone", "Betamethasone", "Hydrocortisone",
    "Azathioprine", "Imuran", "Methotrexate",
    "Mycophenolate", "Tacrolimus", "Cyclosporine",
    "Leflunomide", "Sulfasalazine",

    # ── Urology / Prostate ────────────────────────────────────────────────────
    "Tamsulosin", "Urimax 0.4", "Flomax",
    "Finasteride", "Proscar", "Dutasteride", "Avodart",
    "Tadalafil", "Sildenafil", "Viagra", "Cialis",
    "Solifenacin", "Oxybutynin", "Tolterodine",

    # ── Gout / Arthritis ──────────────────────────────────────────────────────
    "Allopurinol", "Zyloric 100", "Zyloric 300", "Zyloprim",
    "Colchicine", "Febuxostat", "Uloric",
    "Probenecid", "Benzbromarone",

    # ── Ophthalmology / ENT ───────────────────────────────────────────────────
    "Timolol", "Latanoprost", "Travoprost",
    "Brimonidine", "Dorzolamide", "Brinzolamide",
    "Ciprofloxacin Eye Drops", "Tobramycin Eye Drops",
    "Moxifloxacin Eye Drops", "Ofloxacin Ear Drops",
    "Prednisolone Eye Drops", "Dexamethasone Eye Drops",
    "Betaxolol", "Pilocarpine",

    # ── Dermatology ───────────────────────────────────────────────────────────
    "Isotretinoin", "Accutane", "Doxycycline",
    "Tretinoin", "Adapalene", "Benzoyl Peroxide",
    "Clobetasol", "Halobetasol", "Fluocinolone",
    "Calcipotriol", "Tacrolimus Ointment", "Pimecrolimus",

    # ── Oncology (oral) ───────────────────────────────────────────────────────
    "Imatinib", "Gleevec", "Dasatinib", "Nilotinib",
    "Tamoxifen", "Letrozole", "Anastrozole", "Exemestane",
    "Capecitabine", "Xeloda",

    # ── Pain – Topical ───────────────────────────────────────────────────────
    "Diclofenac Gel", "Voltaren Gel", "Ketoprofen Gel",
    "Lidocaine", "Capsaicin", "Methyl Salicylate",
]

# ── Fallback frequency codes ──────────────────────────────────────────────────
_FALLBACK_FREQUENCY_CODES: Dict[str, Dict[str, Any]] = {
    "OD":   {"full_name": "Once Daily",      "times_per_day": 1,  "default_times": ["08:00"]},
    "QD":   {"full_name": "Once Daily",      "times_per_day": 1,  "default_times": ["08:00"]},
    "BD":   {"full_name": "Twice Daily",     "times_per_day": 2,  "default_times": ["08:00", "20:00"]},
    "BID":  {"full_name": "Twice Daily",     "times_per_day": 2,  "default_times": ["08:00", "20:00"]},
    "TDS":  {"full_name": "Thrice Daily",    "times_per_day": 3,  "default_times": ["08:00", "13:00", "20:00"]},
    "TID":  {"full_name": "Thrice Daily",    "times_per_day": 3,  "default_times": ["08:00", "13:00", "20:00"]},
    "QID":  {"full_name": "Four Times Daily","times_per_day": 4,  "default_times": ["08:00", "12:00", "16:00", "20:00"]},
    "HS":   {"full_name": "At Bedtime",      "times_per_day": 1,  "default_times": ["22:00"]},
    "SOS":  {"full_name": "As Needed",       "times_per_day": 0,  "default_times": []},
    "PRN":  {"full_name": "As Needed",       "times_per_day": 0,  "default_times": []},
    "STAT": {"full_name": "Immediately",     "times_per_day": 1,  "default_times": []},
    "AC":   {"full_name": "Before Meals",    "times_per_day": 3,  "default_times": ["07:30", "12:30", "19:30"]},
    "PC":   {"full_name": "After Meals",     "times_per_day": 3,  "default_times": ["09:00", "14:00", "21:00"]},
    "AM":   {"full_name": "Morning",         "times_per_day": 1,  "default_times": ["08:00"]},
    "PM":   {"full_name": "Evening",         "times_per_day": 1,  "default_times": ["18:00"]},
    "Q4H":  {"full_name": "Every 4 Hours",   "times_per_day": 6,  "default_times": ["06:00", "10:00", "14:00", "18:00", "22:00", "02:00"]},
    "Q6H":  {"full_name": "Every 6 Hours",   "times_per_day": 4,  "default_times": ["06:00", "12:00", "18:00", "00:00"]},
    "Q8H":  {"full_name": "Every 8 Hours",   "times_per_day": 3,  "default_times": ["06:00", "14:00", "22:00"]},
    "Q12H": {"full_name": "Every 12 Hours",  "times_per_day": 2,  "default_times": ["08:00", "20:00"]},
    "WEEKLY": {"full_name": "Once Weekly",   "times_per_day": 0,  "default_times": ["09:00"]},
}


class SupabaseService:
    """
    Centralised data-access layer.
    Falls back to in-memory data when Supabase credentials are absent.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = None
        self._medicine_names: List[str] = []
        self._frequency_codes: Dict[str, Dict[str, Any]] = {}
        self._use_supabase = bool(settings.supabase_url and settings.supabase_key)

    async def initialize(self) -> None:
        if self._use_supabase:
            try:
                from supabase import create_client
                self._client = create_client(
                    self._settings.supabase_url,
                    self._settings.supabase_key,
                )
                await self._load_from_supabase()
                logger.info("Supabase connected — medicine DB and frequency codes loaded.")
            except Exception as exc:
                logger.warning(f"Supabase init failed ({exc}). Using fallback in-memory data.")
                self._use_supabase = False
                self._load_fallback()
        else:
            logger.info("No Supabase credentials — using fallback in-memory dataset.")
            self._load_fallback()

    async def _load_from_supabase(self) -> None:
        # Load medicine names
        res = self._client.table("medicines_db").select("name").execute()
        self._medicine_names = [row["name"] for row in res.data]

        # Load frequency codes
        res = self._client.table("frequency_codes").select("*").execute()
        self._frequency_codes = {
            row["code"]: {
                "full_name": row["full_name"],
                "times_per_day": row["times_per_day"],
                "default_times": row.get("default_times") or [],
            }
            for row in res.data
        }

    def _load_fallback(self) -> None:
        self._medicine_names = list(_FALLBACK_MEDICINES)
        self._frequency_codes = dict(_FALLBACK_FREQUENCY_CODES)

    def get_all_medicine_names(self) -> List[str]:
        return self._medicine_names

    def get_frequency_codes(self) -> Dict[str, Dict[str, Any]]:
        return self._frequency_codes

    async def save_prescription(self, result_dict: Dict[str, Any]) -> Optional[str]:
        """Persist parsed prescription. Returns UUID or None if DB unavailable."""
        if not self._use_supabase or not self._client:
            return str(uuid.uuid4())
        try:
            payload = {
                "raw_text": result_dict.get("raw_text", ""),
                "doctor_name": result_dict.get("doctor_name", ""),
                "patient_name": result_dict.get("patient_name", ""),
                "medicines": result_dict.get("medicines", []),
                "warnings": result_dict.get("warnings", []),
                "overall_confidence": result_dict.get("overall_confidence", 0.0),
            }
            res = self._client.table("prescriptions").insert(payload).execute()
            return res.data[0]["id"] if res.data else None
        except Exception as exc:
            logger.error(f"Failed to save prescription: {exc}")
            return None

    async def save_reminders(self, prescription_id: str, schedule: Dict[str, Any]) -> None:
        if not self._use_supabase or not self._client:
            return
        try:
            for med in schedule.get("medicines", []):
                self._client.table("reminders").insert({
                    "prescription_id": prescription_id,
                    "medicine_name": med.get("medicine_name", ""),
                    "schedule": med,
                }).execute()
        except Exception as exc:
            logger.error(f"Failed to save reminders: {exc}")


# Module-level singleton — set during app lifespan startup
_instance: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    if _instance is None:
        raise RuntimeError("SupabaseService not initialised. Call set_supabase_service() first.")
    return _instance


def set_supabase_service(svc: SupabaseService) -> None:
    global _instance
    _instance = svc
