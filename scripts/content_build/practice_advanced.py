"""Build 100 contextual four-skill micropractice topics at each advanced stage.

The C1, pre-C2 and C2 banks deliberately revisit 100 original situations with
increasingly demanding productive briefs. They are a practice spiral, not three
certified CEFR test forms. Reading comes from original project narratives;
listening follow-ups, interpretations and contrasts are separately authored in
practice_advanced_source.py. No external provider, textbook or random generation.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from practice_advanced_source import EXPECTED_TITLES, SCENES

ROOT = Path(__file__).resolve().parents[2]
LANGS = ("nl", "en", "fa")


def tri(nl, en, fa):
    return dict(zip(LANGS, (nl, en, fa), strict=True))


def join(*parts, separator=" "):
    return {lang: separator.join(part[lang] for part in parts) for lang in LANGS}


def sentences(paragraph):
    # Source narratives have ordinary prose, no decimal numbers or abbreviations.
    return {lang: re.split(r"(?<=[.!?؟])\s+", paragraph[lang].strip()) for lang in LANGS}


def question(key, prompt, correct, wrong, explanation, position):
    options = list(wrong)
    answer_index = position % (len(options) + 1)
    options.insert(answer_index, correct)
    return {"id": key, "prompt": prompt, "options": options,
            "answer_index": answer_index, "explanation": explanation}


# Actual recipients, genres and communicative intentions vary across domains.
RECIPIENTS = [
    tri("de voorzitter van het bewonersoverleg", "the chair of the residents' meeting", "رئیس نشست ساکنان"),
    tri("de onderzoekscoördinator", "the research coordinator", "هماهنگ‌کنندهٔ پژوهش"),
    tri("de teamleider", "the team leader", "سرپرست گروه"),
    tri("de eindredacteur", "the commissioning editor", "دبیر نهایی تحریریه"),
    tri("de verantwoordelijke dossierbeheerder", "the responsible case manager", "مسئول رسیدگی به پرونده"),
    tri("de projectverantwoordelijke", "the project lead", "مسئول پروژه"),
    tri("de redacteur van het culturele programma", "the cultural programme editor", "ویراستار برنامهٔ فرهنگی"),
    tri("de coördinator van de ondersteuning", "the support coordinator", "هماهنگ‌کنندهٔ حمایت"),
    tri("de penningmeester", "the treasurer", "خزانه‌دار"),
    tri("de verantwoordelijke voor de dienstverlening", "the service lead", "مسئول ارائهٔ خدمات"),
]
GENRES = [
    tri("een besluitvoorstel", "a decision proposal", "پیشنهاد تصمیم"),
    tri("een kritische onderzoeksnotitie", "a critical research note", "یادداشت انتقادی پژوهش"),
    tri("een interne werkafspraak", "an internal working agreement", "توافق داخلی کار"),
    tri("een redactioneel advies", "an editorial recommendation", "پیشنهاد تحریریه"),
    tri("een verduidelijkingsbrief voor dit fictieve dossier", "a clarification letter for this fictional case", "نامهٔ روشنگر برای این پروندهٔ خیالی"),
    tri("een afwegingsnota", "an options appraisal", "یادداشت سنجش گزینه‌ها"),
    tri("een beargumenteerde programmatoelichting", "a reasoned programme note", "توضیح مستدل برنامه"),
    tri("een respectvol afstemmingsbericht", "a respectful coordination message", "پیام محترمانهٔ هماهنگی"),
    tri("een financiële beslisnotitie voor dit fictieve project", "a financial decision note for this fictional project", "یادداشت تصمیم مالی برای این پروژهٔ خیالی"),
    tri("een beargumenteerd verbetervoorstel", "a reasoned improvement proposal", "پیشنهاد مستدل بهبود"),
]
FOCUS = {
    "c1": tri(
        "Feit en interpretatie onderscheiden; een voorstel onderbouwen met oorzaak, gevolg en een voorwaarde.",
        "Distinguish fact from interpretation; justify a proposal using cause, consequence and a condition.",
        "واقعیت را از تفسیر جدا کنید؛ پیشنهاد را با علت، پیامد و شرط پشتیبانی کنید."),
    "pre-c2": tri(
        "Een standpunt herformuleren; een concessie maken zonder het kernbezwaar op te geven; onzekerheid afbakenen.",
        "Reformulate a position; concede a point without abandoning the central objection; delimit uncertainty.",
        "موضع را بازگویی کنید؛ امتیازی بدهید بدون کنارگذاشتن ایراد اصلی؛ عدم‌قطعیت را محدود کنید."),
    "c2": tri(
        "Impliciete aannames expliciteren; register en strekking beheersen; een plausibele tegenlezing zorgvuldig begrenzen.",
        "Make implicit assumptions explicit; control register and intent; carefully delimit a plausible alternative reading.",
        "فرض ضمنی را روشن کنید؛ لحن و منظور را کنترل کنید؛ خوانش جایگزینِ پذیرفتنی را دقیق محدود کنید."),
}
SPEAK_EXTRA = {
    "c1": tri(
        "Geef één reden uit de leestekst en formuleer één haalbare voorwaarde voor uitvoering.",
        "Give one reason from the reading and state one feasible condition for implementation.",
        "یک دلیل از متن خواندن و یک شرط عملی برای اجرا بیان کنید."),
    "pre-c2": tri(
        "Erken een redelijk belang van de ander, maar begrens wat u nu kunt toezeggen. Vraag om één verduidelijking.",
        "Acknowledge a reasonable concern of the other person while limiting what you can promise now. Ask one clarifying question.",
        "نگرانی موجهِ طرف مقابل را بپذیرید، اما وعدهٔ فعلی را محدود کنید. یک پرسش روشنگر بپرسید."),
    "c2": tri(
        "Benoem één impliciete aanname in het voorstel. Maak tactvol duidelijk wat nog onzeker is en spreek een controleerbare vervolgstap af.",
        "Name one implicit assumption in the proposal. Tactfully clarify what remains uncertain and agree a verifiable next step.",
        "یک فرض ضمنیِ پیشنهاد را بیان کنید. با ملاحظه عدم‌قطعیت را روشن و گام بعدیِ قابل‌بررسی تعیین کنید."),
}
WRITE_EXTRA = {
    "c1": tri(
        "Scheid de oorspronkelijke afloop van de nieuwe ontwikkeling. Gebruik twee concrete brongegevens, formuleer een aanbeveling en noem één uitvoeringsvoorwaarde.",
        "Separate the original outcome from the new development. Use two concrete source details, make a recommendation and name one implementation condition.",
        "نتیجهٔ اولیه را از تحول تازه جدا کنید. دو جزئیات مشخص منبع، یک پیشنهاد و یک شرط اجرا بیاورید."),
    "pre-c2": tri(
        "Weeg de oorspronkelijke oplossing af tegen de nieuwe ontwikkeling. Verwerk een redelijke tegenwerping, een concessie en een voorwaardelijke aanbeveling. Benoem welke informatie nog ontbreekt.",
        "Weigh the original solution against the new development. Include a reasonable objection, a concession and a conditional recommendation. Name missing information.",
        "راه‌حل اولیه را در برابر تحول تازه بسنجید. ایراد موجه، پذیرش بخشی از آن و توصیهٔ مشروط بیاورید. اطلاعاتِ ناموجود را نام ببرید."),
    "c2": tri(
        "Synthetiseer beide bronnen zonder hun tijdlijn te vermengen. Onderzoek een plausibele tegenlezing en haar grens. Maak een impliciete aanname expliciet; adviseer met passende terughoudendheid en een controleerbare voorwaarde.",
        "Synthesise both sources without mixing their timelines. Examine a plausible alternative reading and its limit. Make an implicit assumption explicit; advise with suitable restraint and a verifiable condition.",
        "دو منبع را بدون مخلوط‌کردن ترتیب زمانی ترکیب کنید. خوانش جایگزینِ پذیرفتنی و حد آن را بررسی کنید. فرض ضمنی را روشن و با احتیاط و شرطِ قابل‌بررسی توصیه کنید."),
}


INTENT = [
    tri("een verantwoordelijke voor het voorgestelde vervolg vastleggen", "identify someone responsible for the proposed follow-up", "تعیین مسئول پیگیری پیشنهادی"),
    tri("de voorwaarden voor steun aan het voorgestelde vervolg verduidelijken", "clarify the conditions for supporting the proposed follow-up", "روشن‌کردن شرایط حمایت از پیگیری پیشنهادی"),
    tri("ontbrekende informatie benoemen voordat het voorgestelde vervolg wordt goedgekeurd", "identify missing information before approving the proposed follow-up", "نام‌بردن اطلاعاتِ ناموجود پیش از تأیید پیگیری پیشنهادی"),
]


def voice_message(first, scene, stage, intent):
    opening = tri("Dag, ik bel met een vervolg op ons vorige overleg.",
                  "Hello, I am calling with a follow-up to our previous discussion.",
                  "سلام، برای پیگیری گفت‌وگوی قبلی تماس می‌گیرم.")
    transition = tri("Dat was het vertrekpunt. Intussen is er een nieuwe ontwikkeling:",
                     "That was the starting point. There is now a new development:",
                     "آن نقطهٔ شروع بود. اکنون تحول تازه‌ای رخ داده است:")
    if stage == "c1":
        proposal = tri("Daarom stel ik deze volgende stap voor:", "I therefore propose this next step:", "بنابراین این گام بعدی را پیشنهاد می‌کنم:")
    elif stage == "pre-c2":
        proposal = tri("Het lijkt mij verdedigbaar om de volgende stap te overwegen:", "It seems defensible to consider the following step:", "به‌نظرم بررسی گام بعدی قابل‌دفاع است:")
    else:
        proposal = tri("Zonder daarmee de eerdere keuze af te vallen, zou ik deze stap ter overweging willen meegeven:", "Without thereby rejecting the earlier choice, I would like to put this step forward for consideration:", "بدون ردکردن انتخاب قبلی، می‌خواهم این گام را برای بررسی مطرح کنم:")
    ending = [
        tri("Over de voorwaarden wil ik later overleggen. Mijn vraag nu is: wie kan de verantwoordelijkheid voor dit vervolg opnemen?", "I want to discuss conditions later. My question now is: who can take responsibility for this follow-up?", "می‌خواهم بعداً دربارهٔ شرط‌ها گفت‌وگو کنم. پرسش فعلی این است: چه کسی می‌تواند مسئولیت این پیگیری را بپذیرد؟"),
        tri("Een verantwoordelijke zoeken we daarna. Ik hoor nu graag onder welke voorwaarden u dit voorstel kunt steunen.", "We will find someone responsible afterwards. For now I would like to hear under what conditions you can support this proposal.", "بعداً مسئول را پیدا می‌کنیم. اکنون مایلم بدانم با چه شرایطی از پیشنهاد حمایت می‌کنید."),
        tri("Over de uitvoering beslissen we later. Welke informatie ontbreekt volgens u nog om dit voorstel te kunnen beoordelen?", "We will decide about implementation later. Which information do you think is still missing to assess this proposal?", "بعداً دربارهٔ اجرا تصمیم می‌گیریم. به‌نظر شما برای ارزیابی پیشنهاد هنوز چه اطلاعاتی کم است؟"),
    ][intent]
    return join(opening, first, transition, scene["fact"], proposal, scene["action"], ending)


def linked_words(story, source_words, target):
    """Prefer actual same-term links; otherwise offer related category vocabulary.

    The advanced libraries intentionally contain different subsets. A category
    word is presented as supplementary vocabulary, not falsely quoted as a word
    from the source. No cross-stage or nonexistent IDs are emitted.
    """
    terms = {source_words[key]["term"] for key in story["vocabulary_ids"]}
    direct = [word["id"] for word in target["vocabulary"] if word["term"] in terms]
    if direct:
        return direct
    candidates = [word for word in target["vocabulary"] if word["topic"]["nl"] == story["topic"]["nl"]]
    # Prefer familiar conceptual terms before specialised supplementary items.
    return [word["id"] for word in candidates[:3]]


def productive(topic_id, story, scene, category_index, stage):
    title = story["title"]
    recipient = RECIPIENTS[category_index]
    genre = GENRES[category_index]
    speaking_prompt = tri(
        f"Situatie: {title['nl']}. U bent de collega die het vervolgbericht ontvangt. Reageer in een spraakbericht aan {recipient['nl']}. Beantwoord dit voorstel: {scene['action']['nl']} Houd rekening met de nieuwe vaststelling: {scene['fact']['nl']} Spreek maximaal 60 seconden.",
        f"Situation: {title['en']}. You are the colleague receiving the follow-up message. Reply by voice message to {recipient['en']}. Respond to this proposal: {scene['action']['en']} Account for the new finding: {scene['fact']['en']} Speak for at most 60 seconds.",
        f"موقعیت: {title['fa']}. شما همکار دریافت‌کنندهٔ پیام پیگیری هستید. با پیام صوتی به {recipient['fa']} پاسخ دهید. به این پیشنهاد واکنش نشان دهید: {scene['action']['fa']} یافتهٔ تازه را لحاظ کنید: {scene['fact']['fa']} حداکثر ۶۰ ثانیه صحبت کنید.")
    speaking_prompt = join(speaking_prompt, SPEAK_EXTRA[stage])
    # A modelled response acknowledges the fact, accepts a *proposed* action and
    # asks for role confirmation. It does not invent implementation or outcomes.
    sample = join(
        tri("Dank voor uw bericht. Ik zie waarom een vervolg nodig is:", "Thank you for your message. I see why a follow-up is needed:", "از پیام شما سپاسگزارم. روشن است چرا پیگیری لازم است:"),
        scene["fact"],
        tri("Uw voorstel lijkt mij verdedigbaar:", "Your proposal seems defensible:", "پیشنهاد شما به‌نظر قابل‌دفاع است:"),
        scene["action"],
        tri("Ik kan de voorbereiding opnemen, mits we eerst afspreken wie de uitkomst controleert. Kunt u dat bevestigen?", "I can take on preparation provided we first agree who verifies the outcome. Can you confirm that?", "می‌توانم آماده‌سازی را بر عهده بگیرم، به‌شرط آنکه ابتدا مسئول بررسی نتیجه را مشخص کنیم. می‌توانید تأیید کنید؟"))
    if stage == "c1":
        sample = join(
            tri("Dank voor uw bericht.", "Thank you for your message.", "از پیام شما سپاسگزارم."),
            scene["interpretation"], scene["fact"],
            tri("Daarom steun ik uw voorstel:", "I therefore support your proposal:", "پس از پیشنهاد شما حمایت می‌کنم:"), scene["action"],
            tri("Ik kan de voorbereiding opnemen, mits we eerst afspreken wie het resultaat controleert.", "I can prepare this provided we first agree who checks the result.", "می‌توانم آماده‌سازی را انجام دهم، به‌شرط توافق قبلی دربارهٔ مسئول بررسی نتیجه."))
    elif stage == "c2":
        sample = join(
            tri("Dank voor uw bericht.", "Thank you for your message.", "از پیام شما سپاسگزارم."), scene["fact"],
            tri("Uw voorstel bouwt voort op een les uit de eerdere situatie:", "Your proposal builds on a lesson from the earlier situation:", "پیشنهاد شما بر نکته‌ای از موقعیت قبلی تکیه دارد:"), scene["interpretation"],
            tri("Dat maakt deze stap verdedigbaar:", "That makes this step defensible:", "این، گام بعدی را قابل‌دفاع می‌کند:"),
            scene["action"],
            tri("De aanname dat die aanpak ook nu volstaat, moeten we nog toetsen. Welk gegeven ontbreekt volgens u daarvoor?", "We still need to test the assumption that this approach suffices now too. Which information do you think is missing for that?", "هنوز باید فرضِ کافی‌بودن همان رویکرد در شرایط فعلی را بسنجیم. به‌نظر شما برای این کار چه اطلاعاتی کم است؟"))
    common = [
        tri("U reageert op de concrete nieuwe vaststelling en het voorgestelde vervolg; u presenteert een voorstel niet als uitgevoerd feit.", "You respond to the specific new finding and proposed follow-up; you do not present a proposal as an accomplished fact.", "به یافتهٔ مشخص تازه و پیگیری پیشنهادی پاسخ می‌دهید؛ پیشنهاد را واقعیت اجراشده معرفی نمی‌کنید."),
        SPEAK_EXTRA[stage],
        tri("Uw antwoord is samenhangend, verstaanbaar en passend voor een professioneel overleg.", "Your answer is coherent, intelligible and appropriate for a professional discussion.", "پاسخ شما منسجم، قابل‌فهم و مناسب گفت‌وگوی حرفه‌ای است."),
    ]
    writing_prompt = tri(
        f"Situatie: {title['nl']}. Schrijf {genre['nl']} aan {recipient['nl']} naar aanleiding van de leestekst en het nieuwe spraakbericht. Uw doel is een bruikbaar vervolg afspreken bij deze ontwikkeling: {scene['fact']['nl']} Behandel het concrete voorstel: {scene['action']['nl']} Gebruik een passende aanspreking en een helder slot. Voeg geen niet-gegeven bedragen, data, bevoegdheden of wettelijke conclusies toe.",
        f"Situation: {title['en']}. Write {genre['en']} to {recipient['en']} in response to the reading and the new voice message. Your purpose is to agree a useful follow-up to this development: {scene['fact']['en']} Address the specific proposal: {scene['action']['en']} Use an appropriate opening and clear ending. Do not add unstated amounts, dates, powers or legal conclusions.",
        f"موقعیت: {title['fa']}. در پاسخ به متن خواندن و پیام صوتی تازه، {genre['fa']} برای {recipient['fa']} بنویسید. هدف توافق بر پیگیریِ کاربردیِ این تحول است: {scene['fact']['fa']} این پیشنهاد مشخص را بررسی کنید: {scene['action']['fa']} آغاز مناسب و پایان روشن داشته باشید. مبلغ، تاریخ، اختیار یا نتیجهٔ حقوقیِ ذکرنشده اضافه نکنید.")
    writing_prompt = join(writing_prompt, WRITE_EXTRA[stage])
    excerpt = join(
        tri("De oorspronkelijke situatie vraagt om deze nuance:", "The original situation calls for this qualification:", "موقعیت اولیه به این نکتهٔ ظریف نیاز دارد:"), scene["interpretation"],
        tri("De nieuwe informatie verandert de praktische afweging:", "The new information changes the practical appraisal:", "اطلاعات تازه سنجش عملی را تغییر می‌دهد:"), scene["fact"],
        tri("Daarom wil ik het volgende voorstel onder voorwaarden verder uitwerken:", "I therefore want to develop the following proposal subject to conditions:", "بنابراین می‌خواهم پیشنهاد بعدی را با شرایطی بیشتر بررسی کنم:"), scene["action"])
    bounds = {"c1": (160, 230), "pre-c2": (200, 290), "c2": (240, 340)}[stage]
    return {
        "speaking": {"prompt": speaking_prompt, "criteria": common, "sample": sample,
                     "sample_is_excerpt": False, "min_words": 35, "max_words": 100},
        "writing": {"prompt": writing_prompt,
                    "criteria": [WRITE_EXTRA[stage], common[0],
                                 tri("U schrijft voor de genoemde ontvanger in het gevraagde genre met een logische opbouw en passende formuleringen.", "You write for the named recipient in the requested genre with logical organisation and appropriate phrasing.", "برای گیرندهٔ نام‌برده و در قالب خواسته‌شده، با ساختار منطقی و عبارت مناسب می‌نویسید."),
                                 tri("U gebruikt bronfeiten nauwkeurig en onderscheidt voorstellen, aannames en bevestigde gebeurtenissen.", "You use source facts accurately and distinguish proposals, assumptions and confirmed events.", "واقعیت منبع را دقیق به کار می‌برید و پیشنهاد، فرض و رخداد تأییدشده را جدا می‌کنید.")],
                    "sample": excerpt, "sample_is_excerpt": True,
                    "min_words": bounds[0], "max_words": bounds[1]},
    }


def build(stage):
    source = json.loads((ROOT / "content/library/c1.json").read_text())
    target = json.loads((ROOT / f"content/library/{stage}.json").read_text())
    words = {word["id"]: word for word in source["vocabulary"]}
    topics = []
    for number, story in enumerate(source["stories"], 1):
        assert story["title"]["nl"] == EXPECTED_TITLES[number], "source narrative identity changed; review its follow-up"
        scene = SCENES[number]
        key = f"{stage}-t{number:03}"
        first = {lang: sentences(story["paragraphs"][0])[lang][0] for lang in LANGS}
        last = {lang: sentences(story["paragraphs"][-1])[lang][-1] for lang in LANGS}
        reading = join(*story["paragraphs"], separator="\n\n")
        reading_questions = [
            question(key + "-r1", tri("Welke mededeling beschrijft het vertrekpunt, vóór de beschreven bijsturing?", "Which statement describes the starting point, before the adjustment described?", "کدام گفته نقطهٔ شروع را پیش از تغییر توصیف‌شده بیان می‌کند؟"),
                     first, [last],
                     join(tri("De openingszin situeert het aanvankelijke probleem; de andere optie hoort bij de latere afloop.", "The opening sentence establishes the initial problem; the other option belongs to the later outcome.", "جملهٔ آغازین مشکل اولیه را مشخص می‌کند؛ گزینهٔ دیگر به نتیجهٔ بعدی مربوط است."), first), number),
            question(key + "-r2", tri("Welke gevolgtrekking is door de beschreven gebeurtenissen gerechtvaardigd?", "Which inference is justified by the events described?", "کدام استنباط با رخدادهای توصیف‌شده توجیه می‌شود؟"),
                     scene["interpretation"], [scene["alternative"]],
                     join(scene["interpretation"], tri("De slotinformatie ondersteunt die beperkte conclusie:", "The ending supports this limited conclusion:", "اطلاعات پایانی این نتیجهٔ محدود را پشتیبانی می‌کند:"), last), number + 1),
        ]
        intent = (number - 1) % 3
        listening = voice_message(first, scene, stage, intent)
        listening_questions = [
            question(key + "-l1", tri("Welke nieuwe ontwikkeling meldt de spreker na het vorige overleg?", "Which new development does the speaker report after the previous discussion?", "گوینده پس از گفت‌وگوی قبلی چه تحول تازه‌ای گزارش می‌کند؟"),
                     scene["fact"], [first],
                     join(tri("De spreker onderscheidt het vroegere vertrekpunt van deze nieuwe vaststelling:", "The speaker distinguishes the earlier starting point from this new finding:", "گوینده نقطهٔ شروع قبلی را از این یافتهٔ تازه جدا می‌کند:"), scene["fact"]), number + 1),
            question(key + "-l2", tri("Welke reactie vraagt de spreker nu, in de afsluitende vraag?", "Which response does the speaker request now, in the closing question?", "گوینده در پرسش آخر اکنون چه پاسخی می‌خواهد؟"),
                     INTENT[intent], [value for index, value in enumerate(INTENT) if index != intent],
                     join(tri("De laatste vraag vraagt specifiek om", "The final question specifically asks to", "پرسش آخر مشخصاً این را می‌خواهد:"), INTENT[intent]), number),
        ]
        topic = {"id": key, "title": story["title"], "category": story["topic"],
                 "objectives": [tri(
                     "Een eerdere oplossing beoordelen wanneer nieuwe informatie om een passend vervolg vraagt.",
                     "Assess an earlier solution when new information calls for a suitable follow-up.",
                     "راه‌حل قبلی را وقتی اطلاعات تازه پیگیریِ مناسبی می‌طلبد ارزیابی کنید."),
                     FOCUS[stage]], "language_focus": FOCUS[stage],
                 "vocabulary_ids": linked_words(story, words, target),
                 "reading": {"text": reading, "questions": reading_questions},
                 "listening": {"text": listening, "questions": listening_questions},
                 **productive(key, story, scene, (number - 1) // 10, stage)}
        topics.append(topic)
    result = {"schema_version": 1, "stage_id": stage, "review_status": "unreviewed", "topics": topics}
    assert len(topics) == 100
    assert len({topic["title"]["nl"] for topic in topics}) == 100
    for skill in ("reading", "listening", "speaking", "writing"):
        field = "text" if skill in ("reading", "listening") else "prompt"
        assert len({topic[skill][field]["nl"] for topic in topics}) == 100
    for topic in topics:
        n = len(re.findall(r"\b[\w'-]+\b", topic["speaking"]["sample"]["nl"]))
        assert 35 <= n <= 100, (topic["id"], n)
        assert topic["vocabulary_ids"]
        for skill in ("reading", "listening"):
            for q in topic[skill]["questions"]:
                assert all(len({o[lang] for o in q["options"]}) == len(q["options"]) for lang in LANGS)
    (ROOT / "content/practice").mkdir(exist_ok=True)
    (ROOT / f"content/practice/{stage}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{stage}: 100 topics, 400 skill activities; original drafts awaiting review")


if __name__ == "__main__":
    for stage in ("c1", "pre-c2", "c2"):
        build(stage)
