"""Build small authored word-use packs without changing the existing word banks.

The examples are original drafts awaiting language review. They are deliberately
explicit: Dutch forms, translations and scenarios are not guessed by inflection
rules or generated from a list of unrelated nouns.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def L(nl, en, fa):
    return {"nl": nl, "en": en, "fa": fa}


SETTINGS = {
    "home": L("Thuis", "At home", "در خانه"),
    "school": L("In de les", "In class", "در کلاس"),
    "shop": L("In de winkel", "In a shop", "در فروشگاه"),
    "travel": L("Onderweg", "On a journey", "در مسیر"),
    "work": L("Op het werk", "At work", "در محل کار"),
    "cafe": L("In het café", "At the café", "در کافه"),
    "friends": L("Met vrienden", "With friends", "با دوستان"),
    "research": L("Bij een onderzoek", "In a research project", "در یک پژوهش"),
    "meeting": L("Tijdens het overleg", "During a meeting", "در جلسه"),
    "culture": L("Bij een verhaal of voorstelling", "With a story or performance", "دربارهٔ یک داستان یا نمایش"),
    "service": L("Aan het loket", "At a service desk", "پشت باجه"),
    "debate": L("In een discussie", "In a discussion", "در یک بحث"),
}
PROMPTS = {
    "pre-a1": L("Zeg één korte zin met dit woord. Je mag een naam of plaats veranderen.",
                "Say one short sentence with this word. You may change a name or place.",
                "با این واژه یک جملهٔ کوتاه بگو. می‌توانی نام یا مکان را عوض کنی."),
    "a1": L("Maak een eigen zin met dit woord. Stel daarna een korte vraag.",
            "Make your own sentence with this word. Then ask a short question.",
            "با این واژه جمله‌ای از خودت بساز. سپس یک سؤال کوتاه بپرس."),
    "pre-a2": L("Gebruik dit woord in een andere situatie. Geef een korte reden met want.",
                "Use this word in a different situation. Give a short reason using want.",
                "این واژه را در موقعیت دیگری به کار ببر. با «want» یک دلیل کوتاه بیاور."),
    "a2": L("Gebruik dit woord in twee zinnen: leg de situatie uit en zeg wat je nodig hebt.",
            "Use this word in two sentences: explain the situation and say what you need.",
            "این واژه را در دو جمله به کار ببر: موقعیت را توضیح بده و بگو چه لازم داری."),
    "pre-b1": L("Gebruik dit woord om twee mogelijkheden te vergelijken. Leg je keuze uit.",
                "Use this word to compare two possibilities. Explain your choice.",
                "با این واژه دو امکان را مقایسه کن. دلیل انتخابت را توضیح بده."),
    "b1": L("Vertel een eigen voorbeeld met dit woord. Beschrijf ook het gevolg.",
            "Give your own example using this word. Describe the consequence too.",
            "با این واژه مثالی از خودت بزن. پیامد آن را هم توضیح بده."),
    "pre-b2": L("Formuleer met dit woord een voorstel en één bezwaar tegen dat voorstel.",
                "Use this word to formulate a proposal and one objection to it.",
                "با این واژه پیشنهادی مطرح کن و یک ایراد آن را هم بگو."),
    "b2": L("Gebruik dit woord in een standpunt. Erken daarna een beperking of tegenargument.",
            "Use this word in a position statement. Then acknowledge a limitation or counterargument.",
            "این واژه را در بیان نظرت به کار ببر. سپس یک محدودیت یا استدلال مخالف را بپذیر."),
    "pre-c1": L("Gebruik dit woord voor twee verschillende gesprekspartners. Pas toon en uitleg aan.",
                "Use this word for two different audiences. Adapt your tone and explanation.",
                "این واژه را برای دو مخاطب متفاوت به کار ببر. لحن و توضیحت را متناسب کن."),
    "c1": L("Gebruik dit woord in een onderbouwde uitleg. Maak duidelijk wat vaststaat en wat onzeker blijft.",
            "Use this word in a reasoned explanation. Distinguish what is established from what remains uncertain.",
            "این واژه را در توضیحی مستدل به کار ببر. روشن کن چه چیزی قطعی است و چه چیزی هنوز نامطمئن است."),
    "pre-c2": L("Gebruik dit woord om twee mogelijke interpretaties af te wegen, zonder ze gelijk te stellen.",
                "Use this word to weigh two possible interpretations without treating them as equivalent.",
                "با این واژه دو برداشت ممکن را بسنج، بدون اینکه آن‌ها را هم‌ارز فرض کنی."),
    "c2": L("Gebruik dit woord nauwkeurig in een genuanceerd betoog. Herformuleer het daarna voor een andere doelgroep.",
            "Use this word precisely in a nuanced argument. Then reformulate it for a different audience.",
            "این واژه را دقیق در استدلالی ظریف به کار ببر. سپس آن را برای مخاطبی دیگر بازنویسی کن."),
}

# stage, exact bank term, part of speech, plural (only when useful), contexts:
# each context is a setting, structure and one aligned Dutch/English/Persian text.
ENTRIES = [
    ("pre-a1", "de naam", "noun", "namen", [
        ("school", "present", L("Mijn naam is Sara.", "My name is Sara.", "نام من سارا است.")),
        ("service", "present", L("Wat is uw naam?", "What is your name?", "نام شما چیست؟")),
        ("friends", "present", L("Zijn naam is Amir.", "His name is Amir.", "نام او امیر است.")),
    ]),
    ("pre-a1", "gaan", "verb", None, [
        ("home", "present", L("Ik ga naar huis.", "I am going home.", "من به خانه می‌روم.")),
        ("school", "present", L("Wij gaan naar school.", "We are going to school.", "ما به مدرسه می‌رویم.")),
        ("friends", "present", L("Ga je mee?", "Are you coming along?", "تو هم می‌آیی؟")),
    ]),
    ("pre-a1", "blij", "adjective", None, [
        ("home", "adjective", L("Ik ben blij.", "I am happy.", "من خوشحالم.")),
        ("school", "adjective", L("Sara is blij.", "Sara is happy.", "سارا خوشحال است.")),
        ("friends", "adjective", L("Ben je blij?", "Are you happy?", "خوشحالی؟")),
    ]),
    ("a1", "de sleutel", "noun", "sleutels", [
        ("home", "present", L("Mijn sleutel ligt op de tafel.", "My key is on the table.", "کلید من روی میز است.")),
        ("work", "present", L("Heb je de sleutel van de kast?", "Do you have the key to the cupboard?", "کلید کمد را داری؟")),
        ("friends", "present", L("Je sleutel zit in mijn jas.", "Your key is in my coat.", "کلیدت در کت من است.")),
    ]),
    ("a1", "vragen", "verb", None, [
        ("school", "present", L("Ik vraag de leerkracht om hulp.", "I ask the teacher for help.", "من از معلم کمک می‌خواهم.")),
        ("shop", "present", L("Wij vragen de prijs van het brood.", "We ask the price of the bread.", "ما قیمت نان را می‌پرسیم.")),
        ("cafe", "modal", L("Mag ik iets vragen?", "May I ask something?", "می‌توانم چیزی بپرسم؟")),
    ]),
    ("a1", "rustig", "adjective", None, [
        ("home", "adjective", L("Dit is een rustige straat.", "This is a quiet street.", "این خیابان آرامی است.")),
        ("cafe", "adjective", L("Het café is rustig.", "The café is quiet.", "کافه آرام است.")),
        ("school", "present", L("Spreek rustig, alstublieft.", "Please speak calmly.", "لطفاً با آرامش صحبت کنید.")),
    ]),
    ("pre-a2", "de afspraak", "noun", "afspraken", [
        ("service", "present", L("Ik heb dinsdag een afspraak bij de tandarts.", "I have a dentist's appointment on Tuesday.", "سه‌شنبه وقت دندان‌پزشکی دارم.")),
        ("friends", "modal", L("Kunnen we onze afspraak verplaatsen?", "Can we move our appointment?", "می‌توانیم زمان قرارمان را عوض کنیم؟")),
        ("work", "present", L("Onze afspraak is om twee uur, want daarna heb ik les.", "Our appointment is at two because I have class afterwards.", "قرارمان ساعت دو است، چون بعد از آن کلاس دارم.")),
    ]),
    ("pre-a2", "kiezen", "verb", None, [
        ("cafe", "present", L("Ik kies thee, want ik drink geen koffie.", "I choose tea because I do not drink coffee.", "چای را انتخاب می‌کنم، چون قهوه نمی‌نوشم.")),
        ("travel", "present", L("Welke bus kies je?", "Which bus do you choose?", "کدام اتوبوس را انتخاب می‌کنی؟")),
        ("school", "modal", L("We kunnen een ander onderwerp kiezen.", "We can choose another topic.", "می‌توانیم موضوع دیگری انتخاب کنیم.")),
    ]),
    ("pre-a2", "beschikbaar", "adjective", None, [
        ("work", "adjective", L("Ik ben vrijdag beschikbaar.", "I am available on Friday.", "جمعه وقت دارم.")),
        ("school", "present", L("Is dit lokaal morgen beschikbaar?", "Is this room available tomorrow?", "این کلاس فردا در دسترس است؟")),
        ("shop", "adjective", L("Deze jas is beschikbaar in blauw en groen.", "This coat is available in blue and green.", "این کت در رنگ‌های آبی و سبز موجود است.")),
    ]),
    ("a2", "de uitnodiging", "noun", "uitnodigingen", [
        ("friends", "past", L("Ik heb een uitnodiging voor Sara's verjaardag gekregen.", "I received an invitation to Sara's birthday party.", "دعوت‌نامه‌ای برای جشن تولد سارا دریافت کرده‌ام.")),
        ("work", "future", L("Morgen stuur ik de uitnodiging voor ons overleg.", "Tomorrow I will send the invitation to our meeting.", "فردا دعوت‌نامهٔ جلسه‌مان را می‌فرستم.")),
        ("school", "present", L("In de uitnodiging staat het adres van de school.", "The invitation gives the school's address.", "نشانی مدرسه در دعوت‌نامه نوشته شده است.")),
    ]),
    ("a2", "terugbellen", "verb", None, [
        ("service", "modal", L("Kunt u mij vanmiddag terugbellen?", "Could you call me back this afternoon?", "می‌توانید امروز بعدازظهر به من زنگ بزنید؟")),
        ("friends", "past", L("Ik heb je teruggebeld, maar je nam niet op.", "I called you back, but you did not answer.", "در پاسخ به تماست زنگ زدم، اما جواب ندادی.")),
        ("work", "future", L("Ik bel de klant morgen terug.", "I will call the customer back tomorrow.", "فردا دوباره به مشتری زنگ می‌زنم.")),
    ]),
    ("a2", "duidelijk", "adjective", None, [
        ("travel", "adjective", L("De uitleg over het perron is duidelijk.", "The explanation about the platform is clear.", "توضیح مربوط به سکو روشن است.")),
        ("school", "present", L("Kunt u dat duidelijker zeggen?", "Could you say that more clearly?", "می‌توانید آن را روشن‌تر بگویید؟")),
        ("work", "adjective", L("Ik heb een duidelijke afspraak met mijn collega.", "I have a clear agreement with my colleague.", "با همکارم توافق روشنی دارم.")),
    ]),
    ("pre-b1", "de vertraging", "noun", "vertragingen", [
        ("travel", "past", L("Door de vertraging heb ik mijn aansluiting gemist.", "Because of the delay, I missed my connection.", "به‌دلیل تأخیر، وسیلهٔ نقلیهٔ بعدی را از دست دادم.")),
        ("work", "present", L("Er is vertraging bij de levering, dus we bellen de klant.", "The delivery is delayed, so we call the customer.", "تحویل با تأخیر روبه‌رو شده است، پس به مشتری زنگ می‌زنیم.")),
        ("friends", "future", L("Als de vertraging langer duurt, kom ik met de bus.", "If the delay lasts longer, I will come by bus.", "اگر تأخیر طولانی‌تر شود، با اتوبوس می‌آیم.")),
    ]),
    ("pre-b1", "overstappen", "verb", None, [
        ("travel", "modal", L("In Gent moet je overstappen op de trein naar Kortrijk.", "In Ghent, you have to change to the train to Kortrijk.", "در گنت باید سوار قطار کورتریک شوی.")),
        ("friends", "past", L("We zijn in Brugge overgestapt en waren toch op tijd.", "We changed in Bruges and still arrived on time.", "در بروژ وسیله‌مان را عوض کردیم و با این حال به‌موقع رسیدیم.")),
        ("work", "future", L("Volgende maand stap ik over op een andere werkregeling.", "Next month I will switch to a different work schedule.", "ماه آینده برنامهٔ کاری‌ام را عوض می‌کنم.")),
    ]),
    ("pre-b1", "haalbaar", "adjective", None, [
        ("school", "adjective", L("Drie hoofdstukken per week lijken mij haalbaar.", "Three chapters a week seem manageable to me.", "به نظرم سه فصل در هفته شدنی است.")),
        ("travel", "conditional", L("Met de fiets zou dat tijdstip niet haalbaar zijn.", "That arrival time would not be achievable by bicycle.", "با دوچرخه رسیدن در آن ساعت شدنی نخواهد بود.")),
        ("friends", "comparison", L("Een klein feest is voor ons haalbaarder dan een groot feest.", "A small party is more manageable for us than a large one.", "برگزاری یک مهمانی کوچک برای ما شدنی‌تر از مهمانی بزرگ است.")),
    ]),
    ("b1", "het contract", "noun", "contracten", [
        ("work", "past", L("Voordat ik het contract tekende, vroeg ik uitleg over de werkuren.", "Before I signed the contract, I asked for an explanation of the working hours.", "پیش از امضای قرارداد، دربارهٔ ساعت‌های کاری توضیح خواستم.")),
        ("home", "present", L("In mijn contract staat dat de huur op de eerste dag betaald wordt.", "My contract says that the rent is paid on the first day.", "در قراردادم نوشته شده که اجاره در روز اول پرداخت می‌شود.")),
        ("service", "modal", L("Mag ik het contract eerst rustig thuis lezen?", "May I first read the contract carefully at home?", "می‌توانم اول قرارداد را با حوصله در خانه بخوانم؟")),
    ]),
    ("b1", "vergelijken", "verb", None, [
        ("shop", "past", L("Ik heb twee fietsen vergeleken voordat ik er één kocht.", "I compared two bicycles before buying one.", "پیش از خریدن یک دوچرخه، دو دوچرخه را مقایسه کردم.")),
        ("school", "present", L("We vergelijken de verhalen om de verschillen tussen de personages te begrijpen.", "We compare the stories to understand the differences between the characters.", "داستان‌ها را مقایسه می‌کنیم تا تفاوت شخصیت‌ها را بفهمیم.")),
        ("work", "future", L("Morgen vergelijken we de voorstellen en kiezen we de beste oplossing.", "Tomorrow we will compare the proposals and choose the best solution.", "فردا پیشنهادها را مقایسه می‌کنیم و بهترین راه‌حل را انتخاب می‌کنیم.")),
    ]),
    ("b1", "onzeker", "adjective", None, [
        ("friends", "adjective", L("Ik voel me onzeker omdat ik niet weet wat zij van mij verwacht.", "I feel uncertain because I do not know what she expects of me.", "احساس تردید می‌کنم، چون نمی‌دانم او چه انتظاری از من دارد.")),
        ("travel", "adjective", L("Het is nog onzeker of de laatste trein zal rijden.", "It is still uncertain whether the last train will run.", "هنوز معلوم نیست آخرین قطار حرکت خواهد کرد یا نه.")),
        ("work", "past", L("De planning was onzeker, dus hebben we een tweede mogelijkheid besproken.", "The schedule was uncertain, so we discussed a second option.", "برنامه‌ریزی قطعی نبود، بنابراین دربارهٔ گزینهٔ دومی صحبت کردیم.")),
    ]),
    ("pre-b2", "het voorstel", "noun", "voorstellen", [
        ("meeting", "present", L("Het voorstel bespaart tijd, maar vraagt in het begin extra uitleg.", "The proposal saves time but requires extra explanation at first.", "این پیشنهاد در زمان صرفه‌جویی می‌کند، اما در آغاز به توضیح بیشتری نیاز دارد.")),
        ("friends", "conditional", L("Ik zou je voorstel aanvaarden als we de kosten eerlijk verdelen.", "I would accept your proposal if we shared the costs fairly.", "اگر هزینه‌ها را منصفانه تقسیم کنیم، پیشنهادت را می‌پذیرم.")),
        ("school", "past", L("Na de bespreking hebben we het voorstel aangepast aan de reacties.", "After the discussion, we adapted the proposal to the feedback.", "پس از بحث، پیشنهاد را با توجه به بازخوردها اصلاح کردیم.")),
    ]),
    ("pre-b2", "afwegen", "verb", None, [
        ("work", "present", L("We wegen de lagere prijs af tegen het risico op vertraging.", "We weigh the lower price against the risk of delay.", "قیمت پایین‌تر را در برابر خطر تأخیر می‌سنجیم.")),
        ("home", "past", L("Ze heeft de voordelen van verhuizen zorgvuldig afgewogen.", "She carefully weighed the advantages of moving.", "او مزایای اسباب‌کشی را با دقت سنجیده است.")),
        ("meeting", "conditional", L("Ik zou eerst afwegen wie door deze keuze wordt geraakt.", "I would first consider who is affected by this choice.", "من ابتدا بررسی می‌کردم که این انتخاب بر چه کسانی اثر می‌گذارد.")),
    ]),
    ("pre-b2", "redelijk", "adjective", None, [
        ("shop", "adjective", L("Die prijs lijkt redelijk, zolang de herstelling inbegrepen is.", "That price seems reasonable, as long as the repair is included.", "این قیمت منطقی به نظر می‌رسد، به‌شرط اینکه تعمیر را هم شامل شود.")),
        ("work", "comparison", L("Een week uitstel is redelijker dan een onhaalbare belofte.", "A week's postponement is more reasonable than an impossible promise.", "یک هفته تعویق منطقی‌تر از قولی انجام‌نشدنی است.")),
        ("debate", "adjective", L("Het is redelijk om te vragen waarop die conclusie gebaseerd is.", "It is reasonable to ask what that conclusion is based on.", "منطقی است بپرسیم آن نتیجه بر چه اساسی است.")),
    ]),
    ("b2", "het misverstand", "noun", "misverstanden", [
        ("friends", "past", L("Het misverstand ontstond doordat mijn korte antwoord boos klonk.", "The misunderstanding arose because my brief reply sounded angry.", "سوءتفاهم از آنجا پیش آمد که پاسخ کوتاهم عصبانی به نظر رسید.")),
        ("work", "present", L("Om een misverstand te voorkomen, bevestig ik de afspraak schriftelijk.", "To prevent a misunderstanding, I confirm the agreement in writing.", "برای جلوگیری از سوءتفاهم، توافق را به‌صورت کتبی تأیید می‌کنم.")),
        ("culture", "conditional", L("Zonder dat misverstand zou het toneelstuk heel anders eindigen.", "Without that misunderstanding, the play would end very differently.", "بدون آن سوءتفاهم، نمایش پایان کاملاً متفاوتی داشت.")),
    ]),
    ("b2", "nuanceren", "verb", None, [
        ("debate", "present", L("Ik wil die uitspraak nuanceren: niet iedereen heeft dezelfde keuzevrijheid.", "I want to qualify that statement: not everyone has the same freedom of choice.", "می‌خواهم آن گفته را تعدیل کنم: همه آزادی انتخاب یکسانی ندارند.")),
        ("research", "past", L("De onderzoeker heeft haar conclusie genuanceerd na de nieuwe meting.", "The researcher qualified her conclusion after the new measurement.", "پژوهشگر پس از اندازه‌گیری جدید، نتیجه‌گیری‌اش را تعدیل کرده است.")),
        ("friends", "future", L("In mijn bericht zal ik mijn standpunt nuanceren en ook jouw bezwaar erkennen.", "In my message, I will qualify my position and acknowledge your objection too.", "در پیامم موضعم را تعدیل خواهم کرد و ایراد تو را هم خواهم پذیرفت.")),
    ]),
    ("b2", "betrouwbaar", "adjective", None, [
        ("research", "adjective", L("Een betrouwbare bron maakt ook haar beperkingen duidelijk.", "A reliable source also makes its limitations clear.", "یک منبع معتبر، محدودیت‌های خود را هم روشن می‌کند.")),
        ("friends", "comparison", L("Hij blijkt betrouwbaarder dan ik na onze eerste ontmoeting had verwacht.", "He turns out to be more reliable than I expected after our first meeting.", "معلوم می‌شود او قابل‌اعتمادتر از چیزی است که پس از نخستین دیدارمان انتظار داشتم.")),
        ("travel", "adjective", L("Het systeem is betrouwbaar, al kan geen enkele voorspelling elke vertraging voorzien.", "The system is reliable, although no prediction can foresee every delay.", "سامانه قابل‌اعتماد است، هرچند هیچ پیش‌بینی‌ای نمی‌تواند همهٔ تأخیرها را پیش‌بینی کند.")),
    ]),
    ("pre-c1", "de toelichting", "noun", "toelichtingen", [
        ("meeting", "present", L("Zonder nadere toelichting blijft onduidelijk wie het besluit moet uitvoeren.", "Without further explanation, it remains unclear who must carry out the decision.", "بدون توضیح بیشتر، روشن نیست چه کسی باید تصمیم را اجرا کند.")),
        ("culture", "past", L("De toelichting van de regisseur veranderde mijn kijk op de laatste scène.", "The director's explanation changed how I viewed the final scene.", "توضیح کارگردان نگاه مرا به صحنهٔ پایانی تغییر داد.")),
        ("service", "register", L("Kunt u uw schriftelijke toelichting aanvullen met een concreet voorbeeld?", "Could you supplement your written explanation with a concrete example?", "می‌توانید توضیح کتبی خود را با یک مثال مشخص تکمیل کنید؟")),
    ]),
    ("pre-c1", "weerleggen", "verb", None, [
        ("debate", "present", L("Je weerlegt zijn argument niet door alleen zijn bedoelingen in twijfel te trekken.", "You do not refute his argument merely by questioning his intentions.", "صرفاً با زیر سؤال بردن نیت او، استدلالش را رد نمی‌کنی.")),
        ("research", "past", L("Het tegenvoorbeeld heeft de algemene bewering weerlegd, maar verklaart het verschijnsel nog niet.", "The counterexample refuted the general claim but does not yet explain the phenomenon.", "مثال نقض، ادعای کلی را رد کرده است، اما هنوز پدیده را توضیح نمی‌دهد.")),
        ("work", "conditional", L("Om dat bezwaar te weerleggen, zouden we eerst de ontbrekende gegevens moeten verzamelen.", "To refute that objection, we would first need to collect the missing data.", "برای رد آن ایراد، ابتدا باید داده‌های گمشده را جمع‌آوری کنیم.")),
    ]),
    ("pre-c1", "vooralsnog", "adverb", None, [
        ("research", "present", L("Vooralsnog wijzen de gegevens op samenhang, niet op een oorzakelijk verband.", "For now, the data indicate an association, not a causal relationship.", "در حال حاضر داده‌ها از همبستگی حکایت دارند، نه رابطهٔ علّی.")),
        ("meeting", "future", L("We zullen het voorstel vooralsnog niet uitvoeren; eerst willen we de betrokkenen horen.", "We will not implement the proposal for now; first we want to hear those affected.", "فعلاً پیشنهاد را اجرا نخواهیم کرد؛ ابتدا می‌خواهیم نظر افراد درگیر را بشنویم.")),
        ("friends", "register", L("Vooralsnog houd ik mijn plannen voor mezelf, al sluit ik een gesprek later niet uit.", "For now, I am keeping my plans to myself, though I do not rule out a conversation later.", "فعلاً برنامه‌هایم را پیش خودم نگه می‌دارم، هرچند گفت‌وگو در آینده را منتفی نمی‌دانم.")),
    ]),
    ("c1", "de hypothese", "noun", "hypothesen", [
        ("research", "present", L("De hypothese is toetsbaar, maar de huidige gegevens laten nog geen overtuigende conclusie toe.", "The hypothesis is testable, but the current data do not yet allow a convincing conclusion.", "فرضیه آزمون‌پذیر است، اما داده‌های کنونی هنوز اجازهٔ نتیجه‌گیری قانع‌کننده‌ای نمی‌دهند.")),
        ("culture", "conditional", L("Als we die hypothese over de verteller volgen, krijgt zijn zwijgen een andere betekenis.", "If we follow that hypothesis about the narrator, his silence takes on a different meaning.", "اگر آن فرضیه دربارهٔ راوی را بپذیریم، سکوت او معنای دیگری پیدا می‌کند.")),
        ("work", "past", L("Onze hypothese over de dalende verkoop bleek slechts een deel van het probleem te verklaren.", "Our hypothesis about falling sales turned out to explain only part of the problem.", "معلوم شد فرضیهٔ ما دربارهٔ کاهش فروش فقط بخشی از مشکل را توضیح می‌دهد.")),
    ]),
    ("c1", "de achterban", "noun", None, [
        ("meeting", "present", L("De vertegenwoordiger steunt het compromis, maar moet het nog aan zijn achterban voorleggen.", "The representative supports the compromise but still has to put it to his supporters.", "نماینده از سازش حمایت می‌کند، اما هنوز باید آن را با حامیانش در میان بگذارد.")),
        ("debate", "conditional", L("Zonder overleg met de achterban zou haar mandaat gemakkelijk ter discussie komen te staan.", "Without consulting her constituency, her mandate could easily be called into question.", "بدون مشورت با حامیانش، اختیار نمایندگی او به‌آسانی زیر سؤال می‌رفت.")),
        ("work", "past", L("De vakbond heeft haar achterban uitgelegd waarom zij niet op alle eisen kon ingaan.", "The trade union explained to its members why it could not meet every demand.", "اتحادیه برای اعضای خود توضیح داده است که چرا نمی‌توانسته همهٔ خواسته‌ها را بپذیرد.")),
    ]),
    ("c1", "de betrouwbaarheid", "noun", None, [
        ("research", "present", L("De betrouwbaarheid van de meting zegt niet vanzelf of we ook het juiste verschijnsel meten.", "The reliability of a measurement does not by itself show whether we are measuring the right phenomenon.", "پایایی اندازه‌گیری به‌خودی‌خود نشان نمی‌دهد که آیا پدیدهٔ درستی را اندازه می‌گیریم.")),
        ("friends", "past", L("Zijn betrouwbaarheid werd pas zichtbaar toen hij ook op moeilijke momenten zijn afspraken nakwam.", "His reliability became apparent only when he kept his promises even in difficult times.", "قابل‌اعتماد بودن او زمانی آشکار شد که حتی در شرایط دشوار هم به قول‌هایش عمل کرد.")),
        ("work", "comparison", L("We moeten niet alleen de snelheid, maar ook de betrouwbaarheid van beide diensten vergelijken.", "We must compare not only the speed but also the reliability of both services.", "باید نه‌فقط سرعت، بلکه قابل‌اعتماد بودن هر دو خدمت را مقایسه کنیم.")),
    ]),
    ("pre-c2", "de interpretatie", "noun", "interpretaties", [
        ("culture", "present", L("Die interpretatie van de slotzin is verdedigbaar, zolang je de eerdere ironie niet buiten beschouwing laat.", "That interpretation of the closing sentence is defensible, provided you do not disregard the earlier irony.", "این برداشت از جملهٔ پایانی دفاع‌پذیر است، به‌شرط آنکه طنز کنایه‌آمیز پیشین را نادیده نگیری.")),
        ("research", "past", L("De aanvullende analyse heeft de interpretatie bijgesteld, zonder de oorspronkelijke waarnemingen ongeldig te maken.", "The additional analysis revised the interpretation without invalidating the original observations.", "تحلیل تکمیلی برداشت را اصلاح کرده است، بدون اینکه مشاهدات اولیه را بی‌اعتبار کند.")),
        ("debate", "conditional", L("Een ruimere interpretatie zou meer gevallen omvatten, maar ook de grens van de regel minder voorspelbaar maken.", "A broader interpretation would cover more cases but would also make the rule's boundary less predictable.", "برداشتی گسترده‌تر موارد بیشتری را در بر می‌گرفت، اما مرز قاعده را هم کمتر پیش‌بینی‌پذیر می‌کرد.")),
    ]),
    ("pre-c2", "de veralgemening", "noun", "veralgemeningen", [
        ("research", "present", L("Die veralgemening gaat verder dan de steekproef rechtvaardigt, ook al klinkt de verklaring aannemelijk.", "That generalisation goes beyond what the sample justifies, even though the explanation sounds plausible.", "این تعمیم فراتر از چیزی است که نمونه توجیه می‌کند، هرچند توضیح باورپذیر به نظر می‌رسد.")),
        ("friends", "past", L("Haar veralgemening over mensen die verhuizen bleek vooral op één pijnlijke ervaring te berusten.", "Her generalisation about people who move away turned out to rest mainly on one painful experience.", "معلوم شد تعمیم او دربارهٔ کسانی که نقل مکان می‌کنند، بیشتر بر یک تجربهٔ تلخ استوار بوده است.")),
        ("debate", "conditional", L("Met een voorzichtiger veralgemening zou hij zijn punt behouden zonder uitzonderingen weg te redeneren.", "With a more cautious generalisation, he would retain his point without explaining away exceptions.", "با تعمیمی محتاطانه‌تر، او می‌توانست نکته‌اش را حفظ کند، بدون آنکه استثناها را با استدلال کنار بزند.")),
    ]),
    ("pre-c2", "de concessie", "noun", "concessies", [
        ("meeting", "present", L("De concessie lijkt eenzijdig, maar maakt deel uit van een ruimer akkoord waarvan niet alle bepalingen openbaar zijn.", "The concession seems one-sided but forms part of a wider agreement whose provisions are not all public.", "امتیاز داده‌شده یک‌طرفه به نظر می‌رسد، اما بخشی از توافقی گسترده‌تر است که همهٔ بندهای آن علنی نیست.")),
        ("debate", "register", L("Die concessie in je betoog verzwakt je standpunt niet; ze maakt de afbakening ervan juist duidelijker.", "That concession in your argument does not weaken your position; it makes its scope clearer.", "پذیرش آن نکته در استدلالت، موضعت را تضعیف نمی‌کند؛ بلکه حدود آن را روشن‌تر می‌کند.")),
        ("friends", "past", L("Wat zij als een kleine concessie beschouwde, had hij ervaren als het prijsgeven van hun gezamenlijke plan.", "What she considered a small concession, he had experienced as abandoning their shared plan.", "چیزی که او امتیازی کوچک می‌دانست، از نگاه مرد به معنای کنار گذاشتن برنامهٔ مشترکشان بوده بود.")),
    ]),
    ("c2", "de legitimiteit", "noun", None, [
        ("debate", "present", L("De juridische geldigheid van het besluit staat vast; de discussie over zijn democratische legitimiteit is daarmee niet beslecht.", "The decision's legal validity is established; that does not settle the debate over its democratic legitimacy.", "اعتبار حقوقی تصمیم قطعی است؛ اما این امر بحث دربارهٔ مشروعیت دموکراتیک آن را حل نمی‌کند.")),
        ("culture", "present", L("De roman ontleent zijn spanning aan een verteller die de legitimiteit van zijn eigen oordeel ongemerkt ondergraaft.", "The novel derives its tension from a narrator who subtly undermines the legitimacy of his own judgement.", "کشش رمان از راوی‌ای می‌آید که بی‌آنکه آشکار باشد، اعتبار داوری خودش را سست می‌کند.")),
        ("meeting", "conditional", L("Meer inspraak zou de legitimiteit kunnen versterken, mits deelnemers daadwerkelijk invloed op de uitkomst krijgen.", "Greater participation could strengthen legitimacy, provided participants genuinely influence the outcome.", "مشارکت بیشتر می‌تواند مشروعیت را تقویت کند، به‌شرط آنکه شرکت‌کنندگان واقعاً بر نتیجه اثر بگذارند.")),
    ]),
    ("c2", "de aannemelijkheid", "noun", None, [
        ("research", "present", L("De aannemelijkheid van een verklaring vormt een vertrekpunt voor onderzoek, geen vervanging voor toetsbaar bewijs.", "The plausibility of an explanation is a starting point for investigation, not a substitute for testable evidence.", "باورپذیری یک توضیح نقطهٔ آغاز پژوهش است، نه جایگزینی برای شواهد آزمون‌پذیر.")),
        ("culture", "past", L("De auteur had de aannemelijkheid van het alibi zo zorgvuldig opgebouwd dat de kleine tegenspraak mij aanvankelijk ontging.", "The author had built the alibi's plausibility so carefully that I initially missed the small contradiction.", "نویسنده باورپذیری ادعای حضور در جای دیگر را چنان دقیق ساخته بود که ابتدا متوجه تناقض کوچک نشدم.")),
        ("debate", "conditional", L("Een beroep op ervaring kan de aannemelijkheid vergroten, maar zou pas overtuigen als ook alternatieve verklaringen worden besproken.", "An appeal to experience can increase plausibility but would convince only if alternative explanations were also discussed.", "استناد به تجربه می‌تواند باورپذیری را بیشتر کند، اما فقط وقتی قانع‌کننده خواهد بود که توضیح‌های جایگزین هم بررسی شوند.")),
    ]),
    ("c2", "de gevolgtrekking", "noun", "gevolgtrekkingen", [
        ("research", "present", L("De gevolgtrekking is logisch binnen dat model, maar haar toepasbaarheid hangt af van aannames die nog niet zijn getoetst.", "The inference is logical within that model, but its applicability depends on assumptions that have not yet been tested.", "این استنتاج در چارچوب آن مدل منطقی است، اما کاربردپذیری آن به فرض‌هایی بستگی دارد که هنوز آزموده نشده‌اند.")),
        ("culture", "past", L("Mijn eerste gevolgtrekking over haar zwijgen bleek achteraf meer over mijn verwachtingen te zeggen dan over haar bedoelingen.", "My first inference about her silence turned out to reveal more about my expectations than about her intentions.", "بعداً معلوم شد برداشت اولیه‌ام از سکوت او بیشتر دربارهٔ انتظارهای خودم بوده تا نیت او.")),
        ("debate", "conditional", L("Als die premisse vervalt, moeten we de gevolgtrekking herzien in plaats van alleen de formulering af te zwakken.", "If that premise no longer holds, we must revise the inference rather than merely soften its wording.", "اگر آن مقدمه برقرار نباشد، باید استنتاج را بازنگری کنیم، نه اینکه فقط بیان آن را ملایم‌تر کنیم.")),
    ]),
]


def build(root=ROOT):
    content = root / "content"
    grouped = {}
    for stage, term, pos, plural, examples in ENTRIES:
        if stage not in PROMPTS:
            raise ValueError("unknown vocabulary transfer stage")
        bank = json.loads((content / "library" / f"{stage}.json").read_text(encoding="utf-8"))
        matches = [word for word in bank["vocabulary"] if word["term"] == term]
        if len(matches) != 1:
            raise ValueError(f"expected one existing {stage} word: {term}")
        word_id = matches[0]["id"]
        entry = {"word_id": word_id, "term": term, "part_of_speech": pos,
                 "contexts": [{"id": f"{word_id}-use-{index}", "setting": SETTINGS[setting],
                               "sentence": sentence, "production_prompt": PROMPTS[stage], "structure": structure}
                              for index, (setting, structure, sentence) in enumerate(examples, 1)]}
        if pos == "noun":
            entry["article"] = term.split()[0]
        if plural:
            entry["plural"] = plural
        # Forms are complete authored sentences, not guessed stems or tense tables.
        labels = {"present": L("Tegenwoordige tijd", "Present tense", "زمان حال"),
                  "past": L("Verleden tijd", "Past tense", "زمان گذشته"),
                  "future": L("Toekomst", "Future reference", "اشاره به آینده"),
                  "modal": L("Met een hulpwerkwoord", "With a modal verb", "با فعل وجهی"),
                  "conditional": L("Voorwaardelijke vorm", "Conditional form", "ساخت شرطی")}
        if pos == "verb":
            entry["forms"] = [{"label": labels[structure], "text": sentence}
                              for _, structure, sentence in examples if structure in labels]
        if any(item["word_id"] == word_id for item in grouped.get(stage, [])):
            raise ValueError("vocabulary transfer cannot repeat a word")
        grouped.setdefault(stage, []).append(entry)
    directory = content / "vocabulary-transfer"
    directory.mkdir(parents=True, exist_ok=True)
    for stage, entries in grouped.items():
        payload = {"schema_version": 1, "stage_id": stage, "review_status": "unreviewed", "entries": entries}
        (directory / f"{stage}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return grouped


if __name__ == "__main__":
    packs = build()
    print(f"Built {len(packs)} stage packs with {sum(map(len, packs.values()))} authored word journeys.")
