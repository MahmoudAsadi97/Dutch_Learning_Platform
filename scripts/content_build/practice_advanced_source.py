"""Original follow-up situations for the advanced four-skill spiral.

Each numbered scene is paired with the corresponding original C1 library story.
Fields: new spoken fact, requested next action, supported reading interpretation,
and a plausible but unsupported reading interpretation. NL | EN | FA.
These are editorial drafts, not reviewed or certified language content.
"""

SCENES = {}


def add(number, fact, action, interpretation, alternative):
    def tri(value):
        values = value.split(" | ")
        assert len(values) == 3, (number, value)
        return dict(zip(("nl", "en", "fa"), values, strict=True))
    SCENES[number] = {
        "fact": tri(fact), "action": tri(action),
        "interpretation": tri(interpretation), "alternative": tri(alternative),
    }


add(1,
    "De verplaatste banken krijgen in de late namiddag toch opnieuw zon. | The relocated benches are back in the sun in late afternoon. | نیمکت‌های جابه‌جا‌شده اواخر بعدازظهر دوباره آفتاب می‌گیرند.",
    "We controleren de schaduw op verschillende uren voordat we opnieuw verplaatsen. | We check the shade at different times before moving them again. | پیش از جابه‌جایی دوباره، سایه را در ساعت‌های مختلف بررسی می‌کنیم.",
    "Inspraak leidde tot een aanpassing binnen de bestaande bevoegdheid en middelen. | Consultation led to a change within the existing authority and resources. | مشارکت مردم به تغییری در محدودهٔ اختیار و امکانات موجود انجامید.",
    "De ontwerpster kreeg door de inspraak alsnog toestemming voor extra bomen. | The consultation eventually authorised the designer to add trees. | نظرخواهی در نهایت به طراح اجازهٔ کاشت درخت اضافی داد.")
add(2,
    "Een leverancier gebruikt een bredere kar dan op de eerste foto stond. | A supplier uses a wider trolley than the one in the first photograph. | یکی از تأمین‌کنندگان از چرخی پهن‌تر از عکس اول استفاده می‌کند.",
    "We testen de doorgang met die kar voordat we de rekken vastzetten. | We test the passage with that trolley before fixing the racks in place. | پیش از نصب قطعی پایه‌ها، مسیر را با همان چرخ امتحان می‌کنیم.",
    "Fietsparkeren en leveringen bleken met een gerichte aanpassing verenigbaar. | A targeted adjustment made bicycle parking and deliveries compatible. | تغییر مشخصی امکان سازگاری پارک دوچرخه و تحویل کالا را فراهم کرد.",
    "Het bezwaar werd opgelost door het fietsparkeren helemaal te schrappen. | The objection was resolved by removing bicycle parking entirely. | اعتراض با حذف کامل پارک دوچرخه حل شد.")
add(3,
    "Voor de tweede zaterdag ontbreekt nog een medewerker met een toegangssleutel. | The second Saturday still lacks a staff member with an access key. | برای شنبهٔ دوم هنوز کارمندی با کلید ورودی تعیین نشده است.",
    "Personeelszaken en gebouwbeheer bevestigen samen wie het gebouw opent. | Personnel and building management jointly confirm who opens the building. | امور کارکنان و مدیریت ساختمان با هم مسئول بازکردن ساختمان را تأیید می‌کنند.",
    "Een toegelaten proef is pas uitvoerbaar wanneer de praktische voorwaarden kloppen. | A permitted trial becomes feasible only when its practical conditions are met. | مجازبودن یک آزمایش به‌تنهایی کافی نیست؛ شرایط اجرایی نیز باید فراهم باشد.",
    "De beleidsruimte maakte verdere afspraken over personeel en toegang overbodig. | Policy discretion made further staffing and access arrangements unnecessary. | اختیار اجرایی، هماهنگی دربارهٔ کارکنان و ورود را غیرضروری کرد.")
add(4,
    "De ochtendleveringen blijken op woensdag een halfuur langer te duren. | Morning deliveries turn out to last half an hour longer on Wednesdays. | تحویل‌های صبح چهارشنبه نیم ساعت بیشتر طول می‌کشند.",
    "We bespreken een apart beginuur voor woensdag met beide straten. | We discuss a separate Wednesday starting time with both streets. | ساعت شروع جداگانهٔ چهارشنبه را با ساکنان هر دو خیابان بررسی می‌کنیم.",
    "De omleiding gaf ook afwezige bewoners een legitiem belang bij de beslissing. | The diversion gave absent residents a legitimate stake in the decision too. | مسیر انحرافی به ساکنان غایب نیز حق مشارکت در تصمیم می‌داد.",
    "Alleen de bewoners die op de eerste vergadering spraken hadden een relevant belang. | Only residents speaking at the first meeting had a relevant interest. | فقط کسانی که در جلسهٔ نخست صحبت کردند ذی‌نفع بودند.")
add(5,
    "Een afgewezen vereniging vraagt waarom bereik zwaarder woog dan lage kosten. | An unsuccessful association asks why reach outweighed low costs. | انجمنی که انتخاب نشده می‌پرسد چرا گسترهٔ مخاطبان مهم‌تر از هزینهٔ کم بوده است.",
    "De commissie licht de weging toe met dezelfde criteria als bij de selectie. | The committee explains the weighting using the original selection criteria. | کمیته وزن معیارها را با همان معیارهای انتخاب اولیه توضیح می‌دهد.",
    "Een navolgbare motivering kan begrip vergroten zonder iedereen tevreden te stellen. | A traceable explanation can improve understanding without satisfying everyone. | توضیح قابل‌پیگیری می‌تواند درک را بیشتر کند، حتی اگر همه راضی نباشند.",
    "Publicatie van de vergelijking bewees dat iedereen de uitkomst ideaal vond. | Publishing the comparison proved that everyone considered the outcome ideal. | انتشار مقایسه ثابت کرد که همه نتیجه را ایدئال می‌دانستند.")
add(6,
    "Een vereniging begrijpt het einduur als het einde van de muziek, niet van het opruimen. | One association interprets the deadline as the end of music, not of clearing up. | انجمنی ساعت پایان را پایان موسیقی می‌داند، نه پایان جمع‌کردن وسایل.",
    "We leggen afzonderlijk vast wanneer muziek stopt en wanneer opruimen eindigt. | We specify separately when music stops and when clearing up ends. | زمان پایان موسیقی و پایان جمع‌کردن وسایل را جدا مشخص می‌کنیم.",
    "Het gekozen einduur beperkt hinder met minder gevolgen dan een algemeen verbod. | The chosen finishing time reduces nuisance with fewer consequences than a general ban. | ساعت پایان مشخص، مزاحمت را با پیامدهای کمتری از ممنوعیت عمومی کاهش می‌دهد.",
    "Het bestuur behandelde alle verenigingen als veroorzakers van dezelfde klachten. | The board treated every association as responsible for the same complaints. | مدیریت همهٔ انجمن‌ها را مسئول همان شکایت‌ها دانست.")
add(7,
    "Een proeflezer begrijpt de nieuwe reden, maar weet nog niet waar hij het document indient. | A test reader understands the new reason but still does not know where to submit the document. | خوانندهٔ آزمایشی دلیل جدید را می‌فهمد، اما هنوز نمی‌داند مدرک را کجا تحویل دهد.",
    "We voegen het juiste contactpunt toe en laten de brief opnieuw nalezen. | We add the correct contact point and have the letter checked again. | محل تماس درست را اضافه می‌کنیم و نامه را دوباره برای بازخوانی می‌دهیم.",
    "Begrijpelijke motivering omvat ook een bruikbare vervolgstap voor de ontvanger. | An understandable explanation also includes a usable next step for the recipient. | توضیح روشن باید گام بعدیِ قابل‌انجام برای گیرنده را نیز مشخص کند.",
    "De aanpassing verplichtte iedereen om meteen alle oude dossiers te herschrijven. | The change required everyone to rewrite all old files immediately. | تغییر همه را ملزم کرد فوراً تمام پرونده‌های قدیمی را بازنویسی کنند.")
add(8,
    "Eén lid kan zijn nieuwe pas pas twee dagen na de tijdelijke einddatum ophalen. | One member can collect the new pass only two days after the temporary deadline. | یک عضو دو روز پس از پایان مهلت موقت می‌تواند کارت جدیدش را بگیرد.",
    "We vragen de verantwoordelijke om een vastgelegde individuele oplossing. | We ask the person responsible for a documented individual solution. | از مسئول مربوط راه‌حل فردیِ ثبت‌شده می‌خواهیم.",
    "De tijdelijke toegang combineerde continuïteit met controle en een duidelijke grens. | Temporary access combined continuity with verification and a clear limit. | ورود موقت، تداوم دسترسی را با کنترل و محدودیت روشن همراه کرد.",
    "Het oude papieren register werd een blijvende vervanging voor de nieuwe passen. | The old paper register permanently replaced the new passes. | دفتر کاغذی قدیمی برای همیشه جای کارت‌های جدید را گرفت.")
add(9,
    "De hersteldatum is verstreken en de lift werkt nog altijd niet. | The repair date has passed and the lift still does not work. | موعد تعمیر گذشته و آسانسور هنوز کار نمی‌کند.",
    "De verantwoordelijke registreert de vertraging en geeft een nieuwe onderbouwde planning. | The responsible person records the delay and provides a new justified schedule. | مسئول تأخیر را ثبت می‌کند و برنامهٔ تازه‌ای با توضیح ارائه می‌دهد.",
    "Registratie met een verantwoordelijke maakt opvolging mogelijk, maar herstelt de lift niet vanzelf. | Recording responsibility enables follow-up but does not repair the lift by itself. | ثبت مسئول، پیگیری را ممکن می‌کند اما خودبه‌خود آسانسور را تعمیر نمی‌کند.",
    "Omdat meldingen mondeling waren toegelaten, waren ze ook allemaal terug te vinden. | Because oral reports were permitted, every report could be retrieved. | چون گزارش شفاهی مجاز بود، همهٔ گزارش‌ها نیز قابل‌بازیابی بودند.")
add(10,
    "Beide verenigingen willen dezelfde extra avond vóór een gezamenlijk optreden. | Both associations want the same additional evening before a joint performance. | هر دو انجمن پیش از اجرای مشترک یک شب اضافهٔ یکسان می‌خواهند.",
    "We vergelijken hun noodzakelijke repetitietijd en zoeken een eenmalige verdeling. | We compare their essential rehearsal time and seek a one-off allocation. | زمان ضروری تمرین دو گروه را مقایسه می‌کنیم و تقسیم موقتی می‌یابیم.",
    "Aandacht voor feitelijke behoeften doorbrak een conflict over vaste aanspraken. | Attention to actual needs broke a conflict over fixed claims. | توجه به نیاز واقعی، بن‌بست بر سر سهم ثابت را شکست.",
    "De oplossing werkte omdat beide verenigingen uiteindelijk elke vrijdag nodig hadden. | The solution worked because both associations ultimately needed every Friday. | راه‌حل مؤثر بود چون هر دو انجمن در نهایت به تمام جمعه‌ها نیاز داشتند.")

add(11,
    "De nieuwe thermometer toont koelte, maar enkele bezoekers vertrekken nog steeds vroeg. | The new thermometer shows cool conditions, but some visitors still leave early. | دماسنج جدید خنکی را نشان می‌دهد، اما برخی بازدیدکنندگان همچنان زود می‌روند.",
    "We vragen naar andere vertrekredenen voordat we warmte als verklaring behouden. | We ask about other reasons for leaving before retaining heat as the explanation. | پیش از پذیرفتن گرما به‌عنوان علت، دربارهٔ دلیل‌های دیگر رفتن می‌پرسیم.",
    "Een gebrekkige meting kan een aannemelijke hypothese ten onrechte ondersteunen. | A faulty measurement can wrongly support a plausible hypothesis. | اندازه‌گیری نادرست می‌تواند فرضیه‌ای پذیرفتنی را به‌اشتباه تأیید کند.",
    "De eerste waarneming bewees dat een koelinstallatie de enige oplossing was. | The first observation proved that cooling equipment was the only solution. | مشاهدهٔ نخست ثابت کرد سیستم سرمایش تنها راه‌حل است.")
add(12,
    "De grotere proef levert uiteenlopende resultaten op bij beginnende en ervaren gebruikers. | The larger trial produces different results for novice and experienced users. | آزمایش بزرگ‌تر برای کاربران تازه‌کار و باتجربه نتیجه‌های متفاوتی دارد.",
    "We rapporteren beide groepen apart en behouden de onzekerheidsmarges. | We report both groups separately and retain the uncertainty intervals. | هر دو گروه را جدا گزارش می‌کنیم و دامنه‌های عدم‌قطعیت را نگه می‌داریم.",
    "Een herhaalbare score hoeft niet de bedoelde praktische vaardigheid te meten. | A repeatable score need not measure the intended practical skill. | امتیاز تکرارپذیر لزوماً مهارت عملی موردنظر را نمی‌سنجد.",
    "Het benoemen van pictogrammen bleek hetzelfde als zelfstandig boeken vinden. | Naming pictograms proved equivalent to independently finding books. | نام‌بردن نمادها با پیداکردن مستقل کتاب یکسان از آب درآمد.")
add(13,
    "Via werkgevers antwoorden vooral mensen met een kantoorfunctie. | Responses through employers mainly come from office workers. | پاسخ‌های دریافت‌شده از طریق کارفرما بیشتر از کارکنان دفتری است.",
    "We zoeken ook werknemers met wisselende diensten en vermelden de wervingskanalen. | We also seek shift workers and state the recruitment channels. | سراغ کارکنان شیفتی نیز می‌رویم و مسیرهای جذب پاسخ‌دهنده را ذکر می‌کنیم.",
    "Een vragenlijst op één locatie kan mensen uitsluiten die men juist wil bereiken. | A questionnaire at one location can exclude the people it aims to reach. | پرسش‌نامه در یک محل ممکن است همان گروه هدف را کنار بگذارد.",
    "De eerste balievragenlijst vertegenwoordigde afwezige werknemers voldoende. | The initial counter questionnaire represented absent workers adequately. | پرسش‌نامهٔ اولیهٔ باجه به‌قدر کافی نمایندهٔ کارکنان غایب بود.")
