"""
i18n_strings.py
===============
Version 5.1 — Bilingual (English / Hindi) string tables for the UI.

Design approach
----------------
Rather than re-rendering server-side on every language toggle (which would
need a round-trip to Gradio for every already-rendered result), this module
provides the data used to render BOTH languages into the DOM up front. A
single `data-lang` attribute on the app root then shows/hides the matching
language via CSS, and a small JS dictionary (UI_STRINGS_JS, injected once
into the page <head>) handles static chrome labels client-side.

This keeps language switching instant (no server call) and means a result
rendered before a toggle still shows correctly in the newly chosen language.

Three string sets:
1. STATIC_UI       — chrome labels (buttons, headers, accordion titles,
                      placeholders) consumed by client-side JS via
                      data-i18n="key" attributes.
2. VERDICT_LABELS  — the 9 verdict names in Hindi, keyed by the EXACT
                      English verdict string used elsewhere as a dict key
                      and CSS class (VERDICT_META in constants.py). The
                      English key itself is never changed, only displayed
                      alongside its Hindi translation.
3. EVIDENCE_LABELS — SUPPORTING / CONTRADICTING / NEUTRAL source
                      classification labels in Hindi.

AI Fake News Detection & Live Verification System — Version 5.1
Government Polytechnic West Champaran — AI & ML Internship 2026
"""

from __future__ import annotations


# ── Static UI chrome (client-side JS dictionary) ──────────────────────────────
# Keys here MUST match data-i18n="key" attributes used in app.py HTML output.
STATIC_UI: dict[str, dict[str, str]] = {
    "app.title": {
        "en": "AI Fake News Detection",
        "hi": "एआई फेक न्यूज़ डिटेक्शन",
    },
    "app.tagline": {
        "en": "9-Verdict System · Live Evidence · ML Classification · Verified Facts",
        "hi": "9-निर्णय प्रणाली · लाइव साक्ष्य · एमएल वर्गीकरण · सत्यापित तथ्य",
    },
    "input.label": {
        "en": "News Text or URL",
        "hi": "समाचार पाठ या यूआरएल",
    },
    "input.placeholder": {
        "en": "Paste news headline, article text, or a news URL here…\nMinimum 5 characters.",
        "hi": "यहाँ समाचार शीर्षक, लेख का पाठ, या यूआरएल पेस्ट करें…\nकम से कम 5 अक्षर ज़रूरी हैं।",
    },
    "input.samples_label": {
        "en": "Try a sample",
        "hi": "एक उदाहरण आज़माएँ",
    },
    "btn.clear": {
        "en": "Clear",
        "hi": "साफ़ करें",
    },
    "btn.analyze": {
        "en": "Verify",
        "hi": "जाँचें",
    },
    "btn.analyzing": {
        "en": "Verifying…",
        "hi": "जाँच जारी है…",
    },
    "export.title": {
        "en": "Export Report",
        "hi": "रिपोर्ट निर्यात करें",
    },
    "export.desc": {
        "en": "Run a verification first, then download the report.",
        "hi": "पहले एक जाँच पूरी करें, फिर रिपोर्ट डाउनलोड करें।",
    },
    "export.txt": {
        "en": "TXT Report",
        "hi": "TXT रिपोर्ट",
    },
    "export.json": {
        "en": "JSON Report",
        "hi": "JSON रिपोर्ट",
    },
    "export.pdf": {
        "en": "PDF Report",
        "hi": "PDF रिपोर्ट",
    },
    "export.copy_label": {
        "en": "Quick Copy Summary",
        "hi": "त्वरित सारांश कॉपी करें",
    },
    "history.title": {
        "en": "Verification History",
        "hi": "जाँच इतिहास",
    },
    "history.desc": {
        "en": "Last 100 verifications (this session)",
        "hi": "पिछली 100 जाँचें (इस सत्र में)",
    },
    "history.search_placeholder": {
        "en": "Search history…",
        "hi": "इतिहास में खोजें…",
    },
    "history.search_btn": {
        "en": "Search",
        "hi": "खोजें",
    },
    "history.clear_btn": {
        "en": "Clear All",
        "hi": "सभी साफ़ करें",
    },
    "history.export_btn": {
        "en": "Export JSON",
        "hi": "JSON निर्यात करें",
    },
    "result.placeholder": {
        "en": "Your verification result will appear here.",
        "hi": "आपका जाँच परिणाम यहाँ दिखाई देगा।",
    },
    "result.confidence_breakdown": {
        "en": "Confidence Breakdown",
        "hi": "विश्वसनीयता विवरण",
    },
    "result.overall_confidence": {
        "en": "Overall Confidence",
        "hi": "समग्र विश्वसनीयता",
    },
    "result.ml_confidence": {
        "en": "ML Model Confidence",
        "hi": "एमएल मॉडल विश्वसनीयता",
    },
    "result.evidence_confidence": {
        "en": "Evidence Confidence",
        "hi": "साक्ष्य विश्वसनीयता",
    },
    "result.linguistic_confidence": {
        "en": "Linguistic Confidence",
        "hi": "भाषाई विश्वसनीयता",
    },
    "result.verified_fact": {
        "en": "Verified Fact",
        "hi": "सत्यापित तथ्य",
    },
    "result.sources": {
        "en": "Sources",
        "hi": "स्रोत",
    },
    "result.reasoning": {
        "en": "Reasoning",
        "hi": "तर्क"
    },
    "result.no_sources": {
        "en": "No trusted sources found. Check your network connection.",
        "hi": "कोई विश्वसनीय स्रोत नहीं मिला। अपना नेटवर्क कनेक्शन जाँचें।",
    },
    "team.title": {
        "en": "Project Team",
        "hi": "परियोजना टीम",
    },
    "team.tap_hint": {
        "en": "Tap a name to view full profile",
        "hi": "पूरी प्रोफ़ाइल देखने के लिए नाम पर टैप करें",
    },
    "team.modal.skills": {
        "en": "Skills",
        "hi": "कौशल",
    },
    "team.modal.contributions": {
        "en": "Key Contributions",
        "hi": "मुख्य योगदान",
    },
    "team.modal.close": {
        "en": "Close",
        "hi": "बंद करें",
    },
    "theme.toggle_to_dark": {
        "en": "Switch to dark mode",
        "hi": "डार्क मोड में बदलें",
    },
    "theme.toggle_to_light": {
        "en": "Switch to light mode",
        "hi": "लाइट मोड में बदलें",
    },
}


