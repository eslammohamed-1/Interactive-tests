# -*- coding: utf-8 -*-
"""يولّد json/index.json من أسماء ملفات الاختبار في json/ (ما عدا index.json و *_ERROR.json)."""
import json
import os
import re

JSON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json")

PENDING_PDFS = [
    "French1_prim3_tr2_w1.pdf",
    "ICT_English_Prim4_TR2_W6.pdf",
    "Deutsch_language_Prim5_TR2_W7.pdf",
    "ICT_english_Prim5_TR2_W4.pdf",
    "ICT_english_Prim5_TR2_W7.pdf",
    "Italiano_language_prim5_TR2_W2.pdf",
    "Espanol_language_Prim6_TR2_W2.pdf",
    "ICT_ARABIC_Prim6_TR2_W1.pdf",
]

GRADE_AR = {
    1: "الصف الأول الابتدائي",
    2: "الصف الثاني الابتدائي",
    3: "الصف الثالث الابتدائي",
    4: "الصف الرابع الابتدائي",
    5: "الصف الخامس الابتدائي",
    6: "الصف السادس الابتدائي",
}
SEC_GRADE_AR = {
    1: "الصف الأول الثانوي",
    2: "الصف الثاني الثانوي",
    3: "الصف الثالث الثانوي",
}
TERM_AR = {
    1: "الفصل الدراسي الأول",
    2: "الفصل الدراسي الثاني",
}
WEEK_AR = [
    "",
    "الأول",
    "الثاني",
    "الثالث",
    "الرابع",
    "الخامس",
    "السادس",
    "السابع",
    "الثامن",
    "التاسع",
    "العاشر",
    "الحادي عشر",
    "الثاني عشر",
]


def parse_meta(stem: str):
    """ابتدائي: Prim / prim في الاسم"""
    g = re.search(r"(?i)(?:Prim\s*(\d+)|prim(\d+))", stem)
    if not g:
        return None
    grade = int(g.group(1) or g.group(2))
    tm = re.search(r"(?i)TR(\d)", stem)
    term = int(tm.group(1)) if tm else 2
    wm = re.search(r"(?i)[_ ]([Ww])(\d+)", stem)
    week = int(wm.group(2)) if wm else 1
    return grade, term, week


def parse_meta_secondary(stem: str):
    """ثانوي: Sec1 أو Secondary1 … + TR1/TR2 (اختياري) + Wn أو ALL_Wn أو TR2-Wn"""
    s = stem.replace(" ", "")
    m = re.search(r"(?i)Secondary(\d+)|Secondry(\d+)", s)
    if m:
        grade = int(m.group(1) or m.group(2))
    else:
        m = re.search(r"(?i)Sec(\d+)", s)
        if not m:
            return None
        grade = int(m.group(1))
    tm = re.search(r"(?i)TR(\d)", s)
    term = int(tm.group(1)) if tm else 2
    weeks = list(re.finditer(r"(?i)W(\d+)", s))
    week = int(weeks[-1].group(1)) if weeks else 1
    return grade, term, week


def subject_ar(stem: str) -> str:
    s0 = stem
    s = stem.lower().replace(" ", "")
    if s0.startswith("French1"):
        return "لغة فرنسية (أولى)"
    if s0.startswith("French2"):
        return "لغة فرنسية (ثانية)"
    if "deutsch" in s:
        return "اللغة الألمانية"
    if "espanol" in s:
        return "اللغة الإسبانية"
    if "italiano" in s:
        return "اللغة الإيطالية"
    if "ict_arabic" in s:
        return "الكمبيوتر وتكنولوجيا المعلومات (عربي)"
    if "ict_english" in s or "ict_eglish" in s or "ictenglish" in s:
        return "الكمبيوتر وتكنولوجيا المعلومات (إنجليزي)"
    return stem.split("_")[0]