add(14,
    "Het derde filiaal telt afgebroken zoekpogingen opnieuw op een andere manier. | The third branch once again counts abandoned searches differently. | شعبهٔ سوم باز هم جست‌وجوهای نیمه‌تمام را به روش دیگری می‌شمارد.",
    "We spreken de telregels af voordat we de filialen vergelijken. | We agree on counting rules before comparing branches. | پیش از مقایسهٔ شعبه‌ها، دربارهٔ قواعد شمارش توافق می‌کنیم.",
    "Gedeelde opdrachten volstaan niet zonder dezelfde verwerking van de uitkomsten. | Shared tasks are insufficient without consistent processing of outcomes. | تکلیف‌های یکسان بدون پردازش یکسان نتیجه‌ها کافی نیستند.",
    "De verschillen verdwenen alleen doordat de snelste gebruikers werden behouden. | The differences disappeared only because the fastest users were retained. | اختلاف‌ها فقط به‌خاطر نگه‌داشتن سریع‌ترین کاربران از بین رفتند.")
add(15,
    "De nieuwe parkeerplek voor karren blokkeert tijdens leveringen een zijdeur. | The new trolley parking space blocks a side door during deliveries. | جای جدید چرخ‌ها هنگام تحویل کالا یک درِ جانبی را می‌بندد.",
    "We testen de volledige route tijdens een levering en verplaatsen de parkeerplek zo nodig. | We test the complete route during a delivery and relocate the parking space if needed. | مسیر کامل را هنگام تحویل آزمایش می‌کنیم و در صورت نیاز جای چرخ‌ها را عوض می‌کنیم.",
    "Een uitzonderlijk slecht resultaat kan een vermijdbaar praktisch obstakel onthullen. | An exceptionally poor result can reveal an avoidable practical obstacle. | نتیجهٔ بسیار نامعمول می‌تواند مانع عملیِ قابل‌پیشگیری را آشکار کند.",
    "De lange wachttijd bewees dat de volledige herinrichting moest verdwijnen. | The long delay proved that the entire redesign had to be removed. | انتظار طولانی ثابت کرد کل چیدمان جدید باید حذف شود.")
add(16,
    "Het alarm gaat vooral af wanneer de tweede medewerker pauze heeft. | The alarm mainly sounds when the second worker is on a break. | هشدار بیشتر زمانی فعال می‌شود که کارمند دوم در استراحت است.",
    "We vergelijken wachttijd en pauzeplanning voordat we de drempel aanpassen. | We compare waiting times and break schedules before changing the threshold. | پیش از تغییر آستانه، زمان انتظار و برنامهٔ استراحت را مقایسه می‌کنیم.",
    "Een stabiele mediaan kan verhullen dat sommige bezoekers veel langer wachten. | A stable median can conceal much longer waits for some visitors. | میانهٔ ثابت می‌تواند انتظار بسیار طولانی‌ترِ برخی بازدیدکنندگان را پنهان کند.",
    "Omdat de mediaan gelijk bleef, waren alle individuele wachttijden onveranderd. | Because the median stayed constant, every individual wait was unchanged. | چون میانه ثابت ماند، زمان انتظار تک‌تک افراد هم تغییر نکرده بود.")
add(17,
    "Een nieuwe bezoeker begrijpt de trapmarkering, maar mist het bord bij de lift. | A new visitor understands the stair marking but misses the sign by the lift. | بازدیدکنندهٔ جدید علامت پله را می‌فهمد، اما تابلوی آسانسور را نمی‌بیند.",
    "We nemen ook de liftroute op in de volgende test met onbekende bezoekers. | We include the lift route in the next test with unfamiliar visitors. | مسیر آسانسور را نیز در آزمایش بعدی با بازدیدکنندگان ناآشنا می‌گنجانیم.",
    "Bekendheid met het gebouw kan ontbrekende informatie onzichtbaar maken in een test. | Familiarity with the building can hide missing information during a test. | آشنایی با ساختمان ممکن است کمبود اطلاعات را در آزمایش پنهان کند.",
    "De twintig ervaren bezoekers maakten een test met nieuwkomers overbodig. | The twenty experienced visitors made testing newcomers unnecessary. | بیست بازدیدکنندهٔ باتجربه، آزمایش با تازه‌واردها را غیرضروری کردند.")
add(18,
    "Na de installatie van de klok blijft één nacht per week een verbruikspiek bestaan. | After installing the timer, a consumption peak remains one night each week. | پس از نصب زمان‌سنج، یک شب در هفته هنوز اوج مصرف دیده می‌شود.",
    "We vergelijken die nacht met reserveringen en de instellingen van de ventilatie. | We compare that night with bookings and ventilation settings. | آن شب را با رزروها و تنظیمات تهویه مقایسه می‌کنیم.",
    "Verschillende informatiebronnen maakten een toetsbare technische verklaring mogelijk. | Several information sources enabled a testable technical explanation. | چند منبع اطلاعات، توضیح فنیِ آزمون‌پذیری را ممکن کردند.",
    "De piek verdween volledig zodra de meeteenheden waren omgerekend. | The peak disappeared completely once the units were converted. | اوج مصرف به‌محض تبدیل واحدها کاملاً ناپدید شد.")
add(19,
    "Twee nieuwe inschrijvingen hebben dezelfde naam maar behoren tot verschillende personen. | Two new registrations share a name but belong to different people. | دو ثبت‌نام جدید هم‌نام‌اند، اما به دو فرد متفاوت تعلق دارند.",
    "We controleren de identiteit zorgvuldig voordat we registraties samenvoegen. | We check identity carefully before merging registrations. | پیش از ادغام ثبت‌نام‌ها، هویت را دقیق بررسی می‌کنیم.",
    "Dubbele inschrijvingen kunnen de scheiding tussen proefgroepen aantasten. | Duplicate registrations can compromise separation between trial groups. | ثبت‌نام تکراری ممکن است تفکیک گروه‌های آزمایش را مختل کند.",
    "Het ontvangen van twee berichten bewees al dat de interventie werkte. | Receiving two messages already proved that the intervention worked. | دریافت دو پیام از قبل ثابت می‌کرد مداخله مؤثر بوده است.")
add(20,
    "De opdrachtgever wil de titel van het verslag positiever maken dan de uitkomst toelaat. | The sponsor wants the report title to be more positive than its result permits. | سفارش‌دهنده می‌خواهد عنوان گزارش از آنچه نتیجه اجازه می‌دهد مثبت‌تر باشد.",
    "We behouden de vooraf vastgelegde grens en beschrijven waarom de bevestiging uitbleef. | We retain the predefined threshold and describe why confirmation was absent. | حد ازپیش‌تعیین‌شده را نگه می‌داریم و دلیل تأییدنشدن را توضیح می‌دهیم.",
    "Ook een niet-bevestigde voorspelling levert informatie op voor verder onderzoek. | An unconfirmed prediction also provides information for further research. | پیش‌بینیِ تأییدنشده نیز برای پژوهش بعدی اطلاعات فراهم می‌کند.",
    "De mislukte bevestiging rechtvaardigde het achterhouden van het verslag. | Failed confirmation justified withholding the report. | تأییدنشدن، پنهان‌کردن گزارش را توجیه می‌کرد.")

add(21,
    "Het etiket is klaar, maar de late ploeg heeft geen toegang tot de voorraadlijst. | The label is ready, but the late shift cannot access the stock list. | برچسب آماده است، اما شیفت بعدی به فهرست موجودی دسترسی ندارد.",
    "We controleren bij de overdracht ook de toegang tot de benodigde informatie. | At handover we also check access to the necessary information. | هنگام تحویل شیفت، دسترسی به اطلاعات لازم را هم بررسی می‌کنیم.",
    "Een vaste overdracht voorkomt dat werkdruk onduidelijkheid voor de volgende ploeg veroorzaakt. | A fixed handover prevents workload from creating uncertainty for the next shift. | تحویل منظم شیفت مانع تبدیل فشار کار به ابهام برای گروه بعد می‌شود.",
    "Het probleem lag uitsluitend bij de onervarenheid van de nieuwe medewerker. | The problem lay solely in the new worker's inexperience. | مشکل فقط از بی‌تجربگی کارمند جدید بود.")
add(22,
    "De tweede collega krijgt vragen die buiten de afgesproken eenvoudige taken vallen. | The second colleague receives questions outside the agreed simple tasks. | همکار دوم با پرسش‌هایی خارج از کارهای سادهٔ توافق‌شده روبه‌رو می‌شود.",
    "We leggen een doorverwijsroute vast zonder Lina op haar vrije dag te bellen. | We establish an escalation route without calling Lina on her day off. | مسیر ارجاع را بدون تماس با لینا در روز آزادش مشخص می‌کنیم.",
    "Gedeelde toegang en duidelijke bevoegdheden verminderen afhankelijkheid van één persoon. | Shared access and clear authority reduce dependence on one person. | دسترسی مشترک و اختیار روشن، وابستگی به یک نفر را کاهش می‌دهد.",
    "Continuïteit werd bereikt doordat Lina voortaan op elke vrije dag bereikbaar bleef. | Continuity was achieved by keeping Lina available on every day off. | تداوم خدمت با در‌دسترس‌بودن لینا در تمام روزهای آزادش حاصل شد.")
add(23,
    "Een echt spoedgeval komt net na het vaste goedkeuringsmoment binnen. | A genuine emergency arrives just after the scheduled approval time. | موردی واقعاً فوری درست پس از زمان ثابت تأیید می‌رسد.",
    "We voorzien een omschreven uitzondering zonder elk dossier opnieuw dringend te noemen. | We define an exception without calling every file urgent again. | استثنایی مشخص می‌کنیم، بدون اینکه دوباره همهٔ پرونده‌ها را فوری بنامیم.",
    "Het team verhoogde de doorstroming door afhankelijkheden in plaats van labels te beoordelen. | The team improved throughput by assessing dependencies rather than labels. | گروه با توجه به وابستگی کارها، نه برچسب‌ها، جریان کار را بهتر کرد.",
    "Meer dossiers tegelijk beginnen bleek de oorzaak van de verbeterde afwerking. | Starting more files simultaneously caused the improved completion rate. | شروع هم‌زمان پرونده‌های بیشتر علت بهبود تکمیل کار بود.")
add(24,
    "Een tweede beginner slaat op de stappenkaart dezelfde controle over. | A second novice skips the same check on the instruction card. | تازه‌کار دوم هم همان بررسی را در کارت مراحل جا می‌اندازد.",
    "We laten de beginner voordoen waar de uitleg onduidelijk wordt. | We ask the novice to demonstrate where the explanation becomes unclear. | از تازه‌کار می‌خواهیم نشان دهد توضیح کجا مبهم می‌شود.",
    "Vakkennis overbrengen vraagt aandacht voor stappen die een expert vanzelfsprekend vindt. | Transferring expertise requires attention to steps an expert takes for granted. | انتقال مهارت نیازمند توجه به مراحلی است که متخصص بدیهی می‌داند.",
    "Noors vragen toonden aan dat haar collega geen technische deskundigheid had. | Noor's questions showed that her colleague lacked technical expertise. | پرسش‌های نور نشان داد همکارش تخصص فنی نداشت.")
add(25,
    "De aangewezen medewerker wordt ziek voordat de terugbelafspraak plaatsvindt. | The designated worker falls ill before the callback. | کارمند تعیین‌شده پیش از موعد تماس بیمار می‌شود.",
    "We wijzen expliciet een vervanger aan en bevestigen de overdracht. | We explicitly assign a substitute and confirm the handover. | جانشینی مشخص تعیین می‌کنیم و تحویل مسئولیت را تأیید می‌کنیم.",
    "Eigen fouten benoemen maakte gezamenlijke verbetering mogelijk zonder wederzijdse beschuldiging. | Acknowledging one's own mistakes enabled joint improvement without mutual blame. | بیان اشتباه شخصی، بهبود مشترک را بدون سرزنش متقابل ممکن کرد.",
    "Het vertrouwen herstelde doordat niemand nog over de fout sprak. | Trust returned because nobody mentioned the error again. | اعتماد بازگشت چون دیگر کسی از اشتباه حرف نزد.")
add(26,
    "Een nieuwe aanvraag past niet duidelijk binnen de afgesproken taakverdeling. | A new request does not clearly fit the agreed division of tasks. | درخواست تازه به‌روشنی در تقسیم کار توافق‌شده جای نمی‌گیرد.",
    "We bespreken de aanvraag met de medewerker voordat we haar taken uitbreiden. | We discuss the request with the worker before extending her duties. | پیش از افزایش وظایف، درخواست را با خود کارمند بررسی می‌کنیم.",
    "Duidelijke grenzen beschermen een geleidelijke terugkeer tegen sluipende taakuitbreiding. | Clear boundaries protect a gradual return from creeping expansion of duties. | مرزهای روشن از بازگشت تدریجی در برابر افزایش پنهانی وظایف محافظت می‌کنند.",
    "Personeelstekort maakte de afspraken over de terugkeer automatisch ongeldig. | Staff shortages automatically invalidated the return-to-work arrangements. | کمبود نیرو خودبه‌خود توافق‌های بازگشت به کار را بی‌اعتبار کرد.")
add(27,
    "De gezamenlijke start overlapt nu met het vertrekuur van een bestelwagen. | The joint briefing now overlaps with a delivery van's departure. | جلسهٔ مشترک آغاز شیفت حالا با زمان حرکت خودروی تحویل هم‌زمان است.",
    "We passen het overleguur aan zonder de informatie-uitwisseling te schrappen. | We adjust the briefing time without removing the information exchange. | زمان جلسه را تغییر می‌دهیم، بدون حذف تبادل اطلاعات.",
    "Een technisch herstel heeft pas effect wanneer aansluitende taken ook klaar zijn. | A technical repair takes effect only when connected tasks are ready too. | تعمیر فنی زمانی نتیجه می‌دهد که کارهای وابسته هم آماده باشند.",
    "De verpakking kon onafhankelijk van labels en technische beslissingen verderwerken. | Packaging could proceed independently of labels and technical decisions. | بسته‌بندی مستقل از برچسب‌ها و تصمیم‌های فنی می‌توانست ادامه یابد.")