# ── Verdict label translations ─────────────────────────────────────────────────
# Keyed by the EXACT English verdict string (also used as a VERDICT_META key
# and CSS class suffix elsewhere) — only the displayed label is bilingual,
# the underlying key/class stays the stable English string throughout.
VERDICT_LABELS_HI: dict[str, str] = {
    "REAL":                  "वास्तविक",
    "LIKELY REAL":           "संभवतः वास्तविक",
    "PARTIALLY TRUE":        "आंशिक रूप से सत्य",
    "UNVERIFIED":            "असत्यापित",
    "INSUFFICIENT EVIDENCE": "अपर्याप्त साक्ष्य",
    "MIXED":                 "मिश्रित",
    "MISLEADING":            "भ्रामक",
    "LIKELY FAKE":           "संभवतः फ़र्ज़ी",
    "FAKE":                  "फ़र्ज़ी",
}

VERDICT_DESCRIPTIONS_HI: dict[str, str] = {
    "REAL":                  "कई विश्वसनीय स्रोतों से इस दावे की पुष्टि होती है।",
    "LIKELY REAL":           "उपलब्ध साक्ष्य और विश्लेषण इस दावे का समर्थन करते हैं।",
    "PARTIALLY TRUE":        "दावे का कुछ हिस्सा सत्य है, परंतु पूरी जानकारी सटीक नहीं है।",
    "UNVERIFIED":            "इस दावे की पुष्टि या खंडन के लिए पर्याप्त जानकारी नहीं मिली।",
    "INSUFFICIENT EVIDENCE": "कोई विश्वसनीय स्रोत नहीं मिला। इस दावे की पुष्टि या खंडन नहीं किया जा सकता।",
    "MIXED":                 "स्रोतों में इस दावे को लेकर मतभेद है।",
    "MISLEADING":            "दावे में कुछ सच्चाई है, परंतु प्रस्तुति भ्रामक है।",
    "LIKELY FAKE":           "उपलब्ध साक्ष्य और विश्लेषण बताते हैं कि यह दावा सही नहीं है।",
    "FAKE":                  "कई विश्वसनीय स्रोत इस दावे का खंडन करते हैं।",
}


# ── Evidence source classification labels ──────────────────────────────────────
EVIDENCE_LABELS_HI: dict[str, str] = {
    "supporting":    "समर्थक",
    "contradicting": "खंडनकारी",
    "neutral":       "तटस्थ",
}


