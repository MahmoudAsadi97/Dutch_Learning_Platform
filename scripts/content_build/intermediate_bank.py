"""Original intermediate vocabulary bank. Editorial review is still required.

Banks use productive sentence patterns within narrow semantic sets. Repeated words
are an intentional recognition spiral, not claims of new or mastered vocabulary.
"""
GROUPS = []
def add(key, topic, patterns, rows):
    items = [line.split('|') for line in rows.strip().splitlines() if line.strip()]
    assert all(len(item) == 4 for item in items), key
    GROUPS.append(dict(key=key, topic=topic, patterns=patterns, items=items))

add('documents', ('Documenten','Documents','مدارک'), [
('Ik leg {nl} klaar voor mijn afspraak.','I get {en} ready for my appointment.','من {fa} را برای قرارم آماده می‌کنم.'),
('Voordat ik naar het loket ga, controleer ik {nl}.','Before I go to the counter, I check {en}.','پیش از رفتن به باجه، {fa} را بررسی می‌کنم.'),
('Ik bewaar {nl} zorgvuldig, zodat ik mijn aanvraag later kan opvolgen.','I keep {en} carefully so I can follow up on my application later.','من {fa} را با دقت نگه می‌دارم تا بعداً بتوانم درخواست خود را پیگیری کنم.')], '''
de identiteitskaart|kaart die toont wie je bent|the identity card|کارت شناسایی
de verblijfskaart|kaart met je verblijfsrecht|the residence card|کارت اقامت
het paspoort|document waarmee je naar het buitenland reist|the passport|گذرنامه
het formulier|blad waarop je gegevens invult|the form|فرم
het attest|officieel bewijs van een situatie|the certificate|گواهی
het diploma|bewijs dat je een opleiding hebt voltooid|the diploma|مدرک تحصیلی
de uitnodiging|bericht waarin je gevraagd wordt te komen|the invitation|دعوت‌نامه
de bevestiging|bericht dat iets afgesproken is|the confirmation|تأییدیه
het contract|schriftelijke afspraak tussen partijen|the contract|قرارداد
de kopie|tweede exemplaar van een document|the copy|رونوشت
''')
add('travelgear', ('Op reis','Travelling','سفر'), [
('Ik neem {nl} mee op reis.','I take {en} on my trip.','من {fa} را به سفر می‌برم.'),
('Voor ik vertrek, stop ik {nl} in mijn reistas.','Before I leave, I put {en} in my travel bag.','پیش از حرکت، {fa} را در کیف سفرم می‌گذارم.'),
('Omdat ik onderweg weinig winkels tegenkom, neem ik {nl} van thuis mee.','Because I will pass few shops on the way, I bring {en} from home.','چون در مسیر فروشگاه‌های کمی می‌بینم، {fa} را از خانه می‌آورم.')], '''
de oplader|toestel waarmee je een batterij oplaadt|the charger|شارژر
de tandenborstel|borstel om je tanden te poetsen|the toothbrush|مسواک
de zonnebril|bril die je ogen tegen zonlicht beschermt|the sunglasses|عینک آفتابی
de reisgids|boek met informatie voor reizigers|the guidebook|کتاب راهنمای سفر
de drinkfles|fles die je opnieuw met drinken vult|the water bottle|بطری آب
de regenjas|jas die water tegenhoudt|the raincoat|بارانی
de zaklamp|kleine lamp die je kunt dragen|the torch|چراغ‌قوه
de zonnecrème|crème die je huid tegen zonlicht beschermt|the sunscreen|کرم ضدآفتاب
de handdoek|doek waarmee je je afdroogt|the towel|حوله
de toilettas|tas voor spullen om je te verzorgen|the washbag|کیف لوازم بهداشتی
''')
add('vehicles', ('Vervoer','Transport','رفت‌وآمد'), [
('Ik zie {nl} aan het station.','I see {en} at the station.','من {fa} را کنار ایستگاه می‌بینم.'),
('We wachten even, want {nl} staat voor de ingang.','We wait a moment because {en} is in front of the entrance.','کمی صبر می‌کنیم، چون {fa} جلوی ورودی است.'),
('Toen ik aankwam, stond {nl} vlak bij de ingang, waardoor ik moest omlopen.','When I arrived, {en} was right by the entrance, so I had to walk around it.','وقتی رسیدم، {fa} درست کنار ورودی بود و مجبور شدم از کنار آن رد شوم.')], '''
de trein|voertuig dat op spoorrails rijdt|the train|قطار
de bus|groot voertuig voor meerdere reizigers|the bus|اتوبوس
de tram|voertuig op rails in een stad|the tram|تراموا
de taxi|auto met chauffeur die je per rit betaalt|the taxi|تاکسی
de fiets|voertuig met twee wielen en pedalen|the bicycle|دوچرخه
de bakfiets|fiets met een grote bak vooraan|the cargo bike|دوچرخه باری
de deelwagen|auto die verschillende gebruikers kunnen huren|the shared car|خودروی اشتراکی
de bestelwagen|voertuig om goederen te vervoeren|the van|ون باری
de scooter|klein gemotoriseerd voertuig op twee wielen|the scooter|اسکوتر
de rolstoel|stoel met wielen om zich te verplaatsen|the wheelchair|صندلی چرخ‌دار
''')
add('station', ('Wegwijs in het station','Finding your way at the station','پیدا کردن مسیر در ایستگاه'), [
('Waar vind ik {nl}?','Where can I find {en}?','{fa} را کجا پیدا کنم؟'),
('Kunt u uitleggen waar ik {nl} kan vinden?','Could you explain where I can find {en}?','می‌توانید توضیح بدهید که {fa} را کجا پیدا کنم؟'),
('Omdat ik hier voor het eerst ben, vraag ik een medewerker waar {nl} is.','Because this is my first visit, I ask a staff member where {en} is.','چون اولین بار است که اینجا هستم، از یک کارمند می‌پرسم {fa} کجاست.')], '''
het perron|plaats waar reizigers op de trein stappen|the platform|سکوی قطار
het loket|balie waar je een medewerker aanspreekt|the ticket counter|باجه بلیت
de uitgang|plaats waar je een gebouw verlaat|the exit|خروجی
de ingang|plaats waar je een gebouw binnengaat|the entrance|ورودی
de lift|toestel dat mensen tussen verdiepingen vervoert|the lift|آسانسور
de trap|reeks treden tussen verdiepingen|the stairs|راه‌پله
de wachtzaal|ruimte waar mensen op vervoer wachten|the waiting room|سالن انتظار
de fietsenstalling|plaats waar je een fiets achterlaat|the bicycle parking area|محل پارک دوچرخه
de ticketautomaat|machine waar je zelf een ticket koopt|the ticket machine|دستگاه فروش بلیت
het informatiebord|bord met berichten voor reizigers|the information board|تابلوی اطلاعات
''')
add('timeplans', ('Reisplanning','Travel planning','برنامه‌ریزی سفر'), [
('Ik controleer {nl} voor ik vertrek.','I check {en} before I leave.','من پیش از حرکت {fa} را بررسی می‌کنم.'),
('Mijn collega vraagt of ik {nl} al gecontroleerd heb.','My colleague asks whether I have already checked {en}.','همکارم می‌پرسد آیا {fa} را بررسی کرده‌ام.'),
('Hoewel ik de route ken, controleer ik {nl} opnieuw om verrassingen te vermijden.','Although I know the route, I check {en} again to avoid surprises.','با اینکه مسیر را می‌شناسم، {fa} را دوباره بررسی می‌کنم تا غافلگیر نشوم.')], '''
de vertrektijd|tijdstip waarop het vervoer vertrekt|the departure time|زمان حرکت
de aankomsttijd|tijdstip waarop het vervoer aankomt|the arrival time|زمان رسیدن
de dienstregeling|overzicht van geplande ritten|the timetable|جدول زمان‌بندی
de aansluiting|volgende rit waarop je kunt overstappen|the connection|وسیله بعدی در مسیر
het traject|route tussen vertrekpunt en bestemming|the route|مسیر
de reistijd|tijd die de volledige reis duurt|the journey time|مدت سفر
de bestemming|plaats waar je naartoe reist|the destination|مقصد
de reservatie|plaats of dienst die vooraf vastgelegd is|the reservation|رزرو
de vertraging|tijd waarmee een rit later is|the delay|تأخیر
het treinticket|vervoerbewijs voor een treinrit|the train ticket|بلیت قطار
''')
add('rooms', ('Wonen','Housing','مسکن'), [
('We maken {nl} vandaag schoon.','We clean {en} today.','ما امروز {fa} را تمیز می‌کنیم.'),
('Op zaterdag maken we {nl} schoon voordat onze vrienden komen.','On Saturday we clean {en} before our friends arrive.','روز شنبه، پیش از آمدن دوستانمان، {fa} را تمیز می‌کنیم.'),
('We verdelen het werk eerlijk: ik maak {nl} schoon en mijn huisgenoot doet de was.','We divide the work fairly: I clean {en} and my housemate does the washing.','کار را منصفانه تقسیم می‌کنیم: من {fa} را تمیز می‌کنم و هم‌خانه‌ام لباس‌ها را می‌شوید.')], '''
de keuken|ruimte waar je eten klaarmaakt|the kitchen|آشپزخانه
de badkamer|ruimte waar je je wast|the bathroom|حمام
de slaapkamer|kamer waarin je slaapt|the bedroom|اتاق خواب
de woonkamer|kamer waarin je zit en bezoek ontvangt|the living room|اتاق نشیمن
de gang|ruimte die kamers met elkaar verbindt|the corridor|راهرو
de kelder|ruimte onder de grond|the cellar|زیرزمین
de zolder|ruimte onder het dak|the attic|اتاق زیرشیروانی
het balkon|kleine buitenruimte aan een verdieping|the balcony|بالکن
het terras|buitenruimte waar je kunt zitten|the terrace|تراس
de berging|ruimte om spullen op te bergen|the storage room|انباری
''')
add('furniture', ('Meubels','Furniture','وسایل خانه'), [
('We kopen {nl} voor ons nieuwe huis.','We buy {en} for our new home.','ما {fa} را برای خانه جدیدمان می‌خریم.'),
('We meten de kamer op voordat we {nl} kopen.','We measure the room before buying {en}.','پیش از خریدن {fa}، اتاق را اندازه می‌گیریم.'),
('We vergelijken tweedehandsaanbiedingen, omdat we {nl} graag betaalbaar willen kopen.','We compare second-hand offers because we want to buy {en} at an affordable price.','پیشنهادهای دست‌دوم را مقایسه می‌کنیم، چون می‌خواهیم {fa} را با قیمت مناسبی بخریم.')], '''
de tafel|meubel met een vlak blad en poten|the table|میز
de stoel|zitmeubel voor één persoon|the chair|صندلی
de kast|meubel waarin je spullen bewaart|the cupboard|کمد
de zetel|comfortabel zitmeubel voor één of meer personen|the sofa|مبل
het bed|meubel waarop je slaapt|the bed|تخت
de matras|zacht deel van een bed waarop je ligt|the mattress|تشک
het bureau|tafel waaraan je werkt of studeert|the desk|میز تحریر
de boekenkast|kast met planken voor boeken|the bookcase|قفسه کتاب
de eettafel|tafel waaraan je maaltijden eet|the dining table|میز غذاخوری
het nachtkastje|klein kastje naast een bed|the bedside table|پاتختی
''')
add('kitchen', ('In de keuken','In the kitchen','در آشپزخانه'), [
('Ik leg {nl} op het aanrecht.','I put {en} on the kitchen counter.','من {fa} را روی پیشخوان آشپزخانه می‌گذارم.'),
('Nadat ik de afwas heb gedaan, leg ik {nl} op het aanrecht.','After washing up, I put {en} on the kitchen counter.','بعد از شستن ظرف‌ها، {fa} را روی پیشخوان می‌گذارم.'),
('Ik leg {nl} alvast klaar, zodat we straks samen kunnen koken zonder lang te zoeken.','I get {en} ready so we can cook together later without searching for things.','من {fa} را از قبل آماده می‌کنم تا بعداً بدون جست‌وجوی طولانی با هم آشپزی کنیم.')], '''
de pan|keukengerei waarin je bakt|the frying pan|ماهیتابه
de kookpot|diepe pot om eten te koken|the cooking pot|قابلمه
het mes|gereedschap waarmee je snijdt|the knife|چاقو
de vork|bestek met tanden om eten op te prikken|the fork|چنگال
de lepel|bestek om vloeibaar eten op te scheppen|the spoon|قاشق
het bord|platte schaal waarvan je eet|the plate|بشقاب
de kom|diepe ronde schaal|the bowl|کاسه
het glas|voorwerp waaruit je drinkt|the glass|لیوان
de snijplank|plank waarop je eten snijdt|the chopping board|تخته برش
het vergiet|schaal met gaatjes om water af te gieten|the colander|آبکش
''')
add('ingredients', ('Samen koken','Cooking together','آشپزی با هم'), [
('Ik doe {nl} in de soep.','I put {en} in the soup.','من {fa} را در سوپ می‌ریزم.'),
('Volgens het recept moet ik {nl} pas op het einde toevoegen.','According to the recipe, I should only add {en} at the end.','طبق دستور، باید {fa} را فقط در پایان اضافه کنم.'),
('Ik voeg eerst een beetje toe en proef dan, want {nl} kan de smaak sterk veranderen.','I add a little first and then taste it, because {en} can strongly change the flavour.','اول کمی اضافه می‌کنم و بعد می‌چشم، چون {fa} می‌تواند مزه را خیلی تغییر بدهد.')], '''
peper|specerij met een scherpe smaak|pepper|فلفل
zout|stof die eten een zoute smaak geeft|salt|نمک
knoflook|plant waarvan de teentjes eten smaak geven|garlic|سیر
gember|wortel met een frisse scherpe smaak|ginger|زنجبیل
room|dik vet gedeelte van melk|cream|خامه
citroensap|zuur sap uit een citroen|lemon juice|آب‌لیمو
peterselie|groen kruid dat je aan eten toevoegt|parsley|جعفری
koriander|kruid met een uitgesproken geur en smaak|coriander|گشنیز
paprikapoeder|poeder van gedroogde paprika|paprika powder|پودر پاپریکا
olijfolie|olie gemaakt van olijven|olive oil|روغن زیتون
''')
add('symptoms', ('Bij de huisarts','At the doctor’s','پیش پزشک عمومی'), [
('Ik heb last van {nl}.','I am troubled by {en}.','من از {fa} رنج می‌برم.'),
('Ik vertel de huisarts dat ik sinds gisteren last heb van {nl}.','I tell the doctor that I have been troubled by {en} since yesterday.','به پزشک می‌گویم که از دیروز از {fa} رنج می‌برم.'),
('Tijdens de afspraak leg ik uit wanneer {nl} begonnen is en wat ik toen aan het doen was.','During the appointment I explain when {en} started and what I was doing then.','در وقت ملاقات توضیح می‌دهم {fa} از چه زمانی شروع شد و آن موقع چه می‌کردم.')], '''
hoofdpijn|pijn in je hoofd|a headache|سردرد
keelpijn|pijn in je keel|a sore throat|گلودرد
buikpijn|pijn in je buik|a stomach ache|دل‌درد
rugpijn|pijn in je rug|back pain|کمردرد
koorts|lichaamstemperatuur die hoger is dan normaal|a fever|تب
hoest|herhaald krachtig uitblazen van lucht|a cough|سرفه
misselijkheid|gevoel dat je moet overgeven|nausea|حالت تهوع
duizeligheid|gevoel dat jij of de omgeving draait|dizziness|سرگیجه
vermoeidheid|gevoel dat je weinig energie hebt|tiredness|خستگی
jeuk|gevoel waardoor je wilt krabben|itching|خارش
''')
add('professionals', ('Hulp en diensten','Help and services','کمک و خدمات'), [
('Ik bel {nl} voor een afspraak.','I call {en} for an appointment.','من برای گرفتن وقت به {fa} زنگ می‌زنم.'),
('Ik vraag aan {nl} of er deze week nog plaats is.','I ask {en} whether there is an appointment available this week.','از {fa} می‌پرسم آیا این هفته هنوز وقت خالی وجود دارد.'),
('Als de afspraak niet kan doorgaan, verwittig ik {nl} op tijd en stel ik een andere datum voor.','If the appointment cannot go ahead, I notify {en} in time and suggest another date.','اگر ملاقات ممکن نباشد، به‌موقع به {fa} خبر می‌دهم و تاریخ دیگری پیشنهاد می‌کنم.')], '''
de huisarts|arts voor algemene gezondheidsvragen|the family doctor|پزشک عمومی
de tandarts|zorgverlener die tanden behandelt|the dentist|دندان‌پزشک
de kinesist|zorgverlener die beweging en herstel begeleidt|the physiotherapist|فیزیوتراپیست
de verpleegkundige|zorgverlener die patiënten verzorgt|the nurse|پرستار
de psycholoog|deskundige die helpt bij psychische vragen|the psychologist|روان‌شناس
de maatschappelijk werker|persoon die helpt bij sociale problemen|the social worker|مددکار اجتماعی
de oogarts|arts die ogen onderzoekt|the eye doctor|چشم‌پزشک
de logopedist|zorgverlener die spraak en taal begeleidt|the speech therapist|گفتاردرمانگر
de diëtist|deskundige die advies over voeding geeft|the dietitian|متخصص تغذیه
de vroedvrouw|zorgverlener die zwangerschap en geboorte begeleidt|the midwife|ماما
''')
add('body', ('Het lichaam','The body','بدن'), [
('De arts onderzoekt {nl}.','The doctor examines {en}.','پزشک {fa} را معاینه می‌کند.'),
('Ik vertel precies waar het pijn doet voordat de arts {nl} onderzoekt.','I explain exactly where it hurts before the doctor examines {en}.','پیش از آنکه پزشک {fa} را معاینه کند، دقیق توضیح می‌دهم کجا درد دارد.'),
('Tijdens het onderzoek vraagt de arts of ik {nl} na de val nog normaal kon bewegen.','During the examination the doctor asks whether I could still move {en} normally after the fall.','در معاینه، پزشک می‌پرسد آیا بعد از افتادن هنوز می‌توانستم {fa} را به‌طور عادی حرکت بدهم.')], '''
mijn arm|deel van mijn lichaam tussen schouder en hand|my arm|بازوی من
mijn been|deel van mijn lichaam waarop ik sta|my leg|پای من
mijn schouder|verbinding tussen mijn arm en romp|my shoulder|شانه من
mijn knie|gewricht midden in mijn been|my knee|زانوی من
mijn enkel|gewricht tussen mijn been en voet|my ankle|مچ پای من
mijn pols|gewricht tussen mijn arm en hand|my wrist|مچ دست من
mijn vinger|een van de delen aan mijn hand|my finger|انگشت دست من
mijn teen|een van de delen aan mijn voet|my toe|انگشت پای من
mijn nek|deel dat mijn hoofd met mijn romp verbindt|my neck|گردن من
mijn elleboog|gewricht midden in mijn arm|my elbow|آرنج من
''')
add('jobs', ('Beroepen','Occupations','شغل‌ها'), [
('Mijn buur werkt als {nl}.','My neighbour works as {en}.','همسایه من به‌عنوان {fa} کار می‌کند.'),
('Mijn buur werkt als {nl} en vertelt graag over het werk.','My neighbour works as {en} and enjoys talking about the job.','همسایه من به‌عنوان {fa} کار می‌کند و دوست دارد درباره کارش حرف بزند.'),
('Mijn buur is tevreden met de baan als {nl}, hoewel de werkuren soms moeilijk te combineren zijn met het gezin.','My neighbour is happy with the job as {en}, although the working hours can be hard to combine with family life.','همسایه من از کارش به‌عنوان {fa} راضی است، هرچند هماهنگ کردن ساعت‌های کار با زندگی خانوادگی گاهی دشوار است.')], '''
leerkracht|persoon die lesgeeft|a teacher|معلم
kok|persoon die beroepsmatig kookt|a cook|آشپز
bakker|persoon die brood en gebak maakt|a baker|نانوا
chauffeur|persoon die beroepsmatig een voertuig bestuurt|a driver|راننده
elektricien|vakpersoon die elektrische installaties herstelt|an electrician|برق‌کار
loodgieter|vakpersoon die waterleidingen herstelt|a plumber|لوله‌کش
verkoper|persoon die goederen aan klanten verkoopt|a salesperson|فروشنده
programmeur|persoon die computerprogramma’s schrijft|a programmer|برنامه‌نویس
poetshulp|persoon die helpt met schoonmaken|a cleaner|نیروی نظافت
boekhouder|persoon die financiële gegevens bijhoudt|a bookkeeper|حسابدار
''')
add('worktools', ('Veilig aan het werk','Working safely','کار ایمن'), [
('Voor het werk controleer ik {nl}.','Before work, I check {en}.','پیش از کار، {fa} را بررسی می‌کنم.'),
('Mijn collega toont mij hoe ik {nl} veilig kan gebruiken.','My colleague shows me how to use {en} safely.','همکارم به من نشان می‌دهد چطور از {fa} به‌طور ایمن استفاده کنم.'),
('Als ik twijfel over {nl}, vraag ik eerst uitleg in plaats van zomaar te beginnen.','If I am unsure about {en}, I ask for an explanation first instead of just starting.','اگر درباره {fa} تردید داشته باشم، به‌جای شروع بی‌مقدمه ابتدا توضیح می‌خواهم.')], '''
de ladder|verplaatsbaar voorwerp met sporten om hoger te komen|the ladder|نردبان
de boormachine|elektrisch gereedschap om gaten te maken|the drill|دریل
de hamer|gereedschap waarmee je slaat|the hammer|چکش
de schroevendraaier|gereedschap om schroeven vast te draaien|the screwdriver|پیچ‌گوشتی
de veiligheidsgordel|band die je bij gevaar op je plaats houdt|the safety belt|کمربند ایمنی
de veiligheidsbril|bril die je ogen tijdens werk beschermt|the safety goggles|عینک ایمنی
de gehoorbescherming|middel dat je oren tegen lawaai beschermt|the hearing protection|محافظ گوش
de helm|harde bescherming voor je hoofd|the helmet|کلاه ایمنی
de brandblusser|toestel waarmee je een kleine brand blust|the fire extinguisher|کپسول آتش‌نشانی
de noodknop|knop om een toestel onmiddellijk te stoppen|the emergency stop button|دکمه توقف اضطراری
''')
add('studythings', ('Studeren','Studying','درس خواندن'), [
('Ik gebruik {nl} tijdens de les.','I use {en} during the lesson.','من در کلاس از {fa} استفاده می‌کنم.'),
('Als ik iets niet begrijp, gebruik ik {nl} om het opnieuw te bekijken.','If I do not understand something, I use {en} to look at it again.','اگر چیزی را نفهمم، از {fa} استفاده می‌کنم تا دوباره آن را بررسی کنم.'),
('Ik combineer {nl} met mijn eigen notities, zodat ik de uitleg beter kan onthouden.','I combine {en} with my own notes so I can remember the explanation better.','من {fa} را با یادداشت‌های خودم ترکیب می‌کنم تا توضیح را بهتر به یاد بسپارم.')], '''
het handboek|boek dat de leerstof uitlegt|the textbook|کتاب درسی
het woordenboek|boek of hulpmiddel dat woorden uitlegt|the dictionary|واژه‌نامه
het werkblad|blad met opdrachten om te oefenen|the worksheet|برگه تمرین
het schema|beknopt overzicht van informatie|the diagram|نمودار
het voorbeeld|concreet geval dat een uitleg duidelijk maakt|the example|مثال
de samenvatting|korte weergave van de hoofdpunten|the summary|خلاصه
de opname|bewaard geluid of beeld|the recording|فایل ضبط‌شده
het stappenplan|uitleg van handelingen in de juiste volgorde|the step-by-step plan|راهنمای گام‌به‌گام
de oefening|opdracht waarmee je iets leert|the exercise|تمرین
de presentatie|uitleg met woorden en vaak beelden|the presentation|ارائه
''')
add('learnverbs', ('Leren leren','Learning to learn','یاد گرفتن روش یادگیری'), [
('Ik wil deze tekst {nl}.','I want to {en} this text.','من می‌خواهم این متن را {fa}.'),
('Na de les probeer ik deze tekst zonder hulp te {nl}.','After the lesson I try to {en} this text without help.','بعد از کلاس سعی می‌کنم این متن را بدون کمک {fa}.'),
('Om te controleren of ik de inhoud begrijp, probeer ik deze tekst met een klasgenoot te {nl}.','To check whether I understand the content, I try to {en} this text with a classmate.','برای بررسی درکم از محتوا، سعی می‌کنم این متن را همراه یک هم‌کلاسی {fa}.')], '''
lezen|geschreven woorden begrijpen|read|بخوانم
begrijpen|weten wat iets betekent|understand|بفهمم
samenvatten|de belangrijkste informatie kort weergeven|summarise|خلاصه کنم
bespreken|samen over iets praten|discuss|بررسی کنم
vertalen|in een andere taal weergeven|translate|ترجمه کنم
vergelijken|overeenkomsten en verschillen zoeken|compare|مقایسه کنم
herschrijven|opnieuw in andere woorden schrijven|rewrite|بازنویسی کنم
verbeteren|fouten wegnemen of iets beter maken|improve|اصلاح کنم
analyseren|onderdelen en verbanden nauwkeurig onderzoeken|analyse|تحلیل کنم
voorlezen|een geschreven tekst hardop lezen|read aloud|بلند بخوانم
''')
add('messages', ('Contact houden','Keeping in touch','در تماس ماندن'), [
('Ik stuur {nl} naar mijn collega.','I send {en} to my colleague.','من {fa} را برای همکارم می‌فرستم.'),
('Voordat ik vertrek, stuur ik {nl} naar mijn collega.','Before leaving, I send {en} to my colleague.','پیش از رفتن، {fa} را برای همکارم می‌فرستم.'),
('Ik stuur {nl} naar mijn collega en vraag om een reactie, zodat we misverstanden kunnen voorkomen.','I send {en} to my colleague and ask for a response so we can prevent misunderstandings.','من {fa} را برای همکارم می‌فرستم و پاسخ می‌خواهم تا از سوءتفاهم جلوگیری کنیم.')], '''
een bericht|korte mededeling voor iemand|a message|یک پیام
een e-mail|digitaal bericht met een adres|an email|یک ایمیل
een sms|kort tekstbericht via de telefoon|a text message|یک پیامک
een uitnodigingsbrief|brief waarin je iemand vraagt te komen|an invitation letter|یک دعوت‌نامه کتبی
een herinnering|bericht waardoor je iets niet vergeet|a reminder|یک یادآوری
een voorstel|idee dat anderen kunnen bespreken|a proposal|یک پیشنهاد
een vraag|zin waarmee je informatie vraagt|a question|یک سؤال
een antwoord|reactie op een vraag|an answer|یک پاسخ
een verslag|beschrijving van wat gebeurd is|a report|یک گزارش
een bijlage|bestand dat samen met een bericht meegaat|an attachment|یک پیوست
''')
add('plans', ('Afspreken en plannen','Making plans','قرار و برنامه‌ریزی'), [
('We bespreken {nl} morgen.','We discuss {en} tomorrow.','ما فردا درباره {fa} گفت‌وگو می‌کنیم.'),
('We bespreken {nl} morgen, omdat vandaag niet iedereen aanwezig is.','We discuss {en} tomorrow because not everyone is here today.','ما فردا درباره {fa} گفت‌وگو می‌کنیم، چون امروز همه حاضر نیستند.'),
('Voordat we een beslissing nemen, bespreken we {nl} en luisteren we naar ieders bezwaren.','Before making a decision, we discuss {en} and listen to everyone’s concerns.','پیش از تصمیم‌گیری، درباره {fa} گفت‌وگو می‌کنیم و به نگرانی‌های همه گوش می‌دهیم.')], '''
de afspraak|wat mensen samen hebben afgesproken|the appointment|قرار
de planning|overzicht van wat wanneer moet gebeuren|the schedule|برنامه زمانی
de taakverdeling|afspraak over wie welke taak doet|the division of tasks|تقسیم وظایف
de deadline|uiterste tijdstip waarop iets klaar moet zijn|the deadline|مهلت نهایی
de beschikbaarheid|momenten waarop iemand tijd heeft|the availability|زمان‌های آزاد
de voorbereiding|werk dat je vooraf doet|the preparation|آماده‌سازی
de wijziging|verandering in een plan of situatie|the change|تغییر
de oplossing|manier om een probleem te verhelpen|the solution|راه‌حل
het alternatief|andere mogelijkheid om uit te kiezen|the alternative|گزینه جایگزین
het overleg|gesprek waarin mensen samen afstemmen|the consultation|جلسه هماهنگی
''')
add('movement', ('Onderweg','On the move','در راه'), [
('We moeten hier {nl}.','We need to {en} here.','ما باید اینجا {fa}.'),
('De medewerker legt uit waarom we hier moeten {nl}.','The staff member explains why we need to {en} here.','کارمند توضیح می‌دهد چرا باید اینجا {fa}.'),
('Omdat de situatie veranderd is, vragen we eerst of we hier nog mogen {nl}.','Because the situation has changed, we first ask whether we are still allowed to {en} here.','چون وضعیت عوض شده، ابتدا می‌پرسیم آیا هنوز اجازه داریم اینجا {fa}.')], '''
wachten|ergens blijven tot iets gebeurt|wait|صبر کنیم
uitstappen|een voertuig verlaten|get off|پیاده شویم
instappen|een voertuig binnengaan|get on|سوار شویم
overstappen|van het ene vervoermiddel naar het andere gaan|change vehicles|وسیله را عوض کنیم
parkeren|een voertuig tijdelijk neerzetten|park|پارک کنیم
omkeren|teruggaan in de richting waaruit je kwam|turn back|برگردیم
oversteken|naar de andere kant van een weg gaan|cross the road|از خیابان رد شویم
afremmen|minder snel gaan rijden|slow down|سرعت را کم کنیم
stoppen|niet verder bewegen|stop|توقف کنیم
verzamelen|als groep bij elkaar komen|gather|جمع شویم
''')
add('helpverbs', ('Samen problemen oplossen','Solving problems together','حل مسئله با هم'), [
('Kun je mij {nl}?','Can you {en} me?','می‌توانی به من {fa}؟'),
('Als ik vastloop, vraag ik of je mij kunt {nl}.','If I get stuck, I ask whether you can {en} me.','اگر گیر کنم، می‌پرسم آیا می‌توانی به من {fa}.'),
('Ik probeer het eerst zelf, maar als dat niet lukt, hoop ik dat je mij kunt {nl}.','I try it myself first, but if that does not work, I hope you can {en} me.','اول خودم امتحان می‌کنم، اما اگر موفق نشوم امیدوارم بتوانی به من {fa}.')], '''
helpen|iemand steun geven bij iets|help|کمک کنی
begeleiden|iemand stap voor stap ondersteunen|guide|راهنمایی بدهی
verwittigen|iemand op tijd iets laten weten|notify|خبر بدهی
waarschuwen|iemand vertellen dat er gevaar of een probleem is|warn|هشدار بدهی
informeren|iemand de nodige informatie geven|inform|اطلاع بدهی
adviseren|iemand een mogelijke aanpak aanraden|advise|مشاوره بدهی
ondersteunen|iemand hulp of vertrouwen geven|support|حمایت برسانی
bellen|via de telefoon contact opnemen|call|تلفن بزنی
terugbellen|bellen als reactie op een eerdere oproep|call back|دوباره زنگ بزنی
herinneren|iemand helpen iets niet te vergeten|remind|یادآوری کنی
''')
add('feelings', ('Gevoelens','Feelings','احساس‌ها'), [
('Vandaag voel ik me {nl}.','Today I feel {en}.','امروز احساس می‌کنم {fa}.'),
('Na het gesprek voel ik me {nl} en vertel ik dat aan een vriend.','After the conversation I feel {en} and tell a friend.','بعد از گفت‌وگو احساس می‌کنم {fa} و این را به دوستی می‌گویم.'),
('Hoewel ik mijn gevoelens niet altijd gemakkelijk uitleg, probeer ik te vertellen waarom ik me {nl} voel.','Although I do not always explain my feelings easily, I try to say why I feel {en}.','با اینکه توضیح احساساتم همیشه آسان نیست، سعی می‌کنم بگویم چرا احساس می‌کنم {fa}.')], '''
blij|met een aangenaam gevoel van vreugde|happy|خوشحال هستم
verdrietig|met een gevoel van verdriet|sad|غمگین هستم
boos|met een gevoel van kwaadheid|angry|عصبانی هستم
onzeker|niet zeker van jezelf of de situatie|uncertain|مطمئن نیستم
rustig|zonder sterke spanning|calm|آرام هستم
gespannen|met veel spanning in je lichaam of gedachten|tense|مضطرب هستم
trots|tevreden over wat iemand bereikt heeft|proud|افتخار می‌کنم
teleurgesteld|ongelukkig omdat iets tegenvalt|disappointed|ناامید شده‌ام
opgelucht|blij omdat een zorg voorbij is|relieved|آسوده شده‌ام
eenzaam|met het gevoel dat je gezelschap mist|lonely|تنها هستم
''')
add('qualities', ('Een plan beoordelen','Evaluating a plan','ارزیابی یک برنامه'), [
('Ik vind dit plan {nl}.','I find this plan {en}.','من این برنامه را {fa} می‌دانم.'),
('Ik vind dit plan {nl}, maar ik wil eerst de details bekijken.','I find this plan {en}, but I want to look at the details first.','من این برنامه را {fa} می‌دانم، اما اول می‌خواهم جزئیات را بررسی کنم.'),
('Op het eerste gezicht vind ik dit plan {nl}; toch wil ik weten wat het voor de andere deelnemers betekent.','At first sight I find this plan {en}; still, I want to know what it means for the other participants.','در نگاه اول این برنامه را {fa} می‌دانم؛ با این حال می‌خواهم بدانم برای دیگر شرکت‌کنندگان چه معنایی دارد.')], '''
haalbaar|mogelijk om werkelijk uit te voeren|feasible|عملی
nuttig|met een duidelijk voordeel|useful|مفید
duidelijk|gemakkelijk te begrijpen|clear|روشن
ingewikkeld|moeilijk door veel verschillende onderdelen|complicated|پیچیده
eerlijk|zonder iemand onterecht te benadelen|fair|منصفانه
veilig|met weinig kans op gevaar|safe|ایمن
betaalbaar|met een prijs die je kunt betalen|affordable|مقرون‌به‌صرفه
praktisch|handig om werkelijk te gebruiken|practical|کاربردی
flexibel|gemakkelijk aan te passen|flexible|انعطاف‌پذیر
realistisch|passend bij wat werkelijk mogelijk is|realistic|واقع‌بینانه
''')
add('weather', ('Het weer','The weather','آب‌وهوا'), [
('Door {nl} blijven we binnen.','Because of {en}, we stay indoors.','به‌دلیل {fa} داخل می‌مانیم.'),
('We wilden buiten wandelen, maar door {nl} blijven we binnen.','We wanted to walk outside, but because of {en} we stay indoors.','می‌خواستیم بیرون قدم بزنیم، اما به‌دلیل {fa} داخل می‌مانیم.'),
('De organisator houdt rekening met {nl} en stelt daarom een activiteit binnen voor.','The organiser takes {en} into account and therefore suggests an indoor activity.','برگزارکننده {fa} را در نظر می‌گیرد و به همین دلیل فعالیتی در فضای بسته پیشنهاد می‌کند.')], '''
de regen|water dat uit wolken valt|the rain|باران
de sneeuw|bevroren neerslag in witte vlokken|the snow|برف
de hagel|harde ijsbolletjes die uit wolken vallen|the hail|تگرگ
de storm|zeer harde wind|the storm|طوفان
het onweer|weer met donder en bliksem|the thunderstorm|رعدوبرق
de mist|kleine waterdruppels die het zicht beperken|the fog|مه
de hitte|erg hoge temperatuur|the heat|گرما
de koude|erg lage temperatuur|the cold|سرما
de gladheid|situatie waarin je gemakkelijk uitglijdt|the slippery conditions|لغزندگی زمین
de wind|lucht die zich verplaatst|the wind|باد
''')
add('waste', ('Minder afval','Reducing waste','کاهش زباله'), [
('Ik sorteer {nl} apart.','I sort {en} separately.','من {fa} را جداگانه تفکیک می‌کنم.'),
('Ik lees de lokale regels voordat ik {nl} apart sorteer.','I read the local rules before sorting {en} separately.','پیش از تفکیک جداگانه {fa}، مقررات محلی را می‌خوانم.'),
('De sorteerregels verschillen soms per gemeente, dus ik zoek eerst op waar {nl} thuishoort.','Sorting rules sometimes differ by municipality, so I first look up where {en} belongs.','قوانین تفکیک گاهی در هر شهر فرق دارند، بنابراین اول بررسی می‌کنم {fa} را کجا باید گذاشت.')], '''
het papier|materiaal waarop je schrijft of drukt|the paper|کاغذ
het karton|dik stevig papier voor verpakkingen|the cardboard|مقوا
het glasafval|weggegooide glazen verpakkingen|the glass waste|زباله شیشه‌ای
het plastic|kunststof die vaak als verpakking dient|the plastic|پلاستیک
het restafval|afval dat na het sorteren overblijft|the residual waste|زباله باقی‌مانده
het groenafval|afval van planten en tuinen|the garden waste|پسماند باغچه
de batterij|voorwerp dat elektrische energie bewaart|the battery|باتری
de verpakking|materiaal rond een product|the packaging|بسته‌بندی
de lege fles|fles waar niets meer in zit|the empty bottle|بطری خالی
het blikje|kleine metalen verpakking voor drank|the drinks can|قوطی نوشیدنی
''')
add('clothes', ('Kleding','Clothing','پوشاک'), [
('Ik pas {nl} in de winkel.','I try on {en} in the shop.','من {fa} را در فروشگاه پرو می‌کنم.'),
('Ik pas {nl} en vraag of er ook een andere maat is.','I try on {en} and ask whether another size is available.','من {fa} را پرو می‌کنم و می‌پرسم آیا اندازه دیگری هم دارد.'),
('Voordat ik {nl} koop, controleer ik of het materiaal prettig aanvoelt en goed te wassen is.','Before buying {en}, I check whether the fabric feels comfortable and is easy to wash.','پیش از خرید {fa}، بررسی می‌کنم آیا جنس آن راحت است و به‌خوبی شسته می‌شود.')], '''
de broek|kledingstuk dat beide benen bedekt|the trousers|شلوار
de trui|warm kledingstuk voor het bovenlichaam|the jumper|پلیور
de jas|kledingstuk dat je buiten over andere kleding draagt|the coat|کت
de rok|kledingstuk vanaf de taille zonder aparte broekspijpen|the skirt|دامن
het hemd|kledingstuk met kraag en knopen|the shirt|پیراهن
het T-shirt|licht kledingstuk met korte mouwen|the T-shirt|تی‌شرت
de jurk|kledingstuk voor bovenlichaam en benen in één stuk|the dress|پیراهن زنانه
de sjaal|lange doek voor rond je nek|the scarf|شال گردن
de muts|zachte warme hoofdbedekking|the woolly hat|کلاه بافتنی
de riem|band die je rond je middel draagt|the belt|کمربند
''')
add('sportsgear', ('Sportmateriaal','Sports equipment','وسایل ورزشی'), [
('Ik leen {nl} van de sportclub.','I borrow {en} from the sports club.','من {fa} را از باشگاه ورزشی قرض می‌گیرم.'),
('Omdat ik pas begin, leen ik {nl} voorlopig van de club.','Because I am just starting, I borrow {en} from the club for now.','چون تازه شروع کرده‌ام، فعلاً {fa} را از باشگاه قرض می‌گیرم.'),
('Ik spreek met de trainer af wanneer ik {nl} terugbreng, zodat een andere deelnemer het daarna kan gebruiken.','I agree with the coach when to return {en} so another participant can use it afterwards.','با مربی هماهنگ می‌کنم چه زمانی {fa} را برگردانم تا شرکت‌کننده دیگری بعداً از آن استفاده کند.')], '''
de voetbal|bal waarmee je voetbal speelt|the football|توپ فوتبال
de basketbal|bal waarmee je basketbal speelt|the basketball|توپ بسکتبال
het racket|voorwerp waarmee je bij tennis een bal slaat|the racket|راکت
het springtouw|touw waarover je tijdens het springen draait|the skipping rope|طناب ورزشی
de yogamat|mat voor oefeningen op de grond|the yoga mat|زیرانداز یوگا
de zwembril|bril die je ogen in het zwembad beschermt|the swimming goggles|عینک شنا
het zwemvest|vest dat helpt om te blijven drijven|the life jacket|جلیقه نجات
de hockeystick|stok waarmee je hockey speelt|the hockey stick|چوب هاکی
de stopwatch|uurwerk waarmee je een tijdsduur meet|the stopwatch|کرنومتر
het trainingshesje|licht vest om een ploeg herkenbaar te maken|the training bib|کاور تمرین
''')
add('sports', ('Bewegen','Being active','فعالیت بدنی'), [
('Ik wil graag {nl}.','I would like to {en}.','من دوست دارم {fa}.'),
('Na het werk wil ik graag {nl}, als ik nog genoeg energie heb.','After work I would like to {en}, if I still have enough energy.','بعد از کار، اگر هنوز انرژی کافی داشته باشم، دوست دارم {fa}.'),
('Om regelmatig te bewegen, spreek ik met een vriend af om elke week samen te {nl}.','To exercise regularly, I arrange with a friend to {en} together every week.','برای ورزش منظم، با دوستی قرار می‌گذارم هر هفته با هم {fa}.')], '''
zwemmen|je in water voortbewegen|swim|شنا کنم
fietsen|je met een fiets verplaatsen|cycle|دوچرخه‌سواری کنم
wandelen|rustig te voet op weg gaan|walk|پیاده‌روی کنم
lopen|je in een sneller tempo te voet verplaatsen|run|بدوم
voetballen|met twee ploegen een bal in een doel proberen te krijgen|play football|فوتبال بازی کنم
tennissen|met rackets een bal over een net slaan|play tennis|تنیس بازی کنم
dansen|bewegen op muziek|dance|برقصم
klimmen|naar boven bewegen met handen en voeten|climb|صعود کنم
schaatsen|op glad ijs bewegen met schaatsen|skate|اسکیت کنم
roeien|een boot met roeispanen vooruit bewegen|row|پاروزنی کنم
''')
add('city', ('In de buurt','Around the neighbourhood','در محله'), [
('We spreken af bij {nl}.','We meet at {en}.','ما کنار {fa} قرار می‌گذاریم.'),
('We spreken af bij {nl}, omdat iedereen die plek kent.','We meet at {en} because everyone knows that place.','ما کنار {fa} قرار می‌گذاریم، چون همه آنجا را می‌شناسند.'),
('We kiezen {nl} als ontmoetingsplaats en sturen iedereen een duidelijke beschrijving van de route.','We choose {en} as our meeting place and send everyone clear directions.','ما {fa} را محل دیدار انتخاب می‌کنیم و توضیح روشنی درباره مسیر برای همه می‌فرستیم.')], '''
de bibliotheek|plaats waar je boeken kunt lezen en lenen|the library|کتابخانه
het buurthuis|gebouw waar buurtbewoners samen activiteiten doen|the community centre|مرکز محله
het stadhuis|gebouw waar het stadsbestuur werkt|the town hall|ساختمان شهرداری
het park|groene openbare ruimte om te ontspannen|the park|پارک
het plein|open ruimte tussen gebouwen|the square|میدان
de brug|bouwwerk over water of een weg|the bridge|پل
het zwembad|plaats met een groot bad om te zwemmen|the swimming pool|استخر
het museum|gebouw waar je verzamelingen kunt bekijken|the museum|موزه
het cultuurcentrum|gebouw voor culturele activiteiten|the cultural centre|مرکز فرهنگی
de sporthal|overdekte ruimte om te sporten|the sports hall|سالن ورزشی
''')
add('shops', ('Winkelen','Shopping','خرید'), [
('Ik ga straks naar {nl}.','I am going to {en} later.','من کمی بعد به {fa} می‌روم.'),
('Ik controleer eerst de openingsuren voordat ik naar {nl} ga.','I check the opening hours before going to {en}.','پیش از رفتن به {fa}، ساعت کاری را بررسی می‌کنم.'),
('Omdat ik weinig tijd heb, zoek ik vooraf uit hoe ik het snelst bij {nl} kan geraken.','Because I have little time, I find out beforehand how to get to {en} fastest.','چون وقت کمی دارم، از قبل بررسی می‌کنم چطور سریع‌تر به {fa} برسم.')], '''
de supermarkt|grote winkel met voeding en huishoudelijke producten|the supermarket|سوپرمارکت
de bakkerij|winkel waar brood en gebak verkocht worden|the bakery|نانوایی
de slagerij|winkel waar vlees verkocht wordt|the butcher’s shop|قصابی
de apotheek|winkel waar je geneesmiddelen krijgt|the pharmacy|داروخانه
de kledingwinkel|winkel die kleding verkoopt|the clothes shop|فروشگاه لباس
de kringwinkel|winkel met herbruikbare tweedehandsspullen|the reuse shop|فروشگاه اجناس دست‌دوم
de boekhandel|winkel waar boeken verkocht worden|the bookshop|کتاب‌فروشی
de fietsenwinkel|winkel die fietsen verkoopt en vaak herstelt|the bicycle shop|فروشگاه دوچرخه
de bloemenwinkel|winkel waar bloemen verkocht worden|the flower shop|گل‌فروشی
de nachtwinkel|kleine winkel die laat open is|the late-night shop|فروشگاه شبانه
''')
add('digital', ('Digitaal contact','Digital communication','ارتباط دیجیتال'), [
('Ik controleer {nl} op mijn computer.','I check {en} on my computer.','من {fa} را در رایانه‌ام بررسی می‌کنم.'),
('Ik controleer {nl} voordat ik het bericht verstuur.','I check {en} before sending the message.','پیش از فرستادن پیام، {fa} را بررسی می‌کنم.'),
('Om te voorkomen dat informatie bij de verkeerde persoon terechtkomt, controleer ik {nl} nog eens.','To prevent information from reaching the wrong person, I check {en} once more.','برای جلوگیری از رسیدن اطلاعات به فرد اشتباه، {fa} را یک بار دیگر بررسی می‌کنم.')], '''
het e-mailadres|digitaal adres waar je berichten ontvangt|the email address|نشانی ایمیل
de ontvanger|persoon aan wie een bericht gericht is|the recipient|گیرنده
de afzender|persoon die een bericht verstuurt|the sender|فرستنده
het onderwerp|korte titel die zegt waar een bericht over gaat|the subject|موضوع
het bestand|digitaal opgeslagen geheel van informatie|the file|فایل
de bestandsnaam|naam waarmee je een digitaal bestand herkent|the filename|نام فایل
de link|aanklikbare verwijzing naar een andere pagina|the link|پیوند
het telefoonnummer|cijfers waarmee je iemand kunt bellen|the phone number|شماره تلفن
de adreslijst|overzicht van contactadressen|the address list|فهرست نشانی‌ها
de handtekening|naam of ondertekening onder een bericht|the signature|امضا
''')
add('devices', ('Toestellen','Devices','دستگاه‌ها'), [
('Ik zet {nl} aan.','I switch on {en}.','من {fa} را روشن می‌کنم.'),
('Voordat de vergadering begint, zet ik {nl} aan.','Before the meeting starts, I switch on {en}.','پیش از شروع جلسه، {fa} را روشن می‌کنم.'),
('Ik test {nl} vooraf, zodat een technisch probleem de vergadering niet onnodig vertraagt.','I test {en} beforehand so a technical problem does not delay the meeting unnecessarily.','من {fa} را از قبل امتحان می‌کنم تا مشکل فنی جلسه را بی‌دلیل عقب نیندازد.')], '''
de laptop|computer die je gemakkelijk meeneemt|the laptop|لپ‌تاپ
de tablet|platte computer met een aanraakscherm|the tablet|تبلت
de smartphone|telefoon met internet en apps|the smartphone|گوشی هوشمند
de printer|toestel dat digitale tekst op papier afdrukt|the printer|چاپگر
de projector|toestel dat beelden groot op een muur toont|the projector|ویدئوپروژکتور
de luidspreker|toestel dat geluid hoorbaar maakt|the speaker|بلندگو
de microfoon|toestel dat je stem opneemt|the microphone|میکروفون
de webcam|camera voor beeldgesprekken via een computer|the webcam|وب‌کم
de router|toestel dat een internetverbinding verdeelt|the router|مسیریاب
het beeldscherm|scherm waarop digitale beelden verschijnen|the monitor|نمایشگر
''')
add('money', ('Geldzaken','Money matters','امور مالی'), [
('Ik schrijf {nl} in mijn overzicht.','I write {en} in my overview.','من {fa} را در جدول خودم می‌نویسم.'),
('Elke maand schrijf ik {nl} in mijn overzicht om mijn budget te volgen.','Every month I write {en} in my overview to keep track of my budget.','هر ماه {fa} را در جدولم می‌نویسم تا بودجه‌ام را پیگیری کنم.'),
('Ik vergelijk {nl} met vorige maand en zoek uit waarom het bedrag veranderd is.','I compare {en} with last month and find out why the amount has changed.','من {fa} را با ماه قبل مقایسه می‌کنم و بررسی می‌کنم چرا مبلغ تغییر کرده است.')], '''
de huur|bedrag dat je voor tijdelijk gebruik van een woning betaalt|the rent|اجاره
het loon|geld dat je voor je werk ontvangt|the wages|دستمزد
het spaargeld|geld dat je opzijgezet hebt|the savings|پس‌انداز
het saldo|bedrag dat op een rekening staat|the balance|موجودی
het inkomen|geld dat je in een periode ontvangt|the income|درآمد
de uitgave|geld dat je aan iets besteedt|the expense|هزینه
de energiekosten|geld dat je voor gas of elektriciteit betaalt|the energy costs|هزینه انرژی
de korting|bedrag waarmee een prijs vermindert|the discount|تخفیف
de waarborg|bedrag dat als zekerheid wordt vastgezet|the deposit|ودیعه
de terugbetaling|geld dat je terugkrijgt|the refund|بازپرداخت
''')
add('community', ('Meedoen in de buurt','Community participation','مشارکت در محله'), [
('Ik help mee met {nl}.','I help with {en}.','من در {fa} کمک می‌کنم.'),
('Op zaterdag help ik mee met {nl}, samen met twee buren.','On Saturday I help with {en}, together with two neighbours.','روز شنبه همراه دو همسایه در {fa} کمک می‌کنم.'),
('Door mee te helpen met {nl}, leer ik nieuwe mensen kennen en begrijp ik beter wat er in de buurt leeft.','By helping with {en}, I meet new people and understand local concerns better.','با کمک کردن در {fa}، با آدم‌های تازه آشنا می‌شوم و دغدغه‌های محله را بهتر می‌فهمم.')], '''
het buurtfeest|feest voor mensen uit dezelfde buurt|the neighbourhood party|جشن محله
de opruimactie|gezamenlijke activiteit om rommel weg te halen|the clean-up|پاک‌سازی محله
de inzameling|actie waarbij spullen of geld worden verzameld|the collection|جمع‌آوری کمک‌ها
de boekenruil|activiteit waarbij mensen boeken uitwisselen|the book swap|مبادله کتاب
de rommelmarkt|markt waar mensen gebruikte spullen verkopen|the flea market|بازار دست‌دوم
de buurtmaaltijd|maaltijd die buurtbewoners samen eten|the community meal|غذای جمعی محله
de herstelling|werk waardoor iets kapots weer bruikbaar wordt|the repair|تعمیر
de taalactiviteit|bijeenkomst om taal te oefenen|the language activity|فعالیت زبانی
de tuinwerking|samenwerking om een tuin te onderhouden|the gardening project|پروژه باغبانی
de voedselbedeling|uitdelen van voedsel aan mensen die het nodig hebben|the food distribution|توزیع غذا
''')
add('participation', ('Samen beslissen','Deciding together','تصمیم‌گیری با هم'), [
('We praten over {nl}.','We talk about {en}.','ما درباره {fa} حرف می‌زنیم.'),
('Tijdens de bijeenkomst praten we over {nl} en stellen we vragen.','During the meeting we talk about {en} and ask questions.','در گردهمایی درباره {fa} حرف می‌زنیم و سؤال می‌پرسیم.'),
('We onderzoeken wat {nl} in de praktijk betekent en geven concrete voorbeelden uit onze buurt.','We explore what {en} means in practice and give concrete examples from our neighbourhood.','بررسی می‌کنیم {fa} در عمل چه معنایی دارد و مثال‌های مشخصی از محله خود می‌زنیم.')], '''
de inspraak|mogelijkheid om je mening bij een besluit te geven|public participation|مشارکت در تصمیم‌گیری
de toegankelijkheid|mate waarin iedereen ergens gebruik van kan maken|accessibility|دسترس‌پذیری
de veiligheid|toestand waarin gevaar zo veel mogelijk beperkt is|safety|ایمنی
de gelijkheid|situatie waarin mensen gelijk behandeld worden|equality|برابری
de samenwerking|samen werken aan een doel|cooperation|همکاری
de verantwoordelijkheid|plicht om voor iets te zorgen en uitleg te geven|responsibility|مسئولیت
de afspraakcultuur|manier waarop mensen afspraken maken en nakomen|the culture of keeping agreements|فرهنگ پایبندی به توافق‌ها
de betrokkenheid|mate waarin mensen meedoen en zich verbonden voelen|involvement|مشارکت و همراهی
de leefbaarheid|mate waarin een omgeving prettig is om in te leven|quality of local life|کیفیت زندگی محلی
de solidariteit|bereidheid om elkaar te steunen|solidarity|همبستگی
''')
add('discussion', ('Een mening uitleggen','Explaining an opinion','توضیح نظر'), [
('Ik luister naar {nl}.','I listen to {en}.','من به {fa} گوش می‌دهم.'),
('Ik luister eerst naar {nl} en geef daarna mijn reactie.','I first listen to {en} and then give my response.','اول به {fa} گوش می‌دهم و بعد پاسخ می‌دهم.'),
('Voordat ik reageer, vat ik {nl} samen om te controleren of ik het goed begrepen heb.','Before responding, I summarise {en} to check that I have understood it correctly.','پیش از پاسخ، {fa} را خلاصه می‌کنم تا مطمئن شوم درست فهمیده‌ام.')], '''
het argument|reden die een mening ondersteunt|the argument|استدلال
het bezwaar|reden waarom iemand ergens tegen is|the objection|اعتراض
het standpunt|mening die iemand over een onderwerp heeft|the position|موضع
het advies|voorstel over wat je het best kunt doen|the advice|توصیه
de uitleg|woorden die iets duidelijk maken|the explanation|توضیح
de kritiek|oordeel over wat beter kan|the criticism|انتقاد
de ervaring|wat iemand zelf meegemaakt heeft|the experience|تجربه
de toelichting|extra uitleg bij een onderwerp|the clarification|توضیح تکمیلی
de conclusie|uitkomst van een redenering of onderzoek|the conclusion|نتیجه‌گیری
de tegenwerping|reactie met een bezwaar tegen een redenering|the counterargument|استدلال مخالف
''')
add('timewords', ('Tijd en gewoontes','Time and habits','زمان و عادت‌ها'), [
('Ik oefen {nl} Nederlands.','I practise Dutch {en}.','من {fa} هلندی تمرین می‌کنم.'),
('Ik oefen {nl} Nederlands, ook als ik maar tien minuten tijd heb.','I practise Dutch {en}, even when I only have ten minutes.','من {fa} هلندی تمرین می‌کنم، حتی وقتی فقط ده دقیقه وقت دارم.'),
('Ik probeer {nl} Nederlands te oefenen door een kort gesprek te voeren over iets wat ik echt moet regelen.','I try to practise Dutch {en} by having a short conversation about something I actually need to arrange.','سعی می‌کنم {fa} با گفت‌وگوی کوتاه درباره کاری که واقعاً باید انجام دهم، هلندی تمرین کنم.')], '''
dagelijks|elke dag|daily|هر روز
regelmatig|vaak en met terugkerende tussenpozen|regularly|به‌طور منظم
soms|af en toe|sometimes|گاهی
vaak|veel keren|often|اغلب
zelden|bijna nooit|rarely|به‌ندرت
wekelijks|elke week|weekly|هر هفته
maandelijks|elke maand|monthly|هر ماه
vandaag|op deze dag|today|امروز
morgen|op de dag na vandaag|tomorrow|فردا
vanavond|op de avond van deze dag|this evening|امشب
''')
add('colleagues', ('Mensen op het werk','People at work','افراد در محیط کار'), [
('Ik vraag het aan {nl}.','I ask {en}.','من از {fa} می‌پرسم.'),
('Als de instructie niet duidelijk is, vraag ik het aan {nl}.','If the instruction is not clear, I ask {en}.','اگر دستور روشن نباشد، از {fa} می‌پرسم.'),
('Ik vraag {nl} om de afspraak te bevestigen, zodat iedereen dezelfde informatie heeft.','I ask {en} to confirm the agreement so everyone has the same information.','از {fa} می‌خواهم توافق را تأیید کند تا همه اطلاعات یکسان داشته باشند.')], '''
mijn collega|persoon met wie ik samenwerk|my colleague|همکارم
mijn leidinggevende|persoon die mijn werk aanstuurt|my manager|مدیرم
mijn werkgever|persoon of organisatie waarvoor ik werk|my employer|کارفرمایم
mijn contactpersoon|persoon bij wie ik met vragen terechtkan|my contact person|مسئول ارتباط من
mijn ploegbaas|persoon die mijn werkploeg leidt|my team supervisor|سرپرست گروهم
mijn mentor|ervaren persoon die mij begeleidt|my mentor|راهنمایم
mijn vervanger|persoon die mijn taak tijdelijk overneemt|my replacement|جانشینم
mijn medewerker|persoon die met of voor mij werkt|my staff member|همکار زیرمجموعه‌ام
mijn klant|persoon die mijn product of dienst gebruikt|my customer|مشتری‌ام
mijn leverancier|persoon die goederen aan mij levert|my supplier|تأمین‌کننده‌ام
''')
add('worklife', ('Werk organiseren','Organising work','سازمان‌دهی کار'), [
('Ik bespreek {nl} met mijn leidinggevende.','I discuss {en} with my manager.','من درباره {fa} با مدیرم صحبت می‌کنم.'),
('Ik maak een afspraak om {nl} rustig met mijn leidinggevende te bespreken.','I make an appointment to discuss {en} calmly with my manager.','وقت می‌گیرم تا با آرامش درباره {fa} با مدیرم صحبت کنم.'),
('Tijdens ons overleg leg ik uit wat {nl} voor mij betekent en vraag ik welke mogelijkheden er zijn.','During our meeting I explain what {en} means for me and ask what options there are.','در جلسه توضیح می‌دهم {fa} برای من چه معنایی دارد و می‌پرسم چه گزینه‌هایی وجود دارد.')], '''
het uurrooster|overzicht van de uren waarop je werkt|the work schedule|برنامه کاری
de werkdruk|hoeveel inspanning het werk vraagt|the workload|فشار کاری
de opleiding|traject waarin je kennis en vaardigheden leert|the training|دوره آموزشی
de vakantie|periode waarin je vrij bent van werk|the holiday|مرخصی
het verlof|toestemming om tijdelijk niet te werken|the leave|مرخصی کاری
de pauze|korte onderbreking van het werk|the break|زمان استراحت
het overwerk|werk buiten je gewone werkuren|the overtime|اضافه‌کاری
de nachtdienst|werkperiode tijdens de nacht|the night shift|شیفت شب
de proefperiode|eerste periode waarin een samenwerking wordt uitgeprobeerd|the trial period|دوره آزمایشی
de werktijd|tijd die je aan betaald werk besteedt|the working time|ساعت کار
''')
add('repairs', ('Problemen in huis','Household problems','مشکلات خانه'), [
('Ik meld {nl} aan de verhuurder.','I report {en} to the landlord.','من {fa} را به صاحب‌خانه گزارش می‌دهم.'),
('Ik maak een foto en meld {nl} aan de verhuurder.','I take a photo and report {en} to the landlord.','عکس می‌گیرم و {fa} را به صاحب‌خانه گزارش می‌دهم.'),
('Ik beschrijf wanneer ik {nl} heb opgemerkt en vraag om een duidelijke afspraak voor de herstelling.','I describe when I noticed {en} and ask for a clear repair appointment.','توضیح می‌دهم چه زمانی متوجه {fa} شدم و برای تعمیر، زمان مشخصی می‌خواهم.')], '''
het lek|opening waardoor water ongewenst ontsnapt|the leak|نشتی
de vochtplek|plek die door vocht verkleurd is|the damp patch|لکه رطوبت
de schimmel|aangroei die vaak in vochtige ruimtes ontstaat|the mould|کپک
de stroompanne|onderbreking van de elektriciteit|the power cut|قطعی برق
de verstopping|blokkade waardoor water niet wegloopt|the blockage|گرفتگی
de kapotte kraan|kraan die niet goed werkt|the broken tap|شیر خراب
het gebroken raam|raam waarvan het glas stuk is|the broken window|پنجره شکسته
de losse tegel|tegel die niet meer goed vastzit|the loose tile|کاشی لق
de defecte verwarming|verwarming die niet goed werkt|the faulty heating|گرمایش خراب
de beschadigde deur|deur waaraan iets stuk is|the damaged door|در آسیب‌دیده
''')
add('renting', ('Huurafspraken','Rental agreements','توافق‌های اجاره'), [
('Ik lees {nl} aandachtig.','I read {en} carefully.','من {fa} را با دقت می‌خوانم.'),
('Ik lees {nl} aandachtig en schrijf mijn vragen op.','I read {en} carefully and write down my questions.','من {fa} را با دقت می‌خوانم و سؤال‌هایم را یادداشت می‌کنم.'),
('Voordat ik akkoord ga, lees ik {nl} en vraag ik uitleg over de bepalingen die ik niet begrijp.','Before agreeing, I read {en} and ask about the provisions I do not understand.','پیش از موافقت، {fa} را می‌خوانم و درباره بندهایی که نمی‌فهمم توضیح می‌خواهم.')], '''
het huurcontract|schriftelijke overeenkomst over het huren van een woning|the tenancy agreement|قرارداد اجاره
de plaatsbeschrijving|beschrijving van de toestand van een woning|the property condition report|گزارش وضعیت ملک
het huisreglement|regels voor het gebruik van een gebouw|the house rules|مقررات ساختمان
de afrekening|overzicht van kosten en betaalde voorschotten|the final statement|صورت‌حساب نهایی
de factuur|document met wat je moet betalen|the invoice|فاکتور
de meterstand|afgelezen hoeveelheid op een verbruiksmeter|the meter reading|عدد کنتور
de opzegbrief|brief waarmee je een overeenkomst beëindigt|the notice letter|نامه فسخ
het ontvangstbewijs|bewijs dat iets ontvangen of betaald is|the receipt|رسید
het betalingsverzoek|bericht met de vraag om een bedrag te betalen|the payment request|درخواست پرداخت
de verzekeringspolis|document met afspraken over een verzekering|the insurance policy|بیمه‌نامه
''')
add('family', ('Familie','Family','خانواده'), [
('Ik ga zondag op bezoek bij {nl}.','I visit {en} on Sunday.','روز یکشنبه به دیدن {fa} می‌روم.'),
('Ik bel eerst om te vragen of ik zondag bij {nl} op bezoek kan komen.','I call first to ask whether I can visit {en} on Sunday.','اول زنگ می‌زنم تا بپرسم آیا می‌توانم یکشنبه به دیدن {fa} بروم.'),
('Omdat we elkaar niet elke week zien, probeer ik tijdens mijn bezoek aan {nl} echt tijd te maken voor een gesprek.','Because we do not see each other every week, I try to make time for a real conversation when visiting {en}.','چون هر هفته همدیگر را نمی‌بینیم، هنگام دیدن {fa} سعی می‌کنم برای گفت‌وگویی واقعی وقت بگذارم.')], '''
mijn moeder|de vrouw die mijn ouder is|my mother|مادرم
mijn vader|de man die mijn ouder is|my father|پدرم
mijn zus|meisje of vrouw met dezelfde ouder of ouders|my sister|خواهرم
mijn broer|jongen of man met dezelfde ouder of ouders|my brother|برادرم
mijn grootmoeder|de moeder van een van mijn ouders|my grandmother|مادربزرگم
mijn grootvader|de vader van een van mijn ouders|my grandfather|پدربزرگم
mijn tante|zus van een ouder of partner van een oom|my aunt|عمه یا خاله‌ام
mijn oom|broer van een ouder of partner van een tante|my uncle|عمو یا دایی‌ام
mijn nicht|dochter van een oom, tante, broer of zus|my female cousin or niece|دخترعمو، دخترخاله یا خواهرزاده‌ام
mijn neef|zoon van een oom, tante, broer of zus|my male cousin or nephew|پسرعمو، پسرخاله یا برادرزاده‌ام
''')
add('relationships', ('Omgaan met mensen','Getting along with people','ارتباط با دیگران'), [
('In onze groep is {nl} belangrijk.','In our group, {en} is important.','در گروه ما {fa} مهم است.'),
('We praten over wat {nl} voor ieder van ons betekent.','We discuss what {en} means to each of us.','گفت‌وگو می‌کنیم که {fa} برای هر یک از ما چه معنایی دارد.'),
('Ook als we het oneens zijn, proberen we {nl} zichtbaar te maken in de manier waarop we met elkaar spreken.','Even when we disagree, we try to show {en} in how we speak to one another.','حتی وقتی اختلاف نظر داریم، سعی می‌کنیم {fa} را در شیوه صحبت با یکدیگر نشان دهیم.')], '''
respect|rekening houden met de waarde en grenzen van iemand|respect|احترام
vertrouwen|gevoel dat je op iemand kunt rekenen|trust|اعتماد
geduld|rustig kunnen wachten of omgaan met vertraging|patience|صبر
beleefdheid|vriendelijke en passende omgangsvorm|politeness|ادب
eerlijkheid|bereidheid om de waarheid te zeggen|honesty|صداقت
aandacht|gericht luisteren of kijken|attention|توجه
begrip|bereidheid om iemands situatie te begrijpen|understanding|درک متقابل
vriendschap|persoonlijke band tussen mensen die elkaar graag zien|friendship|دوستی
gastvrijheid|bezoekers vriendelijk ontvangen|hospitality|مهمان‌نوازی
duidelijkheid|toestand waarin de betekenis goed te begrijpen is|clarity|روشنی
''')
add('culture', ('Vrije tijd','Leisure','اوقات فراغت'), [
('We gaan samen naar {nl}.','We go to {en} together.','ما با هم به {fa} می‌رویم.'),
('We spreken op tijd af, zodat we samen naar {nl} kunnen gaan.','We arrange a time in advance so we can go to {en} together.','از قبل هماهنگ می‌کنیم تا بتوانیم با هم به {fa} برویم.'),
('Voordat we naar {nl} gaan, bekijken we of de locatie goed bereikbaar is met het openbaar vervoer.','Before going to {en}, we check whether the venue is easy to reach by public transport.','پیش از رفتن به {fa}، بررسی می‌کنیم آیا محل با حمل‌ونقل عمومی به‌راحتی قابل دسترسی است.')], '''
het concert|optreden waarbij muzikanten live spelen|the concert|کنسرت
de filmvoorstelling|moment waarop een film aan publiek getoond wordt|the film screening|نمایش فیلم
de tentoonstelling|verzameling werken die publiek bekeken kan worden|the exhibition|نمایشگاه
de theatervoorstelling|verhaal dat spelers op een podium brengen|the theatre performance|نمایش تئاتر
de lezing|uitleg die iemand voor een publiek geeft|the lecture|سخنرانی
de workshop|bijeenkomst waarin je iets praktisch leert|the workshop|کارگاه
de rondleiding|bezoek waarbij iemand uitleg geeft over een plaats|the guided tour|بازدید با راهنما
het festival|evenement met verschillende optredens of activiteiten|the festival|جشنواره
de openluchtfilm|film die buiten vertoond wordt|the open-air film|نمایش فیلم در فضای باز
de quizavond|avond waarop groepen vragen beantwoorden|the quiz night|شب مسابقه دانستنی‌ها
''')
add('nature', ('Natuur dichtbij','Nature nearby','طبیعت نزدیک'), [
('We wandelen langs {nl}.','We walk past {en}.','ما از کنار {fa} قدم می‌زنیم.'),
('Tijdens onze wandeling stoppen we even bij {nl}.','During our walk we stop briefly at {en}.','در طول پیاده‌روی، کمی کنار {fa} می‌ایستیم.'),
('De gids vraagt ons goed naar {nl} te kijken en te beschrijven wat er sinds de vorige wandeling veranderd is.','The guide asks us to look carefully at {en} and describe what has changed since our previous walk.','راهنما از ما می‌خواهد با دقت به {fa} نگاه کنیم و توضیح بدهیم از پیاده‌روی قبلی چه چیزی تغییر کرده است.')], '''
de rivier|grote natuurlijke stroom water|the river|رودخانه
de beek|kleine natuurlijke stroom water|the stream|جویبار
de vijver|klein stilstaand water|the pond|برکه
het bos|gebied met veel bomen|the wood|جنگل
het veld|open stuk grond|the field|دشت
de weide|grasland waarop vaak dieren grazen|the meadow|مرتع
de boom|grote plant met een houten stam|the tree|درخت
de struik|plant met meerdere houten takken vanaf de grond|the bush|بوته
de haag|rij struiken als afscheiding|the hedge|پرچین
de oever|rand van een rivier of ander water|the riverbank|کرانه رود
''')
add('garden', ('In de tuin','In the garden','در باغچه'), [
('Ik zet {nl} in het tuinhuis.','I put {en} in the garden shed.','من {fa} را در انبار باغ می‌گذارم.'),
('Na het tuinwerk maak ik {nl} schoon en zet ik alles weg.','After gardening I clean {en} and put everything away.','بعد از باغبانی، {fa} را تمیز می‌کنم و همه‌چیز را سر جایش می‌گذارم.'),
('Omdat we materiaal delen, spreek ik met de buren af waar we {nl} na gebruik bewaren.','Because we share equipment, I agree with the neighbours where to store {en} after use.','چون وسایل را مشترک استفاده می‌کنیم، با همسایه‌ها هماهنگ می‌کنم {fa} را بعد از استفاده کجا بگذاریم.')], '''
de gieter|kan met tuit om planten water te geven|the watering can|آب‌پاش دستی
de schop|gereedschap waarmee je aarde verplaatst|the shovel|بیل
de hark|gereedschap met tanden om aarde of bladeren bijeen te halen|the rake|شن‌کش
de snoeischaar|schaar om takken af te knippen|the pruning shears|قیچی باغبانی
de kruiwagen|bak op een wiel om materiaal te vervoeren|the wheelbarrow|فرغون
de bloempot|pot waarin een plant groeit|the flowerpot|گلدان
de tuinslang|lange slang om water naar planten te brengen|the garden hose|شلنگ باغ
het plantbakje|kleine bak waarin jonge planten groeien|the seed tray|سینی نشا
de emmer|vat met een handvat om vloeistof te dragen|the bucket|سطل
de bezem|gereedschap waarmee je vuil bijeenveegt|the broom|جارو
''')
add('food', ('Eten kopen','Buying food','خرید خوراکی'), [
('Ik koop {nl} op de markt.','I buy {en} at the market.','من {fa} را از بازار می‌خرم.'),
('Ik koop {nl} op de markt en vraag hoe ik het best alles bewaar.','I buy {en} at the market and ask how best to store it.','من {fa} را از بازار می‌خرم و می‌پرسم بهترین روش نگهداری آن چیست.'),
('Ik kies bewust hoeveel ik van {nl} koop, zodat er thuis zo weinig mogelijk verloren gaat.','I deliberately choose how much of {en} to buy so as little as possible is wasted at home.','با دقت تصمیم می‌گیرم چه مقدار {fa} بخرم تا در خانه تا حد ممکن چیزی هدر نرود.')], '''
appels|ronde vruchten die aan een appelboom groeien|apples|سیب
peren|vruchten met een smalle bovenkant en ronde onderkant|pears|گلابی
bananen|lange gele vruchten|bananas|موز
tomaten|rode vruchten die vaak als groente gebruikt worden|tomatoes|گوجه‌فرنگی
wortelen|oranje wortelgroenten|carrots|هویج
aardappelen|eetbare knollen die onder de grond groeien|potatoes|سیب‌زمینی
champignons|eetbare paddenstoelen|mushrooms|قارچ
uien|groenten met lagen en een scherpe smaak|onions|پیاز
bonen|eetbare zaden of peulen|beans|لوبیا
aardbeien|kleine rode vruchten met zaadjes aan de buitenkant|strawberries|توت‌فرنگی
''')
add('drinks', ('In het café','At the café','در کافه'), [
('Ik bestel {nl}.','I order {en}.','من {fa} سفارش می‌دهم.'),
('Ik bestel {nl} en vraag meteen hoeveel het kost.','I order {en} and immediately ask how much it costs.','من {fa} سفارش می‌دهم و همان موقع می‌پرسم چقدر می‌شود.'),
('Ik bestel {nl}, maar vraag eerst of ik ook mijn eigen herbruikbare beker mag gebruiken.','I order {en}, but first ask whether I may use my own reusable cup.','من {fa} سفارش می‌دهم، اما اول می‌پرسم آیا می‌توانم از لیوان چندبارمصرف خودم استفاده کنم.')], '''
een koffie|een kop van een drank uit koffiebonen|a coffee|یک قهوه
een thee|een kop van een drank uit theebladeren|a tea|یک چای
een glas water|een portie water in een glas|a glass of water|یک لیوان آب
een fruitsap|een glas sap uit fruit|a fruit juice|یک آب‌میوه
een warme chocolademelk|een warme drank met cacao en melk|a hot chocolate|یک شکلات داغ
een bruiswater|water met koolzuurbelletjes|a sparkling water|یک آب گازدار
een muntthee|thee op basis van munt|a mint tea|یک چای نعناع
een cafeïnevrije koffie|koffie waar vrijwel geen cafeïne in zit|a decaf coffee|یک قهوه بدون کافئین
een limonade|zoete verfrissende drank|a lemonade|یک لیموناد
een cappuccino|koffie met warme melk en melkschuim|a cappuccino|یک کاپوچینو
''')
add('restaurant', ('Uit eten','Eating out','غذا خوردن بیرون'), [
('Ik vraag naar {nl}.','I ask about {en}.','من درباره {fa} سؤال می‌کنم.'),
('Voordat ik bestel, vraag ik naar {nl}.','Before I order, I ask about {en}.','پیش از سفارش دادن، درباره {fa} سؤال می‌کنم.'),
('Ik vraag beleefd naar {nl} en leg uit waarom die informatie voor mij belangrijk is.','I politely ask about {en} and explain why that information matters to me.','مؤدبانه درباره {fa} سؤال می‌کنم و توضیح می‌دهم چرا این اطلاعات برای من مهم است.')], '''
de menukaart|overzicht van gerechten en prijzen|the menu|منو
het dagmenu|maaltijd die die dag als menu aangeboden wordt|the daily menu|منوی روز
het vegetarische gerecht|gerecht zonder vlees of vis|the vegetarian dish|غذای گیاهی
de ingrediënten|producten waaruit een gerecht gemaakt is|the ingredients|مواد اولیه
de allergenen|stoffen die bij sommige mensen een allergie veroorzaken|the allergens|مواد حساسیت‌زا
de portiegrootte|hoeveelheid eten voor één persoon|the portion size|اندازه پرس
de wachttijd|tijd die je moet wachten|the waiting time|مدت انتظار
de rekening|overzicht van wat je moet betalen|the bill|صورت‌حساب
de betaalwijze|manier waarop je betaalt|the payment method|روش پرداخت
het kindermenu|maaltijd die speciaal voor kinderen wordt aangeboden|the children’s menu|منوی کودک
''')
add('shoppingdetails', ('Bewust kopen','Buying thoughtfully','خرید آگاهانه'), [
('Ik vraag naar {nl} van dit product.','I ask about {en} of this product.','من درباره {fa} این محصول سؤال می‌کنم.'),
('Ik vergelijk {nl} van dit product met die van een ander product.','I compare {en} of this product with that of another product.','من {fa} این محصول را با محصول دیگری مقایسه می‌کنم.'),
('De prijs is niet het enige wat telt; ik informeer ook naar {nl} van dit product.','Price is not the only thing that matters; I also ask about {en} of this product.','قیمت تنها موضوع مهم نیست؛ درباره {fa} این محصول هم اطلاعات می‌گیرم.')], '''
de kwaliteit|mate waarin iets goed gemaakt is|the quality|کیفیت
de levensduur|tijd dat een product bruikbaar blijft|the lifespan|طول عمر
de garantie|belofte van herstel onder bepaalde voorwaarden|the warranty|ضمانت
de herkomst|plaats waar iets vandaan komt|the origin|منشأ
de prijs|bedrag dat je voor iets betaalt|the price|قیمت
het gewicht|hoe zwaar iets is|the weight|وزن
het formaat|grootte en vorm van iets|the size|اندازه
de kleur|hoe iets eruitziet in het licht|the colour|رنگ
het materiaal|stof waarvan iets gemaakt is|the material|جنس
de houdbaarheid|periode waarin een product goed blijft|the shelf life|مدت ماندگاری
''')
add('news', ('Nieuws begrijpen','Understanding news','درک خبرها'), [
('Ik lees {nl} in de krant.','I read {en} in the newspaper.','من {fa} را در روزنامه می‌خوانم.'),
('Ik lees {nl} en bespreek de belangrijkste informatie met een vriend.','I read {en} and discuss the main information with a friend.','من {fa} را می‌خوانم و اطلاعات اصلی را با دوستی بررسی می‌کنم.'),
('Na het lezen van {nl} controleer ik welke uitspraken feiten zijn en welke een mening weergeven.','After reading {en}, I check which statements are facts and which express an opinion.','پس از خواندن {fa}، بررسی می‌کنم کدام جمله‌ها واقعیت هستند و کدام نظر شخصی را بیان می‌کنند.')], '''
het artikel|geschreven tekst over een onderwerp|the article|مقاله
de reportage|verslag van een plaats of gebeurtenis|the feature report|گزارش میدانی
het interview|gesprek met vragen en antwoorden voor een publiek|the interview|مصاحبه
het lezersbericht|bericht van iemand die de krant leest|the reader’s message|پیام خواننده
het opiniestuk|tekst waarin iemand een mening onderbouwt|the opinion piece|یادداشت تحلیلی
het buurtbericht|kort nieuws over de buurt|the neighbourhood news item|خبر محله
de aankondiging|bericht over iets dat binnenkort gebeurt|the announcement|اعلامیه
het weerbericht|informatie over verwacht weer|the weather report|گزارش هواشناسی
het sportverslag|beschrijving van een sportwedstrijd|the sports report|گزارش ورزشی
het cultuurbericht|nieuws over kunst en culturele activiteiten|the culture news item|خبر فرهنگی
''')
add('events', ('Een activiteit organiseren','Organising an activity','برگزاری یک فعالیت'), [
('We regelen {nl} voor de activiteit.','We arrange {en} for the activity.','ما {fa} را برای فعالیت فراهم می‌کنیم.'),
('We regelen {nl} op voorhand, zodat we op de dag zelf minder haast hebben.','We arrange {en} beforehand so we are less rushed on the day itself.','ما {fa} را از قبل فراهم می‌کنیم تا در روز فعالیت کمتر عجله داشته باشیم.'),
('We vragen wie verantwoordelijk is voor {nl} en leggen de afspraak schriftelijk vast.','We ask who is responsible for {en} and put the agreement in writing.','می‌پرسیم چه کسی مسئول {fa} است و توافق را کتبی ثبت می‌کنیم.')], '''
de zaal|grote ruimte voor een bijeenkomst|the hall|سالن
het vervoer|manier waarop mensen of spullen verplaatst worden|the transport|حمل‌ونقل
de inschrijving|aanmelding om aan iets mee te doen|the registration|ثبت‌نام
de catering|verzorging van eten en drinken|the catering|پذیرایی
de versiering|voorwerpen die een ruimte feestelijk maken|the decoration|تزئینات
de geluidsinstallatie|apparatuur om geluid hoorbaar te maken|the sound system|سیستم صوتی
de verlichting|lampen die een ruimte zichtbaar maken|the lighting|روشنایی
de bewegwijzering|borden die de juiste richting tonen|the signposting|تابلوهای راهنما
de ontvangst|manier waarop bezoekers worden verwelkomd|the reception|استقبال
het programma|overzicht van geplande activiteiten|the programme|برنامه رویداد
''')
add('learningnouns', ('Taal oefenen','Practising language','تمرین زبان'), [
('Ik oefen {nl} met een klasgenoot.','I practise {en} with a classmate.','من {fa} را با یک هم‌کلاسی تمرین می‌کنم.'),
('Ik oefen {nl} eerst met hulp en daarna probeer ik het alleen.','I practise {en} with help first and then try on my own.','ابتدا {fa} را با کمک تمرین می‌کنم و بعد تنها امتحان می‌کنم.'),
('Na het oefenen van {nl} zoek ik een nieuwe situatie waarin ik het geleerde zelfstandig kan gebruiken.','After practising {en}, I look for a new situation in which I can use what I learned independently.','پس از تمرین {fa}، موقعیت تازه‌ای پیدا می‌کنم تا آموخته‌هایم را مستقل به کار ببرم.')], '''
de uitspraak|manier waarop je klanken en woorden zegt|pronunciation|تلفظ
de woordvolgorde|volgorde van woorden in een zin|word order|ترتیب واژه‌ها
de spelling|juiste schrijfwijze van woorden|spelling|املای واژه‌ها
de werkwoordsvorm|vorm van een werkwoord in een zin|the verb form|شکل فعل
de vraagzin|zin waarmee je een vraag stelt|the question form|جمله پرسشی
de beleefde vraag|vraag die rekening houdt met de ander|the polite request|درخواست مؤدبانه
de verleden tijd|werkwoordstijd voor iets dat voorbij is|the past tense|زمان گذشته
de bijzin|zin die deel uitmaakt van een grotere zin|the subordinate clause|جمله وابسته
de klemtoon|deel van een woord of zin dat extra nadruk krijgt|stress|تکیه
het telefoongesprek|gesprek via de telefoon|the telephone conversation|مکالمه تلفنی
''')
assert len(GROUPS) == 52, len(GROUPS)
assert sum(len(g['items']) for g in GROUPS) == 520