add(28,
    "Bij een volgende oplevering vraagt de klant vlak vóór de afgesproken datum opnieuw een extra functie. | For a subsequent delivery the client again requests an additional feature just before the agreed date. | در تحویل بعدی، مشتری درست پیش از تاریخ توافق‌شده دوباره قابلیت اضافه‌ای می‌خواهد.",
    "We bespreken expliciet wat die wijziging betekent voor de overeengekomen levering. | We explicitly discuss what that change means for the agreed delivery. | صریح بررسی می‌کنیم این تغییر چه اثری بر تحویل توافق‌شده دارد.",
    "Het compromis ontstond door minimale gebruiksbehoeften van overige wensen te scheiden. | The compromise came from separating minimum operational needs from other wishes. | سازش با جداکردن نیازهای حداقلیِ استفاده از خواسته‌های دیگر حاصل شد.",
    "De klant kreeg alle nieuwe wensen op de oorspronkelijke datum toegezegd. | The client was promised all additional wishes by the original date. | به مشتری وعده داده شد همهٔ خواسته‌های جدید در تاریخ اولیه تحویل شوند.")
add(29,
    "Een nieuwe stagiair vraagt of hij een twijfel eerst vertrouwelijk mag voorleggen. | A new intern asks whether a concern can first be raised confidentially. | کارآموز تازه می‌پرسد آیا می‌تواند تردیدش را ابتدا محرمانه مطرح کند.",
    "We bieden een veilige vraagroute en houden inhoudelijke correcties bespreekbaar. | We offer a safe route for questions and keep substantive corrections discussable. | مسیر امنی برای پرسش فراهم می‌کنیم و اصلاح محتوایی را قابل‌گفت‌وگو نگه می‌داریم.",
    "Respect voor functies sluit gelijkwaardige aandacht voor ieders inhoudelijke bijdrage niet uit. | Respect for roles does not exclude equal attention to everyone's substantive contribution. | احترام به نقش‌ها با توجه برابر به نظر محتواییِ همه ناسازگار نیست.",
    "Loyaliteit betekende volgens de teamleider dat ervaren collega's nooit tegengesproken mochten worden. | The team leader defined loyalty as never contradicting experienced colleagues. | سرپرست وفاداری را مخالفت‌نکردن با همکاران باتجربه تعریف کرد.")
add(30,
    "De handleiding beschrijft een storing, maar de getoonde machine is intussen vervangen. | The manual describes a fault, but the machine pictured has since been replaced. | راهنما خرابی را توضیح می‌دهد، اما دستگاهِ تصویرشده تعویض شده است.",
    "We laten Karim en een tweede collega de nieuwe instructie samen controleren. | We have Karim and a second colleague check the updated instruction together. | از کریم و همکار دوم می‌خواهیم دستور تازه را با هم بررسی کنند.",
    "Gedeelde diagnosevragen ondersteunen zelfstandigheid beter dan afhankelijkheid van één expert. | Shared diagnostic questions support independence better than dependence on one expert. | پرسش‌های تشخیصی مشترک، استقلال را بهتر از وابستگی به یک متخصص تقویت می‌کنند.",
    "Kennisborging bestond uitsluitend uit het bewaren van Karims persoonlijke schriftje. | Knowledge preservation consisted solely of keeping Karim's private notebook. | حفظ دانش فقط به نگهداری دفتر شخصی کریم محدود شد.")

add(31,
    "Een lezer herkent op de nieuwe kaart een winkel die geen schade heeft gemeld. | A reader recognises a shop on the new map that reported no damage. | خواننده روی نقشهٔ جدید مغازه‌ای می‌بیند که خسارتی گزارش نکرده است.",
    "We controleren dat adres en corrigeren de kaart zichtbaar indien nodig. | We verify that address and visibly correct the map if necessary. | نشانی را بررسی می‌کنیم و در صورت لزوم نقشه را با اعلام اصلاح می‌کنیم.",
    "Broncontrole veranderde zowel het beeldmateriaal als de reikwijdte van het bericht. | Source verification changed both the images and the scope of the report. | بررسی منبع هم تصاویر و هم دامنهٔ خبر را تغییر داد.",
    "Het verhaal over drie winkels rechtvaardigde zonder meer de kop over het hele dorp. | The account of three shops automatically justified a headline about the whole village. | داستان سه مغازه بی‌چون‌وچرا عنوانی دربارهٔ کل روستا را توجیه می‌کرد.")
add(32,
    "Voor een geschreven versie van de afscheidstekst vraagt de collega om één herkenbaar voorbeeld bij de metafoor. | For a written version of the farewell text, the colleague requests one recognisable example alongside the metaphor. | همکار برای نسخهٔ نوشتاریِ متن خداحافظی، یک نمونهٔ آشنا کنار استعاره می‌خواهد.",
    "We noemen het overleg dat zij weer op gang bracht en vermijden de oude grap. | We mention the meeting she restarted and avoid the old joke. | به جلسه‌ای که او دوباره راه انداخت اشاره می‌کنیم و شوخی قدیمی را کنار می‌گذاریم.",
    "Bedoelde ironie kan bij een ander publiek als verwijt overkomen. | Intended irony can sound like criticism to a different audience. | طنزِ عمدی ممکن است برای مخاطبی دیگر به‌صورت سرزنش شنیده شود.",
    "De bedoeling van de schrijver garandeerde dat ieder publiek het compliment begreep. | The writer's intention guaranteed that every audience understood the compliment. | نیت نویسنده تضمین می‌کرد همهٔ مخاطبان تعریف را بفهمند.")
add(33,
    "In een nieuw interview is de opname helder, maar de vrijwilliger noemt een jaartal dat afwijkt van het archief. | In a new interview the recording is clear, but the volunteer gives a date that differs from the archive. | در مصاحبه‌ای تازه ضبط روشن است، اما داوطلب تاریخی متفاوت با آرشیو می‌گوید.",
    "We leggen de afwijking aan hem voor voordat we het fragment uitzenden. | We put the discrepancy to him before broadcasting the excerpt. | پیش از پخش بخش ضبط‌شده، اختلاف را با او مطرح می‌کنیم.",
    "Hoorbare getuigenissen en gecontroleerde feiten versterken elkaar in de reportage. | Audible testimony and checked facts reinforce each other in the report. | شهادت شنیدنی و واقعیت بررسی‌شده در گزارش یکدیگر را تقویت می‌کنند.",
    "De rustige opnameplek maakte controle van jaartallen overbodig. | The quiet recording location made checking dates unnecessary. | محل آرام ضبط، بررسی تاریخ‌ها را غیرضروری کرد.")
add(34,
    "De foutieve kop blijft zichtbaar in een gedeeld bericht op sociale media. | The incorrect headline remains visible in a shared social-media post. | عنوان غلط در پست بازنشرشدهٔ شبکهٔ اجتماعی باقی مانده است.",
    "We plaatsen ook daar de correctie met een verwijzing naar de ouderbrief. | We publish the correction there too, linking to the parent letter. | اصلاح را آنجا هم با ارجاع به نامهٔ والدین منتشر می‌کنیم.",
    "Een zichtbare rectificatie herstelt de context op de plek waar de fout verscheen. | A visible correction restores context where the error appeared. | اصلاح آشکار، زمینه را در محل انتشار خطا بازمی‌گرداند.",
    "De directeur bevestigde dat alle lessen tot maandag waren geschrapt. | The head confirmed that all lessons were cancelled until Monday. | مدیر تأیید کرد تمام کلاس‌ها تا دوشنبه لغو شده‌اند.")
add(35,
    "Bij een latere, vergelijkbare ruzie is de verontschuldiging alleen privé verstuurd, terwijl de beschuldiging in de groepschat staat. | In a later, similar dispute, the apology was sent only privately while the accusation remains in the group chat. | در اختلاف مشابهِ بعدی، عذرخواهی فقط خصوصی فرستاده شده، درحالی‌که اتهام در گفت‌وگوی گروهی مانده است.",
    "We vragen om een rechtzetting voor hetzelfde publiek zonder de verdenking te herhalen. | We request a correction for the same audience without repeating the suspicion. | اصلاحی برای همان مخاطبان می‌خواهیم، بدون تکرار سوءظن.",
    "Een ontbrekend bewijsstuk is niet hetzelfde als bewijs van verdwenen geld. | A missing receipt is not equivalent to evidence of missing money. | نبود رسید با مدرکِ گم‌شدن پول یکسان نیست.",
    "De ontbrekende kasbon bewees dat de nieuwe penningmeester geld had meegenomen. | The missing receipt proved that the new treasurer had taken money. | رسید گم‌شده ثابت کرد خزانه‌دار جدید پول برداشته است.")
add(36,
    "In de ontvangstbevestiging staat opnieuw de verkeerde overstaptijd. | The acknowledgement again states the incorrect connection time. | در تأیید دریافت، زمان تعویض قطار دوباره اشتباه ثبت شده است.",
    "We sturen een rustige correctie met het juiste tijdstip en het dossiernummer. | We send a calm correction with the correct time and reference number. | اصلاحی آرام با ساعت درست و شمارهٔ پرونده می‌فرستیم.",
    "Parafraseren helpt pas wanneer de spreker onjuiste details kan verbeteren. | Paraphrasing helps only when the speaker can correct inaccurate details. | بازگویی زمانی کمک می‌کند که گوینده بتواند جزئیات نادرست را اصلاح کند.",
    "Een samenvatting door de medewerker maakte Mila's verdere controle onnodig. | The worker's summary made further checking by Mila unnecessary. | خلاصهٔ کارمند بررسی بعدی میلا را غیرضروری کرد.")
add(37,
    "De beheerder vraagt welk personeelslid de documenten heeft doorgestuurd. | The manager asks which staff member forwarded the documents. | مدیر می‌پرسد کدام کارمند اسناد را فرستاده است.",
    "We antwoorden over de gecontroleerde feiten zonder de vertrouwelijke bron te identificeren. | We answer about the verified facts without identifying the confidential source. | دربارهٔ واقعیت‌های بررسی‌شده پاسخ می‌دهیم، بدون شناسایی منبع محرمانه.",
    "Publiek belang en bronbescherming kunnen samengaan met nauwkeurige verificatie. | Public interest and source protection can coexist with careful verification. | منفعت عمومی و محافظت از منبع می‌توانند با بررسی دقیق همراه باشند.",
    "Bronbescherming betekende dat de documenten niet meer gecontroleerd hoefden te worden. | Source protection meant that the documents no longer needed verification. | محافظت از منبع یعنی دیگر نیازی به بررسی اسناد نبود.")
add(38,
    "Het gecontroleerde bord hangt er, maar een oude schermafbeelding blijft rondgaan. | The verified notice is posted, but an old screenshot keeps circulating. | تابلوی بررسی‌شده نصب شده، اما تصویر صفحهٔ قدیمی همچنان می‌چرخد.",
    "We delen een gedateerde correctie die gevaarmelding en openingsuren afzonderlijk behandelt. | We share a dated correction addressing the danger claim and opening times separately. | اصلاح تاریخ‌داری منتشر می‌کنیم که ادعای خطر و ساعات کار را جدا بررسی کند.",
    "De onjuiste berichten verschilden in bedoeling, ondanks hun gezamenlijke verwarrende effect. | The false messages differed in intention despite jointly causing confusion. | پیام‌های نادرست با وجود اثر سردرگم‌کنندهٔ مشترک، نیت متفاوتی داشتند.",
    "Beide verspreiders hadden volgens de tekst bewust hetzelfde bedrog gepland. | According to the text, both sharers deliberately planned the same deception. | طبق متن، هر دو منتشرکننده عمداً همان فریب را برنامه‌ریزی کرده بودند.")
add(39,
    "De trailer gebruikt nog altijd alleen de fragmenten met computerproblemen. | The trailer still uses only the scenes showing computer difficulties. | پیش‌نمایش هنوز فقط صحنه‌های مشکل کار با رایانه را نشان می‌دهد.",
    "We passen ook de trailer aan zodat die de verscheidenheid van de film weerspiegelt. | We also revise the trailer to reflect the film's variety. | پیش‌نمایش را نیز اصلاح می‌کنیم تا تنوع فیلم را بازتاب دهد.",
    "Selectie van fragmenten kan een stereotype vormen ondanks een reputatie van zorgvuldigheid. | Selecting excerpts can create a stereotype despite a reputation for care. | گزینش بخش‌ها با وجود شهرت به دقت می‌تواند کلیشه بسازد.",
    "Eén computervaardige deelnemer bewees dat geen enkele oudere hulp nodig had. | One computer-literate participant proved that no older person needed help. | یک شرکت‌کنندهٔ ماهر ثابت کرد هیچ سالمندی کمک لازم ندارد.")
add(40,
    "Voor een vervolgartikel stelt de adverteerder voor de kritiek pas na zijn campagne te publiceren. | For a follow-up article, the advertiser proposes publishing the criticism only after its campaign. | برای مقالهٔ پیگیری، آگهی‌دهنده پیشنهاد می‌کند نقد فقط پس از پایان کارزارش منتشر شود.",
    "De redactie bepaalt het publicatiemoment op journalistieke gronden. | The newsroom determines publication timing on journalistic grounds. | تحریریه زمان انتشار را بر مبنای اصول روزنامه‌نگاری تعیین می‌کند.",
    "Een beleidsredenering faalt wanneer zij een niet-beschikbaar vervoersalternatief veronderstelt. | A policy argument fails when it assumes an unavailable transport alternative. | استدلال سیاستی وقتی گزینهٔ حمل‌ونقلِ ناموجود را فرض کند، ایراد دارد.",
    "De hogere parkeertarieven garandeerden dat avondwerkers de bus konden nemen. | Higher parking charges guaranteed that evening workers could take the bus. | تعرفهٔ بالاتر پارک تضمین می‌کرد کارکنان عصر بتوانند اتوبوس بگیرند.")

