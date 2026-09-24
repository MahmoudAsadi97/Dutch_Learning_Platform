"""Original multilingual narrative bank. Shared adjacent-stage spiral review; unreviewed."""
TOPICS = {
'work': ('Werk en samenwerking','Work and collaboration','کار و همکاری'),
'study': ('Leren en onderzoek','Learning and research','یادگیری و پژوهش'),
'community': ('Buurt en samenleving','Neighbourhood and society','محله و جامعه'),
'housing': ('Wonen en ruimte','Housing and space','مسکن و فضا'),
'media': ('Media en informatie','Media and information','رسانه و اطلاعات'),
'environment': ('Milieu en klimaat','Environment and climate','محیط زیست و اقلیم'),
'culture': ('Cultuur en ontmoeting','Culture and encounters','فرهنگ و دیدار'),
'ethics': ('Keuzes en verantwoordelijkheid','Choices and responsibility','انتخاب و مسئولیت'),
'health': ('Gezondheid en welzijn','Health and wellbeing','سلامت و رفاه'),
'economy': ('Geld en openbare diensten','Money and public services','پول و خدمات عمومی'),
}
DATA = r'''
@work|Een plaats aan tafel|A place at the table|جایی پشت میز
het overleg~gezamenlijke bespreking~consultation~گفت‌وگوی مشترک~Het overleg begon zonder de nieuwe collega.~The consultation started without the new colleague.~گفت‌وگوی مشترک بدون همکار تازه آغاز شد.
de uitnodiging~verzoek om deel te nemen~invitation~دعوت‌نامه~Haar uitnodiging bleek naar een oud adres gestuurd.~Her invitation turned out to have been sent to an old address.~معلوم شد دعوت‌نامهٔ او به نشانی قدیمی فرستاده شده بود.
het misverstand~verkeerd begrip~misunderstanding~سوءتفاهم~De voorzitter legde het misverstand uit en belde haar op.~The chair explained the misunderstanding and called her.~رئیس جلسه سوءتفاهم را توضیح داد و به او زنگ زد.
het voorstel~idee om te bespreken~proposal~پیشنهاد~Op haar voorstel wachtte de groep tien minuten.~At her suggestion, the group waited ten minutes.~با پیشنهاد او، گروه ده دقیقه منتظر ماند.
de deelname~het meedoen~participation~مشارکت~Door haar deelname ontdekte het team een fout in de planning.~Her participation helped the team discover an error in the schedule.~مشارکت او به گروه کمک کرد اشتباهی در برنامه پیدا کند.
@work|De ontbrekende handtekening|The missing signature|امضای گمشده
het contract~schriftelijke overeenkomst~contract~قرارداد~Amir kreeg een contract voor een nieuwe baan.~Amir received a contract for a new job.~امیر قراردادی برای شغل تازه دریافت کرد.
de voorwaarde~eis voor een afspraak~condition~شرط~Eén voorwaarde over avondwerk was hem niet duidelijk.~One condition about evening work was unclear to him.~یکی از شرط‌های مربوط به کار عصر برای او روشن نبود.
de toelichting~extra uitleg~clarification~توضیح تکمیلی~Hij vroeg de personeelsdienst om een schriftelijke toelichting.~He asked the human resources department for written clarification.~از بخش منابع انسانی توضیح کتبی خواست.
de bedenktijd~tijd om na te denken~time to consider~فرصت فکر کردن~Hij kreeg twee dagen bedenktijd voordat hij moest tekenen.~He was given two days to consider before signing.~دو روز فرصت داشت پیش از امضا فکر کند.
de handtekening~geschreven naam ter bevestiging~signature~امضا~Daarna zette hij zijn handtekening onder de aangepaste afspraak.~He then signed the revised agreement.~سپس توافق اصلاح‌شده را امضا کرد.
@work|Een eerlijke planning|A fair schedule|برنامه‌ای منصفانه
het rooster~schema van werktijden~work schedule~برنامهٔ شیفت~Het nieuwe rooster gaf telkens dezelfde collega de late dienst.~The new schedule always gave the same colleague the late shift.~برنامهٔ تازه همیشه شیفت آخر را به همان همکار می‌داد.
de werkdruk~hoeveelheid belasting door werk~workload~فشار کاری~Door de hoge werkdruk durfde niemand daar iets over te zeggen.~Because of the heavy workload, nobody dared mention it.~به‌دلیل فشار کاری زیاد، کسی جرئت نمی‌کرد دربارهٔ آن حرف بزند.
de verdeling~manier van toewijzen~distribution~تقسیم~Sara vroeg tijdens de pauze om een eerlijkere verdeling.~During the break, Sara asked for a fairer distribution.~سارا هنگام استراحت خواستار تقسیم منصفانه‌تری شد.
het beurtensysteem~regeling waarbij mensen afwisselen~rotation system~نظام نوبتی~Samen bedachten ze een beurtensysteem voor de late diensten.~Together, they devised a rotation system for the late shifts.~با هم برای شیفت‌های آخر نظامی نوبتی طراحی کردند.
de instemming~het akkoord gaan~agreement~موافقت~Met instemming van het hele team werd het rooster gewijzigd.~With the whole team's agreement, the schedule was changed.~با موافقت تمام گروه، برنامه تغییر کرد.
@work|Een fout op tijd melden|Reporting an error in time|گزارش به‌موقع اشتباه
het bestand~opgeslagen digitaal document~file~پروندهٔ دیجیتال~Lien stuurde per ongeluk een oud bestand naar een klant.~Lien accidentally sent an old file to a client.~لین اشتباهی پرونده‌ای قدیمی برای مشتری فرستاد.
de vergissing~onbedoelde fout~mistake~اشتباه~Toen ze haar vergissing zag, twijfelde ze even.~When she noticed her mistake, she hesitated briefly.~وقتی متوجه اشتباهش شد، لحظه‌ای تردید کرد.
het herstel~het opnieuw juist maken~correction~اصلاح~Ze stuurde meteen een bericht met een voorstel tot herstel.~She immediately sent a message proposing a correction.~بی‌درنگ پیامی با پیشنهاد اصلاح فرستاد.
de verantwoordelijkheid~plicht om rekenschap te geven~responsibility~مسئولیت~Haar leidinggevende waardeerde dat ze verantwoordelijkheid nam.~Her manager appreciated her taking responsibility.~مدیرش از اینکه مسئولیت پذیرفته بود قدردانی کرد.
het vertrouwen~geloof in iemands betrouwbaarheid~trust~اعتماد~De snelle uitleg hielp het vertrouwen van de klant te behouden.~The prompt explanation helped preserve the client's trust.~توضیح سریع به حفظ اعتماد مشتری کمک کرد.
@work|Het stille idee|The quiet idea|فکر ناگفته
het verbeterpunt~zaak die beter kan~area for improvement~مورد قابل بهبود~Een stagiair zag een verbeterpunt in de levering.~An intern noticed an area for improvement in the delivery process.~کارآموز موردی قابل بهبود در فرایند تحویل دید.
de drempel~hindernis die deelname bemoeilijkt~barrier~مانع~Voor hem was spreken in een grote groep een hoge drempel.~For him, speaking in a large group was a major barrier.~برای او صحبت در گروه بزرگ مانع بزرگی بود.
het aanspreekpunt~persoon bij wie men terechtkan~contact person~فرد پاسخ‌گو~Hij besprak zijn idee eerst met zijn vaste aanspreekpunt.~He first discussed his idea with his usual contact person.~ابتدا فکرش را با فرد پاسخ‌گوی همیشگی خود در میان گذاشت.
de proef~kleine test~trial~آزمایش~De ploeg voerde de volgende week een kleine proef uit.~The team conducted a small trial the following week.~گروه هفتهٔ بعد آزمایشی کوچک اجرا کرد.
de besparing~vermindering van kosten of gebruik~saving~صرفه‌جویی~De proef leverde een duidelijke besparing op verpakkingen op.~The trial produced a clear saving in packaging.~آزمایش به صرفه‌جویی مشخصی در بسته‌بندی انجامید.
@study|De onverwachte bron|The unexpected source|منبع غیرمنتظره
het onderzoek~systematisch zoeken naar kennis~research~پژوهش~Voor haar onderzoek zocht Nora informatie over een oude fabriek.~For her research, Nora sought information about an old factory.~نورا برای پژوهشش دنبال اطلاعاتی دربارهٔ کارخانه‌ای قدیمی بود.
het archief~verzameling bewaarde documenten~archive~بایگانی~In het gemeentelijke archief vond ze alleen bouwplannen.~In the municipal archive, she found only building plans.~در بایگانی شهرداری فقط نقشه‌های ساختمان را یافت.
de getuigenis~verslag van iemand die iets meemaakte~testimony~گواهی شاهد~Een buurvrouw bood een getuigenis over haar werk in de fabriek aan.~A neighbour offered testimony about working in the factory.~یکی از همسایه‌ها پیشنهاد کرد تجربهٔ کارش در کارخانه را بازگو کند.
het perspectief~manier van kijken~perspective~دیدگاه~Dat persoonlijke perspectief ontbrak in de officiële documenten.~That personal perspective was missing from the official documents.~آن دیدگاه شخصی در اسناد رسمی وجود نداشت.
de aanvulling~iets dat het geheel vollediger maakt~addition~تکمیل~Met haar toestemming gebruikte Nora het gesprek als aanvulling.~With her permission, Nora used the conversation as an addition.~نورا با اجازهٔ او از گفت‌وگو برای تکمیل پژوهش استفاده کرد.
@study|Twee verschillende uitkomsten|Two different results|دو نتیجهٔ متفاوت
het resultaat~uitkomst van een handeling~result~نتیجه~Twee studenten kregen een verschillend resultaat bij dezelfde proef.~Two students obtained different results from the same experiment.~دو دانشجو از یک آزمایش نتیجه‌های متفاوت گرفتند.
de meetfout~fout bij het meten~measurement error~خطای اندازه‌گیری~Eerst dachten ze aan een meetfout.~At first, they suspected a measurement error.~ابتدا به خطای اندازه‌گیری شک کردند.
de werkwijze~manier waarop men werkt~method~روش کار~Ze vergeleken daarom stap voor stap hun werkwijze.~They therefore compared their methods step by step.~بنابراین روش کارشان را مرحله‌به‌مرحله مقایسه کردند.
de instelling~gekozen stand van een toestel~setting~تنظیم دستگاه~Bij één toestel stond een instelling nog op de oude waarde.~One device still had a setting at its old value.~تنظیم یکی از دستگاه‌ها هنوز روی مقدار قبلی بود.
de herhaling~het opnieuw uitvoeren~repetition~تکرار~Na herhaling met dezelfde instellingen kwamen de resultaten overeen.~After repeating the test with the same settings, the results matched.~پس از تکرار آزمایش با تنظیم‌های یکسان، نتیجه‌ها مطابقت داشتند.
@study|Niet alleen een cijfer|More than a grade|بیش از یک نمره
de beoordeling~oordeel over een prestatie~assessment~ارزیابی~Yara begreep de beoordeling van haar tekst niet.~Yara did not understand the assessment of her text.~یارا ارزیابی نوشته‌اش را نمی‌فهمید.
de opmerking~korte toelichting of reactie~comment~نظر~De opmerking over haar argumenten was erg algemeen.~The comment about her arguments was very general.~نظر مربوط به استدلال‌های او بسیار کلی بود.
het criterium~maatstaf voor een oordeel~criterion~معیار~Ze vroeg welk criterium ze nog niet had gehaald.~She asked which criterion she had not yet met.~پرسید کدام معیار را هنوز برآورده نکرده است.
het voorbeeld~concreet geval ter verduidelijking~example~مثال~De docent wees een voorbeeld van een onbewezen bewering aan.~The lecturer pointed out an example of an unsupported claim.~مدرس نمونه‌ای از ادعای بدون دلیل را نشان داد.
de herwerking~verbeterde nieuwe versie~revision~بازنویسی~Bij de herwerking voegde Yara passende bronnen toe.~In her revision, Yara added suitable sources.~یارا در بازنویسی منابع مناسب اضافه کرد.
@study|De drukke leeszaal|The busy reading room|سالن مطالعهٔ شلوغ
de concentratie~gerichte aandacht~concentration~تمرکز~In de drukke leeszaal verloor Jonas zijn concentratie.~In the busy reading room, Jonas lost his concentration.~یوناس در سالن مطالعهٔ شلوغ تمرکزش را از دست داد.
de afleiding~iets dat de aandacht wegtrekt~distraction~عامل حواس‌پرتی~Vooral de gesprekken naast hem vormden een afleiding.~The conversations beside him were a particular distraction.~به‌ویژه گفت‌وگوهای کنار او حواسش را پرت می‌کردند.
de afspraak~gezamenlijk gemaakte regeling~agreement~توافق~Hij stelde een afspraak over stille uren voor.~He proposed an agreement about quiet hours.~توافقی دربارهٔ ساعت‌های سکوت پیشنهاد کرد.
de uitzondering~geval waarvoor een regel niet geldt~exception~استثنا~Voor groepswerk kwam er een uitzondering in een aparte ruimte.~An exception was made for group work in a separate room.~برای کار گروهی در اتاقی جدا استثنا قائل شدند.
het evenwicht~goede verhouding tussen belangen~balance~تعادل~Zo ontstond een evenwicht tussen samen leren en rustig lezen.~This created a balance between learning together and reading quietly.~به این ترتیب بین یادگیری مشترک و مطالعهٔ آرام تعادل ایجاد شد.
@study|Een vraag durven stellen|Daring to ask a question|جرئت پرسیدن
de lezing~mondelinge voordracht~lecture~سخنرانی~Tijdens een lezing hoorde Mina een onbekend begrip.~During a lecture, Mina heard an unfamiliar concept.~مینا در سخنرانی با مفهومی ناآشنا روبه‌رو شد.
het begrip~idee met een bepaalde betekenis~concept~مفهوم~Ze schreef het begrip op, maar miste de volgende uitleg.~She wrote down the concept but missed the next explanation.~مفهوم را یادداشت کرد، اما توضیح بعدی را نشنید.
de verduidelijking~uitleg die iets begrijpelijker maakt~clarification~روشن‌سازی~Na afloop vroeg ze de spreker om verduidelijking.~Afterwards, she asked the speaker for clarification.~پس از پایان، از سخنران خواست موضوع را روشن‌تر توضیح دهد.
de vergelijking~verband tussen gelijkaardige zaken~comparison~مقایسه~Hij maakte een vergelijking met een situatie uit het dagelijkse leven.~He drew a comparison with an everyday situation.~او موضوع را با موقعیتی از زندگی روزمره مقایسه کرد.
het inzicht~beter begrip van samenhang~insight~درک~Dankzij dat inzicht kon Mina de rest van haar notities begrijpen.~With that insight, Mina could understand the rest of her notes.~با این درک، مینا توانست بقیهٔ یادداشت‌هایش را بفهمد.
@community|Een bank voor iedereen|A bench for everyone|نیمکتی برای همه
de buurtvergadering~bijeenkomst van buurtbewoners~neighbourhood meeting~جلسهٔ محله~Op de buurtvergadering vroegen bewoners om een nieuwe zitbank.~At the neighbourhood meeting, residents asked for a new bench.~در جلسهٔ محله، ساکنان درخواست نیمکت تازه کردند.
de ligging~plaats waar iets zich bevindt~location~موقعیت~Over de ligging bij het kruispunt waren ze het niet eens.~They disagreed about its location near the junction.~دربارهٔ محل آن کنار چهارراه توافق نداشتند.
de toegankelijkheid~mogelijkheid om iets te bereiken of gebruiken~accessibility~دسترس‌پذیری~Een rolstoelgebruiker wees op de toegankelijkheid van het voetpad.~A wheelchair user raised the issue of pavement accessibility.~فردی با ویلچر به دسترس‌پذیری پیاده‌رو اشاره کرد.
het alternatief~andere mogelijke keuze~alternative~گزینهٔ جایگزین~Een plek naast de bibliotheek bleek een beter alternatief.~A place beside the library proved a better alternative.~محلی کنار کتابخانه گزینهٔ بهتری بود.
het draagvlak~steun voor een plan~support~پشتیبانی~Voor die plaats groeide uiteindelijk voldoende draagvlak.~Eventually, enough support grew for that location.~سرانجام آن محل پشتیبانی کافی به دست آورد.
@community|De vergeten straat|The forgotten street|خیابان فراموش‌شده
de bevraging~verzameling van antwoorden op vragen~survey~نظرسنجی~De stad organiseerde een bevraging over verkeersveiligheid.~The city organised a survey about road safety.~شهر نظرسنجی‌ای دربارهٔ ایمنی راه برگزار کرد.
de verspreiding~het rondsturen of verdelen~distribution~توزیع~Bij de verspreiding van de brief werd één straat overgeslagen.~One street was skipped when the letter was distributed.~هنگام توزیع نامه یک خیابان جا افتاد.
de vertegenwoordiging~het namens anderen aanwezig zijn~representation~نمایندگی~Daardoor ontbrak de vertegenwoordiging van die bewoners in de antwoorden.~As a result, those residents were not represented in the responses.~در نتیجه پاسخ‌ها نمایندهٔ نظر آن ساکنان نبودند.
de termijn~vastgestelde periode~deadline period~مهلت~De stad verlengde de termijn om nog te reageren.~The city extended the period for responding.~شهر مهلت پاسخ‌گویی را تمدید کرد.
de inspraak~mogelijkheid om mee te praten~public participation~مشارکت در تصمیم‌گیری~Ook die straat kreeg zo echte inspraak in het verkeersplan.~That street then gained a real say in the traffic plan.~به این ترتیب آن خیابان نیز در طرح ترافیک نقش واقعی پیدا کرد.
@community|Een sleutel te veel|One key too many|یک کلید اضافه
de vrijwilliger~iemand die onbetaald helpt~volunteer~داوطلب~Een vrijwilliger vond na het buurtfeest een sleutel.~A volunteer found a key after the neighbourhood party.~یکی از داوطلبان بعد از جشن محله کلیدی پیدا کرد.
het voorwerp~tastbaar ding~object~شیء~Hij fotografeerde het voorwerp zonder de sleutelcode te tonen.~He photographed the object without showing the key code.~از شیء عکس گرفت، بدون اینکه شمارهٔ کلید دیده شود.
de oproep~bericht met een verzoek~appeal~فراخوان~Zijn oproep op het buurtbord leverde drie reacties op.~His appeal on the neighbourhood noticeboard received three replies.~فراخوان او روی تابلوی محله سه پاسخ گرفت.
de beschrijving~uitleg van kenmerken~description~توصیف~Slechts één reactie bevatte de juiste beschrijving van de sleutelhanger.~Only one reply correctly described the key ring.~فقط یک پاسخ آویز کلید را درست توصیف کرده بود.
de eigenaar~persoon aan wie iets toebehoort~owner~مالک~De eigenaar haalde de sleutel diezelfde avond op.~The owner collected the key that same evening.~مالک همان شب کلید را تحویل گرفت.
@community|De ruimte delen|Sharing the space|استفادهٔ مشترک از فضا
de vereniging~groep met een gezamenlijk doel~association~انجمن~Twee verenigingen wilden op donderdag dezelfde zaal gebruiken.~Two associations wanted to use the same hall on Thursday.~دو انجمن می‌خواستند پنجشنبه از یک سالن استفاده کنند.
de behoefte~iets dat nodig is~need~نیاز~Bij een gesprek bleek hun behoefte niet helemaal dezelfde.~A conversation revealed that their needs were not exactly the same.~در گفت‌وگو معلوم شد نیازهایشان کاملاً یکسان نیست.
de beschikbaarheid~het vrij zijn voor gebruik~availability~دردسترس‌بودن~De beheerder controleerde de beschikbaarheid van een kleinere ruimte.~The manager checked the availability of a smaller room.~مسئول، در دسترس بودن اتاق کوچک‌تری را بررسی کرد.
de oplossing~manier om een probleem te verhelpen~solution~راه‌حل~Een wisselend schema bood een oplossing voor beide groepen.~An alternating schedule offered both groups a solution.~برنامهٔ چرخشی برای هر دو گروه راه‌حل فراهم کرد.
de samenwerking~gezamenlijk werken~cooperation~همکاری~Uit die afspraak groeide later een samenwerking rond sport.~That agreement later developed into cooperation around sport.~آن توافق بعداً به همکاری در زمینهٔ ورزش انجامید.
@community|Niet iedereen online|Not everyone online|همه آنلاین نیستند
de aanvraag~formeel verzoek~application~درخواست رسمی~Voor een buurtpremie moest elke aanvraag digitaal gebeuren.~Every application for a neighbourhood grant had to be submitted digitally.~همهٔ درخواست‌های کمک‌هزینهٔ محله باید دیجیتال ثبت می‌شد.
de vaardigheid~aangeleerde bekwaamheid~skill~مهارت~Sommige bewoners misten de nodige digitale vaardigheid.~Some residents lacked the necessary digital skill.~بعضی ساکنان مهارت دیجیتال لازم را نداشتند.
de uitsluiting~het niet kunnen meedoen~exclusion~محرومیت از مشارکت~Een medewerker waarschuwde voor uitsluiting van oudere buren.~An employee warned about excluding older neighbours.~کارمندی دربارهٔ کنار گذاشته شدن همسایگان سالمند هشدار داد.
de begeleiding~hulp tijdens een proces~guidance~راهنمایی~Het buurthuis bood daarom persoonlijke begeleiding aan.~The community centre therefore offered individual guidance.~بنابراین مرکز محله راهنمایی فردی ارائه کرد.
het loket~plaats voor dienstverlening~service desk~پیشخوان خدمات~Wie dat wilde, kon zijn aanvraag aan het loket invullen.~Anyone who wished could complete the application at the service desk.~هرکس می‌خواست می‌توانست درخواستش را در پیشخوان تکمیل کند.
@housing|Water op het plafond|Water on the ceiling|آب روی سقف
de huurder~iemand die een woning huurt~tenant~مستأجر~Een huurder zag na een storm water op het plafond.~A tenant saw water on the ceiling after a storm.~مستأجری پس از طوفان روی سقف آب دید.
het lek~opening waar vloeistof ontsnapt~leak~نشتی~Hij dacht eerst dat het lek uit de badkamer kwam.~At first, he thought the leak came from the bathroom.~ابتدا فکر کرد نشتی از حمام است.
de vaststelling~waarneming die wordt genoteerd~finding~یافته~De technicus noteerde echter een andere vaststelling.~The technician, however, recorded a different finding.~اما کارشناس یافتهٔ دیگری ثبت کرد.
de herstelling~het repareren~repair~تعمیر~Een kapotte dakpan maakte een snelle herstelling nodig.~A broken roof tile required a prompt repair.~شکستن یک سفال سقف تعمیر فوری را ضروری کرد.
de schade~nadelige beschadiging~damage~خسارت~Door de snelle melding bleef de schade beperkt.~The prompt report kept the damage limited.~گزارش سریع باعث شد خسارت محدود بماند.
@housing|Een rustige binnenplaats|A quiet courtyard|حیاطی آرام
de binnenplaats~open ruimte tussen gebouwen~courtyard~حیاط داخلی~De binnenplaats van het gebouw werd steeds vaker als parking gebruikt.~The building's courtyard was increasingly used for parking.~حیاط داخلی ساختمان بیشتر و بیشتر برای پارک خودرو استفاده می‌شد.
de overlast~hinder voor anderen~nuisance~مزاحمت~Bewoners klaagden over geluid en overlast onder hun ramen.~Residents complained about noise and nuisance below their windows.~ساکنان از سروصدا و مزاحمت زیر پنجره‌ها شکایت داشتند.
het reglement~verzameling afspraken en regels~regulations~مقررات~In het reglement vonden ze een verbod op langdurig parkeren.~They found a ban on long-term parking in the regulations.~در مقررات ممنوعیت پارک طولانی را پیدا کردند.
de naleving~het volgen van regels~compliance~رعایت مقررات~De beheerder beloofde beter op de naleving toe te zien.~The manager promised to monitor compliance more carefully.~مسئول قول داد رعایت مقررات را دقیق‌تر بررسی کند.
het gebruik~manier waarop iets benut wordt~use~استفاده~Daarna bespraken bewoners een gezamenlijk gebruik als tuin.~The residents then discussed using the space as a shared garden.~سپس ساکنان دربارهٔ استفادهٔ مشترک از فضا به‌عنوان باغ گفت‌وگو کردند.
@housing|De rekening begrijpen|Understanding the bill|فهمیدن صورت‌حساب
de afrekening~overzicht van definitieve kosten~final bill~صورت‌حساب نهایی~Lotte schrok van de jaarlijkse afrekening voor verwarming.~Lotte was shocked by the annual heating bill.~لوته از صورت‌حساب سالانهٔ گرمایش تعجب کرد.
het verbruik~hoeveelheid gebruikte energie of goederen~consumption~مصرف~Volgens het overzicht was haar verbruik verdubbeld.~According to the statement, her consumption had doubled.~طبق صورت‌حساب، مصرف او دو برابر شده بود.
de meterstand~getal op een verbruiksmeter~meter reading~عدد کنتور~Ze vergeleek de meterstand met haar eigen foto.~She compared the meter reading with her own photo.~عدد کنتور را با عکس خودش مقایسه کرد.
de correctie~verbetering van een fout~correction~تصحیح~Een verkeerd overgenomen cijfer leidde tot een correctie.~A digit copied incorrectly led to a correction.~یک رقم اشتباه ثبت‌شده باعث تصحیح شد.
het tegoed~bedrag dat men nog ontvangt~credit~بستانکاری~Na de aanpassing had ze zelfs een klein tegoed.~After the adjustment, she even had a small credit.~پس از اصلاح حتی مبلغ کمی بستانکار شد.
@housing|Bouwen naast het park|Building beside the park|ساخت‌وساز کنار پارک
de vergunning~officiële toestemming~permit~مجوز~Een bouwfirma vroeg een vergunning voor flats naast het park.~A building company applied for a permit for flats beside the park.~شرکت ساختمانی برای آپارتمان‌های کنار پارک مجوز خواست.
de schaduw~gebied zonder direct zonlicht~shade~سایه~Omwonenden vreesden extra schaduw in hun tuinen.~Neighbours feared extra shade in their gardens.~همسایه‌ها نگران سایهٔ بیشتر در باغ‌هایشان بودند.
het bezwaar~formeel gemotiveerd verzet~objection~اعتراض~Ze dienden samen een bezwaar met foto's in.~They jointly submitted an objection with photographs.~با هم اعتراضی همراه عکس ثبت کردند.
de aanpassing~gerichte verandering~adjustment~اصلاح~Een aanpassing van de hoogste verdieping verminderde het probleem.~An adjustment to the top floor reduced the problem.~اصلاح طبقهٔ بالایی مشکل را کمتر کرد.
de afweging~vergelijking van verschillende belangen~weighing of interests~سنجش منافع~De beslissing beschreef de afweging tussen woonruimte en leefbaarheid.~The decision described the balance between housing and liveability.~تصمیم، سنجش میان مسکن و کیفیت زندگی را توضیح داد.
@housing|Een kamer met regels|A room with rules|اتاقی با مقررات
de huisgenoot~persoon met wie men samenwoont~housemate~هم‌خانه~Een nieuwe huisgenoot gebruikte 's nachts vaak de wasmachine.~A new housemate often used the washing machine at night.~هم‌خانهٔ تازه اغلب شب‌ها از ماشین لباس‌شویی استفاده می‌کرد.
de gewoonte~regelmatig terugkerend gedrag~habit~عادت~Voor hem was dat een gewone gewoonte na zijn late dienst.~For him, it was a normal habit after his late shift.~برای او این عادت طبیعی پس از شیفت آخر بود.
de ergernis~gevoel van irritatie~annoyance~دلخوری~Bij de anderen groeide de ergernis door het lawaai.~The noise caused growing annoyance among the others.~سروصدا باعث افزایش دلخوری دیگران شد.
het compromis~oplossing met wederzijdse toegevingen~compromise~سازش~Ze bereikten een compromis over twee vaste wasmomenten.~They reached a compromise on two fixed laundry times.~بر سر دو زمان مشخص برای لباس‌شویی سازش کردند.
de leefbaarheid~kwaliteit van het samenleven~liveability~کیفیت زندگی~De nieuwe afspraak verbeterde de leefbaarheid in het huis.~The new agreement improved life in the shared house.~توافق تازه کیفیت زندگی در خانه را بهتر کرد.
'''
DATA += r'''
@media|De foto zonder datum|The undated photograph|عکس بدون تاریخ
de afbeelding~zichtbare voorstelling~image~تصویر~Een afbeelding van een overstroomde straat werd massaal gedeeld.~An image of a flooded street was widely shared.~تصویر خیابانی آب‌گرفته به‌طور گسترده بازنشر شد.
het onderschrift~tekst onder een beeld~caption~زیرنویس تصویر~Het onderschrift beweerde dat de foto die ochtend genomen was.~The caption claimed the photo had been taken that morning.~زیرنویس ادعا می‌کرد عکس همان صبح گرفته شده است.
de herkomst~plaats of bron waar iets vandaan komt~origin~منشأ~Een journalist onderzocht de herkomst van het beeld.~A journalist investigated the origin of the image.~روزنامه‌نگاری منشأ تصویر را بررسی کرد.
het jaartal~aanduiding van een jaar~year~سال~Op een oudere website vond ze hetzelfde beeld met een ander jaartal.~On an older website, she found the same image with a different year.~در وب‌سایتی قدیمی‌تر همان تصویر را با سالی دیگر یافت.
de rechtzetting~openbare verbetering van onjuiste informatie~correction~اصلاحیه~Ze publiceerde een rechtzetting met een link naar de oorspronkelijke foto.~She published a correction linking to the original photo.~اصلاحیه‌ای با پیوند به عکس اصلی منتشر کرد.
@media|Een kop die te veel belooft|A headline that promises too much|تیتر اغراق‌آمیز
de kop~titel boven een nieuwsbericht~headline~تیتر~De kop boven het artikel beloofde een wondermiddel tegen vermoeidheid.~The headline promised a miracle cure for tiredness.~تیتر مقاله وعدهٔ درمان معجزه‌آسای خستگی را می‌داد.
de bewering~uitspraak die waar zou zijn~claim~ادعا~De sterke bewering steunde op een erg kleine studie.~The strong claim rested on a very small study.~ادعای قاطع بر پژوهشی بسیار کوچک استوار بود.
de steekproef~onderzochte selectie uit een groep~sample~نمونهٔ آماری~De steekproef bestond uit slechts twaalf deelnemers.~The sample consisted of only twelve participants.~نمونهٔ آماری فقط دوازده شرکت‌کننده داشت.
de beperking~grens aan wat iets kan aantonen~limitation~محدودیت~Een lezer vroeg waarom die beperking niet vermeld werd.~A reader asked why that limitation had not been mentioned.~خواننده‌ای پرسید چرا این محدودیت ذکر نشده است.
de nuance~klein maar belangrijk onderscheid~nuance~نکتهٔ ظریف~De redactie paste de kop aan om meer nuance te bieden.~The editors changed the headline to provide more nuance.~تحریریه تیتر را اصلاح کرد تا ظرافت بیشتری داشته باشد.
@media|Een stem in het verslag|A voice in the report|صدایی در گزارش
de redactie~groep die publicaties samenstelt~editorial team~تحریریه~De redactie maakte een verslag over een druk marktplein.~The editorial team prepared a report about a busy market square.~تحریریه گزارشی دربارهٔ میدان شلوغ بازار تهیه کرد.
het citaat~letterlijk overgenomen uitspraak~quotation~نقل‌قول~Eén citaat liet een marktkramer bijzonder boos klinken.~One quotation made a market trader sound particularly angry.~یک نقل‌قول، فروشنده را بسیار عصبانی نشان می‌داد.
de context~omstandigheden die betekenis geven~context~بافت~Buiten de context van het gesprek kreeg zijn grap een andere betekenis.~Outside the context of the conversation, his joke acquired a different meaning.~بیرون از بافت گفت‌وگو، شوخی او معنای دیگری پیدا کرده بود.
de opname~vastgelegd beeld of geluid~recording~ضبط~De journaliste luisterde de opname opnieuw af.~The journalist listened to the recording again.~روزنامه‌نگار دوباره به صدای ضبط‌شده گوش داد.
de weergave~manier waarop iets wordt voorgesteld~representation~بازنمایی~Ze wijzigde de weergave zodat ook zijn uitleg zichtbaar werd.~She changed the account so that his explanation was included too.~گزارش را تغییر داد تا توضیح او نیز دیده شود.
@media|De reclame achter de tip|The advertisement behind the tip|تبلیغ پشت توصیه
de aanbeveling~advies om iets te kiezen~recommendation~توصیه~Een blogger gaf een enthousiaste aanbeveling voor een nieuwe rugzak.~A blogger enthusiastically recommended a new backpack.~وبلاگ‌نویسی با اشتیاق کوله‌پشتی تازه‌ای را توصیه کرد.
de vergoeding~betaling voor een prestatie~payment~حق‌الزحمه~Onderaan stond in kleine letters dat hij een vergoeding had gekregen.~Small print at the bottom said he had received payment.~پایین مطلب با حروف ریز نوشته بود که حق‌الزحمه گرفته است.
de onafhankelijkheid~vrijheid van beïnvloeding~independence~استقلال~Een volger stelde daarom vragen over zijn onafhankelijkheid.~A follower therefore questioned his independence.~یکی از دنبال‌کنندگان به همین دلیل استقلال او را زیر سؤال برد.
de vermelding~het uitdrukkelijk noemen~disclosure~ذکر صریح~De blogger plaatste de vermelding voortaan bovenaan zijn berichten.~The blogger then placed the disclosure at the top of his posts.~پس از آن وبلاگ‌نویس این موضوع را بالای مطالبش ذکر کرد.
de transparantie~duidelijkheid over belangen en handelingen~transparency~شفافیت~Die transparantie liet lezers zelf het advies beoordelen.~That transparency allowed readers to judge the advice themselves.~این شفافیت به خوانندگان اجازه داد خودشان توصیه را ارزیابی کنند.
@media|Een bericht met haast|An urgent message|پیامی فوری
de afzender~persoon die een bericht verstuurt~sender~فرستنده~De afzender van een dringend bericht leek de bank te zijn.~The sender of an urgent message appeared to be the bank.~فرستندهٔ پیام فوری ظاهراً بانک بود.
de waarschuwing~bericht over mogelijk gevaar~warning~هشدار~De waarschuwing zei dat haar rekening onmiddellijk zou worden geblokkeerd.~The warning said her account would be blocked immediately.~هشدار می‌گفت حسابش فوراً مسدود خواهد شد.
de bijlage~extra bestand bij een bericht~attachment~پیوست~Fatima opende de bijlage niet en keek eerst naar het adres.~Fatima did not open the attachment and first checked the address.~فاطمه پیوست را باز نکرد و اول نشانی را بررسی کرد.
de vervalsing~iets dat onterecht echt lijkt~forgery~جعل~Een telefoontje naar de bank bevestigde de vervalsing.~A call to the bank confirmed it was a forgery.~تماس با بانک جعلی بودن آن را تأیید کرد.
de melding~doorgegeven bericht over een probleem~report~گزارش~Ze deed een melding en verwijderde het bericht.~She reported the incident and deleted the message.~موضوع را گزارش کرد و پیام را پاک کرد.
@environment|De natte kelder|The wet cellar|زیرزمین خیس
de neerslag~water dat uit de lucht valt~precipitation~بارش~Na uitzonderlijke neerslag liep een kelder onder water.~After exceptional rainfall, a cellar flooded.~پس از بارش غیرعادی، زیرزمینی پر از آب شد.
de afvoer~weg waarlangs water wegstroomt~drainage~راه خروج آب~De afvoer bleek verstopt met bladeren.~The drain turned out to be blocked with leaves.~معلوم شد راه خروج آب با برگ بسته شده است.
het onderhoud~werk om iets goed te houden~maintenance~نگهداری~De bewoners hadden het jaarlijkse onderhoud uitgesteld.~The residents had postponed the annual maintenance.~ساکنان نگهداری سالانه را عقب انداخته بودند.
de voorzorg~maatregel om problemen te voorkomen~precaution~اقدام پیشگیرانه~Als voorzorg controleerden ze voortaan elke herfst de roosters.~As a precaution, they began checking the grates every autumn.~برای پیشگیری، از آن پس هر پاییز دریچه‌ها را بررسی کردند.
het risico~kans op een nadelige gebeurtenis~risk~خطر~Daarmee verkleinden ze het risico, zonder overstroming volledig uit te sluiten.~This reduced the risk without ruling flooding out completely.~این کار خطر را کاهش داد، اما احتمال سیل را کاملاً از بین نبرد.
@environment|Een boom op de parking|A tree in the car park|درختی در پارکینگ
de hitte~zeer warm weer~heat~گرما~Tijdens de hitte was het schoolplein bijna onbruikbaar.~During the heat, the school playground was almost unusable.~هنگام گرما، حیاط مدرسه تقریباً قابل استفاده نبود.
de verharding~bedekking met steen of asfalt~paving~پوشش سنگی یا آسفالتی~De uitgebreide verharding hield de warmte lang vast.~The extensive paving retained heat for a long time.~پوشش گستردهٔ آسفالت گرما را مدت زیادی نگه می‌داشت.
de vergroening~toevoeging van planten en bomen~greening~افزودن فضای سبز~Ouders vroegen om vergroening van een deel van de parking.~Parents requested greening part of the car park.~والدین خواستند بخشی از پارکینگ به فضای سبز تبدیل شود.
het draagvermogen~hoeveelheid die iets kan dragen~load-bearing capacity~ظرفیت تحمل بار~Een deskundige controleerde eerst het draagvermogen boven de ondergrondse kelder.~An expert first checked the load-bearing capacity above the underground cellar.~کارشناس ابتدا ظرفیت تحمل بار بالای زیرزمین را بررسی کرد.
de beplanting~geheel van geplante gewassen~planting~گیاه‌کاری~Daarna koos de school passende beplanting in lichte bakken.~The school then chose suitable plants in lightweight containers.~سپس مدرسه گیاهان مناسب در گلدان‌های سبک انتخاب کرد.
@environment|De fles die terugkwam|The bottle that returned|بطری‌ای که بازگشت
de verpakking~materiaal rond een product~packaging~بسته‌بندی~Een buurtwinkel wilde minder verpakking weggooien.~A neighbourhood shop wanted to throw away less packaging.~فروشگاه محله می‌خواست بسته‌بندی کمتری دور بریزد.
het statiegeld~terugbetaalbaar bedrag voor verpakking~deposit~ودیعهٔ بسته‌بندی~De winkelier voerde statiegeld op glazen flessen in.~The shopkeeper introduced a deposit on glass bottles.~فروشنده برای بطری‌های شیشه‌ای ودیعه تعیین کرد.
de terugname~het opnieuw aannemen van gebruikte spullen~take-back~پس‌گرفتن~Bij de terugname moesten de flessen wel onbeschadigd zijn.~Bottles had to be undamaged when returned.~هنگام پس‌گرفتن، بطری‌ها باید سالم می‌بودند.
de herbruikbaarheid~mogelijkheid tot herhaald gebruik~reusability~قابلیت استفادهٔ مجدد~Na een maand bleek de herbruikbaarheid groter dan verwacht.~After a month, reusability proved greater than expected.~پس از یک ماه، قابلیت استفادهٔ مجدد بیشتر از انتظار بود.
de afvalberg~grote hoeveelheid weggegooid materiaal~waste mountain~انبوه زباله~De afvalberg werd kleiner, terwijl de klanten aan het systeem gewend raakten.~Waste decreased as customers became used to the system.~با عادت کردن مشتریان به این روش، مقدار زباله کمتر شد.
@environment|Licht op het dak|Light on the roof|روشنایی روی بام
de opbrengst~wat een investering of productie oplevert~yield~بازده~Een vereniging verwachtte een hoge opbrengst van zonnepanelen.~An association expected a high yield from solar panels.~انجمنی از پنل‌های خورشیدی انتظار بازده بالا داشت.
de schatting~benadering zonder volledige zekerheid~estimate~برآورد~De eerste schatting hield geen rekening met een naburig gebouw.~The first estimate did not account for a neighbouring building.~برآورد نخست ساختمان مجاور را در نظر نگرفته بود.
de oriëntatie~richting waarin iets staat~orientation~جهت قرارگیری~Een installateur onderzocht de oriëntatie van het dak opnieuw.~An installer re-examined the roof's orientation.~نصاب جهت قرارگیری بام را دوباره بررسی کرد.
de haalbaarheid~mogelijkheid om een plan uit te voeren~feasibility~امکان‌پذیری~Met minder panelen bleef de haalbaarheid van het project positief.~With fewer panels, the project remained feasible.~با پنل‌های کمتر، طرح همچنان امکان‌پذیر بود.
de terugverdientijd~tijd totdat een investering is terugverdiend~payback period~دورهٔ بازگشت سرمایه~De vereniging aanvaardde een langere terugverdientijd op basis van betere cijfers.~The association accepted a longer payback period based on better figures.~انجمن بر پایهٔ ارقام دقیق‌تر، دورهٔ بازگشت سرمایهٔ طولانی‌تری پذیرفت.
@environment|De stille oever|The quiet riverbank|کرانهٔ آرام
de oever~rand van een rivier of meer~riverbank~کرانه~Wandelaars vonden dode vissen langs de oever.~Walkers found dead fish along the riverbank.~رهگذران در کرانه ماهی‌های مرده پیدا کردند.
de vervuiling~verontreiniging van de omgeving~pollution~آلودگی~Ze vermoedden vervuiling door een bedrijf stroomopwaarts.~They suspected pollution from a company upstream.~به آلودگی ناشی از شرکتی در بالادست شک کردند.
de bemonstering~het nemen van materiaal voor onderzoek~sampling~نمونه‌برداری~Een milieudienst begon met bemonstering op verschillende plaatsen.~An environmental service began sampling at several locations.~ادارهٔ محیط زیست در چند محل نمونه‌برداری را آغاز کرد.
de zuurstof~gas dat levende wezens nodig hebben~oxygen~اکسیژن~Het water bevatte door de warmte uitzonderlijk weinig zuurstof.~Because of the heat, the water contained unusually little oxygen.~آب به‌دلیل گرما اکسیژن بسیار کمی داشت.
de oorzaak~datgene waardoor iets gebeurt~cause~علت~De oorzaak was dus ingewikkelder dan de eerste verdenking deed vermoeden.~The cause was therefore more complex than the first suspicion suggested.~بنابراین علت پیچیده‌تر از چیزی بود که ظن اولیه نشان می‌داد.
@culture|Een verhaal in twee talen|A story in two languages|داستانی به دو زبان
de vertaling~tekst in een andere taal~translation~ترجمه~Voor een buurtpodium maakte Leyla een vertaling van haar verhaal.~For a neighbourhood performance, Leyla translated her story.~لیلا برای اجرای محله داستانش را ترجمه کرد.
de uitdrukking~vaste combinatie van woorden~expression~اصطلاح~Eén uitdrukking klonk letterlijk vertaald erg vreemd.~One expression sounded very strange when translated literally.~یکی از اصطلاح‌ها در ترجمهٔ لفظی بسیار عجیب بود.
de betekenis~inhoud van een woord of zin~meaning~معنا~Ze legde de betekenis aan een Nederlandstalige vriend uit.~She explained its meaning to a Dutch-speaking friend.~معنای آن را برای دوستی هلندی‌زبان توضیح داد.
de gevoelswaarde~emotionele betekenis van taal~emotional connotation~بار عاطفی~Samen zochten ze een zin met dezelfde gevoelswaarde.~Together, they sought a sentence with the same emotional connotation.~با هم دنبال جمله‌ای با همان بار عاطفی گشتند.
de voordracht~het voorlezen of opvoeren van tekst~recitation~دکلمه~Bij de voordracht begreep het publiek de grap zonder extra uitleg.~During the performance, the audience understood the joke without extra explanation.~هنگام دکلمه، مخاطبان بدون توضیح بیشتر شوخی را فهمیدند.
@culture|Een stoel op de eerste rij|A seat in the front row|صندلی ردیف اول
de voorstelling~opvoering voor publiek~performance~نمایش~De voorstelling in het buurthuis was bijna uitverkocht.~The performance at the community centre was nearly sold out.~تقریباً همهٔ بلیت‌های نمایش مرکز محله فروخته شده بود.
de reservering~vooraf vastgelegde plaats~reservation~رزرو~Een bezoeker meldde dat zijn reservering nergens terug te vinden was.~A visitor reported that his reservation could not be found.~یکی از بازدیدکنندگان گفت رزرو او پیدا نمی‌شود.
de bevestiging~bericht dat een afspraak vaststaat~confirmation~تأییدیه~Hij toonde de bevestiging op zijn telefoon.~He showed the confirmation on his phone.~تأییدیه را روی تلفنش نشان داد.
de ontvangst~het verwelkomen en toelaten~reception~پذیرش~De medewerker van de ontvangst ontdekte een dubbele naam in de lijst.~The reception worker discovered a duplicate name on the list.~کارمند پذیرش نامی تکراری در فهرست یافت.
de zitplaats~plaats om te zitten~seat~جای نشستن~Vlak voor het begin kreeg de bezoeker toch zijn zitplaats.~Just before the start, the visitor finally received his seat.~درست پیش از شروع، بازدیدکننده بالاخره جای خود را گرفت.
@culture|Het verdwenen gereedschap|The missing tool|ابزار گمشده
de ambacht~vak met handwerk~craft~پیشهٔ دستی~In een museum demonstreerde een maker een oud ambacht.~At a museum, a maker demonstrated an old craft.~در موزه، صنعتگری یک پیشهٔ دستی قدیمی را نمایش می‌داد.
het gereedschap~middelen om iets te maken~tools~ابزار~Na de middag ontbrak een stuk gereedschap.~After lunch, a tool was missing.~پس از ناهار یک ابزار نبود.
de verplaatsing~het naar een andere plek brengen~relocation~جابه‌جایی~Een medewerker herinnerde zich de verplaatsing van een tafel.~An employee remembered that a table had been moved.~کارمندی به یاد آورد که میزی جابه‌جا شده است.
het voorval~gebeurtenis die aandacht vraagt~incident~پیشامد~Het voorval bleek geen diefstal maar een opruimfout.~The incident turned out to be a tidying mistake rather than theft.~معلوم شد پیشامد دزدی نبوده، بلکه اشتباه هنگام مرتب کردن بوده است.
het vertrouwenwekkende~dat wat vertrouwen wekt~the reassuring aspect~جنبهٔ اطمینان‌بخش~Het vertrouwenwekkende was dat niemand zonder bewijs werd beschuldigd.~The reassuring aspect was that nobody was accused without evidence.~جنبهٔ اطمینان‌بخش این بود که کسی بدون دلیل متهم نشد.
@culture|De lege muur|The empty wall|دیوار خالی
de tentoonstelling~publieke presentatie van werken~exhibition~نمایشگاه~Een tentoonstelling wilde ook werk van buurtbewoners tonen.~An exhibition wanted to include work by local residents.~نمایشگاهی می‌خواست آثار اهالی محله را نیز نشان دهد.
de selectie~keuze uit meerdere mogelijkheden~selection~گزینش~Bij de selectie bleven vooral bekende namen over.~The selection mostly retained well-known names.~در گزینش، بیشتر نام‌های شناخته‌شده باقی ماندند.
de diversiteit~aanwezigheid van verschillen~diversity~تنوع~Een jonge organisator miste diversiteit in de gekozen werken.~A young organiser felt the selected works lacked diversity.~برگزارکننده‌ای جوان در آثار انتخاب‌شده تنوع نمی‌دید.
de oproepprocedure~manier waarop deelnemers worden uitgenodigd~open-call procedure~روند فراخوان~De groep veranderde de oproepprocedure en verspreidde ook papieren folders.~The group changed the open-call procedure and distributed paper leaflets too.~گروه روند فراخوان را تغییر داد و برگهٔ چاپی هم پخش کرد.
de ontdekking~het vinden van iets onbekends~discovery~کشف~De ontdekking van drie onbekende makers gaf de lege muur een nieuwe invulling.~Discovering three unknown artists gave the empty wall a new purpose.~کشف سه هنرمند ناشناخته به دیوار خالی معنای تازه‌ای داد.
@culture|Een feest met twee ritmes|A celebration with two rhythms|جشنی با دو ریتم
de traditie~doorgegeven gewoonte~tradition~سنت~Voor het schoolfeest bracht ieder gezin een eigen traditie mee.~For the school celebration, every family brought a tradition of its own.~برای جشن مدرسه، هر خانواده سنتی از خود آورد.
het ritueel~handeling met symbolische betekenis~ritual~آیین~Een ritueel met kaarsen mocht niet in de sportzaal plaatsvinden.~A candle ritual was not allowed in the sports hall.~اجرای آیینی با شمع در سالن ورزش مجاز نبود.
de gevoeligheid~zaak die zorgvuldig behandeld moet worden~sensitivity~حساسیت~De organisator besprak die gevoeligheid zonder de gewoonte belachelijk te maken.~The organiser discussed the sensitive issue without ridiculing the custom.~برگزارکننده بدون تمسخر رسم، دربارهٔ این حساسیت گفت‌وگو کرد.
de symboliek~betekenis achter een teken of handeling~symbolism~نمادپردازی~Het gezin legde de symboliek van het licht uit.~The family explained the symbolism of the light.~خانواده معنای نمادین نور را توضیح داد.
de wederkerigheid~het over en weer geven~reciprocity~عمل متقابل~Met veilige lampjes en aandacht voor elkaars uitleg ontstond wederkerigheid.~Safe lamps and attention to each other's explanations created reciprocity.~چراغ‌های ایمن و توجه به توضیح یکدیگر، رابطه‌ای متقابل ایجاد کرد.
@ethics|De gevonden portefeuille|The found wallet|کیف پول پیدا‌شده
de portefeuille~kleine tas voor geld en kaarten~wallet~کیف پول~Aan de bushalte vond Rob een portefeuille.~At the bus stop, Rob found a wallet.~روب در ایستگاه اتوبوس کیف پولی پیدا کرد.
de verleiding~aantrekkingskracht om iets te doen~temptation~وسوسه~Even voelde hij de verleiding om het losse geld te houden.~For a moment, he felt tempted to keep the cash.~لحظه‌ای وسوسه شد پول نقد را نگه دارد.
het geweten~innerlijk besef van goed en fout~conscience~وجدان~Zijn geweten liet hem aan de onbekende eigenaar denken.~His conscience made him think of the unknown owner.~وجدانش او را به فکر صاحب ناشناس انداخت.
de teruggave~het teruggeven aan de eigenaar~return~بازگرداندن~Hij regelde de teruggave via het gevondenvoorwerpenloket.~He arranged its return through the lost-property desk.~بازگرداندن آن را از طریق بخش اشیای گمشده پیگیری کرد.
de opluchting~gevoel nadat zorgen verdwijnen~relief~آسودگی~De opluchting van de eigenaar maakte duidelijk wat dat kleine besluit betekende.~The owner's relief showed what that small decision meant.~آسودگی صاحب کیف نشان داد آن تصمیم کوچک چه اهمیتی داشت.
@ethics|Een naam op het verslag|A name on the report|نامی روی گزارش
de bijdrage~aandeel in gezamenlijk werk~contribution~سهم در کار~Bij een groepsverslag was de bijdrage van Emma nauwelijks zichtbaar.~Emma's contribution was barely visible in a group report.~سهم اما در گزارش گروهی به‌سختی دیده می‌شد.
de erkenning~het waarderen en benoemen van inzet~recognition~قدردانی~Ze vroeg niet om een hoger cijfer, maar om erkenning.~She asked for recognition, not a higher grade.~نمرهٔ بالاتر نمی‌خواست، بلکه خواهان به‌رسمیت‌شناختن سهمش بود.
de toeschrijving~het koppelen van werk aan een maker~attribution~انتساب~Het team controleerde de toeschrijving van alle hoofdstukken.~The team checked the attribution of every chapter.~گروه انتساب همهٔ فصل‌ها را بررسی کرد.
de rechtvaardigheid~eerlijke behandeling~fairness~عدالت~Daarbij ging rechtvaardigheid boven het vermijden van een lastig gesprek.~Fairness took priority over avoiding a difficult conversation.~در این کار عدالت بر پرهیز از گفت‌وگوی دشوار اولویت داشت.
de waardering~positief oordeel over inzet~appreciation~ارزش‌گذاری~Een correcte auteurslijst gaf iedereen de nodige waardering.~An accurate author list gave everyone due appreciation.~فهرست درست نویسندگان برای تلاش همه ارزش قائل شد.
@ethics|Kijken of helpen|Watch or help|تماشا یا کمک
de omstander~persoon die erbij staat~bystander~تماشاگر~Een omstander zag iemand naast een fiets vallen.~A bystander saw someone fall beside a bicycle.~یکی از رهگذران دید فردی کنار دوچرخه افتاد.
de aarzeling~kort twijfelen voor een handeling~hesitation~تردید~Na een korte aarzeling vroeg hij of hulp nodig was.~After a brief hesitation, he asked whether help was needed.~پس از تردیدی کوتاه پرسید آیا کمک لازم است.
de toestemming~akkoord om iets te doen~permission~اجازه~Met toestemming van de fietser belde hij een familielid.~With the cyclist's permission, he called a family member.~با اجازهٔ دوچرخه‌سوار به یکی از اعضای خانواده‌اش زنگ زد.
de inmenging~tussenkomst in andermans zaken~interference~دخالت~Zo bleef zijn hulp beperkt en werd ze geen ongewenste inmenging.~His help remained limited and did not become unwanted interference.~به این ترتیب کمکش محدود ماند و به دخالت ناخواسته تبدیل نشد.
de nabijheid~het dichtbij en beschikbaar zijn~presence~حضور نزدیک~Zijn rustige nabijheid hielp de fietser te bekomen.~His calm presence helped the cyclist recover.~حضور آرام او به دوچرخه‌سوار کمک کرد حالش بهتر شود.
@ethics|De lijst met namen|The list of names|فهرست نام‌ها
de privacy~bescherming van het persoonlijke leven~privacy~حریم خصوصی~Een sportclub wilde de privacy van deelnemers beter beschermen.~A sports club wanted to protect participants' privacy better.~باشگاهی ورزشی می‌خواست از حریم خصوصی شرکت‌کنندگان بهتر محافظت کند.
de gegevens~vastgelegde informatie~data~داده‌ها~Toch hing bij de ingang een lijst met telefoongegevens.~Yet a list of phone details hung by the entrance.~با این حال، فهرست شماره‌های تلفن کنار ورودی آویزان بود.
de noodzaak~dat wat werkelijk nodig is~necessity~ضرورت~Een lid vroeg naar de noodzaak van die openbare lijst.~A member questioned the necessity of the public list.~یکی از اعضا دربارهٔ ضرورت عمومی بودن آن فهرست پرسید.
de bewaartermijn~tijd waarin gegevens worden bewaard~retention period~مدت نگهداری~De club bepaalde een korte bewaartermijn voor contactgegevens.~The club set a short retention period for contact details.~باشگاه مدت کوتاهی برای نگهداری اطلاعات تماس تعیین کرد.
de afscherming~beperking van toegang~restricted access~محدودسازی دسترسی~Met afscherming bleven de nummers alleen voor de verantwoordelijke bereikbaar.~Restricted access made the numbers available only to the person responsible.~با محدودسازی دسترسی، فقط مسئول مربوطه به شماره‌ها دسترسی داشت.
@ethics|Een cadeau met een vraag|A gift with a question|هدیه‌ای همراه درخواست
de gunst~voordeel dat iemand verleent~favour~لطف~Een leverancier vroeg een inkoper om een kleine gunst.~A supplier asked a buyer for a small favour.~تأمین‌کننده از مسئول خرید لطف کوچکی خواست.
het geschenk~iets dat men cadeau geeft~gift~هدیه~Tegelijk bood hij haar een duur geschenk aan.~At the same time, he offered her an expensive gift.~هم‌زمان هدیه‌ای گران‌قیمت به او پیشنهاد کرد.
de belangenvermenging~botsing tussen persoonlijke en professionele belangen~conflict of interest~تداخل منافع~Zij herkende het risico op belangenvermenging.~She recognised the risk of a conflict of interest.~او خطر تداخل منافع را تشخیص داد.
de weigering~het niet aanvaarden~refusal~امتناع~Haar beleefde weigering hield de relatie zakelijk.~Her polite refusal kept the relationship professional.~امتناع مؤدبانه‌اش رابطه را حرفه‌ای نگه داشت.
de integriteit~eerlijk en betrouwbaar handelen~integrity~درستکاری~Door de afspraak te registreren beschermde ze ook haar integriteit.~By recording the arrangement, she also protected her integrity.~با ثبت توافق، از درستکاری خود نیز محافظت کرد.
'''
DATA += r'''
@health|Een vraag na het consult|A question after the consultation|پرسشی بعد از ویزیت
het consult~gesprek met een zorgverlener~consultation~ویزیت~Na het consult merkte Eva dat ze een vraag vergeten was.~After the consultation, Eva realised she had forgotten a question.~اوا پس از ویزیت متوجه شد پرسشی را فراموش کرده است.
de bijwerking~ongewenst bijkomend effect~side effect~عارضهٔ جانبی~Ze wist niet welke bijwerking ze moest melden.~She did not know which side effect she should report.~نمی‌دانست کدام عارضهٔ جانبی را باید گزارش کند.
de bijsluiter~informatie bij een geneesmiddel~patient leaflet~برگهٔ راهنمای دارو~De bijsluiter bevatte veel termen die ze niet begreep.~The patient leaflet contained many terms she did not understand.~برگهٔ راهنما اصطلاح‌های زیادی داشت که نمی‌فهمید.
de raadpleging~gesprek om deskundig advies te krijgen~consultation~مشاوره~Bij een korte telefonische raadpleging legde de apotheker de instructies uit.~In a short telephone consultation, the pharmacist explained the instructions.~در مشاورهٔ کوتاه تلفنی، داروساز دستورها را توضیح داد.
de opvolging~verdere controle na een eerste handeling~follow-up~پیگیری~Samen noteerden ze wanneer verdere opvolging nodig was.~Together, they noted when further follow-up would be needed.~با هم یادداشت کردند چه زمانی پیگیری بیشتر لازم است.
@health|Een pauze zonder scherm|A screen-free break|استراحت بدون صفحه‌نمایش
de vermoeidheid~gebrek aan energie~tiredness~خستگی~Na lange werkdagen voelde Pieter steeds meer vermoeidheid.~After long working days, Pieter felt increasingly tired.~پیتر پس از روزهای کاری طولانی خستگی بیشتری احساس می‌کرد.
de belasting~druk op lichaam of geest~strain~فشار~Hij besprak de belasting met zijn leidinggevende.~He discussed the strain with his manager.~دربارهٔ فشار کار با مدیرش صحبت کرد.
de onderbreking~tijdelijke stop~break~وقفه~Een korte onderbreking tussen vergaderingen bleek mogelijk.~A short break between meetings proved possible.~وقفه‌ای کوتاه بین جلسه‌ها امکان‌پذیر بود.
het herstelmoment~tijd om opnieuw op krachten te komen~recovery moment~زمان تجدید قوا~Hij gebruikte dat herstelmoment voor een wandeling zonder telefoon.~He used that recovery moment for a walk without his phone.~از آن زمان برای پیاده‌روی بدون تلفن استفاده کرد.
de volhoudbaarheid~mogelijkheid om iets langdurig vol te houden~sustainability over time~قابلیت ادامه در بلندمدت~Na twee weken bespraken ze de volhoudbaarheid van de nieuwe werkafspraken.~After two weeks, they discussed whether the new work arrangements could be sustained.~پس از دو هفته بررسی کردند آیا می‌توان توافق‌های کاری تازه را ادامه داد.
@health|Een trap te veel|One staircase too many|یک راه‌پلهٔ اضافی
de revalidatie~herstel van functioneren na ziekte of letsel~rehabilitation~توان‌بخشی~Tijdens haar revalidatie mocht Els weer naar de bibliotheek.~During her rehabilitation, Els could return to the library.~الس در دورهٔ توان‌بخشی دوباره توانست به کتابخانه برود.
de mobiliteit~mogelijkheid om zich te verplaatsen~mobility~توان جابه‌جایی~Haar beperkte mobiliteit maakte de ingang met trappen moeilijk.~Her reduced mobility made the stepped entrance difficult.~محدودیت حرکتی، ورود از پله‌ها را برایش دشوار می‌کرد.
de helling~schuin oplopend vlak~ramp~سطح شیب‌دار~Een medewerker wees haar een helling achter het gebouw.~An employee showed her a ramp behind the building.~کارمندی سطح شیب‌دار پشت ساختمان را نشانش داد.
de bewegwijzering~borden die de weg tonen~signage~راهنمای مسیر~Els stelde betere bewegwijzering aan de hoofdingang voor.~Els suggested better signs at the main entrance.~الس پیشنهاد کرد ورودی اصلی راهنمای مسیر بهتری داشته باشد.
de zelfstandigheid~mogelijkheid om zonder hulp te handelen~independence~استقلال~Een duidelijk bord vergrootte haar zelfstandigheid bij volgende bezoeken.~A clear sign increased her independence on future visits.~تابلویی روشن استقلال او را در مراجعه‌های بعدی بیشتر کرد.
@health|De stille mantelzorger|The quiet carer|مراقب خاموش
de mantelzorg~onbetaalde zorg voor een naaste~informal care~مراقبت غیررسمی از نزدیکان~Naast haar baan verleende Nadia mantelzorg aan haar vader.~Alongside her job, Nadia provided informal care for her father.~نادیا علاوه بر شغلش از پدرش مراقبت می‌کرد.
de draagkracht~vermogen om belasting aan te kunnen~capacity to cope~توان تحمل~Na enkele maanden bereikte haar draagkracht een grens.~After several months, her capacity to cope reached a limit.~پس از چند ماه توان تحملش به حد نهایی رسید.
de ondersteuning~praktische of emotionele hulp~support~حمایت~Ze vroeg de lokale dienst welke ondersteuning beschikbaar was.~She asked the local service what support was available.~از خدمات محلی پرسید چه حمایتی در دسترس است.
de ontlasting~vermindering van iemands taken~relief from duties~کاهش بار مسئولیت~Een vaste namiddag opvang gaf haar enige ontlasting.~A regular afternoon of care gave her some relief.~یک بعدازظهر ثابتِ مراقبت جایگزین، بار او را کمی سبک کرد.
de draaglast~hoeveelheid verplichtingen en zorgen~burden~بار مسئولیت~De draaglast verdween niet, maar werd beter verdeeld.~The burden did not disappear, but it became better shared.~بار مسئولیت از بین نرفت، اما بهتر تقسیم شد.
@health|De wandeling die doorging|The walk that went ahead|پیاده‌روی‌ای که انجام شد
de drempelvrees~angst om aan iets nieuws deel te nemen~fear of joining~ترس از شروع مشارکت~Door drempelvrees stelde Koen zijn eerste groepswandeling uit.~Fear of joining made Koen postpone his first group walk.~ترس از پیوستن باعث شد کون نخستین پیاده‌روی گروهی‌اش را عقب بیندازد.
de kennismaking~eerste ontmoeting~introduction~آشنایی~Een begeleider bood vooraf een korte kennismaking aan.~A guide offered a brief introduction beforehand.~راهنما پیشاپیش دیداری کوتاه برای آشنایی پیشنهاد کرد.
de verwachting~idee over wat zal gebeuren~expectation~انتظار~Ze bespraken zijn verwachting over afstand en tempo.~They discussed his expectations about distance and pace.~دربارهٔ انتظار او از مسافت و سرعت صحبت کردند.
de aanmoediging~steun om iets te proberen~encouragement~تشویق~Met die aanmoediging verscheen hij op zaterdagochtend.~With that encouragement, he turned up on Saturday morning.~با آن تشویق، صبح شنبه حاضر شد.
de verbondenheid~gevoel dat men bij anderen hoort~sense of belonging~احساس تعلق~Na afloop bleef vooral een gevoel van verbondenheid hangen.~Afterwards, a sense of belonging was what stayed with him most.~پس از پایان، بیش از همه احساس تعلق در او باقی ماند.
@health|Het formulier aan de balie|The form at reception|فرم پذیرش
de zorgverlener~persoon die professionele zorg biedt~care provider~ارائه‌دهندهٔ خدمات درمانی~Een zorgverlener gaf Ramin een lang formulier.~A care provider gave Ramin a long form.~ارائه‌دهندهٔ خدمات درمانی فرم بلندی به رامین داد.
de voorgeschiedenis~eerdere relevante gebeurtenissen~medical history~سابقهٔ پزشکی~De vragen over zijn voorgeschiedenis waren lastig geformuleerd.~The questions about his medical history were difficult to understand.~پرسش‌های مربوط به سابقهٔ پزشکی او دشوار نوشته شده بودند.
de vertrouwelijkheid~bescherming tegen ongewenste bekendmaking~confidentiality~محرمانگی~Hij vroeg eerst hoe de vertrouwelijkheid geregeld was.~He first asked how confidentiality was ensured.~ابتدا پرسید محرمانگی چگونه رعایت می‌شود.
de uitleg~verduidelijkende informatie~explanation~توضیح~Na een rustige uitleg vulde hij de nodige gegevens in.~After a calm explanation, he filled in the necessary information.~پس از توضیح آرام، اطلاعات لازم را وارد کرد.
de geruststelling~vermindering van ongerustheid~reassurance~اطمینان‌بخشی~De geruststelling kwam vooral doordat hij zelf vragen mocht stellen.~He felt reassured mainly because he was allowed to ask questions himself.~بیشتر به این دلیل آرام شد که می‌توانست خودش سؤال بپرسد.
@health|Een onduidelijke affiche|An unclear poster|پوستر نامفهوم
de preventie~voorkomen van problemen~prevention~پیشگیری~Een affiche over preventie hing in het sportcentrum.~A prevention poster hung in the sports centre.~پوستری دربارهٔ پیشگیری در مرکز ورزشی نصب بود.
de doelgroep~groep voor wie iets bedoeld is~target group~گروه هدف~De doelgroep bestond vooral uit jongeren.~The target group consisted mainly of young people.~گروه هدف بیشتر جوانان بودند.
de vakterm~woord uit een gespecialiseerd domein~technical term~اصطلاح تخصصی~Toch bevatte bijna elke zin een moeilijke vakterm.~Yet almost every sentence contained a difficult technical term.~با این حال تقریباً هر جمله اصطلاح تخصصی دشواری داشت.
de begrijpelijkheid~mate waarin iets duidelijk is~comprehensibility~قابل‌فهم‌بودن~Een jongerenpanel testte de begrijpelijkheid van een nieuwe versie.~A youth panel tested the comprehensibility of a new version.~گروهی از جوانان قابل‌فهم بودن نسخهٔ تازه را آزمایش کردند.
de verbetering~verandering die iets beter maakt~improvement~بهبود~Hun eigen woorden zorgden voor een duidelijke verbetering.~Their own words produced a clear improvement.~استفاده از واژه‌های خودشان باعث بهبود روشنی شد.
@health|De afspraak verplaatsen|Moving the appointment|جابجایی وقت
de beschikbaarheidslijst~overzicht van vrije momenten~availability list~فهرست زمان‌های آزاد~De beschikbaarheidslijst van de praktijk leek helemaal vol.~The practice's availability list appeared completely full.~فهرست زمان‌های آزاد مطب کاملاً پر به نظر می‌رسید.
de annulering~het laten vervallen van een afspraak~cancellation~لغو~Door een annulering kwam toch een plaats vrij.~A cancellation nevertheless freed up a slot.~با یک لغو، بالاخره زمانی آزاد شد.
de verwittiging~bericht om iemand op de hoogte te brengen~notification~اطلاع‌رسانی~De verwittiging bereikte Samira pas tijdens haar werk.~The notification reached Samira while she was at work.~اطلاع‌رسانی زمانی به سمیرا رسید که سر کار بود.
de bereikbaarheid~mogelijkheid om iemand te bereiken~contactability~قابلیت تماس~Ze sprak een beter kanaal voor haar bereikbaarheid af.~She agreed on a better channel for reaching her.~بر سر راه بهتری برای تماس با خودش توافق کرد.
het tijdsvenster~afgebakende periode~time window~بازهٔ زمانی~Binnen het afgesproken tijdsvenster kon ze de nieuwe afspraak bevestigen.~Within the agreed time window, she could confirm the new appointment.~در بازهٔ زمانی توافق‌شده توانست وقت تازه را تأیید کند.
@health|Een veilige sportles|A safe sports class|کلاس ورزشی ایمن
de warming-up~voorbereidende beweging voor sport~warm-up~گرم‌کردن~Een nieuwe lesgever wilde de warming-up overslaan.~A new instructor wanted to skip the warm-up.~مربی تازه می‌خواست گرم‌کردن را حذف کند.
de voorzichtigheid~zorg om schade te vermijden~caution~احتیاط~Een deelnemer vroeg uit voorzichtigheid naar de opbouw van de les.~Out of caution, a participant asked about the structure of the class.~یکی از شرکت‌کنندگان از روی احتیاط دربارهٔ ساختار کلاس پرسید.
de aanpasbaarheid~mogelijkheid om iets te wijzigen~adaptability~قابلیت تطبیق~De vaste oefeningen boden weinig aanpasbaarheid.~The fixed exercises offered little adaptability.~تمرین‌های ثابت قابلیت تطبیق کمی داشتند.
de belastbaarheid~hoeveelheid inspanning die iemand aankan~capacity for exertion~توان تحمل فعالیت~Daarom besprak de groep verschillen in belastbaarheid.~The group therefore discussed differences in capacity for exertion.~بنابراین گروه دربارهٔ تفاوت توان تحمل فعالیت صحبت کرد.
het alternatiefprogramma~ander mogelijk programma~alternative programme~برنامهٔ جایگزین~Een alternatiefprogramma liet iedereen op een passend niveau meedoen.~An alternative programme allowed everyone to participate at a suitable level.~برنامهٔ جایگزین به همه اجازه داد در سطح مناسب شرکت کنند.
@health|De vrije avond|The free evening|عصر آزاد
de beschikbaarheidsdruk~druk om steeds bereikbaar te zijn~pressure to be available~فشار همیشه در دسترس بودن~Door beschikbaarheidsdruk beantwoordde Ilse ook 's avonds werkberichten.~Pressure to be available made Ilse answer work messages in the evening too.~فشار همیشه در دسترس بودن باعث می‌شد ایلسه عصرها هم پیام‌های کاری را پاسخ دهد.
de grens~limiet die men stelt~boundary~مرز~Ze vond het moeilijk om een duidelijke grens te stellen.~She found it difficult to set a clear boundary.~برای او تعیین مرزی روشن دشوار بود.
de herstelbehoefte~nood aan rust en herstel~need for recovery~نیاز به استراحت~Tijdens een teamgesprek benoemde ze haar herstelbehoefte.~During a team discussion, she expressed her need for recovery.~در گفت‌وگوی گروهی نیازش به استراحت را بیان کرد.
de bereikbaarheidstijd~afgesproken tijd om bereikbaar te zijn~availability hours~ساعات پاسخ‌گویی~Het team legde een gezamenlijke bereikbaarheidstijd vast.~The team agreed on shared availability hours.~گروه ساعت‌های مشترک پاسخ‌گویی تعیین کرد.
de rust~afwezigheid van drukte of spanning~rest~آرامش~Die afspraak bracht rust zonder dat dringende zaken onbeantwoord bleven.~That agreement brought calm without leaving urgent matters unanswered.~آن توافق آرامش آورد، بدون اینکه مسائل فوری بی‌پاسخ بمانند.
@economy|Een kleine letter met gevolgen|A small-print clause with consequences|پیامد حروف ریز
het abonnement~overeenkomst voor regelmatige levering~subscription~اشتراک~Mats sloot online een goedkoop abonnement af.~Mats took out a cheap online subscription.~ماتس اشتراک ارزان آنلاینی گرفت.
de verlenging~het langer laten duren~renewal~تمدید~Na zes maanden volgde automatisch een duurdere verlenging.~After six months, it renewed automatically at a higher price.~پس از شش ماه خودکار با قیمت بالاتر تمدید شد.
de opzegtermijn~periode voor het beëindigen van een overeenkomst~notice period~مهلت فسخ~De opzegtermijn stond alleen in de kleine letters.~The notice period appeared only in the small print.~مهلت فسخ فقط در حروف ریز نوشته شده بود.
de klantendienst~dienst die klanten helpt~customer service~خدمات مشتریان~Hij vroeg de klantendienst om een duidelijke einddatum.~He asked customer service for a clear end date.~از خدمات مشتریان تاریخ پایان مشخصی خواست.
de opzegging~het beëindigen van een overeenkomst~cancellation~فسخ~De schriftelijke opzegging voorkwam een nieuwe verlenging.~Written cancellation prevented another renewal.~فسخ کتبی از تمدید دوباره جلوگیری کرد.
@economy|Een prijs op het verkeerde rek|A price on the wrong shelf|قیمت روی قفسهٔ اشتباه
de prijs~bedrag waarvoor iets verkocht wordt~price~قیمت~Aan de kassa bleek de prijs van een jas hoger dan verwacht.~At the till, the jacket's price was higher than expected.~کنار صندوق، قیمت کت بیشتر از انتظار بود.
het etiket~label met informatie~label~برچسب~Het etiket op het rek hoorde bij een ander model.~The label on the rack belonged to a different model.~برچسب روی قفسه متعلق به مدل دیگری بود.
de verwarring~situatie waarin zaken door elkaar lopen~confusion~سردرگمی~De winkelmedewerker begreep de verwarring.~The shop assistant understood the confusion.~کارمند فروشگاه سردرگمی را درک کرد.
de tegemoetkoming~gebaar dat een nadeel vermindert~concession~امتیاز جبرانی~Als tegemoetkoming bood ze een kleine korting aan.~As a concession, she offered a small discount.~برای جبران تخفیف کوچکی پیشنهاد کرد.
de aankoop~het kopen van een product~purchase~خرید~De klant besliste pas daarna of hij de aankoop wilde doen.~Only then did the customer decide whether to make the purchase.~مشتری تنها پس از آن تصمیم گرفت آیا خرید کند.
@economy|De begroting van het buurtfeest|The neighbourhood party budget|بودجهٔ جشن محله
de begroting~vooraf opgesteld kostenoverzicht~budget~بودجه~De begroting van het buurtfeest was te optimistisch.~The neighbourhood party budget was too optimistic.~بودجهٔ جشن محله بیش از حد خوش‌بینانه بود.
de uitgave~bedrag dat men betaalt~expense~هزینه~Vooral de uitgave voor geluid was sterk onderschat.~The sound equipment expense had been particularly underestimated.~به‌ویژه هزینهٔ تجهیزات صدا بسیار کمتر از واقع برآورد شده بود.
de inkomsten~bedragen die men ontvangt~income~درآمد~De verwachte inkomsten uit drankverkoop boden weinig zekerheid.~Expected income from drinks sales offered little certainty.~درآمد پیش‌بینی‌شدهٔ فروش نوشیدنی اطمینان زیادی نمی‌داد.
de reserve~achtergehouden middelen voor later~reserve~ذخیره~De groep wilde toch een kleine reserve behouden.~The group still wanted to keep a small reserve.~گروه همچنان می‌خواست ذخیرهٔ کوچکی نگه دارد.
de prioriteit~zaak die voorrang krijgt~priority~اولویت~Ze gaven veilige voorzieningen prioriteit boven extra versiering.~They prioritised safe facilities over extra decorations.~امکانات ایمن را بر تزیینات بیشتر اولویت دادند.
@economy|Een betaling die bleef hangen|A payment that got stuck|پرداختی که متوقف شد
de overschrijving~overdracht van geld tussen rekeningen~bank transfer~انتقال بانکی~De overschrijving voor een cursus kwam niet aan.~The bank transfer for a course did not arrive.~انتقال بانکی هزینهٔ دوره نرسید.
het rekeningnummer~nummer van een bankrekening~account number~شمارهٔ حساب~Youssef controleerde het rekeningnummer op zijn betalingsbewijs.~Youssef checked the account number on his payment receipt.~یوسف شمارهٔ حساب روی رسید را بررسی کرد.
de mededeling~toegevoegde tekst bij een betaling~payment reference~شرح پرداخت~Het nummer klopte, maar de mededeling ontbrak.~The number was correct, but the payment reference was missing.~شماره درست بود، اما شرح پرداخت وجود نداشت.
de koppeling~verbinding tussen twee gegevens~link~ارتباط~Daardoor had de administratie geen koppeling met zijn inschrijving gemaakt.~The administration had therefore not linked it to his registration.~به همین دلیل بخش اداری آن را به ثبت‌نام او مرتبط نکرده بود.
het betalingsbewijs~document dat een betaling aantoont~proof of payment~رسید پرداخت~Met het betalingsbewijs kon zijn plaats alsnog worden bevestigd.~His proof of payment allowed his place to be confirmed after all.~با رسید پرداخت، جای او بالاخره تأیید شد.
@economy|Een premie op het nippertje|A grant just in time|کمک‌هزینه در آخرین لحظه
de premie~financiële tegemoetkoming~grant~کمک‌هزینه~Een gezin wilde een premie voor dakisolatie aanvragen.~A family wanted to apply for a roof-insulation grant.~خانواده‌ای می‌خواست برای عایق بام کمک‌هزینه بگیرد.
de bewijsstukken~documenten die iets aantonen~supporting documents~مدارک پشتیبان~Bij de aanvraag ontbraken enkele bewijsstukken.~Some supporting documents were missing from the application.~چند مدرک پشتیبان در درخواست نبود.
de factuur~schriftelijk betalingsverzoek~invoice~فاکتور~De aannemer had de factuur naar een verkeerd adres gestuurd.~The contractor had sent the invoice to the wrong address.~پیمانکار فاکتور را به نشانی اشتباه فرستاده بود.
de aanvultermijn~tijd om ontbrekende stukken na te sturen~time to supply missing documents~مهلت تکمیل مدارک~Een medewerker wees hen op de aanvultermijn.~An employee informed them of the time allowed to supply missing documents.~کارمندی مهلت تکمیل مدارک را به آنان یادآوری کرد.
de volledigheid~aanwezigheid van alle nodige onderdelen~completeness~کامل‌بودن~Na controle van de volledigheid kon het dossier verder worden onderzocht.~After checking completeness, the application could be examined further.~پس از بررسی کامل بودن، پرونده برای رسیدگی بیشتر آماده شد.
@economy|De goedkope herstelling|The inexpensive repair|تعمیر کم‌هزینه
de offerte~voorstel met een prijs~quotation~پیشنهاد قیمت~Voor een kapotte fiets kreeg Noor twee offertes.~Noor received two quotations for a broken bicycle.~نور برای دوچرخهٔ خراب دو پیشنهاد قیمت گرفت.
het wisselstuk~onderdeel ter vervanging~spare part~قطعهٔ یدکی~De goedkoopste offerte gebruikte een tweedehands wisselstuk.~The cheapest quotation used a second-hand spare part.~ارزان‌ترین پیشنهاد از قطعهٔ یدکی دست‌دوم استفاده می‌کرد.
de garantie~belofte over kwaliteit of herstel~warranty~ضمانت~Noor vroeg welke garantie daarbij hoorde.~Noor asked what warranty came with it.~نور پرسید چه ضمانتی همراه آن است.
de afruil~keuze waarbij een voordeel een nadeel heeft~trade-off~بده‌بستان~Ze begreep de afruil tussen een lagere prijs en een kortere garantie.~She understood the trade-off between a lower price and a shorter warranty.~بده‌بستان بین قیمت کمتر و ضمانت کوتاه‌تر را فهمید.
de levensduur~tijd dat iets bruikbaar blijft~lifespan~عمر مفید~Uiteindelijk koos ze het onderdeel met de verwachte langere levensduur.~She eventually chose the part with the longer expected lifespan.~سرانجام قطعه‌ای را انتخاب کرد که عمر مفید بیشتری پیش‌بینی می‌شد.
@economy|Een rit die duurder werd|A journey that became more expensive|سفری که گران‌تر شد
de toeslag~extra bedrag boven de gewone prijs~surcharge~هزینهٔ اضافی~Een reiziger ontdekte een toeslag op zijn ticket.~A traveller discovered a surcharge on his ticket.~مسافری روی بلیت خود هزینهٔ اضافی دید.
het tarief~vastgestelde prijs~fare~تعرفه~Hij dacht dat het gewone tarief ook tijdens de spits gold.~He thought the normal fare applied during peak hours too.~فکر می‌کرد تعرفهٔ عادی در ساعت شلوغی هم برقرار است.
de prijslijst~overzicht van prijzen~price list~فهرست قیمت~Aan het loket kreeg hij de volledige prijslijst te zien.~At the ticket desk, he was shown the full price list.~کنار باجه، فهرست کامل قیمت را به او نشان دادند.
de geldigheid~periode of situatie waarin iets geldt~validity~اعتبار~De geldigheid van zijn kortingskaart was beperkter dan hij dacht.~His discount card's validity was more limited than he had thought.~اعتبار کارت تخفیفش محدودتر از تصور او بود.
de vergelijkingstabel~tabel waarmee men opties vergelijkt~comparison table~جدول مقایسه~Met een vergelijkingstabel koos hij voor volgende ritten een passende formule.~Using a comparison table, he chose a suitable option for future trips.~با جدول مقایسه، برای سفرهای بعدی گزینهٔ مناسبی انتخاب کرد.
@economy|Een loket zonder afspraak|A desk without an appointment|پیشخوان بدون وقت قبلی
de wachtrij~rij mensen die op hun beurt wachten~queue~صف انتظار~Voor het gemeenteloket stond een lange wachtrij.~There was a long queue at the municipal service desk.~جلوی پیشخوان شهرداری صف بلندی بود.
de doorverwijzing~verwijzing naar een andere dienst~referral~ارجاع~Na een uur kreeg Iman een doorverwijzing naar een andere dienst.~After an hour, Iman was referred to another department.~ایمان پس از یک ساعت به بخش دیگری ارجاع شد.
de bevoegdheid~recht of taak om iets te beslissen~authority~اختیار~De medewerker legde uit dat zijn bevoegdheid beperkt was.~The employee explained that his authority was limited.~کارمند توضیح داد اختیارش محدود است.
de afstemming~coördinatie tussen betrokkenen~coordination~هماهنگی~Iman vroeg om betere afstemming tussen de loketten.~Iman asked for better coordination between the desks.~ایمان خواستار هماهنگی بهتر میان پیشخوان‌ها شد.
het doorverwijsbriefje~briefje met gegevens voor een andere dienst~referral note~برگهٔ ارجاع~Met een doorverwijsbriefje hoefde hij zijn verhaal niet opnieuw volledig te vertellen.~With a referral note, he did not have to repeat his entire story.~با برگهٔ ارجاع لازم نبود تمام ماجرا را دوباره تعریف کند.
@economy|Het gedeelde toestel|The shared appliance|دستگاه مشترک
de deelkast~kast waar mensen spullen delen~sharing cupboard~کمد اشتراک وسایل~Een buurt opende een deelkast voor klein gereedschap.~A neighbourhood opened a sharing cupboard for small tools.~محله‌ای کمدی برای اشتراک ابزار کوچک راه‌اندازی کرد.
de waarborg~bedrag als zekerheid~security deposit~ودیعهٔ تضمین~Voor de boormachine vroeg men een kleine waarborg.~A small security deposit was required for the drill.~برای دریل ودیعهٔ کمی می‌خواستند.
de uitleen~tijdelijk afstaan van spullen~lending~امانت‌دادن~De uitleen werd in een eenvoudig schrift genoteerd.~Lending was recorded in a simple notebook.~امانت‌دادن در دفتر ساده‌ای ثبت می‌شد.
de slijtage~beschadiging door normaal gebruik~wear~فرسودگی~Na enkele maanden ontstond discussie over normale slijtage.~After several months, a discussion arose about normal wear.~پس از چند ماه دربارهٔ فرسودگی عادی بحث شد.
de kostenverdeling~manier waarop kosten worden gedeeld~cost sharing~تقسیم هزینه~Een afspraak over kostenverdeling maakte het systeem duurzamer.~An agreement on sharing costs made the system more sustainable.~توافق دربارهٔ تقسیم هزینه، نظام را پایدارتر کرد.
@economy|Een goed doel kiezen|Choosing a good cause|انتخاب کار خیر
de schenking~vrijwillig gegeven geld of goed~donation~اهدا~Een school zamelde geld in voor een schenking.~A school raised money for a donation.~مدرسه برای اهدا پول جمع کرد.
de besteding~manier waarop geld wordt gebruikt~use of funds~نحوهٔ خرج پول~Leerlingen wilden weten welke besteding het meeste verschil maakte.~Pupils wanted to know which use of the money would make the greatest difference.~دانش‌آموزان می‌خواستند بدانند کدام مصرف پول بیشترین اثر را دارد.
de verantwoording~uitleg over keuzes en gebruik~accountability~پاسخ‌گویی~Ze vroegen twee organisaties om verantwoording van hun kosten.~They asked two organisations to account for their costs.~از دو سازمان خواستند دربارهٔ هزینه‌هایشان پاسخ‌گو باشند.
het effect~gevolg van een handeling~effect~اثر~Lage administratiekosten bleken niet automatisch meer effect te betekenen.~Low administration costs did not automatically mean greater impact.~هزینهٔ اداری کم لزوماً به معنای اثر بیشتر نبود.
de onderbouwing~redenen en bewijs voor een keuze~justification~استدلال پشتیبان~De uiteindelijke keuze kreeg daarom een bredere onderbouwing.~The final choice therefore received a broader justification.~بنابراین برای انتخاب نهایی استدلال گسترده‌تری ارائه شد.
'''
DATA += r'''
@media|De app die alles vroeg|The app that asked for everything|برنامه‌ای که همه‌چیز می‌خواست
de toepassing~programma voor een bepaalde taak~application~برنامهٔ کاربردی~Een eenvoudige toepassing moest alleen boodschappenlijstjes bewaren.~A simple application was meant only to save shopping lists.~برنامه‌ای ساده قرار بود فقط فهرست خرید را نگه دارد.
de toegang~mogelijkheid om iets te openen of gebruiken~access~دسترسی~Toch vroeg ze toegang tot contacten en foto's.~Yet it requested access to contacts and photographs.~با این حال به مخاطبان و عکس‌ها دسترسی می‌خواست.
de machtiging~toestemming voor een specifieke handeling~authorisation~مجوز دسترسی~De gebruiker weigerde die machtiging.~The user refused that authorisation.~کاربر آن مجوز را نپذیرفت.
de functionaliteit~wat een systeem kan doen~functionality~قابلیت عملکردی~De meeste functionaliteit bleef gewoon beschikbaar.~Most functionality remained available as normal.~بیشتر قابلیت‌ها همچنان عادی در دسترس بودند.
de dataminimalisatie~beperking tot noodzakelijke gegevens~data minimisation~کمینه‌سازی داده~Dat overtuigde hem van het belang van dataminimalisatie.~That convinced him of the importance of data minimisation.~این موضوع اهمیت کمینه‌سازی داده را برایش روشن کرد.
@media|Een machine die selecteert|A machine that selects|ماشینی که انتخاب می‌کند
het algoritme~reeks regels voor verwerking~algorithm~الگوریتم~Een bedrijf liet een algoritme sollicitatiebrieven ordenen.~A company used an algorithm to sort job applications.~شرکتی از الگوریتم برای مرتب‌کردن درخواست‌های شغلی استفاده کرد.
de vooringenomenheid~vooraf bestaande partijdigheid~bias~سوگیری~Een medewerker vermoedde vooringenomenheid tegen ongewone loopbanen.~An employee suspected bias against unusual career paths.~کارمندی به سوگیری علیه مسیرهای شغلی غیرمعمول شک کرد.
de controle~onderzoek of iets correct werkt~check~بررسی~Een handmatige controle bevestigde dat geschikte kandidaten werden gemist.~A manual check confirmed that suitable candidates were being missed.~بررسی دستی تأیید کرد که متقاضیان مناسب نادیده گرفته می‌شوند.
de tussenkomst~ingrijpen in een proces~intervention~مداخله~Daarom bleef menselijke tussenkomst verplicht bij afwijzingen.~Human intervention therefore remained mandatory for rejections.~بنابراین مداخلهٔ انسانی هنگام رد درخواست‌ها الزامی ماند.
de uitlegbaarheid~mogelijkheid om een beslissing te verklaren~explainability~توضیح‌پذیری~Het team eiste ook meer uitlegbaarheid van de leverancier.~The team also demanded greater explainability from the supplier.~گروه از تأمین‌کننده توضیح‌پذیری بیشتری هم خواست.
@media|De verkeerde route|The wrong route|مسیر اشتباه
de route~weg naar een bestemming~route~مسیر~De digitale route stuurde een fietser naar een afgesloten brug.~The digital route sent a cyclist towards a closed bridge.~مسیر دیجیتال دوچرخه‌سوار را به پل بسته هدایت کرد.
de actualisering~het bijwerken met nieuwe informatie~updating~به‌روزرسانی~De actualisering van de kaart liep achter.~The map update was delayed.~به‌روزرسانی نقشه عقب افتاده بود.
de omleiding~andere weg bij een afsluiting~diversion~مسیر انحرافی~Ter plaatse stond gelukkig een duidelijke omleiding.~Fortunately, a clear diversion was marked on site.~خوشبختانه در محل مسیر انحرافی روشنی مشخص شده بود.
de terugmelding~informatie die men teruggeeft~feedback report~بازگزارش~De fietser stuurde een terugmelding naar de kaartendienst.~The cyclist sent a report back to the map service.~دوچرخه‌سوار موضوع را به سرویس نقشه گزارش کرد.
de betrouwbaarheid~mate waarin men op iets kan rekenen~reliability~قابلیت اعتماد~Zo werd zichtbaar dat betrouwbaarheid ook tijdig onderhoud vraagt.~This showed that reliability also requires timely maintenance.~این نشان داد قابلیت اعتماد به نگهداری به‌موقع نیز نیاز دارد.
@media|Het wachtwoord op papier|The password on paper|رمز روی کاغذ
het wachtwoord~geheime code voor toegang~password~رمز عبور~Een gedeeld wachtwoord hing naast de computer van een vereniging.~A shared password hung beside an association's computer.~رمز مشترک کنار رایانهٔ انجمن آویزان بود.
de beveiliging~bescherming tegen ongewenste toegang~security~امنیت~Een nieuw lid merkte op dat de beveiliging daardoor zwak was.~A new member noted that this made security weak.~عضو تازه گفت این کار امنیت را ضعیف کرده است.
de tweestapsverificatie~controle met twee verschillende bewijzen~two-step verification~تأیید دومرحله‌ای~De beheerder stelde tweestapsverificatie voor persoonlijke accounts in.~The administrator set up two-step verification for individual accounts.~مدیر برای حساب‌های شخصی تأیید دومرحله‌ای فعال کرد.
de overdracht~het doorgeven van taken of middelen~handover~تحویل مسئولیت~Voor de overdracht aan nieuwe vrijwilligers kwam een aparte werkwijze.~A separate procedure was created for handover to new volunteers.~برای تحویل مسئولیت به داوطلبان تازه روش جداگانه‌ای تعیین شد.
het toegangsrecht~bevoegdheid om een systeem te gebruiken~access right~حق دسترسی~Wie vertrok, verloor voortaan zijn toegangsrecht.~Anyone who left would now lose their access rights.~از آن پس هرکس می‌رفت حق دسترسی‌اش را از دست می‌داد.
@media|De stille storing|The silent outage|اختلال خاموش
de storing~verstoring van de normale werking~outage~اختلال~Tijdens een online inschrijving ontstond een storing.~An outage occurred during an online registration.~هنگام ثبت‌نام آنلاین اختلالی رخ داد.
de foutmelding~bericht over een fout~error message~پیام خطا~De foutmelding zei alleen dat er iets misgelopen was.~The error message only said that something had gone wrong.~پیام خطا فقط می‌گفت مشکلی پیش آمده است.
de voortgang~mate waarin een taak gevorderd is~progress~پیشرفت~De gebruiker wist niet of zijn voortgang bewaard was.~The user did not know whether his progress had been saved.~کاربر نمی‌دانست پیشرفتش ذخیره شده است یا نه.
de hervatting~het opnieuw verdergaan~resumption~ازسرگیری~Na de hervatting verschenen zijn eerder ingevulde antwoorden opnieuw.~When he resumed, his previously entered answers reappeared.~با ازسرگیری، پاسخ‌های قبلی او دوباره ظاهر شدند.
de statusmelding~bericht over de huidige toestand~status message~پیام وضعیت~Een betere statusmelding had zijn ongerustheid kunnen voorkomen.~A better status message could have prevented his worry.~پیام وضعیت بهتر می‌توانست از نگرانی او جلوگیری کند.
@media|De toegankelijke website|The accessible website|وب‌سایت دسترس‌پذیر
de toegankelijkheidstest~controle of iedereen iets kan gebruiken~accessibility test~آزمون دسترس‌پذیری~Bij een toegankelijkheidstest probeerde Noor de website zonder muis.~During an accessibility test, Noor tried the website without a mouse.~نور در آزمون دسترس‌پذیری وب‌سایت را بدون ماوس امتحان کرد.
de toetsenbordbediening~gebruik via toetsen in plaats van een muis~keyboard operation~کار با صفحه‌کلید~De toetsenbordbediening stopte bij een uitklapmenu.~Keyboard operation stopped at a dropdown menu.~کار با صفحه‌کلید در فهرست بازشونده متوقف شد.
de focus~zichtbare actieve positie op het scherm~focus~نقطهٔ فعال~De focus was nergens meer zichtbaar.~The focus was no longer visible anywhere.~نقطهٔ فعال دیگر هیچ‌جا دیده نمی‌شد.
de gebruiksbarrière~hindernis bij het gebruiken~usability barrier~مانع استفاده~De ontwikkelaar herstelde die gebruiksbarrière.~The developer fixed that usability barrier.~توسعه‌دهنده آن مانع استفاده را برطرف کرد.
de hertest~opnieuw uitgevoerde controle~retest~آزمون دوباره~Bij de hertest kon Noor het formulier zelfstandig afronden.~In the retest, Noor could complete the form independently.~در آزمون دوباره، نور توانست فرم را مستقل تکمیل کند.
@media|Een sensor in de tuin|A sensor in the garden|حسگر در باغ
de sensor~toestel dat iets meet~sensor~حسگر~Een tuinvereniging plaatste een sensor om bodemvocht te meten.~A gardening association installed a sensor to measure soil moisture.~انجمن باغبانی حسگری برای اندازه‌گیری رطوبت خاک نصب کرد.
de kalibratie~afstelling op een betrouwbare referentie~calibration~واسنجی~Zonder kalibratie gaf het toestel voortdurend droogte aan.~Without calibration, the device constantly indicated dryness.~بدون واسنجی، دستگاه همیشه خشکی نشان می‌داد.
de referentie~standaard waarmee men vergelijkt~reference~مرجع~Een handmatige meting diende als referentie.~A manual measurement served as a reference.~اندازه‌گیری دستی به‌عنوان مرجع استفاده شد.
de afwijking~verschil met een verwachte waarde~deviation~انحراف~De afwijking bleek groot genoeg om onnodig water te geven.~The deviation was large enough to cause unnecessary watering.~انحراف آن‌قدر زیاد بود که باعث آبیاری بی‌دلیل شود.
de afstelling~het juist instellen~adjustment~تنظیم دقیق~Na een juiste afstelling gebruikte de vereniging minder water.~After correct adjustment, the association used less water.~پس از تنظیم درست، انجمن آب کمتری مصرف کرد.
@media|Het gedeelde programma|The shared programme|برنامهٔ مشترک
de broncode~leesbare instructies van software~source code~کد منبع~Een vereniging gebruikte software waarvan de broncode openbaar was.~An association used software whose source code was public.~انجمنی از نرم‌افزاری استفاده می‌کرد که کد منبعش عمومی بود.
de licentie~voorwaarden voor toegestaan gebruik~licence~مجوز استفاده~De licentie stond aanpassing toe onder bepaalde voorwaarden.~The licence permitted modification under certain conditions.~مجوز، تغییر را با شرایط معین اجازه می‌داد.
de documentatie~schriftelijke uitleg van een systeem~documentation~مستندات~Door ontbrekende documentatie duurde een kleine wijziging lang.~Missing documentation made a small change take a long time.~نبود مستندات باعث شد تغییری کوچک زمان زیادی ببرد.
de onderhoudbaarheid~gemak waarmee iets aangepast en hersteld wordt~maintainability~قابلیت نگهداری~Een vrijwilliger verbeterde daarom eerst de onderhoudbaarheid.~A volunteer therefore first improved maintainability.~بنابراین یکی از داوطلبان ابتدا قابلیت نگهداری را بهتر کرد.
de herbruikbaarheidsgraad~mate waarin iets opnieuw bruikbaar is~degree of reusability~میزان استفادهٔ مجدد~Daardoor steeg de herbruikbaarheidsgraad voor andere kleine verenigingen.~This increased its reusability for other small associations.~این کار میزان استفادهٔ مجدد برای انجمن‌های کوچک دیگر را بالا برد.
@media|Een bericht voor later|A message for later|پیامی برای بعد
de meldingstoon~geluid bij een nieuw bericht~notification sound~صدای اعلان~Elke meldingstoon onderbrak de vergadering.~Every notification sound interrupted the meeting.~هر صدای اعلان جلسه را قطع می‌کرد.
de aandachtsversnippering~verdeling van aandacht over te veel zaken~fragmented attention~پراکندگی توجه~De groep merkte hoeveel aandachtsversnippering dat veroorzaakte.~The group noticed how much this fragmented their attention.~گروه متوجه شد این کار چقدر توجه را پراکنده می‌کند.
de concentratieperiode~tijd voor ononderbroken aandacht~focus period~بازهٔ تمرکز~Ze spraken dagelijks een concentratieperiode af.~They agreed on a daily focus period.~برای هر روز بازه‌ای برای تمرکز تعیین کردند.
de uitzonderingregel~regel voor bijzondere gevallen~exception rule~قاعدهٔ استثنا~Een uitzonderingsregel bleef gelden voor echt dringende vragen.~An exception rule remained for genuinely urgent questions.~برای پرسش‌های واقعاً فوری قاعدهٔ استثنا باقی ماند.
de werkafspraak~gezamenlijke afspraak over het werk~working agreement~توافق کاری~Na een proefweek behielden ze de nieuwe werkafspraak.~After a trial week, they retained the new working agreement.~پس از یک هفته آزمایشی، توافق کاری تازه را حفظ کردند.
@media|Een oude foto bewaren|Preserving an old photograph|نگهداری عکس قدیمی
de digitalisering~omzetting naar digitale vorm~digitisation~دیجیتال‌سازی~Voor de digitalisering van familiefoto's leende Sofie een scanner.~Sofie borrowed a scanner to digitise family photographs.~سوفی برای دیجیتال‌سازی عکس‌های خانوادگی اسکنر قرض گرفت.
de resolutie~hoeveelheid beeldinformatie~resolution~وضوح تصویر~Een te lage resolutie maakte kleine gezichten onduidelijk.~Too low a resolution made small faces unclear.~وضوح کم، چهره‌های کوچک را نامشخص می‌کرد.
de bewaring~het veilig houden voor later~preservation~نگهداری~Ze vroeg advies over langdurige bewaring.~She sought advice on long-term preservation.~دربارهٔ نگهداری بلندمدت مشورت گرفت.
de reservekopie~extra kopie voor herstel~backup~نسخهٔ پشتیبان~Een reservekopie bewaarde ze op een andere veilige plaats.~She kept a backup in another safe location.~نسخهٔ پشتیبان را در محل امن دیگری نگه داشت.
de overdraagbaarheid~mogelijkheid om iets door te geven~transferability~قابلیت انتقال~Duidelijke bestandsnamen verbeterden de overdraagbaarheid aan haar familie.~Clear filenames made it easier to pass the collection to her family.~نام‌های روشن فایل، انتقال مجموعه به خانواده را آسان‌تر کرد.
@community|De bus aan de overkant|The bus across the road|اتوبوس آن‌طرف خیابان
de halte~plaats waar openbaar vervoer stopt~stop~ایستگاه~Door werken verschoof de halte naar de overkant van de weg.~Roadworks moved the bus stop to the other side of the road.~به‌دلیل عملیات عمرانی، ایستگاه به آن‌طرف خیابان منتقل شد.
de signalisatie~tekens en borden die informatie geven~signage~علائم راهنما~De tijdelijke signalisatie was vanuit één richting slecht zichtbaar.~The temporary signs were hard to see from one direction.~علائم موقت از یک جهت به‌خوبی دیده نمی‌شدند.
de overstap~wisseling naar een ander vervoermiddel~connection~تعویض وسیلهٔ نقلیه~Daardoor miste een reiziger haar overstap.~As a result, a traveller missed her connection.~در نتیجه مسافری وسیلهٔ بعدی را از دست داد.
de vertraging~later aankomen dan gepland~delay~تأخیر~Ze meldde de vertraging samen met een foto van het bord.~She reported the delay with a photograph of the sign.~تأخیر را همراه عکس تابلو گزارش کرد.
de zichtbaarheid~mate waarin iets te zien is~visibility~قابل‌دیدن‌بودن~De volgende dag verbeterde een extra pijl de zichtbaarheid.~The next day, an extra arrow improved visibility.~روز بعد پیکان اضافی باعث شد تابلو بهتر دیده شود.
@community|De laatste aansluiting|The last connection|آخرین اتصال سفر
de aansluiting~aansluitende rit in een reis~connection~وسیلهٔ ارتباطی بعدی~Door een defect dreigde Bram zijn laatste aansluiting te missen.~A breakdown threatened to make Bram miss his last connection.~خرابی ممکن بود باعث شود برام آخرین وسیلهٔ بعدی را از دست بدهد.
de medereiziger~persoon die dezelfde reis maakt~fellow traveller~هم‌سفر~Een medereiziger had hetzelfde probleem.~A fellow traveller had the same problem.~یکی از هم‌سفران همان مشکل را داشت.
de informatiebalie~plaats waar men informatie geeft~information desk~میز اطلاعات~Samen vroegen ze de informatiebalie naar mogelijke alternatieven.~Together, they asked the information desk about possible alternatives.~با هم از میز اطلاعات گزینه‌های ممکن را پرسیدند.
de wachttijd~duur van het wachten~waiting time~زمان انتظار~De wachttijd voor een vervangbus was korter dan verwacht.~The wait for a replacement bus was shorter than expected.~زمان انتظار برای اتوبوس جایگزین کمتر از انتظار بود.
de eindbestemming~laatste doel van een reis~final destination~مقصد نهایی~Zo bereikten ze toch dezelfde avond hun eindbestemming.~They therefore reached their final destination that evening after all.~به این ترتیب همان شب به مقصد نهایی رسیدند.
@community|Een plaats voor fietsen|A place for bicycles|جایی برای دوچرخه‌ها
de fietsenstalling~ruimte om fietsen te parkeren~bicycle parking~محل پارک دوچرخه~De fietsenstalling aan het station zat iedere ochtend vol.~The bicycle parking at the station was full every morning.~محل پارک دوچرخهٔ ایستگاه هر صبح پر بود.
de bezettingsgraad~aandeel van beschikbare plaatsen dat gebruikt wordt~occupancy rate~نرخ اشغال~De stad telde de bezettingsgraad op verschillende uren.~The city measured occupancy at different times.~شهر نرخ اشغال را در ساعت‌های مختلف اندازه گرفت.
de spreiding~verdeling over plaatsen of tijden~distribution~پراکندگی~Een slechte spreiding bleek belangrijker dan het totale aantal rekken.~Poor distribution mattered more than the total number of racks.~پراکندگی نامناسب مهم‌تر از تعداد کل جایگاه‌ها بود.
de verplaatsbaarheid~mogelijkheid om iets te verplaatsen~movability~قابلیت جابه‌جایی~Dankzij hun verplaatsbaarheid konden enkele rekken dichter bij de ingang komen.~Because they could be moved, some racks were placed closer to the entrance.~چون جایگاه‌ها قابل جابه‌جایی بودند، چند مورد نزدیک‌تر به ورودی قرار گرفتند.
de benutting~daadwerkelijk gebruik van beschikbare middelen~utilisation~بهره‌برداری~Dat verbeterde de benutting zonder grote bijkomende kosten.~This improved use without major additional costs.~این کار بدون هزینهٔ اضافی زیاد بهره‌برداری را بهتر کرد.
@community|De smalle doorgang|The narrow passage|گذرگاه باریک
de doorgang~plaats waar men doorheen kan~passage~گذرگاه~Een bestelwagen blokkeerde de doorgang op het voetpad.~A delivery van blocked the passage along the pavement.~ون تحویل کالا گذرگاه پیاده‌رو را بسته بود.
de voetganger~persoon die te voet gaat~pedestrian~عابر پیاده~Een voetganger met een kinderwagen moest uitwijken.~A pedestrian with a pushchair had to move aside.~عابری با کالسکه مجبور شد مسیرش را تغییر دهد.
de hinder~belemmering of last~obstruction~مزاحمت~De chauffeur had de hinder niet opgemerkt.~The driver had not noticed the obstruction.~راننده متوجه مزاحمت نشده بود.
de laadzone~plaats voor laden en lossen~loading zone~محل بارگیری~Na een gesprek gebruikte hij de laadzone iets verderop.~After a conversation, he used the loading zone a little further away.~پس از گفت‌وگو، از محل بارگیری کمی دورتر استفاده کرد.
de doorgankelijkheid~mogelijkheid om vrij door te gaan~clear passage~امکان عبور آزاد~Zo bleef de doorgankelijkheid van het voetpad behouden.~The pavement therefore remained clear for passage.~به این ترتیب امکان عبور آزاد از پیاده‌رو حفظ شد.
@community|Een straat voor spelen|A street for play|خیابانی برای بازی
de speelstraat~tijdelijk autovrije straat voor spelen~play street~خیابان بازی~Bewoners wilden in de zomer een speelstraat organiseren.~Residents wanted to organise a play street in summer.~ساکنان می‌خواستند تابستان خیابان بازی برپا کنند.
de afsluiting~het sluiten van een doorgang~closure~بستن مسیر~Een handelaar vreesde dat de afsluiting klanten zou tegenhouden.~A shopkeeper feared the closure would keep customers away.~فروشنده‌ای نگران بود بستن مسیر مشتریان را دور کند.
de proefperiode~tijd om een nieuwe regeling te testen~trial period~دورهٔ آزمایشی~Ze kwamen een proefperiode van twee zondagen overeen.~They agreed on a trial period of two Sundays.~بر دورهٔ آزمایشی دو یکشنبه توافق کردند.
de evaluatie~beoordeling achteraf~evaluation~ارزیابی پس از اجرا~Bij de evaluatie bleek de winkel even goed bereikbaar te voet.~The evaluation showed the shop remained just as accessible on foot.~ارزیابی نشان داد فروشگاه برای پیاده‌ها به همان اندازه در دسترس بود.
de uitbreiding~het groter maken~expansion~گسترش~Met aangepaste uren kreeg het plan toestemming voor uitbreiding.~With adjusted hours, the plan received permission to expand.~با ساعت‌های اصلاح‌شده، طرح اجازهٔ گسترش گرفت.
@study|Een onbekende bronvermelding|An unfamiliar reference|ارجاع ناشناخته
de bronvermelding~aanduiding waar informatie vandaan komt~reference citation~ارجاع منبع~In een verslag stond een bronvermelding die niemand kon terugvinden.~A report contained a reference nobody could locate.~در گزارشی ارجاعی بود که کسی پیدا نمی‌کرد.
de controleerbaarheid~mogelijkheid om iets na te gaan~verifiability~راستی‌آزمایی‌پذیری~Daardoor kwam de controleerbaarheid van de conclusie in gevaar.~This put the conclusion's verifiability at risk.~این موضوع راستی‌آزمایی نتیجه را به خطر انداخت.
de vindplaats~plaats waar informatie gevonden kan worden~location of a source~محل یافتن منبع~De auteur zocht de oorspronkelijke vindplaats opnieuw op.~The author searched again for the original source location.~نویسنده دوباره محل منبع اصلی را جست‌وجو کرد.
de verwijzing~aanduiding van een andere bron~reference~ارجاع~Een ontbrekend tijdschriftnummer bleek de verwijzing onvolledig te maken.~A missing journal issue number had made the reference incomplete.~نبود شمارهٔ مجله باعث ناقص‌شدن ارجاع شده بود.
de verifieerbaarheid~mogelijkheid om de juistheid te controleren~checkability~امکان بررسی درستی~Met de aanvulling was de verifieerbaarheid hersteld.~The added information restored its checkability.~با افزودن اطلاعات، امکان بررسی دوباره برقرار شد.
@study|Een les op afstand|A remote lesson|کلاس از راه دور
de afstandsles~les zonder gedeelde fysieke ruimte~remote lesson~کلاس از راه دور~Tijdens een afstandsles viel het geluid geregeld weg.~During a remote lesson, the sound kept cutting out.~در کلاس از راه دور صدا مرتب قطع می‌شد.
de verbinding~contact tussen apparaten of mensen~connection~اتصال~De verbinding van één student bleek onstabiel.~One student's connection proved unstable.~اتصال یکی از دانشجویان ناپایدار بود.
de ondertiteling~geschreven tekst bij gesproken taal~captions~زیرنویس~De docent zette ondertiteling aan en deelde de hoofdpunten.~The teacher enabled captions and shared the main points.~مدرس زیرنویس را فعال کرد و نکته‌های اصلی را فرستاد.
de gelijkwaardigheid~gelijke waarde of behandeling~equivalence~برابری در برخورد~Volledige gelijkwaardigheid met een lokaal gesprek was er nog niet.~It was still not fully equivalent to an in-person conversation.~هنوز کاملاً با گفت‌وگوی حضوری برابر نبود.
de inhaalmogelijkheid~kans om gemiste leerstof bij te werken~catch-up opportunity~فرصت جبران~Daarom bood hij een korte inhaalmogelijkheid na de les aan.~He therefore offered a brief catch-up opportunity after class.~بنابراین بعد از کلاس فرصت کوتاهی برای جبران فراهم کرد.
@study|Een plant met twee namen|A plant with two names|گیاهی با دو نام
de benaming~naam die men aan iets geeft~designation~نام‌گذاری~In een schooltuin kreeg dezelfde plant twee benamingen.~In a school garden, the same plant received two names.~در باغ مدرسه به یک گیاه دو نام داده شد.
de streeknaam~naam die in een bepaald gebied gebruikt wordt~regional name~نام محلی~Eén leerling gebruikte een streeknaam van zijn grootmoeder.~One pupil used a regional name from his grandmother.~یکی از دانش‌آموزان نام محلی‌ای را به کار برد که از مادربزرگش شنیده بود.
de standaardterm~algemeen afgesproken term~standard term~اصطلاح معیار~De leraar zette de standaardterm naast de lokale naam.~The teacher placed the standard term beside the local name.~معلم اصطلاح معیار را کنار نام محلی نوشت.
de taalvariatie~verschillen binnen een taal~language variation~تنوع زبانی~Zo werd taalvariatie een onderwerp van onderzoek.~Language variation thus became a topic of investigation.~به این ترتیب تنوع زبانی موضوع پژوهش شد.
de gelijkstelling~het als hetzelfde voorstellen~equating~یکسان‌انگاری~De klas leerde dat herkenning niet hetzelfde is als volledige gelijkstelling.~The class learned that recognising a term is not the same as treating terms as fully equivalent.~کلاس آموخت شناختن اصطلاح با کاملاً یکسان دانستن اصطلاح‌ها فرق دارد.
@environment|De boer en de beek|The farmer and the stream|کشاورز و جویبار
de waterloop~natuurlijke of aangelegde stroom~watercourse~آبراه~Een landbouwer merkte dat de waterloop langs zijn veld sneller uitdroogde.~A farmer noticed the watercourse beside his field drying out faster.~کشاورزی دید آبراه کنار زمینش سریع‌تر خشک می‌شود.
de grondwaterstand~hoogte van het water in de bodem~groundwater level~سطح آب زیرزمینی~Ook de grondwaterstand was lager dan vorige jaren.~The groundwater level was also lower than in previous years.~سطح آب زیرزمینی نیز از سال‌های پیش پایین‌تر بود.
de droogte~langdurig gebrek aan water~drought~خشکسالی~Een vergadering over droogte bracht boeren en bewoners samen.~A meeting about drought brought farmers and residents together.~جلسه‌ای دربارهٔ خشکسالی کشاورزان و ساکنان را گرد هم آورد.
de buffering~tijdelijk vasthouden van water~buffering~ذخیرهٔ موقت آب~Ze onderzochten buffering van regenwater op verschillende percelen.~They investigated temporarily storing rainwater on several plots.~ذخیرهٔ موقت آب باران را در چند قطعه زمین بررسی کردند.
de veerkracht~vermogen om met verstoring om te gaan~resilience~تاب‌آوری~De gezamenlijke aanpak moest de veerkracht van het gebied vergroten.~The joint approach aimed to increase the area's resilience.~رویکرد مشترک قرار بود تاب‌آوری منطقه را بیشتر کند.
@environment|Een tas voor elke keer|A bag for every occasion|کیفی برای هر بار
de wegwerpzak~zak bedoeld voor eenmalig gebruik~disposable bag~کیسهٔ یک‌بارمصرف~Een winkel stopte met de gratis wegwerpzak.~A shop stopped offering free disposable bags.~فروشگاه عرضهٔ کیسهٔ یک‌بارمصرف رایگان را متوقف کرد.
de materiaalkeuze~keuze van grondstof~choice of material~انتخاب جنس~Over de materiaalkeuze van een alternatief ontstond discussie.~The choice of material for an alternative caused debate.~دربارهٔ جنس گزینهٔ جایگزین بحث شد.
de voetafdruk~totale belasting van het milieu~footprint~ردپای زیست‌محیطی~Een stevige tas had bij productie een grotere voetafdruk.~A sturdy bag had a larger footprint during production.~کیف بادوام هنگام تولید ردپای بیشتری داشت.
de gebruiksduur~tijd dat iets gebruikt wordt~duration of use~مدت استفاده~De echte vergelijking hing daarom af van de gebruiksduur.~The real comparison therefore depended on how long it was used.~بنابراین مقایسهٔ واقعی به مدت استفاده بستگی داشت.
de gewoonteverandering~blijvende wijziging in gedrag~habit change~تغییر عادت~Een tas telkens meenemen bleek de belangrijkste gewoonteverandering.~Bringing a bag every time proved the most important habit change.~همراه آوردن کیف در هر بار، مهم‌ترین تغییر عادت بود.
'''
DATA += r'''
@work|De keuze voor vrijdag|The Friday decision|انتخاب روز جمعه
uitstellen~naar een later moment verschuiven~postpone~به تعویق انداختن~Het team wilde een moeilijke beslissing opnieuw uitstellen.~The team wanted to postpone a difficult decision again.~گروه می‌خواست تصمیم دشواری را باز هم عقب بیندازد.
afwegen~voor- en nadelen vergelijken~weigh up~سنجیدن~Een collega vroeg eerst de gevolgen van verder wachten af te wegen.~A colleague first asked them to weigh up the consequences of waiting longer.~همکاری خواست ابتدا پیامدهای انتظار بیشتر را بسنجند.
verduidelijken~duidelijker maken~clarify~روشن کردن~De projectleider verduidelijkte welke informatie nog ontbrak.~The project leader clarified what information was still missing.~مدیر پروژه روشن کرد چه اطلاعاتی هنوز کم است.
begrenzen~een duidelijke limiet stellen~limit~محدود کردن~Ze besloten het bijkomende onderzoek tot vrijdag te begrenzen.~They decided to limit the additional investigation to Friday.~تصمیم گرفتند بررسی اضافی را تا جمعه محدود کنند.
de knoop doorhakken~een definitieve beslissing nemen~decide conclusively~تصمیم نهایی گرفتن~Op vrijdag hakten ze de knoop door op basis van de beschikbare feiten.~On Friday, they made the final decision based on the available facts.~جمعه بر پایهٔ واقعیت‌های موجود تصمیم نهایی گرفتند.
@work|Een ander beginuur|A different starting time|ساعت شروع متفاوت
onderhandelen~bespreken om tot een akkoord te komen~negotiate~مذاکره کردن~Twee ploegen moesten onderhandelen over een nieuw beginuur.~Two teams had to negotiate a new starting time.~دو گروه باید دربارهٔ ساعت شروع تازه مذاکره می‌کردند.
vasthouden~niet loslaten van een standpunt~stick to~پافشاری کردن~Aanvankelijk hield iedereen vast aan zijn eigen voorkeur.~Initially, everyone stuck to their own preference.~در ابتدا همه بر ترجیح خود پافشاری کردند.
luisteren~aandachtig horen wat iemand zegt~listen~گوش دادن~Toen ze naar elkaars redenen luisterden, veranderde de sfeer.~When they listened to one another's reasons, the atmosphere changed.~وقتی به دلیل‌های یکدیگر گوش دادند، فضا تغییر کرد.
toegeven~een deel van de eigen eis loslaten~concede~کوتاه آمدن~Beide ploegen gaven op één punt toe.~Both teams conceded on one point.~هر دو گروه در یک مورد کوتاه آمدند.
vastleggen~officieel noteren of afspreken~record formally~ثبت کردن~Ze legden het akkoord vast en spraken een evaluatiemoment af.~They recorded the agreement and arranged an evaluation date.~توافق را ثبت کردند و زمانی برای ارزیابی گذاشتند.
@work|De onzichtbare taak|The invisible task|کار نامرئی
onderschatten~lager inschatten dan terecht is~underestimate~دست‌کم گرفتن~De manager onderschatte hoeveel tijd klantenopvolging vroeg.~The manager underestimated the time needed for customer follow-up.~مدیر زمان لازم برای پیگیری مشتریان را دست‌کم گرفت.
bijhouden~regelmatig registreren~keep track of~ثبت پیوسته کردن~Een medewerker hield die taken twee weken zorgvuldig bij.~An employee carefully tracked those tasks for two weeks.~کارمندی دو هفته آن کارها را دقیق ثبت کرد.
aantonen~met bewijs duidelijk maken~demonstrate~اثبات کردن~De notities toonden aan dat er dagelijks twee uur naartoe gingen.~The notes showed that the tasks took two hours daily.~یادداشت‌ها نشان داد آن کارها روزانه دو ساعت طول می‌کشند.
herverdelen~opnieuw over mensen verdelen~redistribute~دوباره تقسیم کردن~Daarop besloot het team enkele taken te herverdelen.~The team then decided to redistribute some tasks.~سپس گروه تصمیم گرفت بعضی کارها را دوباره تقسیم کند.
erkennen~als juist of waardevol aanvaarden~acknowledge~به رسمیت شناختن~De manager erkende dat onzichtbaar werk ook echt werk was.~The manager acknowledged that invisible work was real work too.~مدیر پذیرفت کار نامرئی نیز کار واقعی است.
@work|Een melding zonder schuldige|A report without blame|گزارش بدون مقصر
signaleren~de aandacht vestigen op een probleem~flag~گوشزد کردن~Een medewerker signaleerde een fout in de voorraadlijst.~An employee flagged an error in the stock list.~کارمندی خطایی در فهرست موجودی گوشزد کرد.
beschuldigen~iemand verantwoordelijk stellen voor een fout~accuse~متهم کردن~De ploegbaas wilde niemand beschuldigen zonder de oorzaak te kennen.~The supervisor did not want to accuse anyone without knowing the cause.~سرپرست نمی‌خواست بدون شناخت علت کسی را متهم کند.
reconstrueren~opnieuw nagaan wat er gebeurde~reconstruct~بازسازی کردن~Samen reconstrueerden ze hoe de bestelling verwerkt was.~Together, they reconstructed how the order had been processed.~با هم روند پردازش سفارش را بازسازی کردند.
voorkomen~zorgen dat iets niet gebeurt~prevent~پیشگیری کردن~Een extra controle kon dezelfde fout voortaan voorkomen.~An additional check could prevent the same error in future.~بررسی اضافی می‌توانست از تکرار همان خطا جلوگیری کند.
borgen~zorgen dat een verbetering behouden blijft~secure for the future~تثبیت کردن~Ze borgden die controle in de vaste werkwijze.~They embedded that check in the standard procedure.~آن بررسی را در روش ثابت کار گنجاندند.
@work|Het experiment met thuiswerk|The remote-working experiment|آزمایش دورکاری
uitproberen~op kleine schaal testen~try out~امتحان کردن~Een klein bedrijf wilde thuiswerk uitproberen.~A small company wanted to try out remote working.~شرکتی کوچک می‌خواست دورکاری را امتحان کند.
afspreken~gezamenlijk overeenkomen~agree~توافق کردن~De collega's spraken eerst bereikbare uren af.~The colleagues first agreed on contact hours.~همکاران ابتدا دربارهٔ ساعت‌های تماس توافق کردند.
vergelijken~overeenkomsten en verschillen onderzoeken~compare~مقایسه کردن~Na een maand vergeleken ze hun ervaringen.~After a month, they compared their experiences.~پس از یک ماه تجربه‌هایشان را مقایسه کردند.
bijsturen~gericht aanpassen tijdens een proces~adjust course~اصلاح مسیر کردن~Ze stuurden vooral de overdracht tussen collega's bij.~They mainly adjusted how work was handed over between colleagues.~بیشتر روش تحویل کار میان همکاران را اصلاح کردند.
behouden~laten voortbestaan~retain~حفظ کردن~De flexibiliteit behielden ze omdat die voor iedereen bruikbaar bleek.~They retained the flexibility because it proved useful for everyone.~انعطاف را حفظ کردند، چون برای همه مفید بود.
@study|Een conclusie te vroeg|A premature conclusion|نتیجه‌گیری زودهنگام
veronderstellen~iets voorlopig voor waar houden~assume~فرض کردن~Een student veronderstelde dat hogere cijfers altijd meer motivatie betekenden.~A student assumed that higher grades always meant greater motivation.~دانشجویی فرض کرد نمرهٔ بالاتر همیشه به معنای انگیزهٔ بیشتر است.
ondervragen~door vragen informatie verzamelen~question~پرس‌وجو کردن~Hij ondervroeg daarom ook leerlingen met lagere cijfers.~He therefore also questioned pupils with lower grades.~بنابراین از دانش‌آموزان با نمرهٔ کمتر هم پرس‌وجو کرد.
weerleggen~aantonen dat een stelling niet klopt~refute~رد کردن با دلیل~Hun antwoorden weerlegden zijn eenvoudige verklaring.~Their answers refuted his simple explanation.~پاسخ‌هایشان توضیح سادهٔ او را رد کرد.
onderscheiden~verschillen herkennen en benoemen~distinguish~تمایز گذاشتن~Hij leerde motivatie van beschikbare studietijd te onderscheiden.~He learned to distinguish motivation from available study time.~آموخت میان انگیزه و زمان موجود برای مطالعه تمایز بگذارد.
nuanceren~minder absoluut formuleren~qualify~تعدیل کردن~In zijn verslag nuanceerde hij zijn eerste conclusie.~In his report, he qualified his initial conclusion.~در گزارش، نتیجهٔ نخستش را تعدیل کرد.
@study|Een uitleg voor twee lezers|An explanation for two readers|توضیح برای دو خواننده
formuleren~onder woorden brengen~formulate~صورت‌بندی کردن~Een onderzoeker formuleerde haar conclusie voor een vakblad.~A researcher formulated her conclusion for a specialist journal.~پژوهشگری نتیجه‌اش را برای مجلهٔ تخصصی صورت‌بندی کرد.
vereenvoudigen~minder ingewikkeld maken~simplify~ساده کردن~Voor een buurtkrant moest ze dezelfde uitleg vereenvoudigen.~For a local newspaper, she had to simplify the same explanation.~برای روزنامهٔ محلی باید همان توضیح را ساده می‌کرد.
weglaten~niet opnemen~omit~حذف کردن~Ze wilde daarbij geen belangrijke beperkingen weglaten.~She did not want to omit important limitations.~نمی‌خواست محدودیت‌های مهم را حذف کند.
omschrijven~met andere woorden uitleggen~paraphrase~بازگویی کردن~Daarom omschreef ze de vaktermen met herkenbare voorbeelden.~She therefore explained technical terms using familiar examples.~بنابراین اصطلاح‌های تخصصی را با مثال‌های آشنا توضیح داد.
toetsen~nagaan of iets werkt of klopt~test~آزمودن~Een buurvrouw toetste of de nieuwe tekst echt begrijpelijk was.~A neighbour tested whether the new text was truly understandable.~همسایه‌ای آزمود آیا متن تازه واقعاً قابل فهم است.
@study|De ontbrekende tegenspraak|The missing counterargument|استدلال مخالفِ غایب
beargumenteren~met redenen ondersteunen~argue~استدلال کردن~Voor een debat moest een leerling zijn voorkeur beargumenteren.~For a debate, a pupil had to argue for his preference.~دانش‌آموزی برای مناظره باید برای ترجیحش استدلال می‌کرد.
bevestigen~als juist ondersteunen~confirm~تأیید کردن~Hij vond alleen bronnen die zijn mening bevestigden.~He found only sources that confirmed his opinion.~فقط منابعی یافت که نظرش را تأیید می‌کردند.
betwisten~de juistheid in twijfel trekken~dispute~مورد تردید قرار دادن~Een klasgenoot betwistte juist de aanname achter zijn plan.~A classmate disputed the assumption behind his plan.~همکلاسی‌اش فرض پشت طرح را مورد تردید قرار داد.
heroverwegen~opnieuw nadenken over een keuze~reconsider~بازاندیشی کردن~Daardoor moest hij één onderdeel heroverwegen.~This forced him to reconsider one element.~این او را واداشت در یک بخش بازاندیشی کند.
verantwoorden~uitleggen waarom iets verdedigbaar is~justify~توجیه کردن با دلیل~Zijn uiteindelijke voorstel kon hij beter verantwoorden.~He could justify his final proposal more convincingly.~توانست برای پیشنهاد نهایی دلیل قانع‌کننده‌تری بیاورد.
@study|Leren van een moeilijke tekst|Learning from a difficult text|یادگیری از متن دشوار
samenvatten~de hoofdpunten kort weergeven~summarise~خلاصه کردن~Een cursist probeerde een ingewikkelde tekst samen te vatten.~A learner tried to summarise a complicated text.~زبان‌آموزی کوشید متنی پیچیده را خلاصه کند.
markeren~zichtbaar aanduiden~mark~علامت‌زدن~Eerst markeerde ze bijna elke zin.~At first, she marked almost every sentence.~ابتدا تقریباً همهٔ جمله‌ها را علامت زد.
schiften~belangrijke en minder belangrijke zaken scheiden~sort by relevance~غربال کردن~Een docent hielp haar hoofdgedachten van voorbeelden te schiften.~A teacher helped her separate main ideas from examples.~مدرس کمک کرد فکرهای اصلی را از مثال‌ها جدا کند.
verbinden~een verband leggen tussen zaken~connect~پیوند دادن~Daarna verbond ze de hoofdgedachten met passende signaalwoorden.~She then connected the main ideas with suitable linking words.~سپس فکرهای اصلی را با واژه‌های ربط مناسب پیوند داد.
navertellen~in eigen woorden opnieuw vertellen~retell~بازگو کردن~Ten slotte kon ze de inhoud zonder de tekst navertellen.~Finally, she could retell the content without the text.~در پایان توانست محتوا را بدون نگاه به متن بازگو کند.
@study|Een tweede poging|A second attempt|تلاش دوم
reflecteren~bewust nadenken over eigen handelen~reflect~تأمل کردن~Na een mislukte presentatie wilde Daan op zijn aanpak reflecteren.~After an unsuccessful presentation, Daan wanted to reflect on his approach.~دان پس از ارائهٔ ناموفق می‌خواست دربارهٔ روشش تأمل کند.
observeren~aandachtig waarnemen~observe~مشاهده کردن~Hij observeerde in de opname wanneer het publiek afhaakte.~In the recording, he observed when the audience lost interest.~در ویدئو دید مخاطبان چه زمانی توجهشان را از دست می‌دهند.
structureren~in een duidelijke volgorde plaatsen~structure~ساختار دادن~Hij structureerde zijn tweede versie rond drie vragen.~He structured his second version around three questions.~نسخهٔ دوم را حول سه پرسش ساختار داد.
benadrukken~extra aandacht geven aan iets~emphasise~تأکید کردن~Bij elke vraag benadrukte hij één kernidee.~For each question, he emphasised one core idea.~برای هر پرسش روی یک فکر اصلی تأکید کرد.
verankeren~duurzaam vastzetten in kennis of gewoonten~anchor~تثبیت کردن در یادگیری~Een korte oefening hielp dat idee bij de luisteraars te verankeren.~A short exercise helped anchor that idea for the listeners.~تمرینی کوتاه به تثبیت آن فکر در ذهن شنوندگان کمک کرد.
@ethics|Het eenvoudige antwoord|The simple answer|پاسخ ساده
vanzelfsprekend~zo gewoon dat men er niet aan twijfelt~self-evident~بدیهی~Voor de meerderheid was de voorgestelde regel vanzelfsprekend.~To the majority, the proposed rule was self-evident.~برای اکثریت، قاعدهٔ پیشنهادی بدیهی بود.
problematisch~moeilijkheden veroorzakend~problematic~مسئله‌ساز~Voor een kleine groep was dezelfde regel juist problematisch.~For a small group, the same rule was problematic.~برای گروهی کوچک همان قاعده مسئله‌ساز بود.
redelijk~verdedigbaar en niet overdreven~reasonable~معقول~Een uitzondering leek aanvankelijk niet redelijk.~At first, an exception did not seem reasonable.~در ابتدا استثنا معقول به نظر نمی‌رسید.
proportioneel~in verhouding tot het doel~proportionate~متناسب~Na uitleg koos de groep voor een proportionele aanpassing.~After an explanation, the group chose a proportionate adjustment.~پس از توضیح، گروه اصلاحی متناسب انتخاب کرد.
rechtmatig~in overeenstemming met geldende regels~lawful~مطابق مقررات~De aanpassing bleef rechtmatig en liet meer mensen deelnemen.~The adjustment remained lawful and allowed more people to participate.~اصلاح همچنان مطابق مقررات بود و مشارکت افراد بیشتری را ممکن کرد.
@ethics|De twijfel van de jury|The jury's doubt|تردید داوران
onpartijdig~zonder voorkeur voor een partij~impartial~بی‌طرف~Een jury wilde alle inzendingen onpartijdig beoordelen.~A jury wanted to assess all submissions impartially.~هیئت داوران می‌خواست همهٔ آثار را بی‌طرفانه ارزیابی کند.
herkenbaar~gemakkelijk te identificeren~recognisable~قابل‌شناسایی~Toch was het werk van een bekende maker meteen herkenbaar.~Yet a well-known creator's work was immediately recognisable.~با این حال اثر سازندهٔ معروف فوراً قابل‌شناسایی بود.
relevant~belangrijk voor de vraag~relevant~مرتبط~Ze vroegen welke kenmerken werkelijk relevant waren voor de wedstrijd.~They asked which features were truly relevant to the competition.~پرسیدند کدام ویژگی‌ها واقعاً به مسابقه مربوط‌اند.
consistent~telkens volgens dezelfde lijn~consistent~یکنواخت و سازگار~Met vaste criteria werd hun beoordeling consistenter.~Fixed criteria made their assessments more consistent.~معیارهای ثابت ارزیابی را سازگارتر کرد.
verdedigbaar~met goede redenen te ondersteunen~defensible~قابل‌دفاع~De uitslag was daardoor beter verdedigbaar, ook voor wie verloor.~The result was therefore more defensible, including to those who lost.~به این ترتیب نتیجه حتی برای بازندگان قابل‌دفاع‌تر شد.
@ethics|De moeilijke verontschuldiging|The difficult apology|عذرخواهی دشوار
onbedoeld~zonder dat men het wilde~unintended~ناخواسته~Een onbedoelde grap kwetste een collega.~An unintended joke hurt a colleague.~شوخی ناخواسته‌ای همکار را رنجاند.
pijnlijk~verdriet of ongemak veroorzakend~painful~دردناک~Het daaropvolgende stilzwijgen was voor beiden pijnlijk.~The silence that followed was painful for both.~سکوت پس از آن برای هر دو دردناک بود.
oprecht~eerlijk gemeend~sincere~صادقانه~De spreker bood later een oprechte verontschuldiging aan.~The speaker later offered a sincere apology.~گوینده بعداً صادقانه عذرخواهی کرد.
herstelbaar~opnieuw goed te maken~repairable~قابل جبران~De collega zei dat de relatie herstelbaar was, maar tijd nodig had.~The colleague said the relationship could be repaired but needed time.~همکار گفت رابطه قابل ترمیم است، اما زمان می‌خواهد.
zorgvuldig~met aandacht voor mogelijke gevolgen~careful~دقیق و محتاط~Voortaan ging de spreker zorgvuldiger met zulke grappen om.~From then on, the speaker handled such jokes more carefully.~از آن پس گوینده در این‌گونه شوخی‌ها محتاط‌تر شد.
@ethics|Een belofte met grenzen|A promise with limits|وعده‌ای با محدودیت
haalbaar~mogelijk om uit te voeren~feasible~شدنی~Een vrijwilliger beloofde meer dan haalbaar was.~A volunteer promised more than was feasible.~داوطلبی بیش از حد شدنی قول داد.
overmoedig~te veel vertrouwen hebbend~overconfident~بیش‌ازحد مطمئن~Zijn overmoedige planning liet geen ruimte voor onverwachte problemen.~His overconfident schedule left no room for unexpected problems.~برنامهٔ بیش‌ازحد خوش‌بینانه‌اش جایی برای مشکلات پیش‌بینی‌نشده نداشت.
eerlijk~zonder misleiding~honest~صادق~Hij besloot eerlijk te zeggen dat de deadline niet lukte.~He decided to say honestly that he could not meet the deadline.~تصمیم گرفت صادقانه بگوید به موعد نمی‌رسد.
realistisch~passend bij de werkelijkheid~realistic~واقع‌بینانه~Samen maakten ze een realistischer tijdschema.~Together, they created a more realistic schedule.~با هم برنامهٔ زمانی واقع‌بینانه‌تری ساختند.
betrouwbaar~waarop men kan rekenen~reliable~قابل اعتماد~Een kleinere belofte maakte zijn hulp uiteindelijk betrouwbaarder.~A smaller promise ultimately made his help more reliable.~وعدهٔ کوچک‌تر در نهایت کمکش را قابل‌اعتمادتر کرد.
@ethics|Een besluit zonder haast|A decision without haste|تصمیم بدون شتاب
onomkeerbaar~niet terug te draaien~irreversible~برگشت‌ناپذیر~Het weggooien van het oude archief zou onomkeerbaar zijn.~Discarding the old archive would be irreversible.~دور ریختن بایگانی قدیمی برگشت‌ناپذیر بود.
voorlopig~tijdelijk en nog niet definitief~provisional~موقت~De vereniging koos daarom een voorlopige opslagplaats.~The association therefore chose a temporary storage place.~بنابراین انجمن محل نگهداری موقتی انتخاب کرد.
selectief~bewust een deel uitkiezend~selective~گزینشی~Daarna bekeek een vrijwilliger het materiaal selectief.~A volunteer then reviewed the material selectively.~سپس داوطلبی مواد را گزینشی بررسی کرد.
waardevol~van groot belang of nut~valuable~ارزشمند~Tussen oude rekeningen vond hij waardevolle foto's.~Among old bills, he found valuable photographs.~میان صورت‌حساب‌های قدیمی عکس‌های ارزشمند یافت.
doordacht~zorgvuldig overwogen~well-considered~سنجیده~Een doordachte keuze voorkwam dat het geheugen van de buurt verdween.~A well-considered choice prevented the neighbourhood's memory from disappearing.~انتخاب سنجیده مانع از نابودی حافظهٔ محله شد.
@media|Een duidelijke twijfel|A clearly expressed doubt|تردیدی روشن
waarschijnlijk~met een grote maar onzekere kans~probably~احتمالاً~Volgens het eerste bericht zou de brug waarschijnlijk vrijdag opengaan.~According to the first report, the bridge would probably open on Friday.~طبق خبر نخست، پل احتمالاً جمعه باز می‌شد.
voorwaardelijk~afhankelijk van een bepaalde eis~conditional~مشروط~Die datum was echter voorwaardelijk.~That date was conditional, however.~اما آن تاریخ مشروط بود.
naderhand~op een later moment~afterwards~بعداً~Naderhand bleek een laatste controle meer tijd te vragen.~Afterwards, a final inspection proved to need more time.~بعداً معلوم شد بررسی نهایی وقت بیشتری می‌خواهد.
uitdrukkelijk~heel duidelijk gezegd~explicitly~صریحاً~De stad vermeldde uitdrukkelijk dat de opening nog niet vaststond.~The city explicitly stated that the opening was not yet certain.~شهر صریحاً اعلام کرد زمان بازگشایی هنوز قطعی نیست.
vooralsnog~voorlopig op dit moment~for the time being~فعلاً~Vooralsnog bleef de omleiding dus van kracht.~For the time being, the diversion therefore remained in force.~بنابراین فعلاً مسیر انحرافی برقرار ماند.
@media|De twee helften van de grafiek|The two halves of the chart|دو نیمهٔ نمودار
aanzienlijk~duidelijk groot~considerable~قابل‌توجه~Een grafiek leek een aanzienlijke stijging van de kosten te tonen.~A chart appeared to show a considerable rise in costs.~نمودار ظاهراً افزایش قابل‌توجه هزینه‌ها را نشان می‌داد.
misleidend~een verkeerde indruk wekkend~misleading~گمراه‌کننده~De gekozen schaal maakte het beeld misleidend.~The chosen scale made the image misleading.~مقیاس انتخاب‌شده تصویر را گمراه‌کننده می‌کرد.
betrekkelijk~in verhouding kleiner of beperkter~relatively~نسبتاً~In euro's was het verschil betrekkelijk klein.~In euros, the difference was relatively small.~تفاوت به یورو نسبتاً کم بود.
vergelijkbaar~op zinvolle wijze te vergelijken~comparable~قابل‌مقایسه~Een tweede grafiek gebruikte vergelijkbare assen voor beide jaren.~A second chart used comparable axes for both years.~نمودار دوم برای هر دو سال محورهای قابل‌مقایسه به کار برد.
verhelderend~duidelijker makend~illuminating~روشنگر~Die voorstelling was veel verhelderender voor de lezers.~That representation was far more illuminating for readers.~آن نمایش برای خوانندگان بسیار روشنگرتر بود.
@media|De stilte na het debat|The silence after the debate|سکوت پس از مناظره
tegenstrijdig~niet met elkaar verenigbaar~contradictory~متناقض~Twee sprekers gebruikten tegenstrijdige cijfers.~Two speakers used contradictory figures.~دو سخنران ارقام متناقضی استفاده کردند.
zorgwekkend~reden tot ongerustheid gevend~worrying~نگران‌کننده~Dat was zorgwekkend voor een publiek dat een keuze moest maken.~That was worrying for an audience that had to make a choice.~این برای مخاطبانی که باید انتخاب می‌کردند نگران‌کننده بود.
aantoonbaar~met bewijs vast te stellen~demonstrable~قابل‌اثبات~De moderator vroeg welke verschillen aantoonbaar waren.~The moderator asked which differences could be demonstrated.~گرداننده پرسید کدام تفاوت‌ها قابل‌اثبات‌اند.
onderling~tussen de betrokkenen~between those involved~میان طرف‌ها~De sprekers vergeleken onderling de periodes van hun gegevens.~The speakers compared the periods covered by their data.~سخنرانان دوره‌های داده‌هایشان را با هم مقایسه کردند.
uiteindelijk~aan het einde van een proces~eventually~سرانجام~Uiteindelijk bleek dat ze verschillende jaren bespraken.~Eventually, it turned out that they were discussing different years.~سرانجام معلوم شد دربارهٔ سال‌های متفاوت حرف می‌زنند.
@media|Een onderbroken interview|An interrupted interview|مصاحبهٔ قطع‌شده
onvolledig~niet alle delen bevattend~incomplete~ناقص~Een kort fragment gaf een onvolledig beeld van het interview.~A short clip gave an incomplete picture of the interview.~بخشی کوتاه تصویر ناقصی از مصاحبه داد.
weloverwogen~na zorgvuldig nadenken~considered~سنجیده~De spreker had haar antwoord juist weloverwogen opgebouwd.~The speaker had in fact constructed her answer carefully.~گوینده در واقع پاسخ خود را سنجیده ساخته بود.
aanvullend~iets extra toevoegend~additional~تکمیلی~Een aanvullende vraag veranderde later de richting van het gesprek.~An additional question later changed the direction of the conversation.~پرسشی تکمیلی بعداً مسیر گفت‌وگو را تغییر داد.
essentieel~onmisbaar voor goed begrip~essential~اساسی~Dat vervolg bleek essentieel om haar standpunt te begrijpen.~That continuation proved essential to understanding her position.~آن ادامه برای فهم موضع او اساسی بود.
integraal~volledig en als geheel~in full~به‌طور کامل~De redactie plaatste daarom het gesprek integraal online.~The editors therefore published the conversation online in full.~بنابراین تحریریه گفت‌وگو را کامل آنلاین منتشر کرد.
@media|Een titel voor de toekomst|A title for the future|عنوانی برای آینده
voorzichtig~zonder onnodig risico of stellige zekerheid~cautious~محتاط~Een journalist schreef een voorzichtige voorspelling over woningprijzen.~A journalist wrote a cautious prediction about house prices.~روزنامه‌نگاری پیش‌بینی محتاطانه‌ای دربارهٔ قیمت مسکن نوشت.
uitzonderlijk~afwijkend van wat gewoon is~exceptional~استثنایی~Een uitzonderlijk jaar maakte de trend moeilijk leesbaar.~An exceptional year made the trend hard to interpret.~سالی استثنایی تفسیر روند را دشوار کرد.
daarentegen~in tegenstelling tot wat voorafging~by contrast~در مقابل~Een advertentie beloofde daarentegen zekere winst.~An advertisement, by contrast, promised certain profits.~در مقابل، آگهی سود قطعی وعده می‌داد.
aannemelijk~met goede redenen geloofwaardig~plausible~پذیرفتنی~De lezer onderzocht welke uitleg het meest aannemelijk was.~The reader examined which explanation was most plausible.~خواننده بررسی کرد کدام توضیح پذیرفتنی‌تر است.
onzeker~niet met zekerheid bekend~uncertain~نامطمئن~Hij besloot dat de toekomst onzeker bleef, ook met veel cijfers.~He concluded that the future remained uncertain, even with many figures.~نتیجه گرفت حتی با ارقام فراوان، آینده همچنان نامطمئن است.
'''