# ── Team member biodata translations ────────────────────────────────────────────
# Keyed by the developer "id" field in config.py's DEVELOPERS list.
# Naman Kumar's entry is the most detailed, matching the depth of his English bio.
TEAM_HI: dict[str, dict] = {
    "naman-kumar": {
        "role": "फुल स्टैक एआई डेवलपर · यूआई/यूएक्स डिज़ाइनर",
        "badge": "परियोजना प्रमुख",
        "bio": (
            "एआई फेक न्यूज़ डिटेक्शन एंड लाइव वेरिफिकेशन सिस्टम के परियोजना प्रमुख "
            "और मुख्य वास्तुकार। नमन ने पूरी जाँच प्रणाली को डिज़ाइन किया — लाइव "
            "साक्ष्य खोज परत से लेकर एमएल वर्गीकरणकर्ता और 9-निर्णय स्कोरिंग इंजन "
            "तक — और पूरे फोरेंसिक-डोज़ियर इंटरफ़ेस की यूआई/यूएक्स दिशा का "
            "नेतृत्व किया, जिसमें द्विभाषी (अंग्रेज़ी/हिंदी) अनुभव और डार्क/लाइट "
            "थीमिंग प्रणाली शामिल है। उन्हें ऐसी परियोजनाएँ आकर्षित करती हैं जो "
            "एप्लाइड मशीन लर्निंग और इंटरफ़ेस डिज़ाइन के संगम पर हों — ऐसे टूल "
            "बनाना जो केवल उत्तर ही न दें, बल्कि उसके पीछे के तर्क को उपयोगकर्ता "
            "के लिए स्पष्ट भी बनाएँ।"
        ),
        "skills": [
            "पायथन", "ग्रेडियो", "scikit-learn", "सिस्टम आर्किटेक्चर",
            "यूआई/यूएक्स डिज़ाइन", "REST API", "गिट/गिटहब", "प्रोडक्ट थिंकिंग",
        ],
        "contributions": [
            "9-निर्णय निर्णय इंजन और विश्वसनीयता-भारांकन प्रणाली डिज़ाइन की",
            "लाइव बहु-स्रोत साक्ष्य सत्यापन पाइपलाइन का निर्माण किया",
            "द्विभाषी और डार्क/लाइट थीमिंग सहित पूरे यूआई/यूएक्स पुनर्डिज़ाइन का नेतृत्व किया",
            "टीम का समन्वय किया और परियोजना की रूपरेखा की ज़िम्मेदारी निभाई",
        ],
        "quote": "निर्णय तभी भरोसेमंद लगता है जब उस तक पहुँचने का तरीका दिखाई दे।",
    },
    "parmeshwar-kumar": {
        "role": "बैकएंड डेवलपर · एपीआई एकीकरण",
        "badge": "बैकएंड",
        "bio": (
            "बैकएंड डेवलपर, जो लाइव साक्ष्य-खोज एकीकरण परत के लिए ज़िम्मेदार हैं — "
            "कई समाचार और फैक्ट-चेक स्रोतों को एक विश्वसनीय पाइपलाइन में जोड़ना, "
            "साथ ही पुनः प्रयास (रिट्राई) और स्रोत अनुपलब्ध होने पर सहज ह्रास "
            "(ग्रेसफुल डिग्रेडेशन) की व्यवस्था। वास्तविक नेटवर्क परिस्थितियों में "
            "सिस्टम को मज़बूत बनाने पर केंद्रित — न कि केवल आदर्श स्थिति में काम "
            "करने पर।"
        ),
        "skills": ["पायथन", "REST API", "नेटवर्किंग", "एरर हैंडलिंग", "कैशिंग", "कंकरेंसी"],
        "contributions": [
            "कई समाचार और फैक्ट-चेक स्रोतों में लाइव खोज को एकीकृत किया",
            "बाहरी अनुरोधों के लिए रिट्राई लॉजिक और टाइमआउट हैंडलिंग लागू की",
            "अनावश्यक खोजों को कम करने के लिए सोर्स कैशिंग परत बनाई",
        ],
        "quote": "सिस्टम की विश्वसनीयता इस बात से तय होती है कि वह असफल कैसे होता है।",
    },
    "amit-kumar": {
        "role": "एमएल इंजीनियर · डेटासेट व मॉडल प्रशिक्षण",
        "badge": "एमएल / एआई",
        "bio": (
            "एमएल इंजीनियर जिन्होंने सिस्टम के केंद्र में मौजूद टेक्स्ट-वर्गीकरण "
            "मॉडल बनाया और प्रशिक्षित किया — डेटासेट तैयार करने और फ़ीचर "
            "इंजीनियरिंग (टीएफ़-आईडीएफ़ वेक्टराइज़ेशन) से लेकर मॉडल चयन और "
            "मूल्यांकन तक। केवल सटीकता के पीछे भागने के बजाय, वर्गीकरणकर्ता को "
            "इतना व्याख्या-योग्य बनाए रखने पर ध्यान दिया कि उसके विश्वसनीयता "
            "स्कोर का वास्तव में कोई अर्थ हो।"
        ),
        "skills": ["scikit-learn", "Pandas", "NumPy", "टीएफ़-आईडीएफ़ / एनएलपी", "मॉडल मूल्यांकन", "फ़ीचर इंजीनियरिंग"],
        "contributions": [
            "मल्टीनॉमियल नाइव बेज़ वर्गीकरणकर्ता को प्रशिक्षित और परिष्कृत किया",
            "टीएफ़-आईडीएफ़ वेक्टराइज़ेशन पाइपलाइन बनाई",
            "उम्मीदवार एल्गोरिदम में मॉडल मूल्यांकन और चयन किया",
        ],
        "quote": "विश्वसनीयता स्कोर एक वादा है। हमने उस वादे को ईमानदार रखने के लिए इसे परखा।",
    },
    "prince-kumar-chaurasiya": {
        "role": "अनुसंधान व प्रलेखन प्रमुख",
        "badge": "अनुसंधान",
        "bio": (
            "गलत सूचना के पैटर्न और विश्वसनीयता संकेतों पर अनुसंधान का नेतृत्व "
            "किया, जिसने सिस्टम के भाषाई-विश्लेषण नियमों को आकार दिया, और "
            "परियोजना का तकनीकी प्रलेखन तैयार किया — टीम के डिज़ाइन निर्णयों, "
            "समझौतों और निर्णय परिभाषाओं को समीक्षा व भविष्य के रखरखाव के लिए "
            "स्पष्ट रूप से दर्ज रखते हुए।"
        ),
        "skills": ["तकनीकी लेखन", "अनुसंधान", "गलत सूचना अध्ययन", "प्रलेखन", "आवश्यकता विश्लेषण"],
        "contributions": [
            "भाषाई विश्वसनीयता और गलत सूचना के संकेतकों पर अनुसंधान किया",
            "परियोजना का तकनीकी व उपयोगकर्ता प्रलेखन तैयार किया",
            "स्कोरिंग इंजन द्वारा उपयोग की जाने वाली 9-निर्णय वर्गीकरण प्रणाली परिभाषित की",
        ],
        "quote": "अच्छा प्रलेखन ही किसी परियोजना को लॉन्च के बाद भी अपने वादे निभाने में मदद करता है।",
    },
    "dhiraj-kumar": {
        "role": "क्यूए इंजीनियर · प्रदर्शन परीक्षण",
        "badge": "क्यूए",
        "bio": (
            "क्यूए इंजीनियर, जो संपूर्ण जाँच पाइपलाइन का परीक्षण करने के लिए "
            "ज़िम्मेदार हैं — दावे के पाठ में किनारे के मामलों (एज केस), गलत "
            "इनपुट, और नेटवर्क विफलता परिदृश्यों को कवर करते हुए — और लोड के "
            "तहत प्रतिक्रिया समय को पूर्वानुमेय बनाए रखने हेतु प्रदर्शन परीक्षण "
            "के लिए भी।"
        ),
        "skills": ["मैनुअल व एक्सप्लोरेटरी टेस्टिंग", "एज केस विश्लेषण", "प्रदर्शन परीक्षण", "बग ट्राएज"],
        "contributions": [
            "एज केस और गलत इनपुट में जाँच पाइपलाइन का परीक्षण किया",
            "खोज और स्कोरिंग पाइपलाइन पर प्रदर्शन परीक्षण चलाया",
            "विकास चक्रों में बग को ट्राएज और ट्रैक किया",
        ],
        "quote": "अगर किसी अजीब इनपुट पर परीक्षण नहीं हुआ, तो असल में परीक्षण हुआ ही नहीं।",
    },
    "md-tausim-akhtar": {
        "role": "एआई अनुसंधान योगदानकर्ता",
        "badge": "अनुसंधान",
        "bio": (
            "साक्ष्य-भारांकन दृष्टिकोणों पर अनुसंधान में योगदान दिया और निर्णय-"
            "स्कोरिंग लॉजिक के मूल्यांकन में सहायता की, यह समझने में मदद की कि "
            "अंतिम निर्णय में एमएल विश्वसनीयता, लाइव साक्ष्य और भाषाई संकेतों को "
            "कैसे संतुलित किया जाना चाहिए।"
        ),
        "skills": ["एआई अनुसंधान", "डेटा विश्लेषण", "मूल्यांकन डिज़ाइन"],
        "contributions": [
            "स्कोरिंग इंजन के लिए साक्ष्य-भारांकन रणनीतियों पर अनुसंधान किया",
            "नमूना मामलों में निर्णय की सटीकता के मूल्यांकन में सहायता की",
        ],
        "quote": "साक्ष्य को अच्छी तरह तौलना, उसे तेज़ी से तौलने से ज़्यादा मायने रखता है।",
    },
}