add(41,
    "Een nieuwe foto toont dat de vloer al vóór de laatste schoonmaak nat was. | A new photograph shows the floor was wet before the final cleaning. | عکس تازه نشان می‌دهد کف پیش از نظافت آخر خیس بوده است.",
    "We voegen de foto aan het dossier toe en vragen beide partijen om een reactie. | We add the photograph to the file and invite both parties to respond. | عکس را به پرونده اضافه می‌کنیم و از هر دو طرف واکنش می‌خواهیم.",
    "Duidelijkere toekomstige afspraken lossen de bestaande bewijs- en schadevraag niet automatisch op. | Clearer future arrangements do not automatically resolve existing evidence and damage questions. | توافق روشن‌ترِ آینده مسئلهٔ فعلیِ دلیل و خسارت را خودبه‌خود حل نمی‌کند.",
    "Het herschrijven van de passage besliste meteen wie de bestaande schade moest betalen. | Rewriting the clause immediately decided who must pay the existing damage. | بازنویسی بند فوراً تعیین کرد چه کسی باید خسارت فعلی را بپردازد.")
add(42,
    "In het gezamenlijke overzicht staat dezelfde maand tweemaal als openstaand vermeld. | The joint overview lists the same month twice as unpaid. | در جدول مشترک، یک ماه دو بار پرداخت‌نشده ثبت شده است.",
    "We vergelijken elke post met de betalingsreferentie voordat we het overzicht bevestigen. | We compare each entry with its payment reference before confirming the overview. | پیش از تأیید جدول، هر ردیف را با شناسهٔ پرداخت مقایسه می‌کنیم.",
    "Een betaling bewijst alleen de afhandeling van de post waarop zij betrekking heeft. | A payment proves settlement only of the item it concerns. | پرداخت فقط تسویهٔ همان مورد مربوط را ثابت می‌کند.",
    "Eén eerdere betaling toonde aan dat er geen enkele huurpost meer openstond. | One earlier payment showed that no rent item remained unpaid. | یک پرداخت قبلی نشان داد هیچ اجاره‌ای پرداخت‌نشده نمانده است.")
add(43,
    "Het antwoord verduidelijkt de termijn, maar noemt niet op welke beslissing die slaat. | The reply clarifies the deadline but not which decision it concerns. | پاسخ مهلت را روشن می‌کند، اما نمی‌گوید مربوط به کدام تصمیم است.",
    "We vragen de bevoegde contactpersoon de toepasselijke procedure schriftelijk te bevestigen. | We ask the competent contact person to confirm the applicable procedure in writing. | از مسئول دارای صلاحیت می‌خواهیم روند مربوط را کتبی تأیید کند.",
    "Procedurele ontvankelijkheid en de inhoudelijke schadebeoordeling zijn verschillende vragen. | Procedural admissibility and substantive damage assessment are separate questions. | پذیرش شکلی درخواست و ارزیابی ماهوی خسارت دو پرسش جدا هستند.",
    "Het noteren van de ontvangstdatum besliste al over het recht op schadevergoeding. | Recording the receipt date already determined entitlement to compensation. | ثبت تاریخ دریافت از قبل حق دریافت غرامت را تعیین کرد.")
add(44,
    "De nieuwe voorzitter heeft eerder voor de klager gewerkt. | The new chair previously worked for the complainant. | رئیس جدید قبلاً برای شاکی کار کرده است.",
    "We maken ook die band bekend en toetsen de eigen vervangingsafspraken opnieuw. | We disclose that connection too and reassess the internal replacement arrangements. | آن رابطه را هم اعلام می‌کنیم و قواعد داخلیِ جایگزینی را دوباره می‌سنجیم.",
    "Onpartijdigheid moet voor deelnemers controleerbaar zijn, niet alleen door de voorzitter worden beloofd. | Impartiality must be verifiable to participants, not merely promised by the chair. | بی‌طرفی باید برای شرکت‌کنندگان قابل‌بررسی باشد، نه فقط وعدهٔ رئیس.",
    "Een persoonlijke verzekering volstond volgens de commissie als enige waarborg. | A personal assurance was the committee's only required safeguard. | طبق نظر کمیسیون، اطمینان شخصی تنها تضمین لازم بود.")
add(45,
    "De affiche is verwijderd, maar staat nog in een reeds verstuurde nieuwsbrief. | The poster has been removed but remains in a newsletter already sent. | پوستر برداشته شده، اما در خبرنامهٔ ارسال‌شده هنوز هست.",
    "We melden welke verspreiding nog te stoppen is en laten verdere stappen bevestigen. | We explain which distribution can still be stopped and have further steps confirmed. | توضیح می‌دهیم کدام انتشار هنوز متوقف‌شدنی است و گام بعد را تأیید می‌گیریم.",
    "Een toestemming voor één context kan niet zonder onderzoek naar een andere context worden uitgebreid. | Permission for one context cannot be extended to another without checking. | اجازه برای یک زمینه را نمی‌توان بدون بررسی به زمینه‌ای دیگر گسترش داد.",
    "De vroegere toestemming sloot iedere vraag over het nieuwe project bij voorbaat uit. | The earlier permission ruled out every question about the new project in advance. | اجازهٔ قبلی از ابتدا هر پرسشی دربارهٔ پروژهٔ جدید را منتفی کرد.")
add(46,
    "Bij een volgend dossier heeft een medewerker per ongeluk twee verschillende briefversies verstuurd. | In a subsequent case, a worker accidentally sent two different letter versions. | در پروندهٔ بعدی، کارمندی تصادفاً دو نسخهٔ متفاوت نامه فرستاده است.",
    "We laten de verantwoordelijke één gecontroleerde rechtzetting aan alle ontvangers sturen. | We have the responsible person send one checked correction to every recipient. | از مسئول می‌خواهیم یک اصلاح بررسی‌شده برای همهٔ گیرندگان بفرستد.",
    "Woorden voor verschillende maatregelen mogen niet als onderling verwisselbare formuleringen worden gebruikt. | Words describing different measures must not be treated as interchangeable phrasing. | واژه‌های مربوط به اقدام‌های متفاوت را نباید عبارت‌های قابل‌جایگزینی دانست.",
    "De drie concepten verschilden alleen stilistisch en hadden noodzakelijk hetzelfde gevolg. | The three drafts differed only stylistically and necessarily had the same consequence. | سه پیش‌نویس فقط از نظر سبک فرق داشتند و الزاماً پیامد یکسانی داشتند.")
add(47,
    "De nieuwe ingang is bereikbaar, maar er staat geen onthaalmedewerker. | The new entrance is accessible, but no receptionist is present. | ورودی جدید قابل‌دسترسی است، اما کسی برای استقبال آنجا نیست.",
    "We organiseren aan die ingang dezelfde ontvangst zonder persoonlijke gegevens publiek te vragen. | We arrange the same welcome there without publicly asking for personal details. | همان استقبال را در آن ورودی فراهم می‌کنیم، بدون پرسش عمومی دربارهٔ اطلاعات شخصی.",
    "Een bruikbare route is onvoldoende wanneer de ontvangst mensen ongelijk behandelt. | A usable route is insufficient if the welcome treats people unequally. | مسیر قابل‌استفاده کافی نیست اگر استقبال با افراد نابرابر برخورد کند.",
    "De benaming redelijke aanpassing bewees op zichzelf dat de route passend was. | Calling it a reasonable adjustment itself proved that the route was suitable. | نام‌گذاری به‌عنوان سازگارسازی معقول، به‌خودی‌خود مناسب‌بودن مسیر را ثابت می‌کرد.")
add(48,
    "Een ongedateerde kopie van hetzelfde bestand duikt op in een gedeelde map. | An undated copy of the same file appears in a shared folder. | نسخه‌ای بی‌تاریخ از همان فایل در پوشهٔ مشترک پیدا می‌شود.",
    "We laten herkomst en toegang ook voor die kopie onderzoeken. | We have the provenance and access of that copy checked too. | منشأ و دسترسی همان نسخه را هم برای بررسی ارجاع می‌دهیم.",
    "Toegang, herkomst en betrouwbaarheid van gegevens vragen elk afzonderlijke controle. | Access, provenance and reliability each require separate checks. | دسترسی، منشأ و اعتبار داده هرکدام بررسی جدا می‌خواهند.",
    "Een functietitel verschafte volgens het onderzoek automatisch toegang tot alle gevonden gegevens. | A job title automatically granted access to all recovered data according to the investigation. | طبق بررسی، عنوان شغلی خودکار اجازهٔ دسترسی به همهٔ داده‌های یافت‌شده را می‌داد.")
add(49,
    "De oudere foto mist een datum, maar de vrijwilliger herkent de fietstocht. | The older photograph lacks a date, but the volunteer recognises the ride. | عکس قدیمی تاریخ ندارد، اما داوطلب آن دوچرخه‌سواری را می‌شناسد.",
    "We onderscheiden zijn herinnering van bevestigde tijdgegevens in de samenvatting. | In the summary we distinguish his recollection from confirmed timing data. | در خلاصه، خاطرهٔ او را از زمان‌های تأییدشده جدا می‌کنیم.",
    "Partijen kunnen een praktische oplossing vastleggen terwijl sommige feiten onzeker blijven. | Parties can document a practical solution while some facts remain uncertain. | طرف‌ها می‌توانند راه‌حل عملی را ثبت کنند، حتی اگر بعضی واقعیت‌ها نامطمئن بمانند.",
    "Een schikking bewees noodzakelijk dat de huurder de kras had veroorzaakt. | A settlement necessarily proved that the renter caused the scratch. | توافق لزوماً ثابت می‌کرد اجاره‌کننده خراش را ایجاد کرده است.")
add(50,
    "Eén buur ontvangt een gewijzigde technische tekening die de ander nog niet heeft gezien. | One neighbour receives a revised technical drawing the other has not seen. | یکی از همسایه‌ها نقشهٔ فنی اصلاح‌شده‌ای می‌گیرد که دیگری ندیده است.",
    "We bezorgen beide buren dezelfde versie en nieuwe tijd voor afzonderlijke beoordeling. | We give both neighbours the same version and fresh time for separate review. | به هر دو همسایه نسخهٔ یکسان و فرصت تازه برای بررسی جداگانه می‌دهیم.",
    "Gelijke informatie en tijd voor advies ondersteunen een zorgvuldig hervat gesprek. | Equal information and time for advice support carefully resumed discussion. | اطلاعات برابر و زمان مشورت از ازسرگیری سنجیدهٔ گفت‌وگو پشتیبانی می‌کنند.",
    "Een technisch voorstel betekende dat beide buren het onmiddellijk moesten ondertekenen. | A technical proposal meant both neighbours had to sign immediately. | پیشنهاد فنی یعنی هر دو همسایه باید فوراً امضا می‌کردند.")

add(51,
    "Een vrijwilliger wil toch alvast groenten planten in de nog niet onderzochte hoek. | A volunteer wants to plant vegetables in the corner that has not yet been assessed. | داوطلبی می‌خواهد در گوشهٔ هنوز بررسی‌نشده سبزی بکارد.",
    "We wachten op het bodemadvies en houden die hoek voorlopig buiten de moestuin. | We wait for the soil advice and temporarily exclude that corner from food growing. | منتظر نظر دربارهٔ خاک می‌مانیم و فعلاً آن گوشه را وارد باغ سبزی نمی‌کنیم.",
    "Het gewenste gebruik van een terrein moet aansluiten bij de vastgestelde bodemcondities. | A site's intended use must fit its established soil conditions. | کاربری مطلوب زمین باید با شرایط بررسی‌شدهٔ خاک سازگار باشد.",
    "Inheemse planten maakten verder onderzoek naar de bodemkwaliteit overbodig. | Native plants made further investigation of soil quality unnecessary. | گیاهان بومی بررسی بیشتر کیفیت خاک را غیرضروری کردند.")
add(52,
    "Het zonnedoek geeft schaduw, maar hindert bij harde wind de doorgang. | The sunshade provides shade but obstructs the passage in strong wind. | سایه‌بان سایه می‌دهد، اما در باد شدید مسیر را می‌بندد.",
    "We laten de bevestiging nakijken en bewaren een vrije doorgang. | We have the fixing checked and keep the passage clear. | اتصال‌ها را برای بررسی می‌دهیم و مسیر را باز نگه می‌داریم.",
    "Tijdelijke en langetermijnmaatregelen vullen elkaar aan bij jonge bomen. | Temporary and long-term measures complement each other while trees are young. | وقتی درخت‌ها جوان‌اند، اقدام موقت و بلندمدت مکمل یکدیگرند.",
    "De nieuwe bomen boden onmiddellijk genoeg schaduw om iedere tijdelijke maatregel te schrappen. | The new trees immediately provided enough shade to remove every temporary measure. | درخت‌های تازه فوراً سایهٔ کافی برای حذف همهٔ اقدام‌های موقت ایجاد کردند.")
add(53,
    "Na een droge week wil de tuinploeg ook de vrije opvangruimte met water vullen. | After a dry week the gardening team wants to fill the spare stormwater capacity too. | پس از هفته‌ای خشک، گروه باغبانی می‌خواهد فضای خالیِ جذب باران را هم پر کند.",
    "We houden waterreserve en vrije opvangcapaciteit gescheiden volgens het ontwerp. | We keep stored water and spare collection capacity separate according to the design. | طبق طرح، ذخیرهٔ آب و ظرفیت خالی جذب باران را جدا نگه می‌داریم.",
    "Een voorraad voor droogte vervult niet automatisch dezelfde functie als ruimte voor een nieuwe bui. | A drought reserve does not automatically serve the same function as space for new rainfall. | ذخیره برای خشکی خودکار همان نقشِ فضا برای بارش تازه را ندارد.",
    "Een volle regenton garandeerde dat de kelder bij de volgende stortbui droog bleef. | A full rain barrel guaranteed a dry cellar during the next downpour. | بشکهٔ پُر باران تضمین می‌کرد زیرزمین در رگبار بعدی خشک بماند.")