def subject_ar_secondary(stem: str) -> str:
    s = stem.lower().replace(" ", "")
    if s.startswith("math_arabic"):
        return "رياضيات (لغة عربية)"
    if s.startswith("math_english"):
        return "رياضيات (لغة إنجليزية)"
    if "philosophy" in s and "logic" in s:
        return "الفلسفة والمنطق"
    if s.startswith("arabic_language"):
        return "اللغة العربية"
    if "chineese" in s or "chinese" in s:
        return "اللغة الصينية"
    if "christian" in s and "religious" in s:
        return "التربية الدينية المسيحية"
    if "islamic" in s and "religion" in s:
        return "التربية الدينية الإسلامية"
    if s.startswith("deutsch_language"):
        return "اللغة الألمانية"
    if s.startswith("english_language"):
        return "اللغة الإنجليزية"
    if s.startswith("espanol"):
        return "اللغة الإسبانية"
    if stem.startswith("French1") or s.startswith("french1"):
        return "لغة فرنسية (أولى)"
    if stem.startswith("French2") or s.startswith("french2"):
        return "لغة فرنسية (ثانية)"
    if s.startswith("history"):
        return "التاريخ"
    if "ict_arabic" in s:
        return "الكمبيوتر وتكنولوجيا المعلومات (عربي)"
    if "ict_english" in s or "ict_eglish" in s:
        return "الكمبيوتر وتكنولوجيا المعلومات (إنجليزي)"
    if "integrated" in s:
        if "_ar" in s or "arabic" in s:
            return "العلوم المتكاملة (عربي)"
        if "_en" in s or "english" in s or "englis" in s:
            return "العلوم المتكاملة (إنجليزي)"
        return "العلوم المتكاملة"
    if s.startswith("italiano"):
        return "اللغة الإيطالية"
    head = re.split(r"(?i)(?:Secondary\d+|Sec\d+)", stem, maxsplit=1)[0]
    head = head.replace("_", " ").strip(" _-")
    return head or stem.split("_")[0]


def quiz_title(grade: int, term: int, week: int, subj: str) -> str:
    wn = WEEK_AR[week] if 0 < week < len(WEEK_AR) else str(week)
    return f"الأسبوع {wn} – {subj}"


def main():
    tree = {"الإبتدائية": {}, "الثانوية": {}}
    prim = tree["الإبتدائية"]
    sec = tree["الثانوية"]

    for fn in sorted(os.listdir(JSON_DIR)):
        if not fn.endswith(".json") or fn == "index.json":
            continue
        if "ERROR" in fn.upper():
            continue
        stem = fn[:-5].strip()
        meta = parse_meta(stem)
        if meta:
            grade_n, term_n, week_n = meta
            bucket = prim
            grade_label = GRADE_AR.get(grade_n, f"صف {grade_n}")
            subj_fn = subject_ar
        else:
            meta2 = parse_meta_secondary(stem)
            if not meta2:
                continue
            grade_n, term_n, week_n = meta2
            bucket = sec
            grade_label = SEC_GRADE_AR.get(grade_n, f"الصف {grade_n} ثانوي")
            subj_fn = subject_ar_secondary

        term_label = TERM_AR.get(term_n, f"ترم {term_n}")
        title = quiz_title(grade_n, term_n, week_n, subj_fn(stem))

        bucket.setdefault(grade_label, {})
        bucket[grade_label].setdefault(term_label, {})
        base_title = title
        n = 2
        while title in bucket[grade_label][term_label]:
            title = f"{base_title} ({n})"
            n += 1
        bucket[grade_label][term_label][title] = fn

    out = {
        "الإبتدائية": prim,
        "الثانوية": sec,
        "_تعليمات": "مفتاح «لم_يُحوّل_بعد» = أسماء ملفات PDF لم يُنتج لها JSON صالح من المعالج الآلي — أعد معالجتها يدوياً.",
        "لم_يُحوّل_بعد": PENDING_PDFS,
    }

    path = os.path.join(JSON_DIR, "index.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    n_prim = sum(1 for g in prim.values() for t in g.values() for _ in t.values())
    n_sec = sum(1 for g in sec.values() for t in g.values() for _ in t.values())
    print(f"Wrote {path}")
    print(f"Primary quizzes: {n_prim}, Secondary quizzes: {n_sec}")


if __name__ == "__main__":
    main()
