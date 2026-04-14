# -*- coding: utf-8 -*-
"""يولّد json/index.json من أسماء ملفات الاختبار في json/ (ما عدا index.json و *_ERROR.json)."""
import json
import os
import re

JSON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json")

# ملفات PDF فشل تحويلها حسب سجل المعالجة (للمراجعة اليدوية)
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
]


def parse_meta(stem: str):
    """stem بدون .json"""
    g = re.search(r"(?i)(?:Prim\s*(\d+)|prim(\d+))", stem)
    if not g:
        return None
    grade = int(g.group(1) or g.group(2))
    tm = re.search(r"(?i)TR(\d)", stem)
    term = int(tm.group(1)) if tm else 2
    wm = re.search(r"(?i)[_ ]([Ww])(\d+)", stem)
    week = int(wm.group(2)) if wm else 1
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


def quiz_title(grade: int, term: int, week: int, subj: str) -> str:
    wn = WEEK_AR[week] if 0 < week < len(WEEK_AR) else str(week)
    return f"الأسبوع {wn} – {subj}"


def main():
    tree = {"الإبتدائية": {}}
    prim = tree["الإبتدائية"]

    for fn in sorted(os.listdir(JSON_DIR)):
        if not fn.endswith(".json") or fn == "index.json":
            continue
        if "ERROR" in fn.upper():
            continue
        stem = fn[:-5]
        meta = parse_meta(stem)
        if not meta:
            continue
        grade_n, term_n, week_n = meta
        grade_label = GRADE_AR.get(grade_n, f"صف {grade_n}")
        term_label = TERM_AR.get(term_n, f"ترم {term_n}")
        title = quiz_title(grade_n, term_n, week_n, subject_ar(stem))

        prim.setdefault(grade_label, {})
        prim[grade_label].setdefault(term_label, {})
        # إذا تكرر نفس العنوان (نادر) نضيف لاحقة
        base_title = title
        n = 2
        while title in prim[grade_label][term_label]:
            title = f"{base_title} ({n})"
            n += 1
        prim[grade_label][term_label][title] = fn

    # الإبتدائية أولاً للقراءة؛ ثم تعليمات وقائمة الـ PDF التي لم تُحوَّل
    out = {
        "الإبتدائية": prim,
        "_تعليمات": "مفتاح «لم_يُحوّل_بعد» = أسماء ملفات PDF لم يُنتج لها JSON صالح من المعالج الآلي — أعد معالجتها يدوياً.",
        "لم_يُحوّل_بعد": PENDING_PDFS,
    }

    path = os.path.join(JSON_DIR, "index.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    n_quizzes = sum(
        1
        for g in prim.values()
        for t in g.values()
        for _ in t.values()
    )
    print(f"Wrote {path}")
    print(f"Quizzes indexed: {n_quizzes}")
    print(f"Pending PDFs listed: {len(PENDING_PDFS)}")


if __name__ == "__main__":
    main()