add(54,
    "Een leverancier komt buiten de uren omdat een eerdere levering uitliep. | A supplier arrives outside the hours because an earlier delivery overran. | تأمین‌کننده به‌علت طولانی‌شدن تحویل قبلی، خارج از ساعت تعیین‌شده می‌رسد.",
    "We spreken een uitzonderingsroute af zonder wachten met draaiende motor onder het raam. | We agree an exception procedure without idling beneath the window. | روشی برای استثنا تعیین می‌کنیم، بدون انتظار با موتور روشن زیر پنجره.",
    "Minder hinder en toegankelijke verplaatsingen vragen om een afgewogen combinatie. | Less nuisance and accessible travel require a balanced combination. | کاهش مزاحمت و رفت‌وآمد قابل‌دسترسی به ترکیبی سنجیده نیاز دارند.",
    "Els vroeg om elk voertuig te weren, ongeacht de gevolgen voor bezoekers. | Els asked to ban every vehicle regardless of consequences for visitors. | الس خواست همهٔ خودروها بدون توجه به پیامد برای بازدیدکنندگان ممنوع شوند.")
add(55,
    "Bij het eerste toernooi zetten ouders auto's op het begin van de fietsroute. | At the first tournament parents park at the start of the cycle route. | در نخستین مسابقه، والدین خودروها را ابتدای مسیر دوچرخه می‌گذارند.",
    "We maken de route zichtbaar vrij en informeren bezoekers vóór het volgende toernooi. | We clearly keep the route free and inform visitors before the next tournament. | مسیر را آشکارا باز نگه می‌داریم و پیش از مسابقهٔ بعد اطلاع‌رسانی می‌کنیم.",
    "Een ontwerp kan verschillende vervoerswijzen veiliger maken en tegelijk open ruimte sparen. | A design can improve safety for different transport modes while preserving open space. | یک طرح می‌تواند امنیت شیوه‌های مختلف رفت‌وآمد و حفظ فضای باز را هم‌زمان بهبود دهد.",
    "De veiligheid werd bereikt door alle kinderen dezelfde inrit als auto's te laten gebruiken. | Safety was achieved by giving children the same driveway as cars. | ایمنی با استفادهٔ کودکان از همان ورودی خودروها ایجاد شد.")
add(56,
    "De eigenaar wil de lagere energiekosten al adverteren voordat het dak klaar is. | The owner wants to advertise lower energy costs before the roof work is complete. | مالک می‌خواهد پیش از پایان کار سقف، هزینهٔ انرژی پایین‌تر را تبلیغ کند.",
    "We onderscheiden berekende verwachtingen van reeds uitgevoerde verbeteringen. | We distinguish calculated expectations from improvements already carried out. | انتظار محاسبه‌شده را از بهبود اجراشده جدا می‌کنیم.",
    "Zichtbare verfraaiing kan minder dringend zijn dan een verborgen bron van toekomstige kosten. | Visible decoration may be less urgent than a hidden source of future costs. | زیباسازی ظاهری ممکن است از علت پنهانِ هزینه‌های آینده کم‌فوریت‌تر باشد.",
    "Schilderen loste volgens de berekening het warmteverlies via het dak op. | Painting solved heat loss through the roof according to the calculation. | طبق محاسبه، رنگ‌آمیزی اتلاف گرما از سقف را حل می‌کرد.")
add(57,
    "Na de klokcorrectie is de zaal op een uitzonderlijk vroege activiteit nog koud. | After correcting the timer, the room is cold for an unusually early activity. | پس از اصلاح زمان‌سنج، سالن برای برنامه‌ای با شروع غیرعادیِ زودهنگام هنوز سرد است.",
    "We passen de uitzonderlijke reservatie in zonder opnieuw elke nacht te verwarmen. | We accommodate the unusual booking without returning to heating every night. | رزرو استثنایی را لحاظ می‌کنیم، بدون بازگشت به گرمایش هرشب.",
    "Een lagere werkelijke vraag kan de vergelijking tussen investeringen veranderen. | Lower actual demand can change the comparison between investments. | تقاضای واقعی کمتر ممکن است مقایسهٔ سرمایه‌گذاری‌ها را تغییر دهد.",
    "De offerte voor een nieuwe ketel maakte controle van de klokinstellingen overbodig. | The boiler quotation made checking the timer settings unnecessary. | پیشنهاد خرید دیگ جدید، بررسی تنظیمات زمان‌سنج را غیرضروری کرد.")
add(58,
    "De fabrikant wil de losse planken voortaan alleen per tien verkopen. | The manufacturer now wants to sell replacement boards only in packs of ten. | سازنده می‌خواهد تخته‌های جایگزین را از این پس فقط ده‌تایی بفروشد.",
    "We vragen hoe die voorwaarde de onderhoudskosten en opslag beïnvloedt. | We ask how that condition affects maintenance costs and storage. | می‌پرسیم این شرط چه اثری بر هزینهٔ نگهداری و انبار دارد.",
    "De laagste aankoopprijs hoeft niet de beste keuze over de gebruiksduur te zijn. | The lowest purchase price need not be the best choice over the useful lifetime. | کمترین قیمت خرید لزوماً بهترین انتخاب در طول عمر استفاده نیست.",
    "De herstelbare bank moest bij de eerste gebroken plank volledig worden vervangen. | The repairable bench had to be entirely replaced after the first broken board. | نیمکت تعمیرپذیر با شکستن اولین تخته باید کاملاً تعویض می‌شد.")
add(59,
    "De nieuwe pictogrammen worden in het donker bij de uitgang slecht gezien. | The new pictograms are difficult to see at the exit after dark. | نمادهای تازه هنگام تاریکی کنار خروجی خوب دیده نمی‌شوند.",
    "We testen de afvalbakken tijdens de avondopbouw en verbeteren de verlichting. | We test the bins during evening setup and improve the lighting. | سطل‌ها را هنگام آماده‌سازی شبانه آزمایش و نور را بهتر می‌کنیم.",
    "Gescheiden inzameling werkt alleen wanneer de materiaalstroom voldoende zuiver blijft. | Separate collection works only when the material stream stays sufficiently clean. | جمع‌آوری جدا وقتی مؤثر است که جریان مواد به‌اندازهٔ کافی خالص بماند.",
    "Een apart ingezamelde zak kon ongeacht de inhoud opnieuw als grondstof dienen. | A separately collected bag could become raw material regardless of its contents. | کیسهٔ جداگانه بدون توجه به محتوا می‌توانست دوباره مادهٔ اولیه شود.")
add(60,
    "De spreiding over twee weekends leidt tot extra opbouwritten met vrachtwagens. | Spreading the event across two weekends causes extra lorry setup journeys. | تقسیم جشن در دو آخرهفته سفرهای بیشتری برای حمل تجهیزات ایجاد می‌کند.",
    "We wegen die extra ritten mee naast de lagere druk per dag. | We weigh those extra journeys alongside the lower daily pressure. | سفرهای اضافه را در کنار فشار روزانهٔ کمتر می‌سنجیم.",
    "Een maatregel tegen één milieuprobleem neemt de totale draagkrachtgrens niet weg. | Addressing one environmental problem does not remove the overall capacity limit. | اقدام برای یک مشکل محیطی، حد کلی ظرفیت را از بین نمی‌برد.",
    "Collectief vervoer maakte volgens de tekst onbeperkte bezoekersaantallen verantwoord. | Shared transport made unlimited visitor numbers responsible according to the text. | طبق متن، حمل‌ونقل جمعی تعداد نامحدود بازدیدکننده را قابل‌قبول می‌کرد.")

add(61,
    "Een familielid vraagt de beschadigde voering toch uit het zicht te hangen. | A relative asks for the damaged lining to be hidden after all. | یکی از بستگان می‌خواهد آستر آسیب‌دیده از دید پنهان بماند.",
    "We bespreken hoe zowel dagelijks gebruik als familieherinnering zichtbaar kan blijven. | We discuss how everyday use and family memory can both remain visible. | بررسی می‌کنیم چگونه هم استفادهٔ روزمره و هم خاطرهٔ خانوادگی دیده شود.",
    "Materiële slijtage kan een eenzijdig heldenverhaal aanvullen met het dagelijkse leven. | Material wear can complement a one-sided heroic account with everyday life. | فرسودگی جسم می‌تواند روایت قهرمانانهٔ یک‌جانبه را با زندگی روزمره تکمیل کند.",
    "De erfgoedwaarde lag uitsluitend in een herstelde, onbeschadigde uitstraling van de jas. | The heritage value lay solely in restoring the coat to an undamaged appearance. | ارزش میراثی کت فقط در ظاهر ترمیم‌شده و بی‌آسیب آن بود.")
add(62,
    "Een luisteraar noemt de onmogelijke keuken een fout die de maker moet herstellen. | A listener calls the impossible kitchen an error the author must correct. | شنونده‌ای آشپزخانهٔ ناممکن را اشتباهی می‌داند که سازنده باید اصلاح کند.",
    "We vergelijken de letterlijke en symbolische lezing met aanwijzingen uit het verhaal. | We compare literal and symbolic readings using clues from the story. | خوانش لفظی و نمادین را با نشانه‌های داستان مقایسه می‌کنیم.",
    "Ruimtelijke onmogelijkheid kan verlangen verbeelden in plaats van een feitelijke fout te zijn. | Spatial impossibility can represent longing rather than factual error. | ناممکن‌بودن فضا می‌تواند بیان دلتنگی باشد، نه خطای واقعی.",
    "Sara loste het raadsel op door een nauwkeurige, mogelijke plattegrond te tekenen. | Sara solved the puzzle by drawing an accurate, possible floor plan. | سارا معما را با رسم نقشه‌ای دقیق و ممکن حل کرد.")
add(63,
    "Een proeflezer wil de naam van de dief toch naar het laatste hoofdstuk verplaatsen. | A test reader wants to move the thief's name to the final chapter after all. | خوانندهٔ آزمایشی می‌خواهد نام دزد باز هم به فصل آخر منتقل شود.",
    "We leggen uit welke andere vraag de spanning in deze versie draagt. | We explain which other question sustains suspense in this version. | توضیح می‌دهیم کدام پرسش دیگر در این نسخه تعلیق را نگه می‌دارد.",
    "Spanning kan draaien om motieven en keuzes wanneer de identiteit al bekend is. | Suspense can concern motives and choices when identity is already known. | وقتی هویت معلوم است، تعلیق می‌تواند بر انگیزه و انتخاب استوار باشد.",
    "Zodra de dader bekend was, kon het verhaal volgens de redacteur geen spanning meer hebben. | Once the offender was known, the editor considered suspense impossible. | به نظر ویراستار، پس از معلوم‌شدن مجرم دیگر تعلیق ممکن نبود.")
add(64,
    "De actrice stelt voor de betekenis van het open raam in haar laatste zin uit te leggen. | The actress proposes explaining the open window's meaning in her final line. | بازیگر پیشنهاد می‌کند معنای پنجرهٔ باز را در جملهٔ آخر توضیح دهد.",
    "We proberen eerst of het gebaar zonder extra uitleg begrijpelijk blijft. | We first test whether the gesture remains understandable without extra explanation. | ابتدا امتحان می‌کنیم آیا حرکت بدون توضیح اضافه قابل‌فهم می‌ماند.",
    "Een herhaald gebaar krijgt betekenis door verandering binnen het verloop van het stuk. | A repeated gesture gains meaning through change over the course of the play. | حرکت تکرارشونده با تغییر در جریان نمایش معنا می‌گیرد.",
    "De symboliek werd alleen duidelijk door een nieuwe expliciete uitlegscène. | The symbolism became clear only through a new explicit explanatory scene. | نمادپردازی فقط با صحنهٔ تازهٔ توضیح صریح روشن شد.")
add(65,
    "Op de online aankondiging ontbreekt de naam van de zangeres nog steeds. | The singer's name is still missing from the online announcement. | نام خواننده هنوز در اطلاعیهٔ آنلاین نیست.",
    "We trekken de afgesproken vermelding door naar alle aankondigingen. | We extend the agreed attribution to every announcement. | ذکر نامِ توافق‌شده را در همهٔ اطلاعیه‌ها اعمال می‌کنیم.",
    "Een bewerking verandert niet vanzelf de noodzaak om bijdragen en toestemming te bespreken. | An adaptation does not automatically remove the need to discuss contributions and permission. | بازآفرینی خودبه‌خود نیاز به گفت‌وگو دربارهٔ سهم و اجازه را حذف نمی‌کند.",
    "Een sneller ritme maakte iedere verwijzing naar de oorspronkelijke zangeres overbodig. | A faster rhythm made every reference to the original singer unnecessary. | ریتم تندتر هر اشاره‌ای به خوانندهٔ اصلی را غیرضروری کرد.")
add(66,
    "Een leesclublid heeft alleen het toneelstuk gezien en wil het boek nu helemaal overslaan. | A reading-group member has seen only the play and now wants to skip the book entirely. | عضوی از باشگاه فقط نمایش را دیده و حالا می‌خواهد کتاب را کاملاً کنار بگذارد.",
    "We kiezen één veranderde scène en vergelijken de ironie in beide versies. | We select one changed scene and compare the irony in both versions. | یک صحنهٔ تغییرکرده را انتخاب و طنز دو نسخه را مقایسه می‌کنیم.",
    "Een vergelijking met een bewerking kan nieuwe aandacht voor een vertrouwde tekst openen. | Comparing an adaptation can open new attention to a familiar text. | مقایسه با اقتباس می‌تواند توجه تازه‌ای به متن آشنا ایجاد کند.",
    "De hernieuwde waardering kwam uitsluitend doordat de roman tot de canon behoorde. | Renewed appreciation came solely from the novel's canonical status. | ارزش‌گذاری تازه فقط به‌خاطر جایگاه کتاب در آثار مرجع بود.")
