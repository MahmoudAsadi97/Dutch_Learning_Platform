"""Build 100 distinct, trilingual four-skill situations for each beginner stage.

Reading stories are intentionally revisited at increasing complexity. The newly
written listening messages introduce separate, explicit facts. Topic identities
repeat across stages for supported practice; they are not claimed to be 300
unrelated situations. No published content is labelled human reviewed.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from practice_beginner_source import QUESTIONS, ROWS

ROOT = Path(__file__).resolve().parents[2]
LANGS = ("nl", "en", "fa")
STAGES = ("pre-a1", "a1", "pre-a2")


def tr(value: str) -> dict[str, str]:
    values = [piece.strip() for piece in value.split("|")]
    assert len(values) == 3 and all(values), value
    return dict(zip(LANGS, values))


CATEGORIES = [
    tr("Thuis en wonen|Home and housing|خانه و زندگی"),
    tr("Eten en drinken|Food and drink|خوردن و نوشیدن"),
    tr("Winkelen en betalen|Shopping and paying|خرید و پرداخت"),
    tr("Onderweg en vervoer|Travel and transport|مسیر و حمل‌ونقل"),
    tr("School en taal|School and language|مدرسه و زبان"),
    tr("Tijd en afspraken|Time and arrangements|زمان و قرارها"),
    tr("Natuur en vrije tijd|Nature and leisure|طبیعت و اوقات فراغت"),
    tr("Mensen en gevoelens|People and feelings|آدم‌ها و احساسات"),
    tr("Hulp en dienstverlening|Help and services|کمک و خدمات"),
    tr("Werk en samenwerken|Work and cooperation|کار و همکاری"),
]
# One broad category per distinct situation, rather than 100 single-item filters.
CATEGORY_IDS = [
    0,7,8,7,0,0,1,1,1,1, 1,1,1,2,0,0,0,3,3,3,
    3,3,2,2,2,4,4,5,4,5, 5,5,5,6,6,6,6,4,0,8,
    8,6,6,6,7,5,0,0,9,9, 0,7,7,7,0,2,6,1,4,7,
    7,4,1,0,0,2,8,6,6,4, 0,0,0,4,1,1,4,1,9,3,
    0,6,2,8,3,1,0,7,6,7, 5,6,2,5,4,3,9,0,1,7,
]

STOP = {"de", "het", "een", "en", "of", "ik", "je", "jij", "u", "hij", "zij", "ze", "wij", "we", "is", "zijn", "was", "ben", "in", "op", "aan", "om", "er", "te", "dat", "dit", "die", "voor", "van", "naar", "met", "maar", "wat", "waar", "hoe", "welk", "welke", "volgens"}


def evidence(text: dict, answer: dict, question: dict, source_index: int | None = None) -> dict:
    """Quote one short source sentence, keeping source facts visible on retry."""
    nl_sentences = re.split(r"(?<=[.!?])\s+|\n\n", text["nl"])
    answer_terms = set(re.findall(r"\w+", answer["nl"].casefold())) - STOP
    query_terms = set(re.findall(r"\w+", question["nl"].casefold())) - STOP
    def score(sentence):
        words = set(re.findall(r"\w+", sentence.casefold()))
        return len(words & answer_terms) * 10 + len(words & query_terms)
    index = source_index if source_index is not None else max(range(len(nl_sentences)), key=lambda i: score(nl_sentences[i]))
    quoted = {}
    for lang in LANGS:
        sentences = re.split(r"(?<=[.!?؟])\s+|\n\n", text[lang])
        # Translators preserved sentence order; the exact sentence is supporting
        # evidence, not the full passage repeated as an explanation.
        quoted[lang] = sentences[min(index, len(sentences) - 1)]
    return {
        "nl": f"Let op dit detail: ‘{quoted['nl']}’ Dat ondersteunt de keuze ‘{answer['nl'].rstrip('.')}’.",
        "en": f"Notice this detail: ‘{quoted['en']}’ It supports the choice ‘{answer['en'].rstrip('.')}’.",
        "fa": f"به این نکته توجه کن: «{quoted['fa']}» این جمله از گزینهٔ «{answer['fa']}» پشتیبانی می‌کند.",
    }


def question(key: str, prompt: dict, correct: dict, wrong: dict, answer_index: int, explanation: dict):
    options = [correct, wrong] if answer_index == 0 else [wrong, correct]
    return {"id": key, "prompt": prompt, "options": options, "answer_index": answer_index,
            "explanation": explanation}


def lexical_question(key: str, story: dict, vocabulary: dict, index: int) -> dict:
    text = " ".join(paragraph["nl"] for paragraph in story["paragraphs"]).casefold()
    words = [vocabulary[word_id] for word_id in story["vocabulary_ids"]]
    def stem(term):
        return re.sub(r"^(?:de|het|een)\s+", "", term.casefold())
    candidates = [word for word in words if re.search(r"(?<!\w)" + re.escape(stem(word["term"])) + r"(?!\w)", text)]
    assert candidates, (story["id"], "no contextual vocabulary word")
    word = candidates[index % len(candidates)]
    foil = next(other for other in words if other["id"] != word["id"] and other["meaning"] != word["meaning"])
    prompt = {
        "nl": f"Wat betekent ‘{word['term']}’ in deze tekst?",
        "en": f"What does ‘{word['term']}’ mean in this text?",
        "fa": f"«{word['term']}» در این متن چه معنایی دارد؟",
    }
    explanation = {
        "nl": f"‘{word['term']}’ betekent hier: {word['meaning']['nl']}. De andere omschrijving hoort bij ‘{foil['term']}’.",
        "en": f"Here ‘{word['term']}’ means {word['meaning']['en']}. The other definition belongs to ‘{foil['term']}’.",
        "fa": f"اینجا «{word['term']}» یعنی {word['meaning']['fa']}. تعریف دیگر مربوط به «{foil['term']}» است.",
    }
    return question(key, prompt, word["meaning"], foil["meaning"], index % 2, explanation)


def build(stage_id: str):
    library = json.loads((ROOT / "content" / "library" / f"{stage_id}.json").read_text(encoding="utf-8"))
    vocabulary = {word["id"]: copy.deepcopy(word) for word in library["vocabulary"]}
    assert len(ROWS) == len(QUESTIONS) == len(CATEGORY_IDS) == len(library["stories"]) == 100
    index_stage = STAGES.index(stage_id)
    focus = [
        tr("Korte zinnen met ik en je; concrete woorden herkennen; een eenvoudige vraag stellen.|Short sentences with ik and je; recognise concrete words; ask a simple question.|جمله‌های کوتاه با ik و je؛ شناخت واژه‌های عینی؛ پرسیدن سؤال ساده."),
        tr("Vraagzinnen, beleefde verzoeken en plaats of tijd benoemen; zelfstandig een kort antwoord geven.|Questions, polite requests and naming a place or time; give a short answer independently.|جملهٔ پرسشی، درخواست مؤدبانه و نام بردن زمان یا مکان؛ پاسخ کوتاه مستقل."),
        tr("Een passend antwoord met alle gevraagde details; een reden geven als de situatie daarom vraagt; gegevens controleren.|A suitable reply with the requested details; give a reason where the situation calls for it; check information.|پاسخ مناسب با جزئیات خواسته‌شده؛ دلیل آوردن در صورت نیاز موقعیت؛ بررسی اطلاعات."),
    ][index_stage]
    topics = []
    for number, (story, source, qpair, cat) in enumerate(zip(library["stories"], ROWS, QUESTIONS, CATEGORY_IDS), 1):
        topic_id = f"{stage_id}-t{number:03d}"
        listening, fact1, fact2, goal, sample = source
        listening = tr(listening)
        goal, sample = tr(goal), tr(sample)
        reading = {lang: "\n\n".join(paragraph[lang] for paragraph in story["paragraphs"]) for lang in LANGS}
        if stage_id == "a1" and number == 48:
            explicit_problem = tr("De verwarming werkt niet.|The heating is not working.|گرمایش کار نمی‌کند.")
            reading = {lang: explicit_problem[lang] + " " + reading[lang] for lang in LANGS}
        read_q = copy.deepcopy(story["question"])
        read_q["id"] = topic_id + "-r1"
        read_q["explanation"] = evidence(reading, read_q["options"][read_q["answer_index"]], read_q["prompt"],
            {("pre-a1", 72): 0, ("pre-a1", 100): 2, ("a1", 100): 3, ("pre-a2", 75): 0,
             ("pre-a2", 98): 1, ("pre-a2", 55): 0, ("pre-a2", 58): 1}.get((stage_id, number)))
        listen_q = []
        for num, (fact, raw_prompt) in enumerate(zip((fact1, fact2), qpair), 1):
            _kind, good, bad = fact
            prompt, good, bad = tr(raw_prompt), tr(good), tr(bad)
            listen_q.append(question(topic_id + f"-l{num}", prompt, good, bad,
                                     (number + num) % 2, evidence(listening, good, prompt,
                                         {(58, 2): 2, (64, 1): 1}.get((number, num)))))
        if number == 24:
            listen_q[1]["explanation"] = tr("Je hoort twee mogelijkheden: muntgeld én een betaalkaart. Daarom is ‘alleen muntgeld’ niet juist.|You hear two possibilities: coins and a payment card. That is why ‘coins only’ is not correct.|دو امکان می‌شنوی: سکه و کارت بانکی. پس «فقط سکه» درست نیست.")
        original_goal = copy.deepcopy(goal)
        if index_stage == 2:
            checked = tr(fact1[1])
            check_target = tr(qpair[0])
            for lang in LANGS:
                checked[lang] = checked[lang].rstrip(".؟?")
            extra = {
                "nl": f"Controleer daarna ook dit detail: {check_target['nl']} Stel er een korte bevestigingsvraag over.",
                "en": f"Then check this detail too: {check_target['en']} Ask a short confirmation question about it.",
                "fa": f"سپس این نکته را هم بررسی کن: {check_target['fa']} دربارهٔ آن یک سؤال کوتاه برای تأیید بپرس.",
            }
            follow_up = {
                "nl": f"Heb ik dit goed begrepen: {checked['nl']}?",
                "en": f"Have I understood correctly: {checked['en']}?",
                "fa": f"درست فهمیدم: {checked['fa']}؟",
            }
            goal = {lang: goal[lang] + " " + extra[lang] for lang in LANGS}
            sample = {lang: sample[lang] + " " + follow_up[lang] for lang in LANGS}
        speak_prompt = {
            "nl": f"Spreek in deze situatie: {goal['nl']} Gebruik korte zinnen; lees het voorbeeld alleen als je hulp nodig hebt.",
            "en": f"Respond aloud in this situation: {goal['en']} Use short sentences; read the example only if you need help.",
            "fa": f"در این موقعیت شفاهی پاسخ بده: {goal['fa']} جمله‌های کوتاه بگو؛ فقط در صورت نیاز نمونه را بخوان.",
        }
        write_prompt = {
            "nl": f"Schrijf een kort bericht voor deze situatie: {goal['nl']} Gebruik je eigen woorden; het voorbeeld is hulp.",
            "en": f"Write a short message for this situation: {goal['en']} Use your own words; the example is support.",
            "fa": f"برای این موقعیت پیام کوتاهی بنویس: {goal['fa']} از کلمات خودت استفاده کن؛ نمونه فقط برای کمک است.",
        }
        if index_stage == 0:
            support = tr("Je mag eerst naar de woordkaartjes luisteren en de voorbeeldzinnen nazeggen.|You may first listen to the word cards and repeat the model sentences.|می‌توانی اول به کارت واژه‌ها گوش کنی و جمله‌های نمونه را تکرار کنی.")
        else:
            support = tr("Probeer eerst zelf; vergelijk daarna met het voorbeeld.|Try by yourself first; then compare with the example.|اول خودت تلاش کن؛ بعد با نمونه مقایسه کن.")
        for lang in LANGS:
            speak_prompt[lang] += " " + support[lang]
            write_prompt[lang] += " " + support[lang]
        wordcount = len(re.findall(r"\b[\w’'-]+\b", sample["nl"]))
        min_words = min((2, 4, 6)[index_stage], wordcount)
        common = [goal, tr("Behoud de juiste personen, voorwerpen, plaats en tijd uit de opdracht; verzin geen andere afspraak.|Keep the people, objects, place and time in the task correct; do not invent a different arrangement.|افراد، اشیا، مکان و زمان دستور را درست نگه دار؛ قرار دیگری نساز.")]
        speaking = {"prompt": speak_prompt, "criteria": [*common, tr("Spreek rustig en begrijpelijk. Een korte pauze of vraag om herhaling mag.|Speak calmly and intelligibly. A short pause or request for repetition is allowed.|آرام و قابل‌فهم صحبت کن. مکث کوتاه یا درخواست تکرار مجاز است.")], "sample": sample,
                    "sample_is_excerpt": False, "min_words": min_words, "max_words": (40, 60, 80)[index_stage]}
        writing = {"prompt": write_prompt, "criteria": [*common, tr("Maak leesbare zinnen; controleer spelling, hoofdletters en eindtekens.|Write readable sentences; check spelling, capital letters and final punctuation.|جمله‌های خوانا بنویس؛ املا، حروف بزرگ و نشانهٔ پایان جمله را بررسی کن.")], "sample": sample,
                   "sample_is_excerpt": False, "min_words": min_words, "max_words": (40, 60, 90)[index_stage]}
        topics.append({"id": topic_id, "title": story["title"], "category": CATEGORIES[cat],
                       "objectives": [original_goal], "language_focus": focus, "vocabulary_ids": story["vocabulary_ids"],
                       "reading": {"text": reading, "questions": [read_q, lexical_question(topic_id + "-r2", story, vocabulary, number)]},
                       "listening": {"text": listening, "questions": listen_q}, "speaking": speaking, "writing": writing})
    return {"schema_version": 1, "stage_id": stage_id, "review_status": "unreviewed", "topics": topics}


def main():
    output = ROOT / "content" / "practice"
    output.mkdir(exist_ok=True)
    for stage in STAGES:
        bank = build(stage)
        path = output / f"{stage}.json"
        path.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{stage}: {len(bank['topics'])} situations / 400 skill activities")


if __name__ == "__main__":
    main()
