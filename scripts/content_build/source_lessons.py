"""Author original, trilingual practice from checked concepts, never from raw OCR passages.

Run this after editing the compact lesson contracts. It writes additive stage packs;
the original banks, their IDs, progress and final-test content remain intact.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def tr(value: str) -> dict[str, str]:
    parts = value.split("|")
    if len(parts) != 3 or not all(x.strip() for x in parts):
        raise ValueError("Each authored field needs Dutch, English and Persian")
    return dict(zip(("nl", "en", "fa"), (x.strip() for x in parts), strict=True))


UNITS = [
    {
        "stage": "pre-a1", "grammar": "alphabet-spelling", "concept": "alphabet-spelling",
        "sources": [("source-01", 1), ("source-03", 1), ("source-08", 20)],
        "title": "Een naam op de kaart|A name on the card|یک نام روی کارت",
        "focus": "Een naam herkennen en spellen.|Recognising and spelling a name.|تشخیص و هجی کردن نام.",
        "paragraphs": [
            "Ik heet Noor. Ik spel mijn naam: N–O–O–R. Vier letters.|My name is Noor. I spell my name: N–O–O–R. Four letters.|نام من نور است. نامم را هجی می‌کنم: N–O–O–R. چهار حرف.",
            "Ik woon in Gent. Dit is mijn kaart. Op de kaart staat Noor.|I live in Ghent. This is my card. The card says Noor.|در خنت زندگی می‌کنم. این کارت من است. روی کارت نوشته شده نور."
        ],
        "listening": "Dag, ik ben Noor. Mijn naam heeft vier letters: N, O, O, R. Ik woon in Gent.|Hello, I am Noor. My name has four letters: N, O, O, R. I live in Ghent.|سلام، من نور هستم. نام من چهار حرف دارد: N، O، O، R. در خنت زندگی می‌کنم.",
        "reading_q": [
            ("Wat is de naam?|What is the name?|نام چیست؟", "Noor|Noor|نور", "Sam|Sam|سام", "Op de kaart staat Noor.|The card says Noor.|روی کارت نوشته شده نور."),
            ("Waar woont Noor?|Where does Noor live?|نور کجا زندگی می‌کند؟", "Gent|Ghent|خنت", "Brugge|Bruges|بروژ", "Noor zegt: Ik woon in Gent.|Noor says: I live in Ghent.|نور می‌گوید: در خنت زندگی می‌کنم.")
        ],
        "listening_q": [
            ("Hoeveel letters hoor je?|How many letters do you hear?|چند حرف می‌شنوید؟", "Vier|Four|چهار", "Drie|Three|سه", "Je hoort N, O, O en R.|You hear N, O, O and R.|حروف N، O، O و R را می‌شنوید."),
            ("Welke stad hoor je?|Which city do you hear?|نام کدام شهر را می‌شنوید؟", "Gent|Ghent|خنت", "Kortrijk|Kortrijk|کورتریک", "Noor noemt Gent.|Noor names Ghent.|نور نام خنت را می‌گوید.")
        ],
        "speaking": "Zeg je naam en spel die langzaam. De voorbeeldnaam is Noor.|Say your name and spell it slowly. The sample name is Noor.|نامتان را بگویید و آهسته هجی کنید. نام نمونه نور است.",
        "spoken_sample": "Ik heet Noor. N, O, O, R.|My name is Noor. N, O, O, R.|نام من نور است. N، O، O، R.",
        "writing": "Schrijf met het voorbeeld een naam en een woonplaats. Je mag je eigen gegevens gebruiken.|Using the example, write a name and a city. You may use your own details.|با کمک نمونه یک نام و شهر محل زندگی بنویسید. می‌توانید اطلاعات خودتان را بنویسید.",
        "written_sample": "Ik heet Noor. Ik woon in Gent.|My name is Noor. I live in Ghent.|نام من نور است. در خنت زندگی می‌کنم.",
        "bounds": (3, 20),
        "criteria": ["Noem een naam.|Give a name.|یک نام بگویید.", "Geef de gevraagde informatie duidelijk.|Give the requested information clearly.|اطلاعات خواسته‌شده را روشن بیان کنید."],
        "examples": ["Noor: N–O–O–R.|Noor: N–O–O–R.|نور: N–O–O–R.", "Sam: S–A–M.|Sam: S–A–M.|سام: S–A–M.", "Mijn naam is Lina: L–I–N–A.|My name is Lina: L–I–N–A.|نام من لینا است: L–I–N–A."],
        "grammar_q": ("Welke reeks spelt Lina?|Which sequence spells Lina?|کدام ترتیب Lina را هجی می‌کند؟", "L–I–N–A|L–I–N–A|L–I–N–A", "L–N–A|L–N–A|L–N–A", "Lina heeft vier letters, met een i na de l.|Lina has four letters, with i after l.|Lina چهار حرف دارد؛ i پس از l می‌آید."),
        "words": [
            ("de naam", "Hoe iemand heet.|What someone is called.|نام یک فرد.", "Mijn naam is Noor.|My name is Noor.|نام من نور است."),
            ("de letter", "Een teken in een woord.|A character in a word.|یک حرف در واژه.", "N is een letter.|N is a letter.|N یک حرف است."),
            ("spellen", "De letters één voor één noemen.|Name the letters one by one.|گفتن حروف به‌ترتیب.", "Ik kan Noor spellen: N–O–O–R.|I can spell Noor: N–O–O–R.|می‌توانم Noor را هجی کنم: N–O–O–R.")
        ]
    },
    {
        "stage": "a1", "grammar": "clock-time", "concept": "clock-time",
        "sources": [("source-07", 1), ("source-03", 48)],
        "title": "Woensdag om twee uur|Wednesday at two|چهارشنبه ساعت دو",
        "focus": "Een dag en een kloktijd begrijpen en bevestigen.|Understanding and confirming a day and time.|فهمیدن و تأیید روز و ساعت.",
        "paragraphs": [
            "Leila leest een kaart. Haar afspraak is op woensdag om twee uur in de namiddag. De afspraak is in de bibliotheek.|Leila reads a card. Her appointment is on Wednesday at two in the afternoon. The appointment is in the library.|لیلا یک کارت را می‌خواند. قرارش چهارشنبه ساعت دو بعدازظهر است. قرار در کتابخانه است.",
            "Leila doet de kaart in haar tas. Op woensdag gaat ze naar de bibliotheek. Ze toont haar kaart aan de medewerker.|Leila puts the card in her bag. On Wednesday she goes to the library. She shows her card to the staff member.|لیلا کارت را در کیفش می‌گذارد. چهارشنبه به کتابخانه می‌رود. کارت را به کارمند نشان می‌دهد."
        ],
        "listening": "Dag Leila, met de bibliotheek. Uw afspraak is woensdag om twee uur in de namiddag. Neem uw kaart mee, alstublieft. Tot woensdag!|Hello Leila, this is the library. Your appointment is Wednesday at two in the afternoon. Please bring your card. See you Wednesday!|سلام لیلا، از کتابخانه تماس می‌گیریم. قرارتان چهارشنبه ساعت دو بعدازظهر است. لطفاً کارتتان را بیاورید. تا چهارشنبه!",
        "reading_q": [
            ("Op welke dag is de afspraak?|On which day is the appointment?|قرار چه روزی است؟", "Woensdag|Wednesday|چهارشنبه", "Dinsdag|Tuesday|سه‌شنبه", "De kaart noemt woensdag.|The card names Wednesday.|روی کارت چهارشنبه نوشته شده است."),
            ("Waar is de afspraak?|Where is the appointment?|قرار کجاست؟", "In de bibliotheek.|In the library.|در کتابخانه.", "In het station.|In the station.|در ایستگاه.", "Leila gaat naar de bibliotheek.|Leila goes to the library.|لیلا به کتابخانه می‌رود.")
        ],
        "listening_q": [
            ("Hoe laat is de afspraak?|What time is the appointment?|قرار چه ساعتی است؟", "Om 14.00 uur.|At 14:00.|ساعت ۱۴.", "Om 10.00 uur.|At 10:00.|ساعت ۱۰.", "Twee uur in de namiddag is 14.00 uur.|Two in the afternoon is 14:00.|دو بعدازظهر همان ساعت ۱۴ است."),
            ("Wat moet Leila meenemen?|What should Leila bring?|لیلا چه چیزی باید بیاورد؟", "Haar kaart.|Her card.|کارتش را.", "Een foto.|A photo.|یک عکس.", "De medewerker vraagt om de kaart.|The staff member asks for the card.|کارمند کارت را درخواست می‌کند.")
        ],
        "speaking": "Bevestig Leila's afspraak: noem de dag, de tijd en de plaats.|Confirm Leila's appointment: give the day, time and place.|قرار لیلا را تأیید کنید: روز، ساعت و مکان را بگویید.",
        "spoken_sample": "Mijn afspraak is woensdag om twee uur in de namiddag, in de bibliotheek.|My appointment is Wednesday at two in the afternoon, in the library.|قرار من چهارشنبه ساعت دو بعدازظهر در کتابخانه است.",
        "writing": "Schrijf een kort bericht om de afspraak te bevestigen. Vermeld ook de kaart.|Write a short message confirming the appointment. Also mention the card.|پیامی کوتاه برای تأیید قرار بنویسید. کارت را هم ذکر کنید.",
        "written_sample": "Dag, mijn afspraak is woensdag om twee uur in de namiddag. Ik breng mijn kaart mee. Tot woensdag!|Hello, my appointment is Wednesday at two in the afternoon. I will bring my card. See you Wednesday!|سلام، قرار من چهارشنبه ساعت دو بعدازظهر است. کارتم را می‌آورم. تا چهارشنبه!",
        "bounds": (8, 45),
        "criteria": ["Vermeld woensdag en 14.00 uur.|Give Wednesday and 14:00.|چهارشنبه و ساعت ۱۴ را ذکر کنید.", "Bevestig de gevraagde details duidelijk.|Confirm the requested details clearly.|جزئیات خواسته‌شده را روشن تأیید کنید."],
        "examples": ["De les begint om negen uur.|The lesson starts at nine.|درس ساعت نه شروع می‌شود.", "De winkel sluit om half zes.|The shop closes at half past five.|فروشگاه ساعت پنج‌ونیم بسته می‌شود.", "We spreken af om kwart over drie.|We meet at a quarter past three.|ساعت سه‌وربع قرار می‌گذاریم."],
        "grammar_q": ("In de namiddag: hoe laat is half zes?|In the afternoon: what time is half zes?|در بعدازظهر، half zes چه ساعتی است؟", "17.30 uur.|17:30.|ساعت ۱۷:۳۰.", "18.30 uur.|18:30.|ساعت ۱۸:۳۰.", "Half zes is een halfuur vóór zes, hier in de namiddag.|Half zes is half an hour before six, here in the afternoon.|Half zes نیم ساعت پیش از شش است؛ اینجا منظور بعدازظهر است."),
        "words": [
            ("de afspraak", "Een afgesproken ontmoeting.|An arranged meeting.|یک دیدار هماهنگ‌شده.", "Mijn afspraak is woensdag.|My appointment is on Wednesday.|قرار من چهارشنبه است."),
            ("de namiddag", "Het deel van de dag na de middag.|The part of the day after noon.|بخش روز پس از ظهر.", "Ik kom om twee uur in de namiddag.|I will come at two in the afternoon.|ساعت دو بعدازظهر می‌آیم."),
            ("de kaart", "Een kaartje met informatie of gegevens.|A card with information or details.|کارتی با اطلاعات.", "Ik neem mijn kaart mee.|I will bring my card.|کارتم را می‌آورم.")
        ]
    },
    {
        "stage": "pre-a2", "grammar": "negation", "concept": "negation",
        "sources": [("source-07", 4), ("source-06", 1), ("source-08", 30)],
        "title": "Geen koffie, wel water|No coffee, but water|قهوه نه، آب بله",
        "focus": "Met geen en niet een bestelling verduidelijken.|Clarifying an order with geen and niet.|روشن کردن سفارش با geen و niet.",
        "paragraphs": [
            "Mira zit in een café. Ze bestelt brood en een glas water. De medewerker vraagt: Wilt u ook koffie? Mira antwoordt: Nee, ik drink geen koffie.|Mira is in a café. She orders bread and a glass of water. The staff member asks: Would you also like coffee? Mira replies: No, I do not drink coffee.|میرا در یک کافه است. نان و یک لیوان آب سفارش می‌دهد. کارمند می‌پرسد: قهوه هم می‌خواهید؟ میرا پاسخ می‌دهد: نه، من قهوه نمی‌نوشم.",
            "De medewerker zet toch een kop koffie op tafel. Mira zegt rustig: Dit is niet mijn bestelling. Ik wil water, geen koffie. De medewerker brengt een glas water.|The staff member nevertheless puts a cup of coffee on the table. Mira calmly says: This is not my order. I want water, not coffee. The staff member brings a glass of water.|بااین‌حال کارمند یک فنجان قهوه روی میز می‌گذارد. میرا آرام می‌گوید: این سفارش من نیست. آب می‌خواهم، نه قهوه. کارمند یک لیوان آب می‌آورد."
        ],
        "listening": "Dag Mira, hier is uw brood. U wilt geen koffie, maar water. Hier is uw glas water. Wilt u nog iets eten?|Hello Mira, here is your bread. You want water, not coffee. Here is your glass of water. Would you like anything else to eat?|سلام میرا، این نان شماست. آب می‌خواهید، نه قهوه. این لیوان آب شماست. چیز دیگری برای خوردن می‌خواهید؟",
        "reading_q": [
            ("Wat wil Mira drinken?|What does Mira want to drink?|میرا چه می‌خواهد بنوشد؟", "Water.|Water.|آب.", "Koffie.|Coffee.|قهوه.", "Mira vraagt om water.|Mira asks for water.|میرا آب می‌خواهد."),
            ("Wat gaat eerst mis?|What goes wrong first?|ابتدا چه اشتباهی رخ می‌دهد؟", "Mira krijgt koffie.|Mira receives coffee.|برای میرا قهوه می‌آورند.", "Mira krijgt geen brood.|Mira receives no bread.|برای میرا نان نمی‌آورند.", "Er komt een kop koffie op tafel.|A cup of coffee is placed on the table.|یک فنجان قهوه روی میز قرار می‌گیرد.")
        ],
        "listening_q": [
            ("Welke drank brengt de medewerker nu?|Which drink does the staff member bring now?|کارمند اکنون چه نوشیدنی می‌آورد؟", "Een glas water.|A glass of water.|یک لیوان آب.", "Een kop koffie.|A cup of coffee.|یک فنجان قهوه.", "De medewerker zegt: Hier is uw glas water.|The staff member says: Here is your glass of water.|کارمند می‌گوید: این لیوان آب شماست."),
            ("Welke vraag stelt de medewerker op het einde?|What does the staff member ask at the end?|کارمند در پایان چه می‌پرسد؟", "Of Mira nog iets wil eten.|Whether Mira wants anything else to eat.|آیا میرا چیز دیگری برای خوردن می‌خواهد.", "Of Mira koffie wil meenemen.|Whether Mira wants takeaway coffee.|آیا میرا قهوه برای بردن می‌خواهد.", "De laatste vraag gaat over iets eten.|The final question is about something to eat.|پرسش آخر درباره خوردن است.")
        ],
        "speaking": "Je krijgt koffie, maar je wilt water. Leg het probleem beleefd uit en vraag om water.|You receive coffee but ordered water. Explain politely and ask for water.|قهوه گرفته‌اید اما آب سفارش داده بودید. مؤدبانه مشکل را توضیح دهید و آب بخواهید.",
        "spoken_sample": "Sorry, dit is niet mijn bestelling. Ik drink geen koffie. Mag ik een glas water, alstublieft?|Sorry, this is not my order. I do not drink coffee. May I have a glass of water, please?|ببخشید، این سفارش من نیست. قهوه نمی‌نوشم. می‌توانم لطفاً یک لیوان آب داشته باشم؟",
        "writing": "Stuur een kort bericht met je bestelling: brood en water, maar geen koffie.|Send a short message with your order: bread and water, but no coffee.|سفارش خود را در پیامی کوتاه بنویسید: نان و آب، اما قهوه نه.",
        "written_sample": "Hallo, ik wil graag brood en een glas water bestellen. Ik drink geen koffie. Dank u wel!|Hello, I would like to order bread and a glass of water. I do not drink coffee. Thank you!|سلام، می‌خواهم نان و یک لیوان آب سفارش بدهم. قهوه نمی‌نوشم. متشکرم!",
        "bounds": (10, 65),
        "criteria": ["Maak duidelijk wat je wel en niet wilt.|Make clear what you do and do not want.|روشن کنید چه چیزی می‌خواهید و چه چیزی نمی‌خواهید.", "Formuleer een beleefd verzoek.|Make a polite request.|درخواستی مؤدبانه بیان کنید."],
        "examples": ["Ik drink geen koffie.|I do not drink coffee.|قهوه نمی‌نوشم.", "Dit is niet mijn glas.|This is not my glass.|این لیوان من نیست.", "Ik wil water, maar geen koffie.|I want water, but no coffee.|آب می‌خواهم، اما قهوه نه."],
        "grammar_q": ("Vul aan: Ik drink … koffie.|Complete: Ik drink … koffie.|کامل کنید: Ik drink … koffie.", "geen|no|هیچ", "niet|not|نه", "Geen staat hier vóór het zelfstandig naamwoord koffie.|Geen comes before the noun koffie here.|اینجا geen پیش از اسم koffie می‌آید."),
        "words": [
            ("het brood", "Voedsel van meel dat wordt gebakken.|Food made from flour and baked.|خوراکی پخته‌شده از آرد؛ نان.", "Ik bestel brood.|I order bread.|نان سفارش می‌دهم."),
            ("het water", "Een drank zonder kleur.|A colourless drink.|یک نوشیدنی بی‌رنگ؛ آب.", "Ik wil een glas water.|I want a glass of water.|یک لیوان آب می‌خواهم."),
            ("de koffie", "Een drank gemaakt van koffiebonen.|A drink made from coffee beans.|نوشیدنی تهیه‌شده از دانه‌های قهوه.", "Ik drink geen koffie.|I do not drink coffee.|قهوه نمی‌نوشم.")
        ]
    },
    {
        "stage": "a2", "grammar": "perfect", "concept": "perfect-tense",
        "sources": [("source-08", 90), ("source-04", 102)],
        "title": "Een tas na de markt|A bag after the market|کیف پس از خرید از بازار",
        "focus": "Met hebben en zijn vertellen wat er gebeurd is.|Explaining what happened with hebben and zijn.|بیان اتفاق‌ها با hebben و zijn.",
        "paragraphs": [
            "Sam is gisteren naar de markt gegaan. Hij heeft brood gekocht en heeft daarna een winkel bezocht. Toen hij thuiskwam, was zijn blauwe tas er niet. Hij heeft de winkel gebeld.|Sam went to the market yesterday. He bought bread and then visited a shop. When he arrived home, his blue bag was missing. He called the shop.|سام دیروز به بازار رفت. نان خرید و سپس به یک فروشگاه رفت. وقتی به خانه رسید، کیف آبی‌اش همراهش نبود. به فروشگاه تلفن کرد.",
            "De winkelier heeft de tas gevonden en bewaart die achter de toonbank. Sam kan de tas vandaag na vier uur ophalen. Hij heeft het adres genoteerd en gaat vanmiddag terug.|The shopkeeper found the bag and is keeping it behind the counter. Sam can collect it today after four. He noted the address and is returning this afternoon.|فروشنده کیف را پیدا کرده و آن را پشت پیشخوان نگه داشته است. سام می‌تواند امروز پس از ساعت چهار کیف را بگیرد. نشانی را یادداشت کرده و امروز بعدازظهر برمی‌گردد."
        ],
        "listening": "Dag Sam, uw blauwe tas ligt bij ons achter de toonbank. U kunt die vandaag vanaf vier uur ophalen. De winkel sluit om zes uur. Breng iets mee waarmee u kunt tonen dat de tas van u is.|Hello Sam, your blue bag is behind our counter. You can collect it today from four. The shop closes at six. Bring something that can show the bag is yours.|سلام سام، کیف آبی شما پشت پیشخوان ماست. امروز از ساعت چهار می‌توانید آن را بگیرید. فروشگاه ساعت شش بسته می‌شود. چیزی بیاورید که نشان دهد کیف متعلق به شماست.",
        "reading_q": [
            ("Welke kleur heeft Sams tas?|What colour is Sam's bag?|کیف سام چه رنگی است؟", "Blauw.|Blue.|آبی.", "Groen.|Green.|سبز.", "Sam mist zijn blauwe tas.|Sam is missing his blue bag.|سام کیف آبی‌اش را گم کرده است."),
            ("Wat heeft Sam gedaan toen hij thuis was?|What did Sam do when he was home?|سام وقتی به خانه رسید چه کرد؟", "Hij heeft de winkel gebeld.|He called the shop.|به فروشگاه تلفن کرد.", "Hij heeft de tas gekocht.|He bought the bag.|کیف را خرید.", "Na het ontdekken van het probleem belt hij de winkel.|After discovering the problem, he calls the shop.|پس از فهمیدن مشکل، به فروشگاه تلفن می‌کند.")
        ],
        "listening_q": [
            ("Wanneer kan Sam de tas ophalen?|When can Sam collect the bag?|سام چه زمانی می‌تواند کیف را بگیرد؟", "Tussen 16.00 en 18.00 uur.|Between 16:00 and 18:00.|بین ساعت ۱۶ و ۱۸.", "Na 18.00 uur.|After 18:00.|پس از ساعت ۱۸.", "Ophalen kan vanaf vier; de winkel sluit om zes.|Collection starts at four; the shop closes at six.|از ساعت چهار می‌توان کیف را گرفت؛ فروشگاه ساعت شش بسته می‌شود."),
            ("Waar ligt de tas?|Where is the bag?|کیف کجاست؟", "Achter de toonbank.|Behind the counter.|پشت پیشخوان.", "Bij Sam thuis.|At Sam's home.|در خانه سام.", "De winkelier noemt de toonbank.|The shopkeeper mentions the counter.|فروشنده پیشخوان را ذکر می‌کند.")
        ],
        "speaking": "Speel Sam. Vertel kort wat gisteren is gebeurd en zeg dat je om vijf uur komt. Vraag hoe je kunt aantonen dat de tas van jou is.|Play Sam. Briefly explain what happened yesterday and say you will come at five. Ask how you can show the bag is yours.|نقش سام را بازی کنید. اتفاق دیروز را کوتاه توضیح دهید و بگویید ساعت پنج می‌آیید. بپرسید چطور می‌توانید نشان دهید کیف مال شماست.",
        "spoken_sample": "Gisteren ben ik naar de markt gegaan en heb ik uw winkel bezocht. Thuis heb ik mijn tas niet gevonden. Ik kom vandaag om vijf uur. Hoe kan ik tonen dat de tas van mij is?|Yesterday I went to the market and visited your shop. At home I could not find my bag. I will come today at five. How can I show the bag is mine?|دیروز به بازار رفتم و به فروشگاه شما آمدم. در خانه کیفم را پیدا نکردم. امروز ساعت پنج می‌آیم. چطور نشان بدهم کیف مال من است؟",
        "writing": "Bevestig in een kort bericht dat je de blauwe tas vandaag om vijf uur ophaalt. Noem wat gisteren is gebeurd, bedank de winkelier en vraag wat je moet meenemen om te tonen dat de tas van jou is.|Confirm in a short message that you will collect the blue bag today at five. Mention yesterday's events, thank the shopkeeper and ask what to bring to show the bag is yours.|در پیامی کوتاه تأیید کنید که امروز ساعت پنج کیف آبی را می‌گیرید. اتفاق دیروز را ذکر کنید، از فروشنده تشکر کنید و بپرسید برای نشان دادن اینکه کیف متعلق به شماست چه چیزی باید همراه بیاورید.",
        "written_sample": "Beste medewerker, gisteren heb ik uw winkel bezocht en heb ik mijn blauwe tas laten liggen. Bedankt dat u die hebt gevonden. Ik kom de tas vandaag om vijf uur ophalen, vóór de winkel sluit. Kunt u mij zeggen wat ik moet meenemen om te tonen dat de tas van mij is? Met vriendelijke groeten, Sam.|Dear staff member, yesterday I visited your shop and left my blue bag behind. Thank you for finding it. I will collect it today at five, before the shop closes. Could you tell me what I should bring to show the bag is mine? Kind regards, Sam.|کارمند گرامی، دیروز به فروشگاه شما آمدم و کیف آبی‌ام را جا گذاشتم. ممنون که آن را پیدا کردید. امروز ساعت پنج، پیش از بسته شدن فروشگاه، کیف را می‌گیرم. می‌توانید بگویید برای نشان دادن مالکیت کیف چه چیزی همراه داشته باشم؟ با احترام، سام.",
        "bounds": (20, 100),
        "criteria": ["Vertel wat is gebeurd en bevestig een geldige ophaaltijd.|Explain what happened and confirm a valid collection time.|اتفاق را توضیح دهید و زمان مجاز دریافت را تأیید کنید.", "Vraag om het ontbrekende praktische detail.|Ask for the missing practical detail.|جزئیات عملی نامشخص را بپرسید."],
        "examples": ["Ik heb brood gekocht.|I bought bread.|نان خریده‌ام.", "Sam is naar de markt gegaan.|Sam went to the market.|سام به بازار رفته است.", "Wij hebben de winkel gebeld.|We called the shop.|به فروشگاه تلفن کرده‌ایم."],
        "grammar_q": ("Vul aan: Sam … naar de markt gegaan.|Complete: Sam … naar de markt gegaan.|کامل کنید: Sam … naar de markt gegaan.", "is|is|is", "heeft|heeft|heeft", "Gaan naar een bestemming gebruikt hier zijn.|Going to a destination takes zijn here.|رفتن به یک مقصد در این جمله با zijn ساخته می‌شود."),
        "words": [
            ("de markt", "Een plaats met kramen waar mensen producten verkopen.|A place with stalls where people sell products.|محلی با غرفه‌های فروش کالا.", "Ik ben naar de markt gegaan.|I went to the market.|به بازار رفته‌ام."),
            ("de tas", "Een voorwerp waarin je spullen meeneemt.|An object used to carry belongings.|وسیله‌ای برای حمل وسایل؛ کیف.", "Ik heb mijn tas gevonden.|I found my bag.|کیفم را پیدا کرده‌ام."),
            ("kopen", "Iets krijgen door ervoor te betalen.|Get something by paying for it.|گرفتن چیزی در برابر پرداخت پول؛ خریدن.", "Ik heb brood gekocht.|I bought bread.|نان خریده‌ام.")
        ]
    },
    {
        "stage": "pre-b1", "grammar": "because", "concept": "because-clause",
        "sources": [("source-07", 6), ("source-04", 103)],
        "title": "Toch met de trein|Taking the train after all|بالاخره با قطار",
        "focus": "Een keuze verklaren met omdat en de werkwoorden op de juiste plaats.|Explaining a choice with omdat and placing verbs correctly.|توضیح انتخاب با omdat و جای درست فعل‌ها.",
        "paragraphs": [
            "Julie vertrekt naar haar cursus, die om negen uur begint. Ze wil de bus nemen, maar aan de halte leest ze dat de bus twintig minuten vertraging heeft. Haar fiets staat thuis en heeft een lekke band. Julie wil niet te laat komen.|Julie leaves for her course, which begins at nine. She wants to take the bus, but at the stop she reads that the bus is delayed by twenty minutes. Her bicycle is at home with a flat tyre. Julie does not want to be late.|ژولی به سمت کلاسش می‌رود که ساعت نه شروع می‌شود. می‌خواهد اتوبوس بگیرد، اما در ایستگاه می‌خواند که اتوبوس بیست دقیقه تأخیر دارد. دوچرخه‌اش در خانه است و لاستیکش پنچر شده. ژولی نمی‌خواهد دیر برسد.",
            "Ze kiest de trein van halfnegen omdat die op tijd aankomt. Ze koopt een ticket en stuurt haar klasgenoot een bericht. Op het vertrekbord staat spoor drie. Vlak voor vertrek krijgt ze een nieuwe boodschap over het spoor.|She chooses the half-past-eight train because it arrives on time. She buys a ticket and messages her classmate. The departure board says platform three. Just before departure, she receives a new platform message.|قطار ساعت هشت‌ونیم را انتخاب می‌کند چون به‌موقع می‌رسد. بلیت می‌خرد و به هم‌کلاسی‌اش پیام می‌دهد. روی تابلو سکوی سه نوشته شده. درست پیش از حرکت، پیام تازه‌ای درباره سکو دریافت می‌کند."
        ],
        "listening": "Aandacht, reizigers. De trein van acht uur dertig vertrekt vandaag niet van spoor drie, maar van spoor twee. Het vertrekuur verandert niet. Ga naar spoor twee en controleer daar het bord met de bestemming.|Attention, passengers. The 08:30 train departs today from platform two, not three. The departure time has not changed. Go to platform two and check the destination board there.|توجه، مسافران. قطار ساعت هشت‌وسی امروز از سکوی دو حرکت می‌کند، نه سه. ساعت حرکت تغییر نکرده است. به سکوی دو بروید و تابلوی مقصد را آنجا بررسی کنید.",
        "reading_q": [
            ("Waarom neemt Julie de bus niet?|Why does Julie not take the bus?|چرا ژولی اتوبوس نمی‌گیرد؟", "Omdat de bus vertraging heeft.|Because the bus is delayed.|چون اتوبوس تأخیر دارد.", "Omdat ze haar fiets bij zich heeft.|Because she has her bicycle with her.|چون دوچرخه‌اش همراهش است.", "De bus heeft twintig minuten vertraging.|The bus is delayed by twenty minutes.|اتوبوس بیست دقیقه تأخیر دارد."),
            ("Welk vertrekuur kiest Julie?|Which departure time does Julie choose?|ژولی چه ساعت حرکتی را انتخاب می‌کند؟", "08.30 uur.|08:30.|ساعت ۸:۳۰.", "09.00 uur.|09:00.|ساعت ۹.", "Halfnegen is 08.30 uur.|Halfnegen is 08:30.|Halfnegen یعنی ساعت ۸:۳۰.")
        ],
        "listening_q": [
            ("Naar welk spoor moet Julie nu gaan?|Which platform should Julie go to now?|ژولی اکنون باید به کدام سکو برود؟", "Spoor twee.|Platform two.|سکوی دو.", "Spoor drie.|Platform three.|سکوی سه.", "De nieuwe boodschap noemt spoor twee.|The new message names platform two.|پیام تازه سکوی دو را ذکر می‌کند."),
            ("Welke informatie blijft hetzelfde?|Which information stays the same?|کدام اطلاعات تغییر نمی‌کند؟", "Het vertrekuur.|The departure time.|ساعت حرکت.", "Het spoor.|The platform.|سکو.", "De boodschap zegt dat het vertrekuur niet verandert.|The message says the departure time does not change.|پیام می‌گوید ساعت حرکت تغییر نمی‌کند.")
        ],
        "speaking": "Leg Julies keuze aan een klasgenoot uit. Geef de reden, noem het juiste spoor en maak duidelijk wat niet veranderd is.|Explain Julie's choice to a classmate. Give the reason, name the correct platform and clarify what has not changed.|انتخاب ژولی را برای یک هم‌کلاسی توضیح دهید. دلیل و سکوی درست را بگویید و روشن کنید چه چیزی تغییر نکرده است.",
        "spoken_sample": "Julie neemt de trein omdat de bus twintig minuten vertraging heeft. Met de fiets kan ze niet gaan omdat de band lek is. De trein vertrekt nog altijd om halfnegen, maar nu van spoor twee. Ze moet het bord daar nog controleren.|Julie is taking the train because the bus is delayed by twenty minutes. She cannot cycle because the tyre is flat. The train still departs at half past eight, but now from platform two. She still needs to check the board there.|ژولی قطار می‌گیرد چون اتوبوس بیست دقیقه تأخیر دارد. نمی‌تواند با دوچرخه برود چون لاستیک پنچر است. قطار همچنان ساعت هشت‌ونیم حرکت می‌کند، اما اکنون از سکوی دو. باید تابلو را آنجا هم بررسی کند.",
        "writing": "Schrijf als Julie een bericht aan je klasgenoot. Verklaar waarom je de trein neemt, geef het vertrekuur en corrigeer het oude spoor.|Write as Julie to your classmate. Explain why you are taking the train, give the departure time and correct the old platform.|در نقش ژولی به هم‌کلاسی‌تان پیام بدهید. دلیل انتخاب قطار، ساعت حرکت و اصلاح سکوی قبلی را بنویسید.",
        "written_sample": "Dag Lina, ik neem vandaag de trein omdat de bus twintig minuten vertraging heeft. Mijn fiets heeft bovendien een lekke band. Ik vertrek om halfnegen. Eerst stond spoor drie op het bord, maar volgens de nieuwe boodschap moet ik naar spoor twee. Het vertrekuur is hetzelfde gebleven. Ik controleer de bestemming daar nog even. Tot in de les!|Hi Lina, I am taking the train today because the bus is delayed by twenty minutes. My bicycle also has a flat tyre. I leave at half past eight. The board first said platform three, but the new message says I need platform two. The departure time is unchanged. I will check the destination there. See you in class!|سلام لینا، امروز قطار می‌گیرم چون اتوبوس بیست دقیقه تأخیر دارد. دوچرخه‌ام هم پنچر شده است. ساعت هشت‌ونیم حرکت می‌کنم. ابتدا روی تابلو سکوی سه بود، اما پیام تازه می‌گوید باید به سکوی دو بروم. ساعت حرکت تغییر نکرده است. مقصد را آنجا هم بررسی می‌کنم. تا کلاس!",
        "bounds": (30, 100),
        "criteria": ["Verbind de keuze met een duidelijke reden.|Link the choice to a clear reason.|انتخاب را به دلیلی روشن مرتبط کنید.", "Geef het gewijzigde spoor en het ongewijzigde vertrekuur correct.|Give the changed platform and unchanged time correctly.|سکوی تغییریافته و ساعت ثابت را درست بیان کنید."],
        "examples": ["Ik neem de trein omdat de bus te laat is.|I take the train because the bus is late.|قطار می‌گیرم چون اتوبوس دیر می‌رسد.", "Julie wacht omdat het spoor nog niet bekend is.|Julie waits because the platform is not yet known.|ژولی منتظر می‌ماند چون سکو هنوز مشخص نیست.", "We gaan te voet omdat onze fiets kapot is.|We walk because our bicycle is broken.|پیاده می‌رویم چون دوچرخه‌مان خراب است."],
        "grammar_q": ("Welke zin heeft de juiste volgorde?|Which sentence has the correct word order?|کدام جمله ترتیب درست دارد؟", "Ik wacht omdat de bus te laat is.|I wait because the bus is late.|منتظرم چون اتوبوس دیر می‌رسد.", "Ik wacht omdat is de bus te laat.|I wait because is the bus late.|منتظرم چون هست اتوبوس دیر.", "Na omdat staat de persoonsvorm hier achteraan.|After omdat, the finite verb is at the end here.|پس از omdat، فعل صرف‌شده در این جمله در پایان می‌آید."),
        "words": [
            ("de trein", "Een vervoermiddel dat op rails rijdt.|A vehicle that runs on rails.|وسیله نقلیه‌ای روی ریل؛ قطار.", "Ik neem de trein omdat de bus te laat is.|I take the train because the bus is late.|قطار می‌گیرم چون اتوبوس دیر می‌رسد."),
            ("de fiets", "Een voertuig met twee wielen dat je met pedalen aandrijft.|A two-wheeled vehicle moved by pedalling.|وسیله دوچرخی با پدال؛ دوچرخه.", "Mijn fiets heeft een lekke band.|My bicycle has a flat tyre.|لاستیک دوچرخه‌ام پنچر شده است."),
            ("de bus", "Een groot voertuig voor meerdere reizigers.|A large vehicle for several passengers.|وسیله نقلیه بزرگ برای چندین مسافر؛ اتوبوس.", "De bus heeft vertraging.|The bus is delayed.|اتوبوس تأخیر دارد.")
        ]
    },
    {
        "stage": "b1", "grammar": "relative", "concept": "relative-clauses",
        "sources": [("source-09", 12), ("source-09", 80)],
        "title": "De tas die op de bus bleef|The bag left on the bus|کیفی که در اتوبوس جا ماند",
        "focus": "Met die en dat een voorwerp precies beschrijven en ontbrekende informatie vragen.|Describing an object precisely with die and dat, and requesting missing information.|توصیف دقیق وسیله با die و dat و درخواست اطلاعات نامشخص.",
        "paragraphs": [
            "Ravi stapt om 15.10 uur uit bus acht en merkt dat zijn groene tas niet bij hem is. In de tas zit het boek dat hij gisteren heeft gekocht. Op zijn telefoon vindt hij een foto waarop de tas te zien is. Hij weet welke bus hij heeft genomen, maar hij weet nog niet of iemand de tas heeft gevonden.|Ravi gets off bus eight at 15:10 and notices his green bag is missing. The bag contains the book he bought yesterday. On his phone he finds a photo showing the bag. He knows which bus he took, but does not yet know whether anyone found the bag.|راوی ساعت ۱۵:۱۰ از اتوبوس شماره هشت پیاده می‌شود و می‌بیند کیف سبزش همراهش نیست. در کیف کتابی است که دیروز خریده. در تلفنش عکسی پیدا می‌کند که کیف در آن دیده می‌شود. می‌داند سوار کدام اتوبوس شده، اما هنوز نمی‌داند کسی کیف را پیدا کرده یا نه.",
            "Hij stuurt een bericht naar de dienst voor verloren voorwerpen. Hij beschrijft de tas die op de bus is blijven liggen en voegt de foto toe. Ravi vraagt of de medewerker kan controleren of de tas is binnengebracht. Hij vraagt ook waar hij die kan ophalen als ze gevonden is.|He sends a message to the lost-property service. He describes the bag left on the bus and attaches the photo. Ravi asks the staff member to check whether the bag has been handed in. He also asks where he can collect it if it has been found.|به بخش اشیای گمشده پیام می‌دهد. کیفی را که در اتوبوس جا مانده توصیف می‌کند و عکس را ضمیمه می‌کند. راوی می‌خواهد کارمند بررسی کند آیا کیف تحویل داده شده است. همچنین می‌پرسد اگر پیدا شده، کجا می‌تواند آن را بگیرد."
        ],
        "listening": "Dag Ravi, bedankt voor uw bericht. We hebben uw foto ontvangen, maar we kunnen nog niet bevestigen dat uw tas gevonden is. Kunt u het nummer van de bus en het uur waarop u uitstapte doorgeven? Daarmee kunnen we gerichter navragen. We laten u weten waar u de tas kunt ophalen zodra we die hebben gevonden.|Hello Ravi, thank you for your message. We received your photo, but cannot yet confirm that your bag has been found. Could you provide the bus number and the time you got off? That will help us enquire more specifically. We will tell you where to collect the bag once we find it.|سلام راوی، ممنون از پیامتان. عکس را دریافت کرده‌ایم، اما هنوز نمی‌توانیم پیدا شدن کیف را تأیید کنیم. می‌توانید شماره اتوبوس و ساعت پیاده‌شدنتان را بگویید؟ با این اطلاعات دقیق‌تر پیگیری می‌کنیم. وقتی کیف را پیدا کردیم، محل دریافت را به شما اطلاع می‌دهیم.",
        "reading_q": [
            ("Wat zit er in de groene tas?|What is inside the green bag?|داخل کیف سبز چیست؟", "Het boek dat Ravi gisteren kocht.|The book Ravi bought yesterday.|کتابی که راوی دیروز خریده.", "Een kaart die Ravi vandaag kreeg.|A card Ravi received today.|کارتی که راوی امروز گرفته.", "De tekst noemt het boek dat hij gisteren heeft gekocht.|The text names the book he bought yesterday.|متن کتابی را ذکر می‌کند که دیروز خریده است."),
            ("Wat weet Ravi nog niet?|What does Ravi not know yet?|راوی هنوز چه چیزی را نمی‌داند؟", "Of iemand de tas heeft gevonden.|Whether anyone has found the bag.|آیا کسی کیف را پیدا کرده است.", "Welke kleur zijn tas heeft.|What colour his bag is.|کیفش چه رنگی است.", "De kleur is bekend; het vinden van de tas is niet bevestigd.|The colour is known; finding the bag is not confirmed.|رنگ مشخص است؛ پیدا شدن کیف تأیید نشده است.")
        ],
        "listening_q": [
            ("Welke aanvullende informatie vraagt de medewerker?|What additional information does the staff member request?|کارمند چه اطلاعات دیگری می‌خواهد؟", "Het busnummer en het uur van uitstappen.|The bus number and the time Ravi got off.|شماره اتوبوس و ساعت پیاده شدن.", "De prijs van het boek en de naam van de winkel.|The book price and the shop name.|قیمت کتاب و نام فروشگاه.", "De medewerker vraagt naar het busnummer en het uitstapuur.|The staff member asks for the bus number and time Ravi got off.|کارمند شماره اتوبوس و ساعت پیاده شدن را می‌پرسد."),
            ("Is de tas al zeker gevonden?|Has the bag definitely been found?|آیا کیف قطعاً پیدا شده است؟", "Nee, dat is nog niet bevestigd.|No, that is not yet confirmed.|نه، هنوز تأیید نشده است.", "Ja, Ravi kan die meteen ophalen.|Yes, Ravi can collect it immediately.|بله، راوی می‌تواند فوراً آن را بگیرد.", "De dienst kan het vinden van de tas nog niet bevestigen.|The service cannot yet confirm finding the bag.|بخش مربوط هنوز پیدا شدن کیف را تأیید نمی‌کند.")
        ],
        "speaking": "Beschrijf als Ravi je tas en het boek. Geef ook het busnummer en het uitstapuur door. Maak duidelijk wat je weet en wat nog gecontroleerd moet worden. Gebruik minstens één zin met die of dat. Verzin geen bevestiging dat de tas gevonden is.|As Ravi, describe your bag and book. Also provide the bus number and the time you got off. Distinguish what you know from what still needs checking. Use at least one clause with die or dat. Do not invent confirmation that the bag was found.|در نقش راوی کیف و کتاب را توصیف کنید. شماره اتوبوس و ساعت پیاده شدن را نیز بگویید. اطلاعات قطعی را از موارد نیازمند بررسی جدا کنید. حداقل یک جمله با die یا dat به کار ببرید. پیدا شدن کیف را بدون تأیید اعلام نکنید.",
        "spoken_sample": "Ik zoek de groene tas die ik op de bus heb laten liggen. In de tas zit het boek dat ik gisteren heb gekocht. Ik heb een foto gestuurd, maar ik weet nog niet of iemand de tas heeft gevonden. Ik stapte om 15.10 uur uit bus acht. Kunt u daarmee controleren of de tas is binnengebracht?|I am looking for the green bag I left on the bus. It contains the book I bought yesterday. I sent a photo, but do not yet know whether anyone found the bag. I got off bus eight at 15:10. Can you check with those details whether the bag has been handed in?|دنبال کیف سبزی هستم که در اتوبوس جا گذاشته‌ام. داخلش کتابی است که دیروز خریدم. عکس فرستاده‌ام، اما هنوز نمی‌دانم کسی کیف را پیدا کرده است یا نه. ساعت ۱۵:۱۰ از اتوبوس شماره هشت پیاده شدم. می‌توانید با این اطلاعات بررسی کنید آیا کیف تحویل داده شده است؟",
        "writing": "Schrijf een vervolgbericht aan de dienst. Beschrijf de tas en het boek, verwijs naar de foto en geef het gevraagde busnummer en uitstapuur door. Gebruik die bij een de-woord en dat bij een het-woord.|Write a follow-up message to the service. Describe the bag and book, refer to the photo and provide the requested bus number and exit time. Use die with a de-word and dat with a het-word.|پیامی برای پیگیری بنویسید. کیف و کتاب را توصیف کنید، به عکس اشاره کنید و شماره اتوبوس و ساعت پیاده شدن خواسته‌شده را اعلام کنید. برای واژه دارای de از die و برای واژه دارای het از dat استفاده کنید.",
        "written_sample": "Beste medewerker, ik zoek de groene tas die ik op de bus heb laten liggen. In de tas zit het boek dat ik gisteren heb gekocht. De foto die ik eerder heb gestuurd, toont hoe de tas eruitziet. Ik begrijp dat nog niet bevestigd is of de tas gevonden is. Ik stapte om 15.10 uur uit bus acht. Kunt u met deze gegevens nagaan of de tas is binnengebracht? Met vriendelijke groeten, Ravi.|Dear staff member, I am looking for the green bag I left on the bus. It contains the book I bought yesterday. The photo I sent earlier shows what the bag looks like. I understand that finding the bag is not yet confirmed. I got off bus eight at 15:10. Could you use these details to check whether the bag has been handed in? Kind regards, Ravi.|کارمند گرامی، دنبال کیف سبزی هستم که در اتوبوس جا گذاشته‌ام. در آن کتابی است که دیروز خریدم. عکسی که قبلاً فرستاده‌ام ظاهر کیف را نشان می‌دهد. می‌دانم هنوز پیدا شدن کیف تأیید نشده است. ساعت ۱۵:۱۰ از اتوبوس شماره هشت پیاده شدم. می‌توانید با این اطلاعات بررسی کنید آیا کیف تحویل داده شده است؟ با احترام، راوی.",
        "bounds": (40, 100),
        "criteria": ["Beschrijf het voorwerp met een passende relatieve zin.|Describe the object with an appropriate relative clause.|وسیله را با جمله موصولی مناسب توصیف کنید.", "Houd bevestigde feiten en open vragen uit elkaar.|Keep confirmed facts separate from open questions.|اطلاعات تأییدشده را از پرسش‌های باز جدا کنید."],
        "examples": ["De tas die ik zoek, is groen.|The bag I am looking for is green.|کیفی که دنبالش هستم سبز است.", "Het boek dat ik gisteren kocht, ligt in de tas.|The book I bought yesterday is in the bag.|کتابی که دیروز خریدم در کیف است.", "De boeken die ik leen, breng ik terug.|I return the books I borrow.|کتاب‌هایی را که قرض می‌گیرم پس می‌دهم."],
        "grammar_q": ("Vul aan: het boek … ik zoek.|Complete: het boek … ik zoek.|کامل کنید: het boek … ik zoek.", "dat|dat|dat", "die|die|die", "Een enkelvoudig het-woord krijgt hier dat.|A singular het-word takes dat here.|اینجا برای واژه مفرد دارای het از dat استفاده می‌شود."),
        "words": [
            ("de tas", "Een voorwerp waarin je spullen meeneemt.|An object used to carry belongings.|وسیله‌ای برای حمل وسایل؛ کیف.", "De tas die ik zoek, is groen.|The bag I am looking for is green.|کیفی که دنبالش هستم سبز است."),
            ("het boek", "Een werk met bladzijden om te lezen.|A work with pages to read.|اثری با صفحه‌هایی برای خواندن؛ کتاب.", "Het boek dat ik kocht, ligt in de tas.|The book I bought is in the bag.|کتابی که خریدم در کیف است."),
            ("de foto", "Een afbeelding die met een camera is gemaakt.|An image made with a camera.|تصویری ثبت‌شده با دوربین؛ عکس.", "De foto die ik stuur, toont mijn tas.|The photo I am sending shows my bag.|عکسی که می‌فرستم کیفم را نشان می‌دهد.")
        ]
    }
]

CATEGORY = tr("Van woord naar gesprek|From word to conversation|از واژه تا گفت‌وگو")


def question(identifier: str, fields: tuple) -> dict:
    prompt, correct, wrong, explanation = map(tr, fields)
    index = int(hashlib.sha256(identifier.encode()).hexdigest()[-1], 16) % 2
    return {"id": identifier, "prompt": prompt, "options": [correct, wrong] if index == 0 else [wrong, correct],
            "answer_index": index, "explanation": explanation}


def lemma(term: str) -> str:
    return re.sub(r"^(de|het|een) ", "", term.casefold())


def productive_task(unit: dict, kind: str, sample: str) -> dict:
    lo, hi = unit["bounds"]
    return {"prompt": tr(unit[kind]), "sample": tr(unit[sample]), "criteria": list(map(tr, unit["criteria"])),
            "min_words": lo, "max_words": hi}


def build(units: list[dict] | None = None, root: Path = ROOT) -> None:
    """Append stable units to each stage; source-01 identifiers remain unchanged."""
    if units is None:
        # Separate authoring files keep each pack readable without adding a runtime dependency.
        if __package__:
            from .source_lessons_lower import EXTRA_UNITS as lower
            from .source_lessons_upper import EXTRA_UNITS as upper
        else:
            from source_lessons_lower import EXTRA_UNITS as lower
            from source_lessons_upper import EXTRA_UNITS as upper
        units = [*UNITS, *lower, *upper]
    manifest = json.loads((root / "content/source-index/manifest.json").read_text(encoding="utf-8"))
    sources = {s["source_id"]: s for s in manifest["sources"]}
    curriculum = json.loads((root / "content/curriculum/path.json").read_text(encoding="utf-8"))
    rules = {s["id"]: {g["id"] for g in s["grammar"]} for s in curriculum["stages"]}
    grouped = defaultdict(list)
    for unit in units:
        stage, number = unit["stage"], unit.get("unit", 1)
        if stage not in rules or type(number) is not int or not 1 <= number <= 99:
            raise ValueError("source unit needs a known stage and a stable number from 1 to 99")
        if any(previous.get("unit", 1) == number for previous in grouped[stage]):
            raise ValueError("duplicate source unit number in a stage")
        if unit["grammar"] not in rules[stage]:
            raise ValueError("source unit targets an unknown stage grammar rule")
        grouped[stage].append(unit)

    links = []
    packs = {}
    for stage, stage_units in grouped.items():
        base = json.loads((root / f"content/library/{stage}.json").read_text(encoding="utf-8"))
        existing = {lemma(w["term"]): w["id"] for w in base["vocabulary"]}
        pack = {"schema_version": 1, "stage_id": stage, "review_status": "unreviewed",
                "vocabulary": [], "stories": [], "topics": [], "grammar_extensions": []}
        grammar = {}
        for unit in sorted(stage_units, key=lambda item: item.get("unit", 1)):
            number = unit.get("unit", 1)
            targets = []
            for i, (term, meaning, example) in enumerate(unit["words"], 1):
                candidate = (f"{stage}-scan-v{i:03d}" if number == 1
                             else f"{stage}-source-{number:02d}-v{i:03d}")
                identifier = existing.get(lemma(term), candidate)
                targets.append(identifier)
                if lemma(term) not in existing:
                    pack["vocabulary"].append({"id": identifier, "term": term, "topic": CATEGORY,
                                              "meaning": tr(meaning), "example": tr(example)})
                    existing[lemma(term)] = identifier
            if len(targets) != len(set(targets)):
                raise ValueError("source unit repeats a target lemma")
            topic_id, story_id = f"{stage}-t-source-{number:02d}", f"{stage}-s-source-{number:02d}"
            reading = {"text": {lang: "\n\n".join(tr(p)[lang] for p in unit["paragraphs"]) for lang in ("nl", "en", "fa")},
                       "questions": [question(f"{topic_id}-r{i}", q) for i, q in enumerate(unit["reading_q"], 1)]}
            listening = {"text": tr(unit["listening"]),
                         "questions": [question(f"{topic_id}-l{i}", q) for i, q in enumerate(unit["listening_q"], 1)]}
            topic = {"id": topic_id, "title": tr(unit["title"]), "category": CATEGORY,
                     "objectives": [tr(unit["focus"]), tr("Gebruik bekende woorden in een nieuwe situatie.|Use familiar words in a new situation.|واژه‌های آشنا را در موقعیتی تازه به کار ببرید.")],
                     "language_focus": tr(unit["focus"]), "vocabulary_ids": targets,
                     "reading": reading, "listening": listening,
                     "speaking": productive_task(unit, "speaking", "spoken_sample"),
                     "writing": productive_task(unit, "writing", "written_sample")}
            story_q = dict(reading["questions"][0]); story_q.pop("id")
            story = {"id": story_id, "title": tr(unit["title"]), "topic": CATEGORY,
                     "paragraphs": list(map(tr, unit["paragraphs"])), "vocabulary_ids": targets, "question": story_q}
            pack["topics"].append(topic)
            pack["stories"].append(story)
            extra = grammar.setdefault(unit["grammar"], {"id": unit["grammar"], "examples": [], "practice": []})
            extra["examples"].extend(map(tr, unit["examples"]))
            extra["practice"].append(question(f"{stage}-source-grammar-{number:02d}", unit["grammar_q"]))
            refs = []
            for sid, page in unit["sources"]:
                if sid not in sources or type(page) is not int or not 1 <= page <= sources[sid]["pdf_pages"]:
                    raise ValueError("source page outside the supplied PDF")
                refs.append({"source_id": sid, "source_sha256": sources[sid]["sha256"], "pdf_page": page})
            links.append({"stage_id": stage, "topic_id": topic_id, "story_id": story_id, "concept": unit["concept"],
                          "grammar_id": unit["grammar"],
                          "vocabulary_ids": targets, "sources": refs, "authoring": "original_text_from_source_concepts",
                          "language_review": "pending", "level_alignment": "provisional"})
        pack["grammar_extensions"] = list(grammar.values())
        packs[stage] = pack

    # Check all references before writing any stage, then bind every unit to its final stage pack.
    for stage, pack in packs.items():
        destination = root / f"content/source-lessons/{stage}.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        for link in links:
            if link["stage_id"] == stage:
                link["pack_sha256"] = digest
    destination = root / "content/source-index/lesson-links.json"
    destination.write_text(json.dumps({"schema_version": 1, "lessons": links,
        "coverage_limit": "Original supplements for pre-A1 through B1 only; no B2-C2 coverage or exam validity is inferred."},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