add(67,
    "De uitgever vraagt één vaste vertaling om de woordenlijst eenvoudiger te maken. | The publisher asks for one fixed translation to simplify the glossary. | ناشر برای ساده‌کردن واژه‌نامه ترجمه‌ای ثابت می‌خواهد.",
    "We tonen twee contexten waarin dezelfde vertaling betekenis zou verliezen. | We show two contexts where the same translation would lose meaning. | دو زمینه نشان می‌دهیم که ترجمهٔ یکسان در آن‌ها معنا را از دست می‌دهد.",
    "Gelijke spelling garandeert geen identieke betekenis in verschillende culturele contexten. | Identical spelling does not guarantee identical meaning across cultural contexts. | املای یکسان، معنای یکسان را در زمینه‌های فرهنگی متفاوت تضمین نمی‌کند.",
    "Leila vulde alle onduidelijke verwijzingen met verzonnen informatie aan. | Leila filled every unclear reference with invented information. | لیلا همهٔ ارجاع‌های مبهم را با اطلاعات ساختگی پر کرد.")
add(68,
    "Een bezoeker vraagt waarom de stoel niet dezelfde heldere kleur als de foto kreeg. | A visitor asks why the chair was not given the same bright colour as the photograph. | بازدیدکننده می‌پرسد چرا صندلی رنگ روشنِ عکس را نگرفته است.",
    "We leggen de latere inkleuring uit en wijzen op de behouden verfsporen. | We explain the later colourisation and point to the preserved paint traces. | رنگ‌آمیزیِ بعدیِ عکس را توضیح می‌دهیم و رد رنگ حفظ‌شده را نشان می‌دهیم.",
    "Een vertrouwde afbeelding kan een onbetrouwbare basis voor herstel van het origineel zijn. | A familiar image can be an unreliable basis for restoring the original. | تصویر آشنا ممکن است مبنای نامعتبری برای بازسازی اصل باشد.",
    "De ingekleurde foto werd zonder verder onderzoek als bewijs van de oorspronkelijke kleur gebruikt. | The colourised photograph was used without further checking as evidence of the original colour. | عکس رنگ‌شده بدون بررسی بیشتر مدرک رنگ اصلی شمرده شد.")
add(69,
    "Twee families melden eigendom van dezelfde foto, met verschillende ontvangstbewijzen. | Two families claim ownership of the same photograph with different receipts. | دو خانواده با رسیدهای متفاوت مالکیت یک عکس را ادعا می‌کنند.",
    "We stellen publicatie van dat beeld uit tot de tegenstrijdige stukken onderzocht zijn. | We postpone publishing that image until the conflicting documents are examined. | انتشار آن تصویر را تا بررسی اسناد متعارض عقب می‌اندازیم.",
    "Toegankelijk maken van een collectie vergt eerst duidelijkheid over herkomst en gebruik. | Making a collection accessible first requires clarity about provenance and use. | دسترس‌پذیرکردن مجموعه ابتدا به روشن‌شدن منشأ و کاربرد نیاز دارد.",
    "Het ontbreken van een inventarisnummer gaf vanzelf toestemming om alle foto's te publiceren. | Missing an inventory number automatically authorised publication of all photographs. | نبود شمارهٔ فهرست خودبه‌خود اجازهٔ انتشار همهٔ عکس‌ها را می‌داد.")
add(70,
    "Een nieuwe montage van de korte luisterversie bevat de toestemming, maar knipt de betekenisvolle pauze opnieuw weg. | A new edit of the short audio version includes the permission but cuts the meaningful pause again. | تدوین تازهٔ نسخهٔ کوتاه اجازه را دارد، اما مکث معنادار را دوباره حذف می‌کند.",
    "We vergelijken de montage met de afgesproken weergave en herstellen de pauze. | We compare the edit with the agreed presentation and restore the pause. | تدوین را با بازنمایی توافق‌شده مقایسه می‌کنیم و مکث را برمی‌گردانیم.",
    "Stilte kan deel uitmaken van de betekenis van een getuigenis. | Silence can form part of the meaning of testimony. | سکوت می‌تواند بخشی از معنای شهادت باشد.",
    "Alleen uitgesproken jaartallen droegen volgens de tekst betekenis. | Only spoken dates carried meaning according to the text. | طبق متن فقط تاریخ‌های گفته‌شده معنا داشتند.")

add(71,
    "Het aangepaste gesprek valt samen met een onmisbare werkvergadering van Nadia. | Nadia's rescheduled appointment overlaps with an essential work meeting. | گفت‌وگوی جابه‌جاشدهٔ نادیا با جلسهٔ ضروریِ کارش هم‌زمان شده است.",
    "We zoeken samen een haalbaar moment en vragen welke ondersteuning zij zelf wenst. | We jointly seek a feasible time and ask which support she wants. | با هم زمان شدنی پیدا می‌کنیم و می‌پرسیم خودش چه حمایتی می‌خواهد.",
    "Toegankelijkheid omvat ook tijd en kosten, niet alleen fysieke toegang. | Accessibility includes timing and costs, not only physical access. | دسترس‌پذیری زمان و هزینه را هم شامل می‌شود، نه فقط دسترسی فیزیکی.",
    "Een deur zonder trap nam volgens het verhaal alle drempels voor Nadia weg. | A step-free door removed every barrier for Nadia according to the story. | طبق داستان، درِ بدون پله تمام موانع نادیا را برطرف کرد.")
add(72,
    "Het gezin wil wel naar de buurtmaaltijd, maar niet meteen in een groepschat. | The family wants to attend the neighbourhood meal but not immediately join a group chat. | خانواده می‌خواهد به غذای محله بیاید، اما فعلاً وارد گروه پیام‌رسان نشود.",
    "We respecteren die grens en bieden een afzonderlijke uitnodiging aan. | We respect that boundary and offer a separate invitation. | به آن مرز احترام می‌گذاریم و دعوت جداگانه می‌فرستیم.",
    "Verbinding groeit wanneer ondersteuning ruimte laat voor eigen tempo en keuzes. | Connection grows when support leaves room for personal pace and choices. | پیوند وقتی رشد می‌کند که حمایت برای سرعت و انتخاب فرد جا بگذارد.",
    "Het gezin moest eerst elke uitnodiging aanvaarden om ondersteuning te verdienen. | The family first had to accept every invitation to deserve support. | خانواده باید ابتدا همهٔ دعوت‌ها را می‌پذیرفت تا شایستهٔ حمایت شود.")
add(73,
    "De vaste contactpersoon is volgende week afwezig en er is nog geen vervanger genoemd. | The regular contact person is away next week and no substitute has been named. | مسئول تماس ثابت هفتهٔ آینده غایب است و هنوز جانشینی معرفی نشده است.",
    "We bevestigen wie bereikbaar is tijdens het wachten en delen alleen afgesproken informatie. | We confirm who is reachable while waiting and share only agreed information. | تأیید می‌کنیم هنگام انتظار چه کسی در دسترس است و فقط اطلاعات توافق‌شده را می‌دهیم.",
    "Doorverwijzen waarborgt niet vanzelf ondersteuning tijdens de tussenliggende wachttijd. | Referral does not automatically guarantee support during the intervening wait. | ارجاع خودبه‌خود حمایت در مدت انتظار را تضمین نمی‌کند.",
    "De doorverwijzing leverde Karim onmiddellijk een plaats bij de nieuwe dienst op. | The referral immediately gave Karim a place at the new service. | ارجاع فوراً برای کریم در واحد جدید جا فراهم کرد.")
add(74,
    "Eén dienst wijzigt opnieuw een bezoek zonder het gezamenlijke overzicht bij te werken. | One service changes a visit again without updating the shared overview. | یکی از خدمات دوباره دیدار را عوض می‌کند، بدون اصلاح جدول مشترک.",
    "We spreken af wie veranderingen bevestigt aan het gezin en de andere dienst. | We agree who confirms changes to the family and the other service. | توافق می‌کنیم چه کسی تغییر را به خانواده و واحد دیگر تأیید کند.",
    "Meer ondersteuning kan minder bruikbaar worden wanneer diensten elkaar niet afstemmen. | More support can become less usable when services fail to coordinate. | حمایت بیشتر ممکن است بدون هماهنگی خدمات، کم‌کاربردتر شود.",
    "Twee gelijktijdige bezoeken garandeerden volgens het verhaal betere preventie. | Two simultaneous visits guaranteed better prevention according to the story. | طبق داستان دو دیدار هم‌زمان پیشگیری بهتر را تضمین می‌کردند.")
add(75,
    "De bezoeker brengt bij de volgende afspraak een hele doos ongeopende brieven mee. | The visitor brings a whole box of unopened letters to the next appointment. | مراجعه‌کننده در قرار بعد یک جعبه نامهٔ بازنشده می‌آورد.",
    "We kiezen samen een eerste brief en bespreken wat binnen de beschikbare tijd past. | We jointly choose a first letter and discuss what fits the available time. | با هم نامهٔ اول را انتخاب می‌کنیم و دربارهٔ کار شدنی در زمان موجود حرف می‌زنیم.",
    "Nabije ondersteuning kan samengaan met begrenzing en behoud van eigen regie. | Close support can coexist with boundaries and retained personal control. | حمایت نزدیک می‌تواند با مرزبندی و حفظ اختیار فرد همراه باشد.",
    "De medewerker nam alle documenten over zodat de bezoeker niet meer hoefde te kiezen. | The worker took over all documents so the visitor no longer had to choose. | کارمند همهٔ مدارک را گرفت تا مراجعه‌کننده دیگر نیازی به انتخاب نداشته باشد.")
add(76,
    "De vertrouwenspersoon wil het gesprek opnemen, terwijl Els daar nog niet op heeft gereageerd. | The trusted supporter wants to record the discussion, but Els has not responded yet. | فرد مورداعتماد می‌خواهد گفت‌وگو را ضبط کند، اما الس هنوز واکنشی نداده است.",
    "We vragen Els zelf wat zij wil voordat iemand een opname start. | We ask Els herself what she wants before anyone starts recording. | پیش از شروع ضبط، از خود الس می‌پرسیم چه می‌خواهد.",
    "Zwijgen naast een dominantere spreker bewijst geen instemming met diens voorstel. | Silence beside a more dominant speaker does not prove agreement with that person's proposal. | سکوت کنار گویندهٔ مسلط‌تر، موافقت با پیشنهاد او را ثابت نمی‌کند.",
    "Het luidste familielid werd automatisch de vertegenwoordiger voor elke beslissing. | The loudest relative automatically became the representative for every decision. | بلندصداترین خویشاوند خودکار نمایندهٔ همهٔ تصمیم‌ها شد.")
add(77,
    "Tijdens de vrije namiddag bellen drie mensen met niet-dringende administratievragen. | During the free afternoon three people call with non-urgent administrative questions. | در بعدازظهر آزاد، سه نفر با پرسش اداری غیرفوری تماس می‌گیرند.",
    "We leiden die vragen naar het afgesproken contactpunt en beschermen de rusttijd. | We route those questions to the agreed contact point and protect the rest period. | پرسش‌ها را به محل تماس توافق‌شده هدایت و زمان استراحت را حفظ می‌کنیم.",
    "Rust nodig hebben is geen bewijs van onverschilligheid tegenover degene die hulp krijgt. | Needing rest is not evidence of indifference towards the person receiving support. | نیاز به استراحت نشانهٔ بی‌تفاوتی به فردِ دریافت‌کنندهٔ کمک نیست.",
    "Een vergeten afspraak bewees dat de broer niet langer zorgzaam was. | A forgotten appointment proved the brother was no longer caring. | فراموشی یک قرار ثابت کرد برادر دیگر دلسوز نبود.")
add(78,
    "De uitstap is goedkoper, maar de bus vertrekt vóór de eerste verbinding uit een buitenwijk. | The outing is cheaper, but its bus leaves before the first connection from an outlying area. | گردش ارزان‌تر شده، اما اتوبوس پیش از نخستین مسیر از محلهٔ دور حرکت می‌کند.",
    "We toetsen ook het vertrekpunt en de vertrektijd bij mensen die nog niet deelnemen. | We also check the departure point and time with people not yet participating. | محل و ساعت حرکت را هم با کسانی که هنوز شرکت نمی‌کنند بررسی می‌کنیم.",
    "Een open uitnodiging maakt deelname nog niet voor iedereen praktisch mogelijk. | An open invitation does not yet make participation practically possible for everyone. | دعوت عمومی هنوز شرکت عملی را برای همه ممکن نمی‌کند.",
    "Wie zich niet inschreef, had volgens het onderzoek eenvoudig geen belangstelling. | According to the inquiry, anyone not registering simply lacked interest. | طبق بررسی، هرکس ثبت‌نام نکرده بود صرفاً علاقه‌ای نداشت.")
add(79,
    "Een medewerker stelt voor dat familieleden alle digitale formulieren overnemen. | A worker proposes that relatives take over every digital form. | کارمندی پیشنهاد می‌کند اعضای خانواده همهٔ فرم‌های دیجیتال را انجام دهند.",
    "We vragen bezoekers welke hulp zij wensen en behouden een zelfstandig bruikbare keuze. | We ask visitors what help they want and retain an independently usable option. | می‌پرسیم چه کمکی می‌خواهند و گزینه‌ای قابل‌استفادهٔ مستقل نگه می‌داریم.",
    "Verschillende hindernissen vragen passende ondersteuning zonder kennis of onwil te veronderstellen. | Different barriers require suitable support without assumptions about knowledge or unwillingness. | مانع‌های متفاوت به حمایت مناسب نیاز دارند، بدون فرض دربارهٔ دانش یا بی‌میلی.",
    "Het niet gebruiken van een portaal werd terecht als onwil van elke bezoeker behandeld. | Not using the portal was rightly treated as unwillingness in every visitor. | استفاده‌نکردن از درگاه به‌درستی بی‌میلی همهٔ مراجعه‌کنندگان شمرده شد.")
