"""Original beginner units using the teaching functions indexed in the private scans.

These are provisional authored lessons, not copied textbook passages or native reviews.
The main source-lesson builder assigns stable IDs and records their page references.
"""

EXTRA_UNITS = [
    {
        "unit": 2,
        "stage": "pre-a1",
        "grammar": "pronouns",
        "concept": "pronouns",
        "sources": [("source-07", 8), ("source-08", 1), ("source-08", 2)],
        "title": "Hallo, ik ben Sara|Hello, I am Sara|سلام، من سارا هستم",
        "focus": "Met ik en hij een naam en een persoon noemen.|Giving a name and identifying a person with ik and hij.|گفتن نام و معرفی یک فرد با ik و hij.",
        "paragraphs": [
            "Hallo. Ik ben Sara. Mijn naam is Sara.|Hello. I am Sara. My name is Sara.|سلام. من سارا هستم. نام من سارا است.",
            "Dit is Amir. Hij zit in de klas. Ik zit ook in de klas.|This is Amir. He is in the classroom. I am in the classroom too.|این امیر است. او در کلاس است. من هم در کلاس هستم.",
        ],
        "listening": "Hallo, ik ben Lina. Ik woon in Brugge. Dag!|Hello, I am Lina. I live in Bruges. Bye!|سلام، من لینا هستم. در بروژ زندگی می‌کنم. خداحافظ!",
        "reading_q": [
            (
                "Wat is haar naam?|What is her name?|نام او چیست؟",
                "Sara|Sara|سارا",
                "Lina|Lina|لینا",
                "Ze zegt: Mijn naam is Sara.|She says: My name is Sara.|او می‌گوید: نام من سارا است.",
            ),
            (
                "Waar is Amir?|Where is Amir?|امیر کجاست؟",
                "In de klas.|In the classroom.|در کلاس.",
                "In de winkel.|In the shop.|در فروشگاه.",
                "De tekst zegt: Hij zit in de klas.|The text says: He is in the classroom.|متن می‌گوید: او در کلاس است.",
            ),
        ],
        "listening_q": [
            (
                "Welke naam hoor je nu?|Which name do you hear now?|اکنون چه نامی می‌شنوید؟",
                "Lina|Lina|لینا",
                "Sara|Sara|سارا",
                "De nieuwe spreker zegt: Ik ben Lina.|The new speaker says: I am Lina.|گوینده تازه می‌گوید: من لینا هستم.",
            ),
            (
                "Waar woont Lina?|Where does Lina live?|لینا کجا زندگی می‌کند؟",
                "Brugge|Bruges|بروژ",
                "Gent|Ghent|خنت",
                "Je hoort: Ik woon in Brugge.|You hear: I live in Bruges.|می‌شنوید: در بروژ زندگی می‌کنم.",
            ),
        ],
        "speaking": "Zeg hallo. Zeg je naam en je stad. Je mag Lina en Brugge gebruiken.|Say hello. Say your name and city. You may use Lina and Bruges.|سلام کنید. نام و شهرتان را بگویید. می‌توانید از لینا و بروژ استفاده کنید.",
        "spoken_sample": "Hallo. Ik ben Lina. Ik woon in Brugge.|Hello. I am Lina. I live in Bruges.|سلام. من لینا هستم. در بروژ زندگی می‌کنم.",
        "writing": "Schrijf hallo, een naam en een stad. Je mag Lina en Brugge gebruiken.|Write hello, a name and a city. You may use Lina and Bruges.|سلام، یک نام و یک شهر بنویسید. می‌توانید از لینا و بروژ استفاده کنید.",
        "written_sample": "Hallo. Ik ben Lina. Ik woon in Brugge.|Hello. I am Lina. I live in Bruges.|سلام. من لینا هستم. در بروژ زندگی می‌کنم.",
        "bounds": (3, 20),
        "criteria": [
            "Begin met een groet.|Begin with a greeting.|با سلام آغاز کنید.",
            "Noem een naam en een stad.|Give a name and a city.|یک نام و یک شهر بگویید.",
        ],
        "examples": [
            "Ik ben Sara.|I am Sara.|من سارا هستم.",
            "Hij is Amir.|He is Amir.|او امیر است.",
            "Mijn naam is Lina.|My name is Lina.|نام من لینا است.",
        ],
        "grammar_q": (
            "Je noemt jezelf. Vul aan: … ben Sara.|You introduce yourself. Complete: … ben Sara.|خودتان را معرفی می‌کنید. کامل کنید: … ben Sara.",
            "Ik|Ik|Ik",
            "Hij|Hij|Hij",
            "Je gebruikt ik voor jezelf: Ik ben Sara.|Use ik for yourself: Ik ben Sara.|برای خودتان از ik استفاده می‌کنید: Ik ben Sara.",
        ),
        "words": [
            ("hallo", "Een groet als je iemand ontmoet.|A greeting when you meet someone.|سلام هنگام دیدن کسی.", "Hallo, ik ben Sara.|Hello, I am Sara.|سلام، من سارا هستم."),
            ("de naam", "Hoe iemand heet.|What someone is called.|نام یک فرد.", "Mijn naam is Sara.|My name is Sara.|نام من سارا است."),
            ("de klas", "De groep leerlingen of de ruimte voor de les.|The group of learners or the room for the lesson.|گروه زبان‌آموزان یا اتاق درس؛ کلاس.", "Hij zit in de klas.|He is in the classroom.|او در کلاس است."),
        ],
    },
    {
        "unit": 2,
        "stage": "a1",
        "grammar": "spatial-prepositions",
        "concept": "spatial-prepositions",
        "sources": [("source-07", 2)],
        "title": "Waar ligt het boek?|Where is the book?|کتاب کجاست؟",
        "focus": "Met op, onder en naast zeggen waar iets staat of ligt.|Saying where something is with op, onder and naast.|گفتن جای وسایل با op، onder و naast.",
        "paragraphs": [
            "Rosa komt in de klas. De tafel staat naast de deur. Haar boek ligt op de tafel. Haar tas staat onder de stoel.|Rosa enters the classroom. The table is next to the door. Her book is on the table. Her bag is under the chair.|روزا وارد کلاس می‌شود. میز کنار در است. کتابش روی میز است. کیفش زیر صندلی است.",
            "Rosa gaat even naar buiten. Amir blijft in de klas. Hij maakt plaats op de tafel. Hij verplaatst het boek en de tas.|Rosa goes outside for a moment. Amir stays in the classroom. He makes space on the table. He moves the book and the bag.|روزا برای لحظه‌ای بیرون می‌رود. امیر در کلاس می‌ماند. روی میز جا باز می‌کند. کتاب و کیف را جابه‌جا می‌کند.",
        ],
        "listening": "Dag Rosa. Het boek ligt nu onder de tafel. De tas staat op de stoel. De tafel staat nog naast de deur.|Hi Rosa. The book is now under the table. The bag is on the chair. The table is still next to the door.|سلام روزا. کتاب اکنون زیر میز است. کیف روی صندلی است. میز همچنان کنار در است.",
        "reading_q": [
            (
                "Waar staat de tafel?|Where is the table?|میز کجاست؟",
                "Naast de deur.|Next to the door.|کنار در.",
                "Voor het raam.|In front of the window.|جلوی پنجره.",
                "De tekst zegt dat de tafel naast de deur staat.|The text says the table is next to the door.|متن می‌گوید میز کنار در است.",
            ),
            (
                "Waar ligt het boek eerst?|Where is the book at first?|کتاب ابتدا کجاست؟",
                "Op de tafel.|On the table.|روی میز.",
                "Onder de stoel.|Under the chair.|زیر صندلی.",
                "Voor Rosa naar buiten gaat, ligt het boek op de tafel.|Before Rosa goes outside, the book is on the table.|پیش از بیرون رفتن روزا، کتاب روی میز است.",
            ),
        ],
        "listening_q": [
            (
                "Waar ligt het boek nu?|Where is the book now?|کتاب اکنون کجاست؟",
                "Onder de tafel.|Under the table.|زیر میز.",
                "Op de tafel.|On the table.|روی میز.",
                "De nieuwe boodschap zegt: Het boek ligt nu onder de tafel.|The new message says: The book is now under the table.|پیام تازه می‌گوید: کتاب اکنون زیر میز است.",
            ),
            (
                "Waar staat de tas nu?|Where is the bag now?|کیف اکنون کجاست؟",
                "Op de stoel.|On the chair.|روی صندلی.",
                "Onder de stoel.|Under the chair.|زیر صندلی.",
                "Je hoort dat de tas op de stoel staat.|You hear that the bag is on the chair.|می‌شنوید که کیف روی صندلی است.",
            ),
        ],
        "speaking": "Vertel Rosa waar het boek, de tas en de tafel nu zijn. Gebruik de nieuwe boodschap.|Tell Rosa where the book, bag and table are now. Use the new message.|به روزا بگویید کتاب، کیف و میز اکنون کجا هستند. از پیام تازه استفاده کنید.",
        "spoken_sample": "Je boek ligt onder de tafel. Je tas staat op de stoel. De tafel staat naast de deur.|Your book is under the table. Your bag is on the chair. The table is next to the door.|کتابت زیر میز است. کیفت روی صندلی است. میز کنار در است.",
        "writing": "Schrijf een kort bericht aan Rosa. Geef de nieuwe plaats van het boek en de tas. Noem ook de plaats van de tafel.|Write a short message to Rosa. Give the new location of the book and bag. Also say where the table is.|پیامی کوتاه به روزا بنویسید. جای تازه کتاب و کیف را بگویید. جای میز را هم ذکر کنید.",
        "written_sample": "Dag Rosa, je boek ligt nu onder de tafel. Je tas staat op de stoel. De tafel staat naast de deur.|Hi Rosa, your book is now under the table. Your bag is on the chair. The table is next to the door.|سلام روزا، کتابت اکنون زیر میز است. کیفت روی صندلی است. میز کنار در است.",
        "bounds": (12, 35),
        "criteria": [
            "Geef de nieuwe plaats van het boek en de tas correct.|Give the new location of the book and bag correctly.|جای تازه کتاب و کیف را درست بیان کنید.",
            "Gebruik op, onder en naast voor de drie plaatsen.|Use op, onder and naast for the three locations.|برای سه مکان از op، onder و naast استفاده کنید.",
        ],
        "examples": [
            "Het boek ligt op de tafel.|The book is on the table.|کتاب روی میز است.",
            "Het boek ligt onder de tafel.|The book is under the table.|کتاب زیر میز است.",
            "De tafel staat naast de deur.|The table is next to the door.|میز کنار در است.",
        ],
        "grammar_q": (
            "Het boek ligt beneden, niet bovenop de tafel. Vul aan: Het boek ligt … de tafel.|The book is below, not on top of the table. Complete: Het boek ligt … de tafel.|کتاب پایین است، نه روی میز. کامل کنید: Het boek ligt … de tafel.",
            "onder|onder|onder",
            "op|op|op",
            "Onder betekent lager dan de tafel, niet op het tafelblad.|Onder means below the table, not on the tabletop.|Onder یعنی پایین‌تر از میز، نه روی سطح آن.",
        ),
        "words": [
            ("het boek", "Iets met bladzijden om te lezen.|Something with pages to read.|چیزی با صفحه‌هایی برای خواندن؛ کتاب.", "Het boek ligt onder de tafel.|The book is under the table.|کتاب زیر میز است."),
            ("de tafel", "Een meubel met een blad en poten.|A piece of furniture with a top and legs.|وسیله‌ای با سطح و پایه؛ میز.", "De tafel staat naast de deur.|The table is next to the door.|میز کنار در است."),
            ("de stoel", "Een meubel waarop je zit.|A piece of furniture you sit on.|وسیله‌ای برای نشستن؛ صندلی.", "De tas staat op de stoel.|The bag is on the chair.|کیف روی صندلی است."),
        ],
    },
    {
        "unit": 2,
        "stage": "pre-a2",
        "grammar": "modal",
        "concept": "modal-verbs",
        "sources": [("source-07", 4), ("source-06", 72)],
        "title": "Mag ik met Rosa werken?|May I work with Rosa?|می‌توانم با روزا کار کنم؟",
        "focus": "Met moeten, mogen en kunnen een opdracht en een hulpvraag verduidelijken.|Clarifying a task and a request for help with moeten, mogen and kunnen.|روشن کردن تکلیف و درخواست کمک با moeten، mogen و kunnen.",
        "paragraphs": [
            "Amir zit in de klas. Hij heeft zijn boek bij zich. Op het bord staat: Maak voor morgen twee oefeningen. Amir wil samen met Rosa werken. Hij weet niet of dat mag.|Amir is in the classroom. He has his book with him. The board says: Complete two exercises for tomorrow. Amir wants to work with Rosa. He does not know whether that is allowed.|امیر در کلاس است. کتابش همراهش است. روی تخته نوشته: برای فردا دو تمرین انجام دهید. امیر می‌خواهد با روزا کار کند. نمی‌داند اجازه دارد یا نه.",
            "De leraar begint te spreken. Amir begrijpt de opdracht niet goed. Hij wil iets vragen. Hij zegt: Kunt u wat langzamer spreken, alstublieft? De leraar herhaalt de opdracht.|The teacher starts speaking. Amir does not understand the task well. He wants to ask something. He says: Could you speak a little more slowly, please? The teacher repeats the task.|معلم شروع به صحبت می‌کند. امیر تکلیف را خوب نمی‌فهمد. می‌خواهد چیزی بپرسد. می‌گوید: لطفاً می‌توانید کمی آهسته‌تر صحبت کنید؟ معلم تکلیف را تکرار می‌کند.",
        ],
        "listening": "Amir, er is een kleine verandering. Voor morgen moet je drie oefeningen maken, niet twee. Je mag samen met Rosa werken. Neem je boek mee. Als iets niet duidelijk is, mag je een vraag stellen.|Amir, there is a small change. For tomorrow you must do three exercises, not two. You may work with Rosa. Bring your book. If something is unclear, you may ask a question.|امیر، یک تغییر کوچک داریم. برای فردا باید سه تمرین انجام بدهی، نه دو تمرین. می‌توانی با روزا کار کنی. کتابت را بیاور. اگر چیزی روشن نیست، می‌توانی سؤال بپرسی.",
        "reading_q": [
            (
                "Hoeveel oefeningen staan er eerst op het bord?|How many exercises are on the board at first?|ابتدا چند تمرین روی تخته نوشته شده است؟",
                "Twee.|Two.|دو.",
                "Drie.|Three.|سه.",
                "Op het bord staat eerst: Maak voor morgen twee oefeningen.|The board initially says: Complete two exercises for tomorrow.|ابتدا روی تخته نوشته: برای فردا دو تمرین انجام دهید.",
            ),
            (
                "Wat vraagt Amir aan de leraar?|What does Amir ask the teacher?|امیر از معلم چه می‌خواهد؟",
                "Om wat langzamer te spreken.|To speak a little more slowly.|کمی آهسته‌تر صحبت کند.",
                "Om de les vroeger te stoppen.|To finish the lesson earlier.|کلاس را زودتر تمام کند.",
                "Amir begrijpt de opdracht niet goed en vraagt om langzamer te spreken.|Amir does not understand the task well and asks the teacher to speak more slowly.|امیر تکلیف را خوب نمی‌فهمد و می‌خواهد معلم آهسته‌تر صحبت کند.",
            ),
        ],
        "listening_q": [
            (
                "Hoeveel oefeningen moet Amir nu maken?|How many exercises must Amir do now?|امیر اکنون باید چند تمرین انجام دهد؟",
                "Drie.|Three.|سه.",
                "Twee.|Two.|دو.",
                "De leraar verandert de opdracht van twee naar drie oefeningen.|The teacher changes the task from two to three exercises.|معلم تعداد تمرین‌ها را از دو به سه تغییر می‌دهد.",
            ),
            (
                "Mag Amir met Rosa werken?|May Amir work with Rosa?|آیا امیر اجازه دارد با روزا کار کند؟",
                "Ja, ze mogen samenwerken.|Yes, they may work together.|بله، می‌توانند با هم کار کنند.",
                "Nee, hij moet alleen werken.|No, he must work alone.|نه، باید تنها کار کند.",
                "De leraar zegt: Je mag samen met Rosa werken.|The teacher says: You may work with Rosa.|معلم می‌گوید: می‌توانی با روزا کار کنی.",
            ),
        ],
        "speaking": "Bevestig als Amir hoeveel oefeningen je nu moet maken en met wie je mag werken. Vraag de leraar beleefd om de opdracht nog eens langzaam te herhalen.|As Amir, confirm how many exercises you must now do and who you may work with. Politely ask the teacher to repeat the task slowly once more.|در نقش امیر تعداد تازه تمرین‌ها و کسی را که می‌توانید با او کار کنید تأیید کنید. مؤدبانه از معلم بخواهید تکلیف را یک بار دیگر آهسته تکرار کند.",
        "spoken_sample": "Ik moet voor morgen drie oefeningen maken. Ik mag met Rosa werken. Kunt u de opdracht nog eens langzaam herhalen, alstublieft? Dan weet ik wat ik moet doen.|I must do three exercises for tomorrow. I may work with Rosa. Could you repeat the task slowly once more, please? Then I will know what I must do.|باید برای فردا سه تمرین انجام بدهم. می‌توانم با روزا کار کنم. لطفاً می‌توانید تکلیف را یک بار دیگر آهسته تکرار کنید؟ آن وقت می‌دانم باید چه کار کنم.",
        "writing": "Schrijf als Amir een kort bericht aan de leraar. Bevestig de drie oefeningen en de toestemming om met Rosa te werken. Vraag beleefd om de opdracht nog eens te herhalen.|As Amir, write a short message to the teacher. Confirm the three exercises and permission to work with Rosa. Politely ask for the task to be repeated once more.|در نقش امیر پیامی کوتاه به معلم بنویسید. سه تمرین و اجازه کار با روزا را تأیید کنید. مؤدبانه بخواهید تکلیف یک بار دیگر تکرار شود.",
        "written_sample": "Beste leraar, ik moet voor morgen drie oefeningen maken. Ik mag met Rosa werken. Kunt u de opdracht nog eens herhalen, alstublieft? Ik wil zeker zijn dat ik alles begrijp. Dank u wel! Amir.|Dear teacher, I must do three exercises for tomorrow. I may work with Rosa. Could you repeat the task once more, please? I want to be sure I understand everything. Thank you! Amir.|معلم گرامی، باید برای فردا سه تمرین انجام بدهم. می‌توانم با روزا کار کنم. لطفاً می‌توانید تکلیف را یک بار دیگر تکرار کنید؟ می‌خواهم مطمئن شوم همه چیز را می‌فهمم. متشکرم! امیر.",
        "bounds": (15, 65),
        "criteria": [
            "Bevestig de drie oefeningen en de toestemming om met Rosa te werken.|Confirm the three exercises and permission to work with Rosa.|سه تمرین و اجازه کار با روزا را تأیید کنید.",
            "Vraag beleefd om herhaling van de opdracht.|Politely ask for the task to be repeated.|مؤدبانه بخواهید تکلیف تکرار شود.",
        ],
        "examples": [
            "Ik moet drie oefeningen maken.|I must do three exercises.|باید سه تمرین انجام بدهم.",
            "Ik mag met Rosa werken.|I may work with Rosa.|می‌توانم با روزا کار کنم.",
            "Kunt u de opdracht herhalen?|Could you repeat the task?|می‌توانید تکلیف را تکرار کنید؟",
        ],
        "grammar_q": (
            "Er is toestemming, geen verplichting. Vul aan: Ik … met Rosa werken.|There is permission, not an obligation. Complete: Ik … met Rosa werken.|اجازه داده شده، نه اجبار. کامل کنید: Ik … met Rosa werken.",
            "mag|mag|mag",
            "moet|moet|moet",
            "Mag geeft hier toestemming; moet geeft een verplichting.|Mag expresses permission here; moet expresses an obligation.|اینجا mag اجازه را بیان می‌کند و moet الزام را.",
        ),
        "words": [
            ("het boek", "Een werk met bladzijden om te lezen.|A work with pages to read.|اثری با صفحه‌هایی برای خواندن؛ کتاب.", "Ik moet mijn boek meenemen.|I must bring my book.|باید کتابم را بیاورم."),
            ("spreken", "Met je stem woorden zeggen.|Saying words with your voice.|گفتن واژه‌ها با صدا؛ صحبت کردن.", "Kunt u langzamer spreken?|Could you speak more slowly?|می‌توانید آهسته‌تر صحبت کنید؟"),
            ("vragen", "Iets zeggen om informatie of hulp te krijgen.|Saying something to obtain information or help.|گفتن چیزی برای دریافت اطلاعات یا کمک؛ پرسیدن.", "Ik wil iets vragen.|I want to ask something.|می‌خواهم چیزی بپرسم."),
        ],
    },
]
