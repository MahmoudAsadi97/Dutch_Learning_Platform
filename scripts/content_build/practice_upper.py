"""Build 100 four-skill situations for each upper transition stage.

The existing original story is the reading document. An independently authored
follow-up decision and rationale form a new voice message. Speaking and writing
then require a reply with an audience, purpose and evidence, rather than mere
topic naming. Adjacent stages deliberately revisit situations at increasing
productive demands; this is not a claim of 300 unrelated underlying plots.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from practice_upper_source import FOLLOWUPS, READING_PROMPTS, SPOKEN_OUTCOMES
from upper_build import FIXES, blocks
from upper_development import DEVELOPMENTS

ROOT = Path(__file__).resolve().parents[2]
LANGS = ("nl", "en", "fa")
STAGES = ("pre-b2", "b2", "pre-c1")


def tri(nl, en, fa):
    return dict(zip(LANGS, (nl, en, fa)))


def combine(*parts, separator=" "):
    return {lang: separator.join(part[lang] for part in parts) for lang in LANGS}


def parse_rows(text, width):
    rows = {}
    for raw in text.strip().splitlines():
        columns = raw.split("|")
        assert len(columns) == width + 1, raw
        key = int(columns[0])
        assert key not in rows
        values = [tri(*column.split("~")) for column in columns[1:]]
        assert all(all(value.values()) for value in values)
        rows[key] = values
    assert set(rows) == set(range(1, 101))
    return rows


def question(key, prompt, answer, distractors, position, explanation):
    options = list(distractors)
    position %= len(options) + 1
    options.insert(position, answer)
    return {"id": key, "prompt": prompt, "options": options,
            "answer_index": position, "explanation": explanation}


AUDIENCES = {
    "Werk en samenwerking": tri("de teamcoördinator", "the team coordinator", "هماهنگ‌کنندهٔ گروه"),
    "Leren en onderzoek": tri("de studiebegeleider", "the study supervisor", "راهنمای آموزشی"),
    "Buurt en samenleving": tri("de buurtcoördinator", "the neighbourhood coordinator", "هماهنگ‌کنندهٔ محله"),
    "Wonen en ruimte": tri("de verantwoordelijke voor het woonoverleg", "the housing discussion coordinator", "مسئول گفت‌وگوی مسکن"),
    "Media en informatie": tri("de verantwoordelijke redacteur", "the responsible editor", "سردبیر مسئول"),
    "Milieu en klimaat": tri("de coördinator van de milieuwerkgroep", "the environmental working-group coordinator", "هماهنگ‌کنندهٔ کارگروه محیط زیست"),
    "Cultuur en ontmoeting": tri("de organisator van de activiteit", "the activity organiser", "برگزارکنندهٔ فعالیت"),
    "Keuzes en verantwoordelijkheid": tri("de verantwoordelijke van de vereniging", "the association coordinator", "مسئول انجمن"),
    "Gezondheid en welzijn": tri("de contactpersoon die de ondersteuning coördineert", "the contact person coordinating support", "فرد پاسخ‌گوی هماهنگ‌کنندهٔ پشتیبانی"),
    "Geld en openbare diensten": tri("de verantwoordelijke voor het dossier", "the person responsible for the case", "مسئول پرونده"),
}

# Audience overrides keep administrative messages addressed to the actual actor,
# rather than forcing a broad category contact onto every specific situation.
RECIPIENTS = r'''
2|de personeelsdienst~the human resources department~بخش منابع انسانی
4|de klant die het oude bestand kreeg~the client who received the old file~مشتری دریافت‌کنندهٔ پروندهٔ قدیمی
6|de onderzoeksbegeleider~the research supervisor~راهنمای پژوهش
8|de docent die de tekst beoordeelde~the lecturer who assessed the text~مدرسی که متن را ارزیابی کرد
9|de verantwoordelijke van de leeszaal~the reading-room manager~مسئول سالن مطالعه
10|de spreker van de lezing~the lecturer who gave the talk~سخنران نشست
12|de dienst die de verkeersbevraging organiseert~the service organising the traffic survey~ادارهٔ برگزارکنندهٔ نظرسنجی ترافیک
13|de beheerder van het buurtbord~the neighbourhood noticeboard manager~مسئول تابلوی اعلانات محله
14|de zaalbeheerder~the venue manager~مسئول سالن
15|de medewerker van het buurthuis~the community-centre staff member~کارمند مرکز محله
16|de verhuurder~the landlord~صاحب‌خانه
18|de dienst die de verwarmingskosten berekent~the service calculating the heating charges~بخش محاسبهٔ هزینهٔ گرمایش
19|de bouwfirma~the construction company~شرکت ساختمانی
20|de huisgenoten~the housemates~هم‌خانه‌ها
24|de blogger~the blogger~وبلاگ‌نویس
25|een familielid dat ook het verdachte bericht kreeg~a relative who also received the suspicious message~عضو خانواده که او هم پیام مشکوک گرفته است
27|de schooldirectie~the school management~مدیریت مدرسه
28|de winkelier~the shopkeeper~مغازه‌دار
29|het bestuur van de vereniging~the association's committee~هیئت‌مدیرهٔ انجمن
30|de milieudienst~the environmental service~ادارهٔ محیط زیست
31|de organisator van het buurtpodium~the neighbourhood-stage organiser~برگزارکنندهٔ اجرای محله
32|de verantwoordelijke van de ontvangst~the reception supervisor~مسئول پذیرش
33|de museumcoördinator~the museum coordinator~هماهنگ‌کنندهٔ موزه
36|het gevondenvoorwerpenloket~the lost-property desk~بخش اشیای گمشده
37|de andere auteurs van het groepsverslag~the other authors of the group report~نویسندگان دیگر گزارش گروهی
38|de coördinator van een oefenbijeenkomst over respectvolle hulp~the coordinator of a practice session on respectful assistance~هماهنگ‌کنندهٔ نشست تمرینی کمک محترمانه
39|het bestuur van de sportclub~the sports club committee~هیئت‌مدیرهٔ باشگاه
40|de leverancier~the supplier~تأمین‌کننده
41|de apotheker~the pharmacist~داروساز
42|de leidinggevende~the manager~مدیر
43|de bibliotheekmedewerker~the library staff member~کارمند کتابخانه
44|de lokale ondersteuningsdienst~the local support service~خدمات پشتیبانی محلی
45|de wandelbegeleider~the walking-group guide~راهنمای گروه پیاده‌روی
46|de medewerker aan de zorgbalie~the staff member at the care reception desk~کارمند پذیرش مرکز مراقبت
47|de maker van de affiche~the poster designer~طراح پوستر
48|de medewerker van de praktijk~the practice receptionist~کارمند مطب
49|de lesgever~the instructor~مربی
50|de teamleider~the team leader~سرپرست گروه
51|de klantendienst~customer service~خدمات مشتری
52|de winkelverantwoordelijke~the shop manager~مسئول فروشگاه
53|de organisatoren van het buurtfeest~the neighbourhood-party organisers~برگزارکنندگان جشن محله
54|de cursusadministratie~the course administration~بخش اداری دوره
55|de dossierbeheerder~the case officer~مسئول پرونده
56|de fietshersteller~the bicycle repairer~تعمیرکار دوچرخه
57|de klantendienst van de vervoerder~the transport operator's customer service~خدمات مشتری شرکت حمل‌ونقل
58|de gemeentelijke dienst~the municipal service~خدمات شهرداری
59|de beheerder van de deelkast~the shared-tool cupboard manager~مسئول کمد ابزار مشترک
60|de leerlingenraad~the student council~شورای دانش‌آموزی
61|de ontwikkelaar van de boodschappenapp~the shopping-list app developer~توسعه‌دهندهٔ برنامهٔ فهرست خرید
62|de personeelsverantwoordelijke~the human resources manager~مسئول منابع انسانی
63|de kaartendienst~the mapping service~خدمات نقشه
64|de accountbeheerder~the account administrator~مسئول حساب‌ها
65|de organisator van de online inschrijving~the organiser of online enrolment~برگزارکنندهٔ ثبت‌نام اینترنتی
66|de webontwikkelaar~the web developer~توسعه‌دهندهٔ وب
67|de tuinvereniging~the gardening association~انجمن باغبانی
68|de nieuwe softwarevrijwilliger~the new software volunteer~داوطلب تازهٔ نرم‌افزار
69|de teamcoördinator~the team coordinator~هماهنگ‌کنندهٔ گروه
70|een familielid dat het fotoarchief mee beheert~a relative helping manage the photo archive~عضو خانواده که در مدیریت بایگانی عکس کمک می‌کند
71|de vervoersmaatschappij~the transport company~شرکت حمل‌ونقل
72|de reizigersdienst~the passenger service~خدمات مسافران
73|de stedelijke mobiliteitsdienst~the city mobility service~خدمات حمل‌ونقل شهری
74|de leverancier van de bestelwagen~the van's delivery company~شرکت تحویل‌دهنده با وانت
75|de handelaar in de speelstraat~the shopkeeper in the play street~مغازه‌دار خیابان بازی
76|de auteur van het verslag~the report's author~نویسندهٔ گزارش
77|de docent van de afstandsles~the remote-class lecturer~مدرس کلاس از راه دور
78|de leerkracht van de schooltuin~the school-garden teacher~معلم باغ مدرسه
79|de werkgroep rond droogte~the drought working group~کارگروه خشکی
80|de winkelverantwoordelijke~the shop manager~مسئول فروشگاه
81|de projectleider~the project manager~مدیر پروژه
82|de vertegenwoordigers van beide ploegen~the representatives of both teams~نمایندگان دو گروه
83|de manager~the manager~مدیر
84|de ploegbaas~the team supervisor~سرپرست گروه
85|de thuiswerkcoördinator~the remote-work coordinator~هماهنگ‌کنندهٔ دورکاری
86|de onderzoeksbegeleider~the research supervisor~راهنمای پژوهش
87|de redactie van de buurtkrant~the neighbourhood newspaper editors~تحریریهٔ روزنامهٔ محله
88|de debatbegeleider~the debate supervisor~راهنمای مناظره
89|de taaldocent~the language teacher~مدرس زبان
90|de presentatiebegeleider~the presentation coach~راهنمای ارائه
91|de voorzitter van het overleg~the meeting chair~رئیس جلسه
92|de juryvoorzitter~the jury chair~رئیس هیئت داوری
93|de collega die de grap maakte~the colleague who made the joke~همکاری که شوخی کرد
94|de vrijwilligerscoördinator~the volunteer coordinator~هماهنگ‌کنندهٔ داوطلبان
95|de archiefwerkgroep~the archive working group~کارگروه بایگانی
96|de stedelijke communicatiedienst~the city's communications service~بخش ارتباطات شهرداری
97|de maker van de grafiek~the chart's creator~سازندهٔ نمودار
98|de moderator van het debat~the debate moderator~مدیر مناظره
99|de redactie die het interview publiceert~the editors publishing the interview~تحریریهٔ منتشرکنندهٔ مصاحبه
100|de journalist die over woningprijzen schrijft~the journalist covering housing prices~روزنامه‌نگار حوزهٔ قیمت مسکن
'''


def productive(stage, scene, follow, audience, spoken_outcome):
    title = scene["title"]
    facts = [row["sentence"] for row in scene["rows"]]
    plan, reason = follow
    quote = {lang: f'“{plan[lang]}”' for lang in LANGS}
    context_speaking = tri(
        f'Neem de rol van de spreker uit het vervolgbericht over “{title["nl"]}” op. Geef een nieuwe collega die er niet bij was een korte briefing. U bespreekt wat u bij een volgende gelijkaardige situatie zou doen. Uw voorstel luidt: {quote["nl"]}',
        f'Take the role of the speaker in the follow-up message about “{title["en"]}”. Brief a new colleague who was not there. You are discussing what you would do in a future similar situation. Your proposal is: {quote["en"]}',
        f'نقش گویندهٔ پیام پیگیری دربارهٔ «{title["fa"]}» را بگیرید. برای همکار تازه‌ای که در جریان نبوده توضیح کوتاه بدهید. دربارهٔ کاری صحبت می‌کنید که در موقعیت مشابه بعدی انجام خواهید داد. پیشنهاد شما این است: {quote["fa"]}',
    )
    context_writing = tri(
        f'Schrijf een e-mail aan {audience["nl"]} over “{title["nl"]}”. Gebruik het leesverslag en het afzonderlijke vervolgbericht als bronnen. Uw doel is een afspraak over deze aanpak voor een volgende gelijkaardige situatie: {quote["nl"]}',
        f'Write an email to {audience["en"]} about “{title["en"]}” using the written account and separate follow-up message as sources. Your aim is agreement on this approach for a future similar situation: {quote["en"]}',
        f'دربارهٔ «{title["fa"]}» به {audience["fa"]} ایمیل بنویسید. از گزارش خواندنی و پیام پیگیری جداگانه به‌عنوان منبع استفاده کنید. هدف، توافق دربارهٔ این روش برای موقعیت مشابه بعدی است: {quote["fa"]}',
    )
    if stage == "pre-b2":
        speaking_instruction = tri(
            'Leg het probleem kort uit, steun het voorstel met een reden uit het bericht en vraag of de ontvanger akkoord gaat. Gebruik uw eigen woorden; spreek maximaal één minuut.',
            'Briefly explain the problem, support the proposal with a reason from the message, and ask whether the recipient agrees. Use your own words; speak for at most one minute.',
            'مشکل را کوتاه توضیح دهید، با دلیلی از پیام از پیشنهاد پشتیبانی کنید و موافقت گیرنده را بپرسید. با کلمات خودتان حداکثر یک دقیقه صحبت کنید.',
        )
        writing_instruction = tri(
            'Maak duidelijk wat al gebeurd is en wat u nu vraagt. Geef een reden en sluit af met een concrete vraag om bevestiging. Verzin geen nieuwe afspraak als voldongen feit.',
            'Make clear what has already happened and what you are requesting now. Give a reason and end with a specific request for confirmation. Do not present a new arrangement as an established fact.',
            'روشن کنید چه اتفاقی افتاده و اکنون چه می‌خواهید. دلیل بیاورید و با درخواست مشخص برای تأیید پایان دهید. توافق تازه‌ای را به‌صورت واقعیت قطعی نسازید.',
        )
        ending = tri('Kunt u bevestigen of u met deze vervolgstap akkoord gaat?', 'Could you confirm whether you agree with this next step?', 'می‌توانید تأیید کنید که با این گام بعدی موافقید؟')
        speak_bounds, write_bounds = (30, 100), (50, 180)
        third_criterion = tri('Geef een relevante reden en vraag om bevestiging.', 'Give a relevant reason and ask for confirmation.', 'دلیلی مرتبط بیاورید و تأیید بخواهید.')
    elif stage == "b2":
        speaking_instruction = tri(
            'Vergelijk de eerdere oplossing met deze vervolgstap. Verdedig waarom de extra stap nuttig is, noem één mogelijke zorg als mogelijkheid en stel een controlevraag. Spreek maximaal één minuut.',
            'Compare the earlier solution with this next step. Defend why the extra step is useful, identify one possible concern as a possibility, and ask a checking question. Speak for at most one minute.',
            'راه‌حل قبلی را با این گام بعدی مقایسه کنید. توضیح دهید چرا گام اضافه مفید است، یک نگرانی احتمالی را به‌صورت احتمال بیان کنید و پرسش بررسی مطرح کنید. حداکثر یک دقیقه صحبت کنید.',
        )
        writing_instruction = tri(
            'Vergelijk wat de eerdere oplossing al bereikt heeft met wat het nieuwe voorstel nog toevoegt. Bespreek een mogelijk bezwaar, reageer erop en vraag om een haalbare volgende afspraak. Scheid feiten van uw voorstellen.',
            'Compare what the earlier solution has achieved with what the new proposal adds. Discuss a possible objection, respond to it and ask for a feasible next arrangement. Separate facts from your proposals.',
            'دستاورد راه‌حل قبلی را با ارزش افزودهٔ پیشنهاد تازه مقایسه کنید. یک ایراد احتمالی را بررسی و پاسخ دهید و توافق بعدی عملی بخواهید. واقعیت‌ها را از پیشنهادهای خود جدا کنید.',
        )
        ending = tri('De extra controle kost mogelijk tijd. Kunnen we samen bepalen hoe we die haalbaar organiseren?', 'The extra check may take time. Can we decide together how to organise it practically?', 'بررسی اضافه ممکن است زمان ببرد. می‌توانیم با هم تعیین کنیم چگونه آن را عملی سازمان دهیم؟')
        speak_bounds, write_bounds = (40, 100), (100, 220)
        third_criterion = tri('Vergelijk de oplossingen en bespreek een mogelijk bezwaar zonder het als feit te presenteren.', 'Compare the solutions and discuss a possible objection without presenting it as fact.', 'راه‌حل‌ها را مقایسه کنید و ایراد احتمالی را بدون قطعی جلوه دادن بررسی کنید.')
    else:
        speaking_instruction = tri(
            'Geef een afgewogen reactie: verbind de eerdere uitkomst met het voorstel, benoem het belang voor de betrokkenen en formuleer een voorwaarde voor uw steun. Maak onzekerheid expliciet en vraag naar bezwaren. Maximaal één minuut.',
            'Give a balanced response: connect the earlier outcome to the proposal, explain its significance for those involved and state a condition for your support. Make uncertainty explicit and ask about objections. At most one minute.',
            'پاسخی سنجیده بدهید: نتیجهٔ قبلی را به پیشنهاد وصل کنید، اهمیت آن برای افراد درگیر را توضیح دهید و شرط حمایت خود را بیان کنید. عدم قطعیت را روشن کنید و دربارهٔ ایرادها بپرسید. حداکثر یک دقیقه.',
        )
        writing_instruction = tri(
            'Schrijf een genuanceerd voorstel met een korte aanleiding, een afweging van belangen en een beargumenteerde vervolgstap. Bespreek een mogelijk tegenargument en een voorwaarde waaronder u het plan zou herzien. Vraag om concrete terugkoppeling en maak duidelijk wat nog niet vaststaat.',
            'Write a nuanced proposal with brief background, a weighing of interests and a justified next step. Discuss a possible counterargument and a condition under which you would revise the plan. Ask for specific feedback and make clear what is not yet established.',
            'پیشنهادی سنجیده با زمینهٔ کوتاه، سنجش منافع و گام بعدی مستدل بنویسید. استدلال مخالف احتمالی و شرطی را بررسی کنید که در آن برنامه را بازنگری می‌کنید. بازخورد مشخص بخواهید و نکات هنوز نامطمئن را روشن کنید.',
        )
        ending = tri('Ik steun dit, mits de extra controle haalbaar blijft. Anders moeten we de aanpak herzien. Welke bezwaren ziet u?', 'I support this provided the extra check remains feasible. Otherwise we must revise the approach. What objections do you see?', 'از این کار حمایت می‌کنم به شرط عملی ماندن بررسی اضافه. در غیر این صورت باید روش را بازنگری کنیم. چه ایرادهایی می‌بینید؟')
        speak_bounds, write_bounds = (45, 100), (180, 300)
        third_criterion = tri('Weeg belangen af, benoem onzekerheid en maak een voorwaarde voor herziening expliciet.', 'Weigh interests, identify uncertainty and state a condition for revision explicitly.', 'منافع را بسنجید، عدم قطعیت را مشخص کنید و شرط بازنگری را روشن بیان کنید.')

    first_criterion = tri(
        f'Beschrijf de concrete aanleiding rond “{scene["rows"][0]["term"]}” zonder de bronfeiten te wijzigen.',
        f'Describe the specific background involving “{scene["rows"][0]["term"]}” without changing the source facts.',
        f'زمینهٔ مشخص مربوط به «{scene["rows"][0]["term"]}» را بدون تغییر واقعیت‌های منبع شرح دهید.',
    )
    second_criterion = tri('Maak de voorgestelde vervolgactie en het doel ervan duidelijk.', 'Make the proposed follow-up action and its purpose clear.', 'اقدام پیگیری پیشنهادی و هدف آن را روشن کنید.')
    register = tri('Spreek de ontvanger respectvol aan en verbind uw zinnen logisch.', 'Address the recipient respectfully and connect your sentences logically.', 'گیرنده را محترمانه خطاب کنید و جمله‌ها را منطقی به هم پیوند دهید.')
    # The complete spoken example is deliberately bounded to the recording limit.
    future = tri('Voor een volgende gelijkaardige situatie heb ik dit voorstel.', 'For a future similar situation, I have this proposal.', 'برای موقعیت مشابه بعدی این پیشنهاد را دارم.')
    speak_sample = combine(facts[0], spoken_outcome, future, plan, reason, ending)
    if len(re.findall(r"\b[\w'-]+\b", speak_sample["nl"])) > 100:
        speak_sample = combine(spoken_outcome, future, plan, reason, ending)
    if len(re.findall(r"\b[\w'-]+\b", speak_sample["nl"])) > 100:
        raise ValueError(f"spoken sample too long: {stage} {title['nl']}")

    opening = tri(
        f'Beste,\n\nIk schrijf u over “{title["nl"]}”.',
        f'Hello,\n\nI am writing about “{title["en"]}”.',
        f'با سلام،\n\nدربارهٔ «{title["fa"]}» برایتان می‌نویسم.',
    )
    background = combine(*facts) if stage != "pre-b2" else combine(facts[0], facts[1], spoken_outcome)
    quoted_proposal = tri(
        f'In het vervolgbericht staat voor een volgende gelijkaardige situatie dit voorstel: {quote["nl"]}',
        f'For a future similar situation, the follow-up message makes this proposal: {quote["en"]}',
        f'پیام پیگیری برای موقعیت مشابه بعدی این پیشنهاد را دارد: {quote["fa"]}',
    )
    body = combine(background, combine(quoted_proposal, reason), separator="\n\n")
    if stage == "b2":
        comparison = tri(
            'De eerdere oplossing was dus nuttig, maar deze vervolgstap maakt de opvolging duidelijker. Een mogelijk bezwaar is de extra tijd. Ik stel voor de uitvoering daarom eerst kort samen te plannen, zodat de controle geen onnodige last wordt.',
            'The earlier solution was useful, but this next step makes follow-up clearer. A possible objection is the extra time. I therefore suggest briefly planning its implementation together first so that the check does not become an unnecessary burden.',
            'راه‌حل قبلی مفید بود، اما این گام بعدی پیگیری را روشن‌تر می‌کند. ایراد احتمالی زمان اضافه است. بنابراین پیشنهاد می‌کنم ابتدا اجرای آن را کوتاه با هم برنامه‌ریزی کنیم تا بررسی به بار غیرضروری تبدیل نشود.',
        )
        body = combine(body, comparison, separator="\n\n")
    written_ending = ending if stage != 'b2' else tri(
        'Kunt u aangeven of u met deze aanpak akkoord gaat en welke aanpassing nodig is?',
        'Could you indicate whether you agree with this approach and which adjustment is needed?',
        'می‌توانید بگویید با این روش موافقید و چه اصلاحی لازم است؟',
    )
    closing = combine(written_ending, tri('Met vriendelijke groeten', 'Kind regards', 'با احترام'), separator="\n\n")
    write_sample = combine(opening, body, closing, separator="\n\n")
    excerpt = stage == "pre-c1"
    if excerpt:
        # This is explicitly a partial opening and argument, not a completed essay.
        write_sample = combine(opening, background, combine(quoted_proposal, reason), separator="\n\n")
    return (
        {"prompt": combine(context_speaking, speaking_instruction),
         "criteria": [first_criterion, second_criterion, third_criterion, register],
         "sample": speak_sample, "sample_is_excerpt": False,
         "min_words": speak_bounds[0], "max_words": speak_bounds[1]},
        {"prompt": combine(context_writing, writing_instruction),
         "criteria": [first_criterion, second_criterion, third_criterion,
                      tri('Gebruik een passende aanhef, duidelijke alinea’s en een concrete slotvraag.', 'Use an appropriate greeting, clear paragraphs and a specific closing question.', 'آغاز مناسب، بندهای روشن و پرسش پایانی مشخص به کار ببرید.')],
         "sample": write_sample, "sample_is_excerpt": excerpt,
         "min_words": write_bounds[0], "max_words": write_bounds[1]},
    )


def build():
    scenes = blocks()
    for scene in scenes:
        for row in scene["rows"]:
            if row["term"] in FIXES:
                fixed = FIXES[row["term"]]
                row.update(term=fixed[0], meaning=tri(*fixed[1:4]), sentence=tri(*fixed[4:7]))
    follows = parse_rows(FOLLOWUPS, 2)
    reading_prompts = parse_rows(READING_PROMPTS, 1)
    spoken_outcomes = {}
    for line in SPOKEN_OUTCOMES.strip().splitlines():
        number, values = line.split("|")
        spoken_outcomes[int(number)] = tri(*values.split("~"))
    developments = {}
    for line in DEVELOPMENTS.strip().splitlines():
        if not line.strip():
            continue
        fields = line.split("~")
        developments[int(fields[0])] = (tri(*fields[1:4]), tri(*fields[4:7]))
    recipients = {}
    for line in RECIPIENTS.strip().splitlines():
        number, values = line.split("|")
        recipients[int(number)] = tri(*values.split("~"))

    for stage in STAGES:
        library = json.loads((ROOT / "content" / "library" / f"{stage}.json").read_text())
        topics = []
        for number, (scene, story) in enumerate(zip(scenes, library["stories"]), 1):
            assert scene["title"] == story["title"]
            key = f"{stage}-t{number:03d}"
            facts = [row["sentence"] for row in scene["rows"]]
            plan, reason = follows[number]
            # The voice message adds independently authored information. It is
            # not a prefixed or synthetic reading of the written story.
            introduction = tri('Dag, ik heb een voorstel op basis van onze eerdere ervaring.', 'Hello, I have a proposal based on our earlier experience.', 'سلام، بر پایهٔ تجربهٔ قبلی‌مان پیشنهادی دارم.')
            future = tri('Voor een volgende gelijkaardige situatie stel ik deze aanpak voor.', 'For a future similar situation, I suggest this approach.', 'برای موقعیت مشابه بعدی این روش را پیشنهاد می‌کنم.')
            outcome = spoken_outcomes.get(number, facts[4])
            if stage == 'pre-b2':
                prior = combine(facts[0], outcome)
            elif stage == 'b2':
                prior = combine(facts[0], outcome, developments[number][0])
            else:
                prior = combine(facts[0], outcome, developments[number][1])
            listening = combine(introduction, prior, future, plan, reason)
            audience = recipients.get(number, AUDIENCES[scene["topic"]["nl"]])
            speaking, writing = productive(stage, scene, follows[number], audience, outcome)

            # Alternatives are taken from other original situations in the SAME
            # broad domain, prioritising shared vocabulary over arbitrary rows.
            candidates = [i for i, other in enumerate(scenes, 1)
                          if i != number and other["topic"]["nl"] == scene["topic"]["nl"]]
            current_terms = set(re.findall(r"[a-zà-ÿ]{5,}", combine(prior, plan, reason)["nl"].lower()))
            candidates.sort(key=lambda i: (-len(current_terms & set(re.findall(
                r"[a-zà-ÿ]{5,}", combine(*follows[i])["nl"].lower()))), abs(i - number), i))
            alternatives = candidates[:2]
            assert len(alternatives) == 2
            detail_explanation = tri(
                f'Dit detail staat aan het begin van het verslag: {facts[1]["nl"]} De andere antwoorden beschrijven latere ontwikkelingen.',
                f'This detail appears near the start of the account: {facts[1]["en"]} The other answers describe later developments.',
                f'این جزئیات در آغاز گزارش آمده است: {facts[1]["fa"]} پاسخ‌های دیگر تحولات بعدی را توصیف می‌کنند.',
            )
            reading_questions = [question(
                key + "-r1", reading_prompts[number][0], facts[1], [facts[3], facts[4]], number,
                detail_explanation,
            ), {**story["question"], "id": key + "-r2"}]
            listening_questions = [question(
                key + "-l1",
                tri('Welke vervolgstap stelt de spreker in dit bericht voor?', 'Which next step does the speaker propose in this message?', 'گوینده در این پیام چه گام بعدی پیشنهاد می‌کند؟'),
                plan, [follows[i][0] for i in alternatives], number + 1,
                tri(f'De spreker formuleert deze nieuwe actie: {plan["nl"]} Het gaat om een voorstel, niet om een al uitgevoerde afspraak.',
                    f'The speaker proposes this new action: {plan["en"]} It is a proposal, not an already completed arrangement.',
                    f'گوینده این اقدام تازه را مطرح می‌کند: {plan["fa"]} این پیشنهاد است، نه توافقی که قبلاً اجرا شده باشد.'),
            ), question(
                key + "-l2",
                tri('Welke reden geeft de spreker uitdrukkelijk voor die vervolgstap?', 'Which reason does the speaker explicitly give for that next step?', 'گوینده صریحاً چه دلیلی برای آن گام بعدی می‌آورد؟'),
                reason, [follows[i][1] for i in reversed(alternatives)], number + 2,
                tri(f'De reden volgt op het voorstel: {reason["nl"]} Ze verklaart welk probleem de extra stap moet aanpakken.',
                    f'The rationale follows the proposal: {reason["en"]} It explains the problem the extra step is meant to address.',
                    f'دلیل پس از پیشنهاد آمده است: {reason["fa"]} توضیح می‌دهد گام اضافه قرار است کدام مشکل را برطرف کند.'),
            )]
            focus = {
                'pre-b2': tri('Een concrete aanleiding, een voorstel en een reden verbinden; beleefde bevestigingsvragen met “kunt u”.', 'Connect a specific background, a proposal and a reason; polite confirmation questions with “kunt u”.', 'پیوند زمینهٔ مشخص، پیشنهاد و دلیل؛ پرسش تأیید مؤدبانه با «kunt u».'),
                'b2': tri('Oplossingen vergelijken met “maar” en “terwijl”; een bezwaar als mogelijkheid formuleren met “mogelijk” en “kan”.', 'Compare solutions with “maar” and “terwijl”; phrase an objection as a possibility using “mogelijk” and “kan”.', 'مقایسهٔ راه‌حل‌ها با «maar» و «terwijl»؛ بیان ایراد به‌صورت احتمال با «mogelijk» و «kan».'),
                'pre-c1': tri('Belangen en onzekerheid nuanceren; steun aan een voorwaarde verbinden met “mits”; feiten van voorstellen onderscheiden.', 'Qualify interests and uncertainty; make support conditional with “mits”; distinguish facts from proposals.', 'بیان سنجیدهٔ منافع و عدم قطعیت؛ شرط‌گذاری برای حمایت با «mits»؛ تمایز واقعیت از پیشنهاد.'),
            }[stage]
            topics.append({
                'id': key, 'title': story['title'], 'category': scene['topic'],
                'objectives': [
                    tri(f'De aanleiding en de uitkomst in “{story["title"]["nl"]}” begrijpen.', f'Understand the background and outcome in “{story["title"]["en"]}”.', f'زمینه و نتیجهٔ «{story["title"]["fa"]}» را بفهمید.'),
                    tri('Een gesproken vervolgvoorstel en de bijbehorende reden herkennen.', 'Recognise a spoken follow-up proposal and its rationale.', 'پیشنهاد پیگیری شفاهی و دلیل آن را تشخیص دهید.'),
                    tri(f'Mondeling en schriftelijk een passende vervolgstap met {audience["nl"]} afspreken.', f'Agree on an appropriate next step orally and in writing with {audience["en"]}.', f'شفاهی و کتبی با {audience["fa"]} دربارهٔ گام بعدی مناسب توافق کنید.'),
                ],
                'language_focus': focus, 'vocabulary_ids': story['vocabulary_ids'],
                'reading': {'text': combine(*story['paragraphs'], separator='\n\n'), 'questions': reading_questions},
                'listening': {'text': listening, 'questions': listening_questions},
                'speaking': speaking, 'writing': writing,
            })
        bank = {'schema_version': 1, 'stage_id': stage, 'review_status': 'unreviewed', 'topics': topics}
        path = ROOT / 'content' / 'practice' / f'{stage}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        from dlp.domains.curriculum.service import word_count
        from dlp.domains.curriculum.topics import TopicBank
        TopicBank.model_validate(bank)
        print(stage, len(topics), 'topics;', len(topics) * 4, 'skill activities;',
              'spoken sample range', min(word_count(t['speaking']['sample']['nl']) for t in topics),
              max(word_count(t['speaking']['sample']['nl']) for t in topics),
              'answer positions', dict(Counter(q['answer_index'] for t in topics for skill in ('reading', 'listening') for q in t[skill]['questions'])))


if __name__ == '__main__':
    build()