add(80,
    "Jo reageert op de nieuwe uitnodiging, maar wil eerst alleen telefonisch kennismaken. | Jo responds to the new invitation but wants an initial telephone introduction only. | یو به دعوت تازه پاسخ می‌دهد، اما ابتدا فقط آشنایی تلفنی می‌خواهد.",
    "We bevestigen dat voorstel en spreken samen een passend vervolg af. | We confirm that proposal and jointly agree a suitable follow-up. | پیشنهاد را تأیید می‌کنیم و با هم ادامهٔ مناسبی تعیین می‌کنیم.",
    "Afwezigheid kan ook iets vertellen over de eerdere ontvangst door de dienst. | Absence can also reveal something about a service's earlier welcome. | غیبت ممکن است دربارهٔ برخورد قبلیِ خدمات نیز چیزی نشان دهد.",
    "Jo's afwezigheid bewees uitsluitend dat hij zich niet aan het oude plan wilde houden. | Jo's absence proved only that he refused to follow the old plan. | غیبت یو فقط ثابت می‌کرد او نمی‌خواست برنامهٔ قدیمی را رعایت کند.")

add(81,
    "De raamcontrole ontdekt één raam waarvan het herstel niet veilig kan worden uitgesteld. | The window check finds one window whose repair cannot safely be postponed. | بررسی پنجره‌ها یک پنجره را پیدا می‌کند که تعمیرش را نمی‌توان با حفظ ایمنی عقب انداخت.",
    "We herzien de fasering met de nieuwe veiligheidsinformatie en maken de kosten zichtbaar. | We revise the phasing using the new safety information and show the costs. | با اطلاعات ایمنی تازه مرحله‌بندی را بازبینی و هزینه‌ها را روشن می‌کنیم.",
    "Schaarse middelen vragen een gemotiveerde prioriteit die bij nieuwe informatie kan veranderen. | Scarce resources require justified priorities that may change with new information. | منابع محدود اولویت مستدل می‌خواهند که با اطلاعات تازه تغییرپذیر باشد.",
    "De lage eerste dakraming bleef ondanks de bekende meerkosten de definitieve begroting. | The low initial roof estimate remained the final budget despite known additional costs. | برآورد کمِ اولیهٔ سقف با وجود هزینهٔ اضافهٔ معلوم، بودجهٔ نهایی ماند.")
add(82,
    "De offerte voor de kleine oven blijkt de noodzakelijke aansluiting niet te omvatten. | The small oven quotation turns out not to include the necessary connection. | پیشنهاد قیمت فر کوچک اتصال ضروری را شامل نمی‌شود.",
    "We rekenen die kost mee voordat we het beschikbare herstelbudget vastleggen. | We include that cost before fixing the available repair reserve. | پیش از تعیین ذخیرهٔ تعمیر، آن هزینه را نیز حساب می‌کنیم.",
    "Een rendementsvergelijking hangt af van realistische aannames en alle relevante kosten. | Comparing returns depends on realistic assumptions and all relevant costs. | مقایسهٔ بازده به فرض‌های واقع‌بینانه و همهٔ هزینه‌های مربوط بستگی دارد.",
    "De hoogste energieprijs uit één jaar bood vanzelf de beste basis voor de investering. | One year's highest energy price automatically offered the best investment basis. | بالاترین قیمت انرژیِ یک سال خودکار بهترین مبنای سرمایه‌گذاری بود.")
add(83,
    "Het nieuwe kostenoverzicht gebruikt het gemiddelde gezin en mist de hoge vervoerskosten van deze medewerker. | The new cost overview uses an average household and misses this worker's high travel costs. | جدول تازه خانوادهٔ متوسط را مبنا می‌گیرد و هزینهٔ بالای رفت‌وآمد این کارمند را نمی‌بیند.",
    "We vergelijken de algemene maatstaf met de concrete kosten zonder ze gelijk te stellen. | We compare the general measure with actual costs without treating them as identical. | معیار کلی را با هزینهٔ واقعی مقایسه می‌کنیم، بدون یکسان‌دانستن آن‌ها.",
    "Een hoger nominaal loon garandeert niet dezelfde koopkracht voor elk huishouden. | Higher nominal pay does not guarantee equal purchasing power for every household. | دستمزد اسمی بیشتر، قدرت خرید یکسان برای همهٔ خانواده‌ها را تضمین نمی‌کند.",
    "Indexering maakte verdere vergelijking van gezinskosten en loonvorming zinloos. | Indexation made further comparison of household costs and pay formation pointless. | شاخص‌بندی، مقایسهٔ بیشتر هزینهٔ خانواده و تعیین دستمزد را بی‌معنا کرد.")
add(84,
    "De inschrijflijst toont per ongeluk wie een lagere bijdrage betaalt. | The registration list accidentally shows who pays a reduced contribution. | فهرست ثبت‌نام تصادفاً نشان می‌دهد چه کسی سهم کمتری می‌پردازد.",
    "We beperken die informatie tot de bevoegde beheerder en herstellen de gedeelde lijst. | We limit that information to the authorised organiser and correct the shared list. | اطلاعات را به مسئول مجاز محدود و فهرست مشترک را اصلاح می‌کنیم.",
    "Gelijke deelname kan verschillende bijdragen vergen zonder iemands situatie publiek te maken. | Equal participation may require different contributions without publicising personal circumstances. | مشارکت برابر ممکن است سهم‌های متفاوت بخواهد، بدون علنی‌کردن شرایط فرد.",
    "Solidariteit vereiste volgens de vereniging een openbare verantwoording van elk gezinsinkomen. | The association considered public disclosure of every household income necessary for solidarity. | انجمن همبستگی را نیازمند اعلام عمومی درآمد همهٔ خانواده‌ها می‌دانست.")
add(85,
    "Een leverancier rekent alvast met een hogere tegemoetkoming die nog niet bevestigd is. | A supplier already assumes a larger reimbursement that has not been confirmed. | تأمین‌کننده از حالا کمک‌هزینهٔ بیشتری را حساب کرده که هنوز تأیید نشده است.",
    "We scheiden bevestigde financiering van verwachtingen in de bijgewerkte raming. | We separate confirmed funding from expectations in the updated estimate. | در برآورد به‌روز، تأمین مالی قطعی را از انتظار جدا می‌کنیم.",
    "Een mogelijke tegemoetkoming is pas een betrouwbare planningsbasis na bevestiging van voorwaarden. | A possible allowance becomes a reliable planning basis only after conditions are confirmed. | کمک‌هزینهٔ احتمالی فقط پس از تأیید شرایط مبنای قابل‌اعتماد برنامه‌ریزی است.",
    "Een aanvraag om vrijstelling was hetzelfde als een toegekende vrijstelling. | Requesting an exemption was equivalent to receiving one. | درخواست معافیت همان دریافت معافیت بود.")
add(86,
    "Een nieuwe schenking is toegezegd, maar wordt pas na de volgende loonbetaling gestort. | A new donation is promised but arrives only after the next wage payment. | کمک مالی تازه وعده داده شده، اما پس از پرداخت حقوق بعدی واریز می‌شود.",
    "We nemen de ontvangstdatum op in de kasplanning voordat we extra uitgaven toestaan. | We include the receipt date in cash planning before allowing additional spending. | پیش از اجازهٔ خرج بیشتر، تاریخ دریافت را در برنامهٔ نقدینگی وارد می‌کنیم.",
    "Voldoende bezit betekent niet dat er op het betaalmoment voldoende geld beschikbaar is. | Sufficient assets do not mean sufficient cash is available when payment is due. | داشتن دارایی کافی به این معنا نیست که در موعد پرداخت حتماً پول کافی در دسترس است.",
    "Een gezonde solvabiliteit sloot ieder tijdelijk liquiditeitsprobleem uit. | Healthy solvency ruled out every temporary cash-flow problem. | توانگری مالی مناسب همهٔ مشکلات موقت نقدینگی را منتفی می‌کرد.")
add(87,
    "Een kandidaat-koper biedt meer, maar wil pas over zes maanden betalen. | A prospective buyer offers more but wants to pay only in six months. | خریدار احتمالی بیشتر پیشنهاد می‌دهد، اما می‌خواهد شش ماه بعد پرداخت کند.",
    "We vergelijken bedrag en betaalmoment voordat we het afbetalingsplan aanpassen. | We compare the amount and payment timing before revising the repayment plan. | پیش از اصلاح برنامهٔ قسط، مبلغ و زمان پرداخت را مقایسه می‌کنیم.",
    "Boekwaarde, verkoopwaarde en ontvangen geld zijn verschillende grootheden. | Book value, sale value and received cash are different quantities. | ارزش دفتری، ارزش فروش و پول دریافت‌شده مقدارهای متفاوتی هستند.",
    "De boekwaarde garandeerde welke prijs een koper onmiddellijk zou betalen. | Book value guaranteed the price a buyer would immediately pay. | ارزش دفتری قیمت پرداخت فوریِ خریدار را تضمین می‌کرد.")
add(88,
    "De tweede aanbieder levert alleen bij een grotere minimale bestelling. | The second supplier delivers only above a larger minimum order. | تأمین‌کنندهٔ دوم فقط با حداقل سفارش بزرگ‌تر تحویل می‌دهد.",
    "We vergelijken de totale voorwaarden voordat we het aanbod als bruikbaar alternatief presenteren. | We compare all terms before presenting the offer as a usable alternative. | پیش از معرفی پیشنهاد به‌عنوان جایگزین عملی، همهٔ شرایط را مقایسه می‌کنیم.",
    "Onderhandelingsruimte groeit pas door een alternatief dat werkelijk beschikbaar is. | Bargaining room grows only through an alternative that is genuinely available. | فضای مذاکره با جایگزینی بیشتر می‌شود که واقعاً در دسترس باشد.",
    "Het gezamenlijke contract bewees dat iedere toekomstige prijsverhoging onredelijk zou zijn. | The joint contract proved that every future price increase would be unreasonable. | قرارداد مشترک ثابت کرد هر افزایش قیمت آینده نامعقول خواهد بود.")
add(89,
    "De gebundelde levering komt vroeger, wanneer de gezamenlijke opslag nog bezet is. | The combined delivery arrives earlier, while shared storage is still occupied. | محمولهٔ مشترک زودتر می‌رسد، وقتی انبار مشترک هنوز پُر است.",
    "We heronderhandelen het levermoment en rekenen eventuele opslagkosten mee. | We renegotiate delivery timing and include any storage costs. | زمان تحویل را دوباره مذاکره و هزینهٔ احتمالی انبار را حساب می‌کنیم.",
    "Schaalvoordelen moeten worden afgewogen tegen opslag en afhankelijkheid. | Economies of scale must be weighed against storage and dependence. | صرفهٔ مقیاس باید در برابر انبار و وابستگی سنجیده شود.",
    "De grootste bestelling was automatisch de beste keuze ongeacht opslagruimte. | The largest order was automatically best regardless of storage space. | بزرگ‌ترین سفارش بدون توجه به فضای انبار خودکار بهترین انتخاب بود.")
add(90,
    "De gekozen leverancier stelt tijdens een proefdag een onduidelijke vervangmaaltijd voor. | During a trial day the chosen supplier proposes an unclear replacement meal. | تأمین‌کنندهٔ انتخاب‌شده در روز آزمایشی غذای جایگزین نامشخصی پیشنهاد می‌دهد.",
    "We toetsen de vervanging aan de afgesproken kwaliteit en leggen afwijkingen vast. | We check the replacement against agreed quality and record deviations. | جایگزین را با کیفیت توافق‌شده می‌سنجیم و انحراف را ثبت می‌کنیم.",
    "Kostenbeheersing omvat voorzienbare gevolgen van onbetrouwbare levering. | Cost control includes foreseeable consequences of unreliable delivery. | کنترل هزینه پیامدهای قابل‌پیش‌بینیِ تحویل نامطمئن را هم دربرمی‌گیرد.",
    "De laagste offerteprijs was volgens de vooraf bepaalde criteria het enige relevante gegeven. | The lowest quoted price was the only relevant factor under the predefined criteria. | طبق معیارهای قبلی فقط کمترین قیمت پیشنهادی مهم بود.")

add(91,
    "Een volgende kandidaat heeft een leeg veld omdat de vraag niet op zijn situatie past. | Another candidate leaves a field blank because the question does not fit their situation. | داوطلب بعدی خانه‌ای را خالی می‌گذارد چون پرسش با شرایطش سازگار نیست.",
    "We laten onvolledige formulieren beoordelen zonder ontbrekende informatie als desinteresse te behandelen. | We review incomplete forms without treating missing information as disinterest. | فرم ناقص را بررسی می‌کنیم، بدون اینکه نبود اطلاعات را بی‌علاقگی بدانیم.",
    "Een ontbrekend digitaal gegeven kan verschillende oorzaken hebben en bewijst geen motivatiegebrek. | Missing digital data can have different causes and does not prove lack of motivation. | دادهٔ دیجیتالِ غایب علت‌های مختلف دارد و بی‌انگیزگی را ثابت نمی‌کند.",
    "De rangschikking gaf automatisch een betrouwbare meting van ieders belangstelling. | The ranking automatically measured everyone's interest reliably. | رتبه‌بندی خودکار علاقهٔ همه را به‌طور معتبر اندازه می‌گرفت.")
add(92,
    "Na de correctie ontvangt de leerling een bevestiging zonder te weten welke aanvraag opnieuw bekeken is. | After correction the learner receives confirmation without knowing which application was reviewed. | پس از اصلاح، دانش‌آموز تأیید می‌گیرد اما نمی‌داند کدام درخواست دوباره بررسی شده است.",
    "We koppelen de uitleg aan de oorspronkelijke aanvraag en de uitgevoerde correctie. | We link the explanation to the original application and the correction made. | توضیح را به درخواست اصلی و اصلاح انجام‌شده پیوند می‌دهیم.",
    "Herstel vraagt zowel een controleerbaar spoor als de mogelijkheid een besluit opnieuw te beoordelen. | Recovery requires a verifiable trail and the ability to reconsider a decision. | اصلاح هم ردِ قابل‌بررسی می‌خواهد و هم امکان بازنگری تصمیم.",
    "De automatische afwijzing moest ongewijzigd blijven omdat zij eenmaal geregistreerd was. | The automatic refusal had to remain unchanged because it had been recorded. | رد خودکار چون یک‌بار ثبت شده بود باید بی‌تغییر می‌ماند.")
