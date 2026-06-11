import logging
from typing import Optional

_log = logging.getLogger("brevet")

OPTIONAL_PATTERNS = [
    "latin", "grec", "lca", "lv3", "chinois", "italien",
    "portugais", "russe", "arabe", "breton", "corse",
    "langue regionale", "theatre", "cinema", "danse",
    "chant choral", "cambridge", "section euro",
    "section internationale", "dnl",
]


def _is_optional(subject_name: str) -> bool:
    name = subject_name.lower().strip()
    for pattern in OPTIONAL_PATTERNS:
        if pattern in name:
            return True
    return False


def _to_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def fetch_and_calculate(url: str, login: str, password: str, ent: str = "") -> dict:
    try:
        import pronotepy
        from pronotepy import ent as pronotepy_ent
    except ImportError:
        return {"error": "pronotepy library not installed. Run: pip install pronotepy"}

    ent_func = None
    if ent:
        ent_name = ent.strip().lower()
        ent_map = {
            "ent_parisclassenumerique": getattr(pronotepy_ent, "paris_classe_numerique", None),
            "paris_classe_numerique":   getattr(pronotepy_ent, "paris_classe_numerique", None),
            "pcn":                      getattr(pronotepy_ent, "paris_classe_numerique", None),
            "educonnect":               getattr(pronotepy_ent, "educonnect", None),
            "ile_de_france":            getattr(pronotepy_ent, "ile_de_france_ent", None),
            "idf":                      getattr(pronotepy_ent, "ile_de_france_ent", None),
            "occitanie":                getattr(pronotepy_ent, "occitanie", None),
            "herault":                  getattr(pronotepy_ent, "herault", None),
            "eclat_bfc":                getattr(pronotepy_ent, "eclat_bfc", None),
            "haute_garonne":            getattr(pronotepy_ent, "haute_garonne", None),
            "atrium_sud":               getattr(pronotepy_ent, "atrium_sud", None),
            "lycee_connecte_normandie": getattr(pronotepy_ent, "lycee_connecte_normandie", None),
            "esidoc":                   getattr(pronotepy_ent, "esidoc", None),
        }
        ent_func = ent_map.get(ent_name)

    try:
        if ent_func is not None:
            client = pronotepy.Client(url, username=login, password=password, ent=ent_func)
        else:
            client = pronotepy.Client(url, username=login, password=password)
    except pronotepy.exceptions.CryptoError:
        return {"error": "Erreur de chiffrement - mot de passe incorrect ou URL invalide."}
    except pronotepy.exceptions.PronoteAPIError as e:
        return {"error": f"Erreur API Pronote : {e}"}
    except Exception as e:
        return {"error": f"Connexion echouee : {e}"}

    info = client.info
    student_name = info.name if info else login
    school = getattr(info, "school", None) or getattr(info, "establishment", None) or "?"
    class_name = getattr(info, "class_name", None) or getattr(info, "classe", None) or "?"

    annual_period = None
    for period in client.periods:
        pname = period.name.lower()
        if "annee" in pname or "année" in pname or "annuel" in pname:
            annual_period = period
            break
    if annual_period is None and client.periods:
        annual_period = client.periods[-1]
    if annual_period is None:
        return {"error": "Aucune periode trouvee dans Pronote."}

    subjects_data = []
    mandatory_sum = 0.0
    mandatory_count = 0
    optional_bonus_total = 0.0
    optional_details = []

    # Try period.averages first
    try:
        averages = annual_period.averages
    except Exception:
        averages = []

    for avg in averages:
        subj_name = avg.subject.name if avg.subject else "?"
        student_avg = _to_float(getattr(avg, "student", None))
        if student_avg is None:
            continue
        # Normalize to /20
        out_of = _to_float(getattr(avg, "out_of", 20))
        if out_of and out_of != 20.0:
            student_avg = student_avg * (20.0 / out_of)

        if _is_optional(subj_name):
            bonus = student_avg - 10.0 if student_avg > 10.0 else 0.0
            optional_bonus_total += bonus
            optional_details.append({
                "subject": subj_name,
                "average": round(student_avg, 2),
                "bonus": round(bonus, 2),
            })
        else:
            mandatory_sum += student_avg
            mandatory_count += 1
            subjects_data.append({
                "subject": subj_name,
                "average": round(student_avg, 2),
            })

    # Fallback: compute subject averages from raw grades
    if mandatory_count == 0:
        _log.info("Averages empty, falling back to grade-level computation")
        grades_by_subject = {}
        try:
            for period in client.periods:
                for g in period.grades:
                    sname = g.subject.name if g.subject else "?"
                    grade_val = _to_float(g.grade)
                    out_of_val = _to_float(g.out_of)
                    if grade_val is None or out_of_val is None or out_of_val == 0:
                        continue
                    normalised = grade_val * (20.0 / out_of_val)
                    if sname not in grades_by_subject:
                        grades_by_subject[sname] = []
                    grades_by_subject[sname].append(normalised)
        except Exception as e:
            return {"error": f"Impossible de recuperer les notes : {e}"}

        for subj_name, grade_list in grades_by_subject.items():
            student_avg = sum(grade_list) / len(grade_list)
            if _is_optional(subj_name):
                bonus = student_avg - 10.0 if student_avg > 10.0 else 0.0
                optional_bonus_total += bonus
                optional_details.append({
                    "subject": subj_name,
                    "average": round(student_avg, 2),
                    "bonus": round(bonus, 2),
                })
            else:
                mandatory_sum += student_avg
                mandatory_count += 1
                subjects_data.append({
                    "subject": subj_name,
                    "average": round(student_avg, 2),
                })

    if mandatory_count == 0:
        return {"error": "Aucune matiere obligatoire trouvee. Verifie que les notes sont disponibles dans Pronote."}

    total_sum = mandatory_sum + optional_bonus_total
    raw_average = total_sum / mandatory_count
    final_average = min(raw_average, 20.0)

    brevet_40_percent = round(final_average * 0.4, 2)

    return {
        "student": student_name,
        "school": school,
        "class": class_name,
        "period": annual_period.name,
        "subjects": subjects_data,
        "optional_subjects": optional_details,
        "mandatory_sum": round(mandatory_sum, 2),
        "mandatory_count": mandatory_count,
        "optional_bonus_total": round(optional_bonus_total, 2),
        "total_sum": round(total_sum, 2),
        "raw_average": round(raw_average, 2),
        "final_controle_continu": round(final_average, 2),
        "brevet_40_percent": brevet_40_percent,
        "capped": raw_average > 20.0,
    }
