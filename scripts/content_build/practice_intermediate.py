"""Build 100 original four-skill situations for A2, the A2–B1 bridge and B1.

The existing original anecdote collection supplies the reading anchors. The
companion source contains manually authored detail questions, new spoken messages
and responses. Adjacent stages deliberately revisit 100 situations with increasing
productive demands; no claim is made that there are 300 unrelated narratives.
All language and level calibration remain unreviewed.

Run from anywhere: python scripts/content_build/practice_intermediate.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANGS = ("nl", "en", "fa")
STAGES = ("a2", "pre-b1", "b1")


def tr(nl, en, fa):
    return dict(zip(LANGS, (nl, en, fa), strict=True))


def source_records():
    raw = Path(__file__).with_name("practice_intermediate_source.txt").read_text()
    records = []
    lines = [line for line in raw.splitlines() if line.strip()]
    assert len(lines) == 500, len(lines)
    for start in range(0, len(lines), 5):
        fields = []
        for line in lines[start:start+5]:
            parts = line.strip().split("|")
            assert len(parts) == 3 and all(parts), line
            fields.append(tr(*parts))
        assert len(fields) == 5, (len(records), len(fields))
        records.append(dict(zip(("question", "correct", "wrong", "voice", "reply"), fields, strict=True)))
    assert len(records) == 100, len(records)
    return records


# Explicit semantic alternatives for the four source families omitted from a
# neighbouring vocabulary bank. These preserve relevant links, not arbitrary IDs.
FOCUS = {
    "a2": [
        tr("Beleefde vragen met kunt u; ontbrekende informatie benoemen.", "Polite requests with kunt u; naming missing information.", "درخواست مؤدبانه با kunt u؛ مشخص کردن اطلاعات کم‌شده."),
        tr("Plaats en richting: in, achter, naast; een praktische reden met want.", "Place and direction: in, achter, naast; a practical reason with want.", "مکان و جهت: in، achter، naast؛ دلیل عملی با want."),
        tr("Een vraag verduidelijken; eerst en daarna voor de volgorde.", "Clarifying a request; eerst and daarna to sequence actions.", "روشن کردن درخواست؛ ترتیب با eerst و daarna."),
        tr("Een bericht verbeteren; dag, tijd en concrete vervolgafspraak.", "Correcting a message; day, time and a concrete next arrangement.", "اصلاح پیام؛ روز، ساعت و قرار بعدی مشخص."),
        tr("Gevoel of probleem beschrijven; een voorstel met kunnen.", "Describing a feeling or problem; a suggestion with kunnen.", "توصیف احساس یا مشکل؛ پیشنهاد با kunnen."),
        tr("Beurten en voorkeuren afspreken; meer, minder en eerst.", "Agreeing turns and preferences; more, less and first.", "توافق نوبت و ترجیح؛ بیشتر، کمتر و اول."),
        tr("Frequentie en planning: vaak, soms, zelden; een afspraak bevestigen.", "Frequency and planning: often, sometimes, rarely; confirming arrangements.", "بسامد و برنامه: اغلب، گاهی، به‌ندرت؛ تأیید قرار."),
        tr("Gericht informatie vragen; eigen notities beschrijven en vergelijken.", "Asking focused questions; describing and comparing one's notes.", "پرسش دقیق؛ توصیف و مقایسه یادداشت شخصی."),
        tr("Een gebeurtenis navertellen; eerst, dan en daarna.", "Retelling an event; first, then and afterwards.", "بازگویی رویداد؛ اول، سپس و بعد."),
        tr("Een fout rustig melden; juist, verkeerd en pas daarna.", "Calmly reporting an error; correct, incorrect and only afterwards.", "گفتن آرام اشتباه؛ درست، نادرست و فقط پس از آن."),
    ],
    "pre-b1": [
        tr("Een verzoek motiveren met omdat; de persoonsvorm achteraan in de bijzin.", "Giving a reason with omdat; placing the verb at the end of the subordinate clause.", "دلیل با omdat؛ فعل در پایان جمله وابسته."),
        tr("Een oplossing vergelijken; als voor een voorwaarde en daarom voor een gevolg.", "Comparing a solution; als for a condition and daarom for a consequence.", "مقایسه راه‌حل؛ شرط با als و پیامد با daarom."),
        tr("Controle vragen met of; de volgorde van een uitleg aangeven.", "Checking with of; indicating the order of instructions.", "بررسی با of؛ نشان دادن ترتیب توضیح."),
        tr("Een eerdere afspraak corrigeren; maar en daarom verbinden de stappen.", "Correcting an earlier arrangement; linking steps with maar and daarom.", "اصلاح قرار قبلی؛ اتصال مرحله‌ها با maar و daarom."),
        tr("Verschil tussen een vermoeden en een feit; ik dacht dat en het blijkt dat.", "Distinguishing guesses and facts; I thought that and it turns out that.", "تفاوت حدس و واقعیت؛ فکر می‌کردم که و معلوم شد که."),
        tr("Een haalbaar alternatief voorstellen en een voorkeur met omdat uitleggen.", "Proposing a feasible alternative and explaining a preference with omdat.", "پیشنهاد جایگزین عملی و توضیح ترجیح با omdat."),
        tr("Tijd en frequentie precies aangeven; voordat en nadat in een korte uitleg.", "Specifying time and frequency; voordat and nadat in a short explanation.", "بیان دقیق زمان و بسامد؛ voordat و nadat در توضیح کوتاه."),
        tr("Objectief melden wat je gezien hebt; het perfectum en een gerichte vervolgvraag.", "Reporting observations objectively; the perfect tense and a focused follow-up question.", "گزارش عینی مشاهده؛ زمان کامل و سؤال پیگیری دقیق."),
        tr("Twee situaties vergelijken; toen, nu en veranderd zijn.", "Comparing situations; then, now and having changed.", "مقایسه دو وضعیت؛ آن زمان، اکنون و تغییر کردن."),
        tr("Een keuze uitstellen tot informatie duidelijk is; eerst, pas als en daarom.", "Delaying a choice until information is clear; first, only if and therefore.", "عقب انداختن انتخاب تا روشن شدن اطلاعات؛ اول، فقط اگر و بنابراین."),
    ],
    "b1": [
        tr("Verzoek, reden en voorwaarde verbinden; beleefde indirecte vragen.", "Linking a request, reason and condition; polite indirect questions.", "پیوند درخواست، دلیل و شرط؛ سؤال غیرمستقیم مؤدبانه."),
        tr("Praktische mogelijkheden afwegen; hoewel, zodat en als correct gebruiken.", "Weighing practical options; using hoewel, zodat and als correctly.", "سنجش گزینه عملی؛ کاربرد درست hoewel، zodat و als."),
        tr("Een instructie in eigen woorden bevestigen; onzekerheid expliciet maken.", "Confirming instructions in one's own words; making uncertainty explicit.", "تأیید دستور با بیان خود؛ روشن کردن تردید."),
        tr("Informatie corrigeren zonder verwijt; verwijswoorden en duidelijke tijdsrelaties.", "Correcting information without blame; reference words and clear time relations.", "اصلاح اطلاعات بدون سرزنش؛ واژه ارجاع و رابطه زمانی روشن."),
        tr("Interpretatie van feiten onderscheiden; nuanceren met misschien en blijkbaar.", "Separating interpretation from facts; qualifying with perhaps and apparently.", "جداسازی تفسیر از واقعیت؛ بیان احتمال با شاید و ظاهراً."),
        tr("Een voorkeur onderbouwen en een alternatief vergelijken met daarentegen of terwijl.", "Supporting a preference and comparing an alternative using daarentegen or terwijl.", "دلیل ترجیح و مقایسه جایگزین با daarentegen یا terwijl."),
        tr("Vaste en veranderbare afspraken onderscheiden; concrete tijdsaanduidingen.", "Distinguishing fixed and changeable arrangements; concrete time expressions.", "جداسازی توافق ثابت و قابل‌تغییر؛ بیان زمان مشخص."),
        tr("Een zakelijke vraag onderbouwen met observaties; geen onbevestigde conclusie.", "Supporting a practical inquiry with observations; avoiding unconfirmed conclusions.", "دلیل آوردن برای درخواست با مشاهده؛ پرهیز از نتیجه تأییدنشده."),
        tr("Een ontwikkeling samenhangend navertellen en de betekenis voor een ander uitleggen.", "Retelling a development coherently and explaining its relevance to someone else.", "بازگویی منسجم تغییر و توضیح اهمیت آن برای دیگری."),
        tr("Informatie kritisch vergelijken; een gevolg met daardoor of daarom toelichten.", "Comparing information critically; explaining consequences with daardoor or daarom.", "مقایسه نقادانه اطلاعات؛ توضیح پیامد با daardoor یا daarom."),
    ],
}


def question(qid, prompt, correct, wrong, explanation, parity):
    options = [correct, wrong]
    index = parity % 2
    if index:
        options.reverse()
    assert correct != wrong
    return dict(id=qid, prompt=prompt, options=options, answer_index=index, explanation=explanation)


def label(prefix, value):
    return {lang: f"{prefix[lang]} {value[lang]}" for lang in LANGS}


def choose_links(anchor, base_vocab, target_vocab, index):
    by_term = {v["term"]: v for v in target_vocab}
    ids = [by_term[base_vocab[v]["term"]]["id"] for v in anchor["vocabulary_ids"] if base_vocab[v]["term"] in by_term]
    if ids:
        return ids[:12]
    # Four anchor families are deliberately absent from neighbouring banks.
    # Link named, semantically appropriate vocabulary instead of a random word.
    terms_by_index = {
        22: ("de knie", "hoofdpijn", "rugpijn"),
        23: ("hoofdpijn", "begrijpen", "uitleggen"),
        76: ("de afspraak", "de taakverdeling", "gastvrijheid"),
        77: ("een herinnering", "duidelijkheid", "samenvatten"),
        86: ("de voorbereiding", "de planning", "de hoeveelheid", "het ingrediënt"),
        87: ("de voorbereiding", "de oplossing", "het alternatief", "room"),
        88: ("de bestelling", "herhalen", "begrijpen", "duidelijkheid"),
        89: ("de bestelling", "controleren", "herhalen", "beleefdheid"),
    }
    ids = [by_term[t]["id"] for t in terms_by_index.get(index, ()) if t in by_term]
    if not ids:
        raise ValueError(f"No relevant vocabulary link: {anchor['title']['nl']}")
    return ids[:5]


def build():
    records = source_records()
    base = json.loads((ROOT / "content/library/a2.json").read_text())
    base_vocab = {v["id"]: v for v in base["vocabulary"]}
    for stage_index, stage in enumerate(STAGES):
        lib = json.loads((ROOT / f"content/library/{stage}.json").read_text())
        stage_stories = {s["title"]["nl"]: s for s in lib["stories"]}
        topics = []
        for i, (anchor, row) in enumerate(zip(base["stories"], records, strict=True)):
            tid = f"{stage}-t{i+1:03d}"
            story = stage_stories.get(anchor["title"]["nl"], anchor)
            # Use narratives, not existing instructional tails, as the source.
            reading = {l: "\n\n".join(p[l] for p in story["paragraphs"][:2]) for l in LANGS}
            insight = anchor["question"]["options"][anchor["question"]["answer_index"]]
            paired = base["stories"][i ^ 1]
            distractor = paired["question"]["options"][paired["question"]["answer_index"]]
            explanation = label(tr("Het beslissende detail is:", "The decisive detail is:", "جزئیات تعیین‌کننده:"), row["correct"])
            rquestions = [
                question(f"{tid}-r1", row["question"], row["correct"], row["wrong"], explanation, i),
                question(f"{tid}-r2", tr("Welke uitleg past bij de aanpak in deze tekst?", "Which explanation matches the approach in this text?", "کدام توضیح با روش این متن سازگار است؟"), insight, distractor, insight, i+1),
            ]
            # The recorded messages are independently authored first-person
            # requests, not a narration of the same reading passage.
            other_reply = records[i ^ 1]["reply"]
            lquestions = [
                question(f"{tid}-l1", row["question"], row["correct"], row["wrong"], explanation, i+1),
                question(f"{tid}-l2", tr("Welke reactie beantwoordt het verzoek in de boodschap?", "Which reply addresses the request in the message?", "کدام پاسخ به درخواست پیام جواب می‌دهد؟"), row["reply"], other_reply,
                         label(tr("Deze reactie sluit aan bij de gevraagde volgende stap:", "This reply matches the requested next step:", "این پاسخ با اقدام بعدی خواسته‌شده هماهنگ است:"), row["reply"]), i),
            ]
            title = anchor["title"]
            speaking_prefix = tr(
                "Je ontvangt de volgende boodschap. Antwoord als de ontvanger in een korte gesproken reactie. Reageer op het verzoek; spreek maximaal 60 seconden.",
                "You receive the following message. Reply as its recipient in a short spoken response. Address the request; speak for at most 60 seconds.",
                "این پیام را دریافت می‌کنی. در نقش گیرنده پاسخ گفتاری کوتاهی بده. به درخواست جواب بده؛ حداکثر ۶۰ ثانیه صحبت کن.")
            writing_prefix = tr(
                "Je ontvangt de volgende boodschap. Schrijf als de ontvanger een duidelijk antwoord met een passende begroeting en afsluiting. Beantwoord het verzoek en maak je volgende stap concreet.",
                "You receive the following message. Write a clear reply as its recipient with a suitable greeting and closing. Address the request and make your next action concrete.",
                "این پیام را دریافت می‌کنی. در نقش گیرنده پاسخ روشن با سلام و پایان مناسب بنویس. به درخواست جواب بده و اقدام بعدی را مشخص کن.")
            stage_demand = [
                tr("Gebruik korte zinnen; geef aan wat je kunt doen of welke informatie nog nodig is.", "Use short sentences; say what you can do or what information is still needed.", "جمله کوتاه به کار ببر؛ بگو چه می‌توانی بکنی یا چه اطلاعاتی کم است."),
                tr("Verbind je antwoord met een reden en een concrete vervolgstap. Vraag om verduidelijking als iets ontbreekt.", "Link your answer to a reason and a concrete next step. Ask for clarification if information is missing.", "پاسخ را به دلیل و اقدام بعدی مشخص وصل کن. اگر اطلاعات کم است، توضیح بخواه."),
                tr("Maak onderscheid tussen wat vaststaat en wat nog gecontroleerd moet worden. Licht je voorstel toe met een reden, voorwaarde of relevant alternatief.", "Distinguish confirmed information from what still needs checking. Explain your proposal with a reason, condition or relevant alternative.", "اطلاعات قطعی را از موارد نیازمند بررسی جدا کن. پیشنهاد را با دلیل، شرط یا جایگزین مرتبط توضیح بده."),
            ][stage_index]
            criteria = [
                tr("Beantwoord het concrete verzoek van de afzender, vanuit de rol van de ontvanger.", "Answer the sender's concrete request from the recipient's role.", "از نقش گیرنده به درخواست مشخص فرستنده پاسخ بده."),
                label(tr("Houd rekening met dit belangrijke detail:", "Respect this key detail:", "این نکته مهم را در نظر بگیر:"), row["correct"]),
                stage_demand,
                tr("Verzin geen bevestigde datum, prijs, oorzaak of beslissing die niet in de situatie staat; vraag ernaar of formuleer een voorstel.", "Do not invent a confirmed date, price, cause or decision absent from the situation; ask about it or frame a proposal.", "تاریخ، قیمت، علت یا تصمیم تأییدشده‌ای که در موقعیت نیست نساز؛ بپرس یا پیشنهاد بده."),
            ]
            spoken_prompt = {l: f"{speaking_prefix[l]} {stage_demand[l]}\n\n{row['voice'][l]}" for l in LANGS}
            written_prompt = {l: f"{writing_prefix[l]} {stage_demand[l]}\n\n{row['voice'][l]}" for l in LANGS}
            # Samples are response openings, not a claim to satisfy the full
            # longer writing target or every advanced response criterion.
            speaking = dict(prompt=spoken_prompt,criteria=criteria,sample=row["reply"],sample_is_excerpt=False,min_words=12,max_words=(75,90,100)[stage_index])
            writing = dict(prompt=written_prompt,criteria=criteria,sample=row["reply"],sample_is_excerpt=True,min_words=(45,60,80)[stage_index],max_words=(90,130,180)[stage_index])
            topics.append(dict(
                id=tid,title=title,category=anchor["topic"],
                objectives=[
                    label(tr("Begrijp de situatie:", "Understand the situation:", "موقعیت را بفهم:"), title),
                    tr("Haal het beslissende detail uit een tekst en een gesproken boodschap.", "Find the decisive detail in a text and a spoken message.", "جزئیات تعیین‌کننده را از متن و پیام شنیداری پیدا کن."),
                    stage_demand,
                ],
                language_focus=FOCUS[stage][i//10],
                vocabulary_ids=choose_links(anchor,base_vocab,lib["vocabulary"],i),
                reading=dict(text=reading,questions=rquestions),
                listening=dict(text=row["voice"],questions=lquestions),
                speaking=speaking,writing=writing,
            ))
        bank=dict(schema_version=1,stage_id=stage,review_status="unreviewed",topics=topics)
        path=ROOT / f"content/practice/{stage}.json"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(bank,ensure_ascii=False,indent=2)+"\n")
        print(f"{stage}: {len(topics)} topics; 100 practices per skill; unreviewed")


if __name__ == "__main__":
    build()