add(93,
    "Een vrijwilliger wil de contactlijst ook gebruiken om zijn eigen evenement te promoten. | A volunteer wants to use the contact list to promote their own event too. | داوطلب می‌خواهد فهرست تماس را برای تبلیغ رویداد خودش هم استفاده کند.",
    "We toetsen dat andere gebruik aan de afgesproken bedoeling voordat gegevens worden gedeeld. | We check that other use against the agreed purpose before sharing data. | پیش از اشتراک داده، کاربرد تازه را با هدف توافق‌شده بررسی می‌کنیم.",
    "Minder gegevens verzamelen en toegang beperken zijn aanvullende maatregelen. | Collecting less data and restricting access are complementary measures. | جمع‌آوری دادهٔ کمتر و محدودکردن دسترسی اقدام‌های مکمل‌اند.",
    "Een begrijpelijk toestemmingsformulier voorkwam op zichzelf iedere ongewenste toegang. | An understandable consent form alone prevented all unauthorised access. | فرم رضایت روشن به‌تنهایی جلوی هر دسترسی ناخواسته را می‌گرفت.")
add(94,
    "Het oude account is gesloten, maar een gedeelde toegangscode is niet gewijzigd. | The old account is closed, but a shared access code has not changed. | حساب قدیمی بسته شده، اما رمز مشترک تغییر نکرده است.",
    "We controleren alle overeengekomen toegangswegen binnen de vertrekprocedure. | We check all agreed access routes within the departure procedure. | در روند خروج همکار، همهٔ مسیرهای دسترسی توافق‌شده را بررسی می‌کنیم.",
    "Geen gevonden misbruik betekent niet dat een aangetoonde kwetsbaarheid genegeerd kan worden. | Finding no misuse does not mean a demonstrated vulnerability can be ignored. | پیدانشدن سوءاستفاده به‌معنای امکان نادیده‌گرفتن آسیب‌پذیریِ آشکار نیست.",
    "Het ontbreken van aanwijzingen voor misbruik maakte afsluiting van het account onnodig. | Lack of evidence of misuse made closing the account unnecessary. | نبود نشانهٔ سوءاستفاده بستن حساب را غیرضروری کرد.")
add(95,
    "De nieuwe regel geeft minder alarmen, maar er is nog geen controle op gemiste tekorten uitgevoerd. | The new rule gives fewer alerts, but missed shortages have not yet been checked. | قاعدهٔ تازه هشدار کمتری می‌دهد، اما کمبودهای ازدست‌رفته هنوز بررسی نشده‌اند.",
    "We meten zowel onterechte waarschuwingen als gemiste tekorten voordat we succes melden. | We measure both false alerts and missed shortages before reporting success. | پیش از اعلام موفقیت، هم هشدار بی‌جا و هم کمبود تشخیص‌داده‌نشده را می‌سنجیم.",
    "Minder meldingen bewijst geen betere beslissing wanneer gemiste gevallen buiten beeld blijven. | Fewer alerts do not prove better decisions when missed cases remain unseen. | هشدار کمتر تصمیم بهتر را ثابت نمی‌کند اگر موارد ازدست‌رفته دیده نشوند.",
    "Het aantal rode lampjes was voldoende om beide soorten fouten tegelijk te beoordelen. | The number of red lights was sufficient to assess both error types together. | تعداد چراغ قرمز برای ارزیابی هر دو نوع خطا کافی بود.")
add(96,
    "De lezer past zijn interesses aan, maar krijgt de volgende week dezelfde beperkte aanbevelingen. | The reader edits their interests but receives the same narrow recommendations the next week. | خواننده علاقه‌هایش را عوض می‌کند، اما هفتهٔ بعد همان پیشنهادهای محدود را می‌گیرد.",
    "We controleren of de aanpassing werkelijk invloed heeft en behouden zoeken buiten het profiel. | We check whether the change truly has an effect and retain searching outside the profile. | اثر واقعی تغییر را بررسی می‌کنیم و جست‌وجوی بیرون از نمایه را نگه می‌داریم.",
    "Uitleengedrag kan de omstandigheden van een keuze tonen zonder iemands voorkeur definitief te bepalen. | Borrowing behaviour can reflect circumstances without definitively defining personal preferences. | رفتار امانت‌گرفتن می‌تواند شرایط انتخاب را نشان دهد، بدون تعریف قطعیِ سلیقهٔ فرد.",
    "Drie ontleende thrillers bewezen dat de lezer uitsluitend thrillers wilde lezen. | Three borrowed thrillers proved the reader wanted to read only thrillers. | سه رمان جناییِ امانت‌گرفته ثابت کرد خواننده فقط همان نوع کتاب را می‌خواهد.")
add(97,
    "Een begeleider wil de herkenningspercentages toch gebruiken om groepen te rangschikken. | An instructor still wants to use recognition percentages to rank groups. | مربی باز هم می‌خواهد درصد تشخیص را برای رتبه‌بندی گروه‌ها استفاده کند.",
    "We beperken de cijfers tot technische oefenfeedback en vragen apart onderzoek naar geschiktheid. | We limit the figures to technical practice feedback and request separate suitability research. | عددها را به بازخورد فنی تمرین محدود می‌کنیم و بررسی جداگانهٔ تناسب می‌خواهیم.",
    "Dezelfde software voor iedereen garandeert geen gelijkwaardige meetkwaliteit bij elke groep. | The same software for everyone does not guarantee equal measurement quality for every group. | نرم‌افزار یکسان برای همه، کیفیت سنجش برابر در هر گروه را تضمین نمی‌کند.",
    "Gelijke software maakte onderzoek naar vertegenwoordiging in de opnamen overbodig. | Identical software made research into representation in the recordings unnecessary. | نرم‌افزار یکسان بررسی نمایندگی افراد در ضبط‌ها را غیرضروری کرد.")
add(98,
    "De optionele keuze staat apart, maar is vooraf al aangevinkt. | The optional choice is separate but already ticked. | گزینهٔ اختیاری جدا شده، اما از قبل علامت دارد.",
    "We onderzoeken of de keuze werkelijk vrij en begrijpelijk wordt aangeboden. | We examine whether the choice is genuinely offered freely and understandably. | بررسی می‌کنیم آیا انتخاب واقعاً آزاد و قابل‌فهم ارائه می‌شود.",
    "Een opvallende doorgaan-knop kan verschillende beslissingen ten onrechte samenvoegen. | A prominent continue button can wrongly combine different decisions. | دکمهٔ برجستهٔ ادامه ممکن است تصمیم‌های متفاوت را به‌اشتباه یکی کند.",
    "Doorgaan met inschrijven bewees zonder meer instemming met elk extra gegevensgebruik. | Continuing registration automatically proved agreement to every additional data use. | ادامهٔ ثبت‌نام بی‌چون‌وچرا موافقت با هر کاربرد اضافی داده را ثابت می‌کرد.")
add(99,
    "Na het herstel ziet een bezoeker een oude schermafbeelding en denkt opnieuw dat zijn boeking ontbreekt. | After recovery a visitor sees an old screenshot and again thinks the booking is missing. | پس از بازیابی، بازدیدکننده تصویری قدیمی می‌بیند و دوباره فکر می‌کند رزروش نیست.",
    "We bevestigen de actuele boeking en leggen het verschil tussen weergave en opslag uit. | We confirm the current booking and explain the difference between display and storage. | رزرو فعلی را تأیید می‌کنیم و فرق نمایش و ذخیره‌سازی را توضیح می‌دهیم.",
    "Onzichtbare gegevens zijn niet noodzakelijk verwijderde gegevens. | Data that are not visible are not necessarily deleted. | دادهٔ دیده‌نشده لزوماً حذف نشده است.",
    "Het verdwijnen van boekingen uit beeld bewees dat alle opslag verloren was. | Bookings disappearing from view proved that all stored data were lost. | ناپدیدشدن رزروها از صفحه ثابت کرد تمام ذخیره‌ها از بین رفته‌اند.")
add(100,
    "De papieren formulieren zijn aanwezig, maar medewerkers weten niet wie ze verwerkt. | Paper forms are available, but staff do not know who processes them. | فرم کاغذی هست، اما کارکنان نمی‌دانند چه کسی آن را پردازش می‌کند.",
    "We wijzen een verantwoordelijke voor verwerking aan en bevestigen de ontvangst aan bezoekers. | We assign responsibility for processing and confirm receipt to visitors. | مسئول پردازش تعیین و دریافت را به مراجعه‌کنندگان تأیید می‌کنیم.",
    "Een terugvaloptie ondersteunt zelfstandigheid alleen wanneer zij ook praktisch verwerkt wordt. | A fallback supports independence only when it is processed in practice too. | گزینهٔ جایگزین وقتی استقلال را پشتیبانی می‌کند که عملاً نیز پردازش شود.",
    "Digitale ondersteuning betekende dat medewerkers alle antwoorden namens bezoekers moesten invullen. | Digital support meant staff had to fill every answer in for visitors. | حمایت دیجیتال یعنی کارمندان باید همهٔ پاسخ‌ها را به‌جای مراجعه‌کننده پر می‌کردند.")

assert set(SCENES) == set(range(1, 101))

# Bind each authored follow-up to its source narrative identity.
EXPECTED_TITLES = {1: 'Een bank in de schaduw',
 2: 'De vergeten achterdeur',
 3: 'Het loket op zaterdag',
 4: 'Ook de stille straat',
 5: 'Een prijs met uitleg',
 6: 'Muziek tot hoe laat?',
 7: 'De tekst die niemand begreep',
 8: 'De oude toegangspas',
 9: 'Een klacht zonder spoor',
 10: 'Twee verenigingen, één zaal',
 11: 'De warme leeshoek',
 12: 'Een score voor de zoekzuil',
 13: 'Wie komt na het werk?',
 14: 'Dezelfde proef in een ander filiaal',
 15: 'De kar tussen de rekken',
 16: 'Een alarm voor lange wachttijden',
 17: 'Pijlen die bijna iedereen begreep',
 18: 'Het verbruik na sluitingstijd',
 19: 'Twee herinneringen voor één persoon',
 20: 'Een resultaat zonder tijdwinst',
 21: 'De bestelling van gisteren',
 22: 'Eén telefoon, twee mensen',
 23: 'Alles leek dringend',
 24: 'De handleiding naast de machine',
 25: 'Wie zou terugbellen?',
 26: 'Terug, maar niet tegelijk alles',
 27: 'Een stilgevallen band',
 28: 'Eerst een kleinere oplevering',
 29: 'De stagiair aan tafel',
 30: 'De oplossing in een schriftje',
 31: 'De foto van gisteren',
 32: 'Een compliment dat schuurt',
 33: 'De stem achter de vitrines',
 34: 'De school die niet verdween',
 35: 'De ontbrekende kasbon',
 36: 'De klacht aan het loket',
 37: 'Een alarm zonder naam',
 38: 'Twee berichten over één brug',
 39: 'Meer dan een onhandige oma',
 40: 'De advertentie naast het onderzoek',
 41: 'De natte vloer na het feest',
 42: 'De derde brief',
 43: 'Een klok naast het dossier',
 44: 'Een voorzitter met een band',
 45: 'De foto op de affiche',
 46: 'Drie brieven, drie gevolgen',
 47: 'De afzonderlijke ingang',
 48: 'Het bestand op de oude computer',
 49: 'De kras op de bakfiets',
 50: 'Een gesprek vóór de procedure',
 51: 'Het braakliggende hoekje',
 52: 'De heetste bank op het plein',
 53: 'De ton die al vol zat',
 54: 'Rust zonder omweg',
 55: 'Het pad naar de sporthal',
 56: 'Wonen boven de oude bakkerij',
 57: 'Eerst meten, dan vervangen',
 58: 'Een bank met losse onderdelen',
 59: 'De verkeerde zak',
 60: 'Een kleiner zomerfeest',
 61: 'De jas aan de kapstok',
 62: 'De keuken die niet bestond',
 63: 'Het hoofdstuk vooraan',
 64: 'Een raam op een kier',
 65: 'Een lied met twee namen',
 66: 'Het boek dat terugkwam',
 67: 'Het woord voor thuis',
 68: 'De stoel van grootvader',
 69: 'De doos zonder nummer',
 70: 'De opname met een stilte',
 71: 'Het loket na sluitingstijd',
 72: 'Een stoel bij de tafel',
 73: 'Tussen twee afspraken',
 74: 'Twee agenda’s voor één gezin',
 75: 'De vraag achter het formulier',
 76: 'Niet over haar heen',
 77: 'Een vrije namiddag',
 78: 'Een activiteit die niemand afmeldt',
 79: 'Het portaal blijft leeg',
 80: 'Een tweede eerste gesprek',
 81: 'Het dak dat voorrang kreeg',
 82: 'De oven van de bakkerij',
 83: 'Een loonstrook en een winkelmand',
 84: 'Een bijdrage naar draagkracht',
 85: 'De werkplaats zonder verrassing',
 86: 'Geld op papier',
 87: 'Een machine op de balans',
 88: 'De enige leverancier',
 89: 'De gezamenlijke bestelling',
 90: 'De goedkoopste offerte verloor',
 91: 'Een naam die werd overgeslagen',
 92: 'De teruggevonden afwijzing',
 93: 'De deelnemerslijst',
 94: 'Een deur die openbleef',
 95: 'Te veel rode lampjes',
 96: 'Het aanbevolen boek',
 97: 'De stem die niet paste',
 98: 'Een knop die te snel akkoord zei',
 99: 'De update op maandagochtend',
 100: 'Zelf kiezen aan het loket'}
