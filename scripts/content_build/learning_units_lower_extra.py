"""Six original narrative units; all language and stage placement await review."""

UNITS = []


def unit(stage, slug, title, genre, focus, lines, listening, reading_q, listening_q,
         speaking, spoken_sample, writing, written_sample, bounds, words):
    UNITS.append({'stage': stage, 'id': slug, 'title': title, 'genre': genre, 'focus': focus,
                      'lines': lines, 'listening': listening, 'reading_q': reading_q,
                      'listening_q': listening_q, 'speaking': speaking,
                      'spoken_sample': spoken_sample, 'writing': writing,
                      'written_sample': written_sample, 'speaking_bounds': bounds,
                      'writing_bounds': bounds, 'criteria': [focus], 'words': words})


unit('pre-a1', 'red-scarf', 'De rode sjaal|The red scarf|شال قرمز',
     'Een ontmoeting|An encounter|یک آشنایی',
     'Benoem een voorwerp en geef het aan iemand terug.|Name an object and return it to someone.|یک وسیله را نام ببر و آن را به صاحبش برگردان.', [
    'Sara is in het park.|Sara is in the park.|سارا در پارک است.',
    'Ze heeft een rode sjaal.|She has a red scarf.|او شال قرمزی دارد.',
    'De sjaal valt.|The scarf falls.|شال می‌افتد.',
    'Sara loopt verder.|Sara walks on.|سارا به راهش ادامه می‌دهد.',
    'Tom ziet de sjaal.|Tom sees the scarf.|تام شال را می‌بیند.',
    'Hij roept: Mevrouw!|He calls: Madam!|صدا می‌زند: خانم!',
    'Sara staat stil.|Sara stops.|سارا می‌ایستد.',
    'Tom zegt: Hier is uw sjaal.|Tom says: Here is your scarf.|تام می‌گوید: این هم شالتان.',
    'Sara lacht.|Sara smiles.|سارا لبخند می‌زند.',
    'Ze zegt: Dank u wel, ik ben Sara.|She says: Thank you, I am Sara.|می‌گوید: خیلی ممنون، من سارا هستم.'
], 'Ik ben Noor. Mijn sjaal is groen. Hij ligt hier, op de stoel.|I am Noor. My scarf is green. It is here, on the chair.|من نور هستم. شال من سبز است. اینجا روی صندلی است.', [
    ('Wie ziet de rode sjaal op de grond?|Who sees the red scarf on the ground?|چه کسی شال قرمز را روی زمین می‌بیند؟', 'Tom.|Tom.|تام.', 'Noor.|Noor.|نور.', 'Tom ziet de sjaal nadat hij valt.|Tom sees the scarf after it falls.|تام بعد از افتادن شال آن را می‌بیند.'),
    ('Wat zegt Sara op het einde?|What does Sara say at the end?|سارا در پایان چه می‌گوید؟', 'Dank u wel, ik ben Sara.|Thank you, I am Sara.|خیلی ممنون، من سارا هستم.', 'Mijn sjaal is groen.|My scarf is green.|شال من سبز است.', 'Sara bedankt Tom en noemt haar naam.|Sara thanks Tom and gives her name.|سارا از تام تشکر می‌کند و نامش را می‌گوید.')
], [
    ('Welke kleur heeft de sjaal van Noor?|What colour is Noor’s scarf?|شال نور چه رنگی است؟', 'Groen.|Green.|سبز.', 'Rood.|Red.|قرمز.', 'Noor zegt: Mijn sjaal is groen.|Noor says: My scarf is green.|نور می‌گوید: شال من سبز است.'),
    ('Waar ligt de sjaal van Noor?|Where is Noor’s scarf?|شال نور کجاست؟', 'Op de stoel.|On the chair.|روی صندلی.', 'In het park.|In the park.|در پارک.', 'In het bericht ligt de sjaal op de stoel.|In the message the scarf is on the chair.|در پیام، شال روی صندلی است.')
], 'Geef Noor haar sjaal terug. Zeg ook welke kleur hij heeft.|Return Noor’s scarf. Say what colour it is too.|شال نور را پس بده. رنگ آن را هم بگو.',
     'Dag Noor. Hier is uw sjaal. Hij is groen.|Hello, Noor. Here is your scarf. It is green.|سلام نور. این هم شالتان. سبز است.',
     'Schrijf de naam en de kleur uit het luisterbericht.|Write the name and colour from the audio message.|نام و رنگی را که در پیام شنیدی بنویس.',
     'Noor. De sjaal is groen.|Noor. The scarf is green.|نور. شال سبز است.', (2, 15), [
    ('de sjaal', 'Een doek voor om je hals.|A cloth worn around your neck.|پارچه‌ای که دور گردن می‌اندازند؛ شال.', 'Sara heeft een sjaal.|Sara has a scarf.|سارا شال دارد.'),
    ('vallen', 'Naar beneden gaan, zonder dat je dat wilt.|To fall down unintentionally.|ناخواسته پایین افتادن.', 'De sjaal valt.|The scarf falls.|شال می‌افتد.'),
    ('rood', 'Een kleur.|A colour.|یک رنگ.', 'De sjaal is rood.|The scarf is red.|شال قرمز است.'),
    ('hier', 'Op deze plaats.|In this place.|در اینجا.', 'Hier is uw sjaal.|Here is your scarf.|این هم شالتان.')
])

unit('a1', 'first-dance', 'Niet meer bij de deur|No longer by the door|دیگر کنار در نیست',
     'Een nieuw begin|A new beginning|یک شروع تازه',
     'Vertel wat je kunt en nodig iemand uit om mee te doen.|Say what you can do and invite someone to join.|بگو چه کاری بلدی و کسی را به همراهی دعوت کن.', [
    'Yara komt voor het eerst naar de dansles.|Yara comes to the dance class for the first time.|یارا برای نخستین بار به کلاس رقص می‌آید.',
    'Ze kent niemand in de zaal.|She does not know anyone in the room.|هیچ‌کس را در سالن نمی‌شناسد.',
    'De muziek begint.|The music starts.|موسیقی شروع می‌شود.',
    'De andere mensen kiezen een partner.|The other people choose a partner.|دیگران برای خود یار انتخاب می‌کنند.',
    'Yara blijft zenuwachtig bij de deur staan.|Yara stays nervously by the door.|یارا با اضطراب کنار در می‌ماند.',
    'Els loopt naar haar toe.|Els walks up to her.|الس به طرفش می‌آید.',
    'Wil je met mij dansen? vraagt Els.|Would you like to dance with me? Els asks.|الس می‌پرسد: می‌خواهی با من برقصی؟',
    'Ik kan niet goed dansen, zegt Yara.|I cannot dance well, Yara says.|یارا می‌گوید: خوب رقصیدن بلد نیستم.',
    'Dan leren we samen, antwoordt Els.|Then we will learn together, Els replies.|الس جواب می‌دهد: پس با هم یاد می‌گیریم.',
    'Bij het volgende lied doet Yara mee.|Yara joins in for the next song.|با آهنگ بعدی، یارا هم با دیگران همراه می‌شود.'
], 'Dag Yara, Els hier. De volgende les is vrijdag. We beginnen om zeven uur in de avond. Neem een fles water mee.|Hi Yara, Els here. The next lesson is on Friday. We start at seven in the evening. Bring a bottle of water.|سلام یارا، الس هستم. کلاس بعدی جمعه است. ساعت هفت عصر شروع می‌کنیم. یک بطری آب همراهت بیاور.', [
    ('Waarom blijft Yara eerst bij de deur?|Why does Yara initially stay by the door?|چرا یارا ابتدا کنار در می‌ماند؟', 'Ze is zenuwachtig en kent niemand.|She is nervous and knows nobody.|مضطرب است و کسی را نمی‌شناسد.', 'Ze wacht op een taxi.|She is waiting for a taxi.|منتظر تاکسی است.', 'Het is haar eerste les en ze kent niemand.|It is her first lesson and she knows nobody.|اولین کلاسش است و کسی را نمی‌شناسد.'),
    ('Wat doet Els?|What does Els do?|الس چه کار می‌کند؟', 'Ze vraagt Yara om samen te dansen.|She asks Yara to dance with her.|از یارا می‌خواهد با او برقصد.', 'Ze zet de muziek uit.|She switches off the music.|موسیقی را خاموش می‌کند.', 'Els loopt naar Yara en nodigt haar uit.|Els approaches Yara and invites her.|الس به یارا نزدیک می‌شود و دعوتش می‌کند.')
], [
    ('Op welke dag is de volgende les?|On which day is the next lesson?|کلاس بعدی چه روزی است؟', 'Vrijdag.|Friday.|جمعه.', 'Woensdag.|Wednesday.|چهارشنبه.', 'Els noemt vrijdag.|Els says Friday.|الس از جمعه می‌گوید.'),
    ('Hoe laat begint de les?|What time does the lesson start?|کلاس چه ساعتی شروع می‌شود؟', 'Om zeven uur in de avond.|At seven in the evening.|ساعت هفت عصر.', 'Om zeven uur in de ochtend.|At seven in the morning.|ساعت هفت صبح.', 'Els zegt dat de les in de avond begint.|Els says the lesson starts in the evening.|الس می‌گوید کلاس عصر شروع می‌شود.')
], 'Je ziet een nieuwe deelnemer bij de deur. Nodig die persoon uit om samen te dansen. Vertel ook wanneer de volgende les is volgens het luisterbericht.|You see a new participant by the door. Invite that person to dance. Also say when the next lesson is, according to the audio message.|شرکت‌کنندهٔ تازه‌ای را کنار در می‌بینی. او را به رقص دعوت کن. زمان کلاس بعدی را هم طبق پیام شنیداری بگو.',
     'Dag, wil je met mij dansen? Ik ben ook nieuw. De volgende les is vrijdag om zeven uur in de avond.|Hello, would you like to dance with me? I am new too. The next lesson is on Friday at seven in the evening.|سلام، می‌خواهی با من برقصی؟ من هم تازه آمده‌ام. کلاس بعدی جمعه ساعت هفت عصر است.',
     'Antwoord op Els. Bevestig de dag en het uur van de volgende les en zeg wat je meebrengt.|Reply to Els. Confirm the day and time of the next lesson and say what you will bring.|به الس جواب بده. روز و ساعت کلاس بعدی را تأیید کن و بگو چه چیزی همراهت می‌آوری.',
     'Dag Els, bedankt! Ik kom vrijdag om zeven uur in de avond. Ik neem water mee. Tot dan!|Hi Els, thanks! I will come on Friday at seven in the evening. I will bring water. See you then!|سلام الس، ممنون! جمعه ساعت هفت عصر می‌آیم. آب هم می‌آورم. تا آن موقع!', (6, 40), [
    ('de partner', 'De persoon met wie je samen iets doet.|The person with whom you do an activity.|کسی که فعالیتی را همراه او انجام می‌دهی؛ یار.', 'Els is mijn partner bij de dansles.|Els is my partner in the dance class.|الس یار من در کلاس رقص است.'),
    ('meedoen', 'Samen met anderen aan een activiteit deelnemen.|To join an activity with others.|در فعالیتی با دیگران شرکت کردن.', 'Yara doet mee met de dansles.|Yara joins the dance class.|یارا در کلاس رقص شرکت می‌کند.'),
    ('zenuwachtig', 'Een beetje bang of onrustig.|A little nervous or anxious.|کمی مضطرب یا نگران.', 'Yara is zenuwachtig.|Yara is nervous.|یارا مضطرب است.'),
    ('samen', 'Met elkaar.|Together.|با هم.', 'We leren samen dansen.|We learn to dance together.|با هم رقصیدن یاد می‌گیریم.')
])

unit('pre-a2', 'silent-waiter', 'Een rol zonder tekst|A role without lines|نقشی بدون دیالوگ',
     'Een vrolijke verrassing|A cheerful surprise|غافلگیری شاد',
     'Beschrijf een oefening en vraag om een verandering.|Describe an exercise and ask for a change.|تمرینی را توصیف کن و تغییری درخواست کن.', [
    'In het buurthuis doet Adam mee aan een toneelles.|Adam joins a drama class at the community centre.|آدم در کلاس تئاتر مرکز محله شرکت می‌کند.',
    'Iedere deelnemer krijgt een kleine rol.|Each participant receives a small role.|هر شرکت‌کننده نقش کوچکی می‌گیرد.',
    'Adam wil graag spreken, maar hij speelt een ober zonder tekst.|Adam wants to speak, but he plays a waiter without lines.|آدم دوست دارد حرف بزند، اما نقش گارسونی بدون دیالوگ را بازی می‌کند.',
    'Tijdens de eerste oefening zet hij een lege kop op tafel.|During the first exercise he puts an empty cup on the table.|در تمرین اول، فنجانی خالی روی میز می‌گذارد.',
    'De actrice vraagt waarom er geen koffie is.|The actress asks why there is no coffee.|بازیگر زن می‌پرسد چرا قهوه‌ای در فنجان نیست.',
    'Adam kijkt in de kop en dan verbaasd naar de zaal.|Adam looks into the cup and then at the room in surprise.|آدم داخل فنجان را نگاه می‌کند و بعد با تعجب به سالن نگاه می‌کند.',
    'Iedereen lacht om het grappige moment.|Everyone laughs at the funny moment.|همه به آن لحظهٔ خنده‌دار می‌خندند.',
    'De begeleidster wil de scène nog eens oefenen.|The instructor wants to practise the scene again.|مربی می‌خواهد صحنه را دوباره تمرین کنند.',
    'Nu begrijpt Adam dat hij ook zonder woorden iets kan vertellen.|Adam now understands that he can communicate something without words too.|حالا آدم می‌فهمد بدون کلمه هم می‌تواند چیزی بیان کند.',
    'Toch vraagt hij voor de volgende oefening één korte zin.|Still, he asks for one short line in the next exercise.|بااین‌حال، برای تمرین بعدی یک جملهٔ کوتاه درخواست می‌کند.'
], 'Adam, na de pauze speel je geen ober maar een klant. Je zegt: Een koffie, alstublieft. Daarna wacht je op de ober. We oefenen de scène twee keer.|Adam, after the break you play a customer rather than a waiter. You say: A coffee, please. Then you wait for the waiter. We practise the scene twice.|آدم، بعد از استراحت به‌جای گارسون نقش مشتری را بازی می‌کنی. می‌گویی: یک قهوه، لطفاً. بعد منتظر گارسون می‌مانی. صحنه را دو بار تمرین می‌کنیم.', [
    ('Waarom lacht de groep?|Why does the group laugh?|چرا گروه می‌خندد؟', 'Adam kijkt verbaasd in een lege kop.|Adam looks into an empty cup in surprise.|آدم با تعجب داخل فنجان خالی نگاه می‌کند.', 'Adam vertelt een lange grap.|Adam tells a long joke.|آدم لطیفه‌ای طولانی تعریف می‌کند.', 'Zijn gezicht maakt de scène grappig, niet een gesproken grap.|His expression makes the scene funny, rather than a spoken joke.|حالت چهره‌اش صحنه را خنده‌دار می‌کند، نه لطیفه‌ای که تعریف کرده باشد.'),
    ('Wat vraagt Adam voor de volgende oefening?|What does Adam ask for in the next exercise?|آدم برای تمرین بعدی چه می‌خواهد؟', 'Eén korte zin.|One short line.|یک جملهٔ کوتاه.', 'Een andere zaal.|A different room.|سالنی دیگر.', 'Hij wil toch ook een beetje spreken.|He would still like to speak a little too.|بااین‌حال می‌خواهد کمی هم حرف بزند.')
], [
    ('Welke rol speelt Adam na de pauze?|Which role does Adam play after the break?|آدم بعد از استراحت چه نقشی بازی می‌کند؟', 'Een klant.|A customer.|مشتری.', 'Een ober.|A waiter.|گارسون.', 'De begeleidster verandert zijn rol in die van klant.|The instructor changes his role to a customer.|مربی نقش او را به مشتری تغییر می‌دهد.'),
    ('Hoe vaak oefenen ze de scène?|How many times do they practise the scene?|صحنه را چند بار تمرین می‌کنند؟', 'Twee keer.|Twice.|دو بار.', 'Eén keer.|Once.|یک بار.', 'In het bericht staat dat ze twee keer oefenen.|The message says they practise twice.|پیام می‌گوید دو بار تمرین می‌کنند.')
], 'Je speelt nu de klant. Herhaal de bestelling uit het luisterbericht en vraag of je twee keer mag oefenen.|You now play the customer. Repeat the order from the audio message and ask to practise twice.|حالا نقش مشتری را بازی می‌کنی. سفارش پیام شنیداری را تکرار کن و بپرس می‌توانی دو بار تمرین کنی.',
     'Een koffie, alstublieft. Mag ik deze zin twee keer oefenen?|A coffee, please. May I practise this line twice?|یک قهوه، لطفاً. می‌توانم این جمله را دو بار تمرین کنم؟',
     'Schrijf Adam een kort bericht over zijn nieuwe rol. Noem de rol, het moment en het aantal oefeningen.|Write Adam a short message about his new role. Include the role, when it starts and how many times they practise.|دربارهٔ نقش تازهٔ آدم برایش پیام کوتاهی بنویس. نقش، زمان شروع و تعداد تمرین را بیان کن.',
     'Dag Adam, na de pauze ben je de klant. Je bestelt een koffie en wacht op de ober. We oefenen twee keer.|Hi Adam, after the break you are the customer. You order a coffee and wait for the waiter. We practise twice.|سلام آدم، بعد از استراحت تو مشتری هستی. قهوه سفارش می‌دهی و منتظر گارسون می‌مانی. دو بار تمرین می‌کنیم.', (8, 55), [
    ('de rol', 'De persoon die je in een toneelstuk speelt.|The character you play in a performance.|شخصیتی که در نمایش بازی می‌کنی؛ نقش.', 'Adam krijgt een rol zonder tekst.|Adam receives a role without lines.|آدم نقشی بدون دیالوگ می‌گیرد.'),
    ('oefenen', 'Iets herhalen om het beter te kunnen.|To repeat something to improve at it.|برای بهتر شدن، کاری را تمرین کردن.', 'We oefenen de scène twee keer.|We practise the scene twice.|صحنه را دو بار تمرین می‌کنیم.'),
    ('verbaasd', 'Verrast doordat je iets niet verwacht.|Surprised because something was unexpected.|متعجب از چیزی که انتظارش را نداشتی.', 'Adam kijkt verbaasd.|Adam looks surprised.|آدم با تعجب نگاه می‌کند.'),
    ('toch', 'Ondanks wat eerder is gezegd of gebeurd.|Nevertheless, despite what was said or happened.|بااین‌حال، با وجود چیزی که گفته شده یا رخ داده است.', 'Toch wil hij een zin zeggen.|Nevertheless, he wants to say a line.|بااین‌حال می‌خواهد یک جمله بگوید.')
])

unit('a2', 'anniversary-cake', 'De scheve cake|The lopsided cake|کیک کج',
     'Liefde en een misverstand|Love and a misunderstanding|عشق و یک سوءتفاهم',
     'Vertel wat er is gebeurd en controleer een nieuwe afspraak.|Explain what happened and check a new arrangement.|بگو چه اتفاقی افتاده و هماهنگی تازه‌ای را بررسی کن.', [
    'Voor hun eerste huwelijksverjaardag heeft Farah een tafel gereserveerd.|Farah has booked a table for their first wedding anniversary.|فرح برای اولین سالگرد ازدواجشان میز رزرو کرده است.',
    'Haar man Benoit komt na zijn werk naar het restaurant.|Her husband Benoit comes to the restaurant after work.|همسرش بنوا بعد از کار به رستوران می‌آید.',
    'Hij zet zijn telefoon bij het begin van de maaltijd op stil.|He silences his phone at the start of the meal.|در شروع غذا تلفنش را روی حالت بی‌صدا می‌گذارد.',
    'Even later licht het scherm toch op.|A moment later the screen lights up nevertheless.|کمی بعد بااین‌حال صفحه روشن می‌شود.',
    'Farah vraagt of zijn werk weer belangrijker is.|Farah asks whether his work is more important again.|فرح می‌پرسد آیا باز هم کارش مهم‌تر است.',
    'Benoit laat haar het bericht zien.|Benoit shows her the message.|بنوا پیام را به او نشان می‌دهد.',
    'Het is een foto van de cake die hun dochter met haar oma heeft gebakken.|It is a photo of the cake their daughter has baked with her grandmother.|عکس کیکی است که دخترشان با مادربزرگش پخته است.',
    'Farah lacht en vraagt hem om één kort antwoord te sturen.|Farah laughs and asks him to send one short reply.|فرح می‌خندد و از او می‌خواهد یک جواب کوتاه بفرستد.',
    'Daarna stoppen ze hun telefoons in haar tas.|Then they put their phones in her bag.|بعد تلفن‌هایشان را در کیف او می‌گذارند.',
    'Thuis wacht geen groot cadeau, maar een scheve cake met een kaars.|No large present awaits them at home, but a lopsided cake with a candle does.|در خانه هدیه‌ای بزرگ منتظرشان نیست، بلکه کیکی کج با یک شمع است.'
], 'Dag Farah, met mama. We zouden jullie dochter vanavond thuisbrengen, maar ze blijft graag bij ons slapen. We brengen haar morgen om tien uur in de voormiddag thuis. Jullie hoeven haar dus vanavond niet op te halen.|Hi Farah, Mum here. We were going to bring your daughter home tonight, but she would like to sleep at our place. We will bring her home tomorrow at ten in the morning. So you do not need to collect her tonight.|سلام فرح، مامان هستم. قرار بود دخترتان را امشب به خانه بیاوریم، اما دوست دارد پیش ما بخوابد. فردا ساعت ده صبح او را به خانه می‌آوریم. پس لازم نیست امشب دنبالش بیایید.', [
    ('Waarom licht de telefoon op?|Why does the phone light up?|چرا صفحهٔ تلفن روشن می‌شود؟', 'Er komt een foto van de cake.|A photo of the cake arrives.|عکس کیک می‌رسد.', 'Benoits werk belt.|Benoit’s workplace is calling.|از محل کار بنوا زنگ می‌زنند.', 'Benoit laat een foto zien van wat hun dochter heeft gebakken.|Benoit shows a photo of what their daughter has baked.|بنوا عکسی از چیزی نشان می‌دهد که دخترشان پخته است.'),
    ('Wat doen ze na het korte antwoord?|What do they do after the short reply?|بعد از جواب کوتاه چه کار می‌کنند؟', 'Ze stoppen hun telefoons in de tas.|They put their phones in the bag.|تلفن‌ها را در کیف می‌گذارند.', 'Ze gaan onmiddellijk naar hun werk.|They go straight to work.|فوراً به محل کارشان می‌روند.', 'Ze kiezen ervoor om de telefoons daarna weg te stoppen.|They choose to put the phones away afterwards.|انتخاب می‌کنند بعد از آن تلفن‌ها را کنار بگذارند.')
], [
    ('Wanneer komt hun dochter thuis?|When does their daughter come home?|دخترشان چه زمانی به خانه می‌آید؟', 'Morgen om tien uur in de voormiddag.|Tomorrow at ten in the morning.|فردا ساعت ده صبح.', 'Vanavond om tien uur.|Tonight at ten.|امشب ساعت ده.', 'De grootmoeder verandert het plan naar morgenochtend.|The grandmother changes the plan to tomorrow morning.|مادربزرگ برنامه را به فردا صبح تغییر می‌دهد.'),
    ('Moeten de ouders haar vanavond ophalen?|Do the parents need to collect her tonight?|آیا پدر و مادر باید امشب دنبالش بروند؟', 'Nee, ze blijft bij haar grootouders slapen.|No, she is sleeping at her grandparents’ home.|نه، پیش پدربزرگ و مادربزرگش می‌خوابد.', 'Ja, na het eten.|Yes, after dinner.|بله، بعد از شام.', 'Het bericht zegt uitdrukkelijk dat ophalen vanavond niet nodig is.|The message explicitly says collection tonight is unnecessary.|پیام صریحاً می‌گوید امشب نیازی به دنبال او رفتن نیست.')
], 'Bel de grootmoeder terug. Bedank haar en controleer de nieuwe afspraak. Zeg dat jullie vanavond niet komen.|Call the grandmother back. Thank her and check the new arrangement. Say that you will not come tonight.|به مادربزرگ زنگ بزن. تشکر کن و هماهنگی تازه را بررسی کن. بگو امشب نمی‌آیید.',
     'Dank je, mama. Ze blijft dus vannacht bij jullie en je brengt haar morgen om tien uur thuis, klopt dat? Dan komen wij haar vanavond niet ophalen.|Thank you, Mum. So she is staying with you tonight and you will bring her home tomorrow at ten, is that right? Then we will not collect her tonight.|ممنون، مامان. پس امشب پیش شما می‌ماند و فردا ساعت ده او را به خانه می‌آوری، درست است؟ پس امشب دنبالش نمی‌آییم.',
     'Schrijf een kort antwoord op het luisterbericht. Bevestig waar je dochter slaapt en wanneer ze thuiskomt.|Write a short reply to the audio message. Confirm where your daughter is sleeping and when she comes home.|پاسخ کوتاهی به پیام شنیداری بنویس. تأیید کن دخترت کجا می‌خوابد و چه زمانی به خانه می‌آید.',
     'Dag mama, bedankt voor je bericht en voor de mooie cake. Het is goed dat ze bij jullie blijft slapen. We komen haar vanavond niet ophalen. Morgen om tien uur zijn we thuis. Tot morgen!|Hi Mum, thank you for your message and the lovely cake. It is fine for her to stay the night with you. We will not collect her tonight. We will be home tomorrow at ten. See you tomorrow!|سلام مامان، از پیامت و کیک قشنگ ممنونم. خوب است که امشب پیش شما می‌ماند. امشب دنبالش نمی‌آییم. فردا ساعت ده خانه هستیم. تا فردا!', (15, 65), [
    ('de kaars', 'Een voorwerp van was dat licht geeft als het brandt.|A wax object that gives light when it burns.|وسیله‌ای مومی که با سوختن نور می‌دهد؛ شمع.', 'Er staat een kaars op de cake.|There is a candle on the cake.|روی کیک یک شمع است.'),
    ('reserveren', 'Vooraf een plaats laten vrijhouden.|To arrange for a place to be kept for you in advance.|از قبل جایی را برای خود نگه داشتن؛ رزرو کردن.', 'Farah heeft een tafel gereserveerd.|Farah has booked a table.|فرح میزی رزرو کرده است.'),
    ('scheef', 'Niet recht.|Not straight or level.|کج؛ صاف و مستقیم نیست.', 'De cake is scheef.|The cake is lopsided.|کیک کج است.'),
    ('daarna', 'Na dat moment.|After that moment.|بعد از آن.', 'Daarna stoppen ze hun telefoons weg.|Afterwards they put their phones away.|بعد تلفن‌هایشان را کنار می‌گذارند.')
])

unit('pre-b1', 'sour-cherries', 'De zure kersen|The sour cherries|گیلاس‌های ترش',
     'Familie en verzoening|Family and reconciliation|خانواده و آشتی',
     'Vertel een herinnering en reageer met respect op een persoonlijke wens.|Tell a memory and respond respectfully to a personal wish.|خاطره‌ای تعریف کن و با احترام به خواستهٔ شخصی دیگری پاسخ بده.', [
    'Na een ruzie hadden Sona en haar zus drie jaar niet met elkaar gesproken.|After an argument, Sona and her sister had not spoken for three years.|سونا و خواهرش پس از دعوایی سه سال با هم حرف نزده بودند.',
    'Van hun moeder hoorde Sona dat haar zus naar Gent was verhuisd.|Sona heard from their mother that her sister had moved to Ghent.|سونا از مادرشان شنید خواهرش به خنت نقل مکان کرده است.',
    'Ze wilde schrijven, maar vond geen goede eerste zin.|She wanted to write, but could not find a good opening sentence.|می‌خواست نامه بنویسد، اما جملهٔ مناسبی برای شروع پیدا نمی‌کرد.',
    'Na drie pogingen lag haar tafel vol papier.|After three attempts her table was covered in paper.|بعد از سه تلاش، میزش پر از کاغذ شده بود.',
    'Toen vond ze een foto waarop ze samen onder een kersenboom zaten.|Then she found a photo of them sitting together under a cherry tree.|بعد عکسی پیدا کرد که در آن با هم زیر درخت گیلاس نشسته بودند.',
    'Op de achterkant schreef ze: Weet je nog hoe zuur de kersen waren?|On the back she wrote: Do you remember how sour the cherries were?|پشت عکس نوشت: یادت هست گیلاس‌ها چقدر ترش بودند؟',
    'Daaronder voegde ze toe: Het spijt me dat ik toen niet luisterde.|Below that she added: I am sorry I did not listen then.|زیر آن اضافه کرد: متأسفم که آن‌وقت به حرفت گوش نکردم.',
    'Een week later kwam er een kaart uit Gent.|A week later a card arrived from Ghent.|یک هفته بعد کارتی از خنت رسید.',
    'Haar zus schreef: De kersen waren zuur, maar we bleven lachen.|Her sister wrote: The cherries were sour, but we kept laughing.|خواهرش نوشته بود: گیلاس‌ها ترش بودند، اما ما همچنان می‌خندیدیم.',
    'Onderaan stond een telefoonnummer; nog die avond belde Sona om bij te praten.|There was a phone number at the bottom; Sona called that same evening to catch up.|پایین کارت شمارهٔ تلفنی بود؛ سونا همان شب زنگ زد تا از حال‌وروز هم باخبر شوند.'
], 'Dag Sona, ik vond ons gesprek fijn. Vrijdagavond kan ik niet opnieuw bellen. Kan het zondag om tien uur in de voormiddag? Ik wil eerst gewoon wat bijpraten. Over de ruzie praten we later, als we er allebei klaar voor zijn.|Hi Sona, I enjoyed our conversation. I cannot call again on Friday evening. Could we call on Sunday at ten in the morning? I would first like to catch up a little. We can talk about the argument later, when we are both ready.|سلام سونا، از گفت‌وگویمان خوشحال شدم. جمعه‌شب نمی‌توانم دوباره تلفنی حرف بزنم. یکشنبه ساعت ده صبح می‌شود؟ اول دوست دارم فقط کمی از حال‌وروز هم باخبر شویم. دربارهٔ دعوا بعداً حرف می‌زنیم، وقتی هر دو آماده باشیم.', [
    ('Wat helpt Sona om te beginnen schrijven?|What helps Sona start writing?|چه چیزی به سونا کمک می‌کند نوشتن را شروع کند؟', 'Een foto van een gedeelde herinnering.|A photo of a shared memory.|عکسی از یک خاطرهٔ مشترک.', 'Een officieel formulier.|An official form.|فرمی رسمی.', 'De foto onder de kersenboom geeft haar een eerste zin.|The photo under the cherry tree gives her an opening sentence.|عکس زیر درخت گیلاس جملهٔ شروع را به ذهنش می‌آورد.'),
    ('Waarom is het antwoord meer dan alleen een herinnering aan fruit?|Why is the reply more than just a memory about fruit?|چرا پاسخ فقط خاطره‌ای دربارهٔ میوه نیست؟', 'Haar zus deelt de herinnering en geeft een telefoonnummer.|Her sister shares the memory and gives a phone number.|خواهرش در خاطره شریک می‌شود و شمارهٔ تلفن می‌دهد.', 'Haar zus vraagt om kersen te kopen.|Her sister asks her to buy cherries.|خواهرش می‌خواهد گیلاس بخرد.', 'De gedeelde herinnering en het nummer openen opnieuw contact.|The shared memory and the number reopen contact.|خاطرهٔ مشترک و شمارهٔ تلفن راه ارتباط دوباره را باز می‌کنند.')
], [
    ('Wanneer stelt haar zus het volgende gesprek voor?|When does her sister propose the next conversation?|خواهرش چه زمانی را برای گفت‌وگوی بعدی پیشنهاد می‌کند؟', 'Zondag om tien uur in de voormiddag.|Sunday at ten in the morning.|یکشنبه ساعت ده صبح.', 'Vrijdag om tien uur in de avond.|Friday at ten in the evening.|جمعه ساعت ده شب.', 'Vrijdag kan niet; het voorstel is zondagvoormiddag.|Friday is not possible; the proposal is Sunday morning.|جمعه نمی‌شود؛ پیشنهاد برای یکشنبه صبح است.'),
    ('Wat wil haar zus eerst bespreken?|What does her sister want to discuss first?|خواهرش ابتدا می‌خواهد دربارهٔ چه چیزی صحبت کند؟', 'Hoe het nu met hen gaat.|How they are doing now.|اینکه این روزها حال‌وروزشان چطور است.', 'Alle details van de oude ruzie.|Every detail of the old argument.|همهٔ جزئیات دعوای قدیمی.', 'Ze wil eerst bijpraten en de ruzie pas later bespreken.|She wants to catch up first and discuss the argument later.|می‌خواهد اول از حال‌وروز هم باخبر شوند و بعداً دربارهٔ دعوا حرف بزنند.')
], 'Reageer op je zus. Bevestig het voorgestelde moment, respecteer haar wens en stel een eenvoudige vraag over haar nieuwe leven.|Respond to your sister. Confirm the proposed time, respect her wish and ask a simple question about her new life.|به خواهرت پاسخ بده. زمان پیشنهادی را تأیید کن، به خواسته‌اش احترام بگذار و سؤال ساده‌ای دربارهٔ زندگی تازه‌اش بپرس.',
     'Zondag om tien uur past voor mij. We hoeven de ruzie niet meteen te bespreken. Ik wil ook graag rustig bijpraten. Hoe bevalt je nieuwe woning in Gent? Heb je al een fijne plek in de buurt ontdekt?|Sunday at ten works for me. We do not need to discuss the argument straight away. I would like to catch up calmly too. How do you like your new home in Ghent? Have you already discovered a nice place nearby?|یکشنبه ساعت ده برای من مناسب است. لازم نیست فوراً دربارهٔ دعوا حرف بزنیم. من هم دوست دارم با آرامش از حال‌وروز هم باخبر شویم. خانهٔ تازه‌ات در خنت چطور است؟ جای خوبی در اطراف پیدا کرده‌ای؟',
     'Schrijf je zus een antwoord. Bevestig de tijd, leg uit dat je haar niet onder druk wilt zetten en vraag iets over Gent.|Write your sister a reply. Confirm the time, explain that you do not want to pressure her and ask something about Ghent.|برای خواهرت پاسخ بنویس. زمان را تأیید کن، توضیح بده نمی‌خواهی به او فشار بیاوری و چیزی دربارهٔ خنت بپرس.',
     'Dag zus, zondag om tien uur in de voormiddag past goed. Ik vond ons eerste gesprek ook fijn. We hoeven niet alles tegelijk op te lossen en ik wil je niet onder druk zetten. Vertel me zondag gerust over je nieuwe buurt. Wat vind je tot nu toe het fijnst aan Gent? Tot zondag, Sona.|Dear sister, Sunday at ten in the morning works well. I enjoyed our first conversation too. We do not need to solve everything at once and I do not want to pressure you. Please tell me about your new neighbourhood on Sunday. What have you liked most about Ghent so far? See you on Sunday, Sona.|خواهر عزیزم، یکشنبه ساعت ده صبح خوب است. من هم از اولین گفت‌وگویمان خوشحال شدم. لازم نیست همه‌چیز را یک‌باره حل کنیم و نمی‌خواهم به تو فشار بیاورم. یکشنبه از محلهٔ تازه‌ات برایم بگو. تا حالا چه چیزی را در خنت بیشتر از همه دوست داشته‌ای؟ تا یکشنبه، سونا.', (25, 90), [
    ('de ruzie', 'Een onvriendelijk meningsverschil tussen mensen.|An unfriendly disagreement between people.|اختلاف و مشاجره میان افراد؛ دعوا.', 'Na de ruzie spraken ze niet meer.|They stopped speaking after the argument.|بعد از دعوا دیگر با هم حرف نمی‌زدند.'),
    ('bijpraten', 'Elkaar vertellen wat er de laatste tijd is gebeurd.|To catch up on what has happened recently.|از اتفاق‌های اخیر و حال‌وروز هم باخبر شدن.', 'Zondag praten de zussen bij.|The sisters catch up on Sunday.|خواهرها یکشنبه از حال‌وروز هم باخبر می‌شوند.'),
    ('zuur', 'Met een smaak zoals die van een citroen.|With a taste like a lemon.|دارای مزه‌ای شبیه لیمو؛ ترش.', 'De kersen waren zuur.|The cherries were sour.|گیلاس‌ها ترش بودند.'),
    ('onderaan', 'Aan de onderkant.|At the bottom.|در پایین.', 'Onderaan staat haar telefoonnummer.|Her phone number is at the bottom.|شمارهٔ تلفنش پایین نوشته شده است.')
])

unit('b1', 'portrait-scar', 'Het litteken op de foto|The scar in the photograph|جای زخم در عکس',
     'Een persoonlijk verhaal|A personal story|روایتی شخصی',
     'Leg een persoonlijke voorkeur uit en maak een duidelijke afspraak over een dienst.|Explain a personal preference and make a clear arrangement for a service.|ترجیح شخصی‌ات را توضیح بده و دربارهٔ یک خدمت روشن هماهنگ کن.', [
    'Voor haar zestigste verjaardag liet Lieve een portret maken.|Lieve had a portrait taken for her sixtieth birthday.|لیفه برای شصتمین سالگرد تولدش عکس پرتره گرفت.',
    'De fotograaf stuurde eerst een sterk bewerkte versie.|The photographer first sent a heavily edited version.|عکاس ابتدا نسخه‌ای بسیار ویرایش‌شده فرستاد.',
    'Haar huid was glad, maar ze herkende haar eigen glimlach nauwelijks.|Her skin was smooth, but she could barely recognise her own smile.|پوستش صاف بود، اما به‌سختی لبخند خودش را می‌شناخت.',
    'Haar dochter vond de foto mooi en begreep haar teleurstelling niet.|Her daughter thought the photo was beautiful and did not understand her disappointment.|دخترش عکس را زیبا می‌دانست و ناراحتی او را نمی‌فهمید.',
    'Lieve legde uit dat het kleine litteken bij haar mond bij haar hoorde.|Lieve explained that the small scar beside her mouth was part of who she was.|لیفه توضیح داد جای زخم کوچک کنار دهانش بخشی از وجود اوست.',
    'Ze had het gekregen tijdens de fietstocht waarop ze haar partner ontmoette.|She had got it during the bicycle ride on which she met her partner.|در همان دوچرخه‌سواری‌ای آن زخم را برداشته بود که با شریک زندگی‌اش آشنا شد.',
    'De fotograaf gaf toe dat hij zonder overleg te veel had veranderd.|The photographer admitted that he had changed too much without consulting her.|عکاس پذیرفت بدون مشورت بیش از حد تغییر ایجاد کرده است.',
    'Hij stuurde de oorspronkelijke foto en vroeg welke aanpassingen zij zelf wilde.|He sent the original photo and asked which changes she herself wanted.|عکس اصلی را فرستاد و پرسید خود او چه تغییرهایی می‌خواهد.',
    'Lieve koos alleen een lichtere achtergrond.|Lieve chose only a lighter background.|لیفه فقط پس‌زمینه‌ای روشن‌تر انتخاب کرد.',
    'Op het feest vertelde ze het verhaal van het litteken bij haar portret.|At the party she told the story of the scar beside her portrait.|در مهمانی کنار پرتره‌اش داستان جای زخم را تعریف کرد.'
], 'Dag Lieve, ik kan de achtergrond lichter maken zonder uw gezicht te veranderen. Een afdruk op A4 kost twintig euro, maar op A3 vijfendertig euro. Ik druk nog niets af voordat u het formaat bevestigt.|Hello, Lieve, I can lighten the background without changing your face. An A4 print costs twenty euros, while A3 costs thirty-five euros. I will not print anything until you confirm the size.|سلام لیفه، می‌توانم بدون تغییر چهره‌تان پس‌زمینه را روشن‌تر کنم. چاپ اندازهٔ A4 بیست یورو و اندازهٔ A3 سی‌وپنج یورو هزینه دارد. تا اندازه را تأیید نکنید چیزی چاپ نمی‌کنم.', [
    ('Waarom is Lieve niet tevreden met de eerste versie?|Why is Lieve dissatisfied with the first version?|چرا لیفه از نسخهٔ اول راضی نیست؟', 'Een persoonlijk kenmerk is te veel veranderd.|A personal feature has been changed too much.|ویژگی شخصی‌اش بیش از حد تغییر کرده است.', 'De foto toont een andere persoon naast haar.|The photo shows another person beside her.|عکس شخص دیگری را کنار او نشان می‌دهد.', 'Het litteken is voor haar verbonden met een belangrijke herinnering.|For her, the scar is linked to an important memory.|جای زخم برای او با خاطره‌ای مهم پیوند دارد.'),
    ('Wat kiest Lieve uiteindelijk?|What does Lieve ultimately choose?|لیفه در پایان چه چیزی انتخاب می‌کند؟', 'Alleen een lichtere achtergrond.|Only a lighter background.|فقط پس‌زمینه‌ای روشن‌تر.', 'Een volledig glad gezicht.|A completely smooth face.|چهره‌ای کاملاً صاف.', 'Ze wil haar gezicht behouden en alleen de achtergrond veranderen.|She wants to keep her face as it is and change only the background.|می‌خواهد چهره‌اش همان‌طور بماند و فقط پس‌زمینه تغییر کند.')
], [
    ('Welke afdruk kost twintig euro?|Which print costs twenty euros?|کدام اندازهٔ چاپ بیست یورو هزینه دارد؟', 'A4.|A4.|A4.', 'A3.|A3.|A3.', 'Het bericht noemt twintig euro voor A4 en vijfendertig voor A3.|The message quotes twenty euros for A4 and thirty-five for A3.|پیام برای A4 بیست یورو و برای A3 سی‌وپنج یورو می‌گوید.'),
    ('Wat moet gebeuren voordat de fotograaf afdrukt?|What must happen before the photographer prints?|پیش از چاپ عکاس چه اتفاقی باید بیفتد؟', 'Lieve moet het formaat bevestigen.|Lieve must confirm the size.|لیفه باید اندازه را تأیید کند.', 'Haar dochter moet een nieuwe foto maken.|Her daughter must take a new photograph.|دخترش باید عکس تازه‌ای بگیرد.', 'De fotograaf wacht op toestemming voor het formaat.|The photographer is waiting for approval of the size.|عکاس منتظر تأیید اندازه است.')
], 'Je hebt maximaal vijfentwintig euro. Kies een passend formaat uit het luisterbericht. Leg uit welke verandering je wilt en geef duidelijk toestemming voor de afdruk.|You have a maximum of twenty-five euros. Choose a suitable size from the audio message. Explain which change you want and clearly authorise printing.|حداکثر بیست‌وپنج یورو داری. از پیام شنیداری اندازهٔ مناسبی انتخاب کن. تغییر دلخواهت را توضیح بده و روشن اجازهٔ چاپ بده.',
     'Ik kies A4 voor twintig euro, want mijn budget is vijfentwintig euro. U mag de achtergrond lichter maken, maar laat mijn gezicht alstublieft zoals het op de oorspronkelijke foto staat. Het litteken hoort bij mij. Als u alleen die achtergrond aanpast, mag u één afdruk op A4 maken.|I choose A4 at twenty euros because my budget is twenty-five euros. You may lighten the background, but please leave my face as it appears in the original photo. The scar is part of me. If you change only the background, you may make one A4 print.|A4 بیست‌یورویی را انتخاب می‌کنم، چون بودجه‌ام بیست‌وپنج یوروست. می‌توانید پس‌زمینه را روشن‌تر کنید، اما لطفاً چهره‌ام را همان‌طور که در عکس اصلی است نگه دارید. جای زخم بخشی از من است. اگر فقط پس‌زمینه را تغییر دهید، می‌توانید یک چاپ A4 تهیه کنید.',
     'Schrijf een bericht aan de fotograaf. Kies binnen een budget van vijfentwintig euro, bevestig de prijs en leg vast wat wel en niet aangepast mag worden.|Write a message to the photographer. Choose within a twenty-five-euro budget, confirm the price and specify what may and may not be changed.|برای عکاس پیام بنویس. با بودجهٔ بیست‌وپنج یورو انتخاب کن، قیمت را تأیید کن و روشن کن چه چیزهایی اجازه دارند یا ندارند تغییر کنند.',
     'Beste fotograaf, bedankt dat u de oorspronkelijke foto hebt doorgestuurd. Ik kies één afdruk op A4 voor twintig euro. Dat past binnen mijn budget van vijfentwintig euro. U mag de achtergrond wat lichter maken. Mijn gezicht en het litteken wil ik graag behouden, omdat ze bij mijn verhaal horen. Andere veranderingen zijn niet nodig. Als u alleen de achtergrond aanpast, geef ik toestemming voor die afdruk. Laat u weten wanneer ik de foto kan ophalen? Met vriendelijke groeten, Lieve.|Dear photographer, thank you for sending the original photo. I choose one A4 print at twenty euros. That fits within my budget of twenty-five euros. You may make the background a little lighter. I would like to keep my face and the scar as they are because they belong to my story. No other changes are needed. If you change only the background, I authorise that print. Please let me know when I can collect the photo. Kind regards, Lieve.|عکاس گرامی، ممنون که عکس اصلی را فرستادید. یک چاپ A4 به قیمت بیست یورو انتخاب می‌کنم. این مبلغ در بودجهٔ بیست‌وپنج یورویی من می‌گنجد. می‌توانید پس‌زمینه را کمی روشن‌تر کنید. می‌خواهم چهره و جای زخم همان‌طور بمانند، چون بخشی از داستان من هستند. تغییر دیگری لازم نیست. اگر فقط پس‌زمینه را تغییر دهید، اجازهٔ همین چاپ را می‌دهم. لطفاً خبر بدهید چه زمانی می‌توانم عکس را تحویل بگیرم. با احترام، لیفه.', (30, 100), [
    ('het litteken', 'Een blijvende plek op de huid na een wond.|A lasting mark on the skin after an injury.|اثری ماندگار روی پوست پس از زخم؛ جای زخم.', 'Het litteken herinnert Lieve aan een fietstocht.|The scar reminds Lieve of a bicycle ride.|جای زخم لیفه را به یاد دوچرخه‌سواری می‌اندازد.'),
    ('bewerken', 'Een tekst, beeld of ander materiaal aanpassen.|To edit a text, image or other material.|متن، تصویر یا مواد دیگر را ویرایش کردن.', 'De fotograaf heeft de foto te sterk bewerkt.|The photographer has edited the photo too heavily.|عکاس عکس را بیش از حد ویرایش کرده است.'),
    ('oorspronkelijk', 'Zoals iets eerst was, vóór veranderingen.|As something was initially, before changes.|به شکل اولیه، پیش از تغییرها؛ اصلی.', 'Lieve vraagt naar de oorspronkelijke foto.|Lieve asks for the original photo.|لیفه عکس اصلی را می‌خواهد.'),
    ('nauwelijks', 'Bijna niet.|Hardly or barely.|به‌سختی؛ تقریباً نه.', 'Ze herkent haar glimlach nauwelijks.|She can barely recognise her smile.|به‌سختی لبخند خودش را می‌شناسد.')
])


# Separate observable requirements keep feedback tied to the requested output.
TASK_CRITERIA = {
    'red-scarf': {
        'speaking': [
            'Geef de sjaal terug aan Noor met een begrijpelijke korte zin.|Return the scarf to Noor with an understandable short phrase.|با جمله‌ای کوتاه و قابل‌فهم شال را به نور برگردان.',
            'Noem groen als kleur van Noors sjaal.|Give green as the colour of Noor’s scarf.|رنگ شال نور را سبز بیان کن.'
        ],
        'writing': [
            'Schrijf de naam Noor uit het luisterbericht.|Write the name Noor from the audio message.|نام نور را از پیام شنیداری بنویس.',
            'Schrijf dat de sjaal groen is.|Write that the scarf is green.|بنویس شال سبز است.'
        ]
    },
    'first-dance': {
        'speaking': [
            'Nodig de andere deelnemer uit om samen te dansen.|Invite the other participant to dance with you.|شرکت‌کنندهٔ دیگر را به رقص با خودت دعوت کن.',
            'Noem vrijdag om zeven uur in de avond als moment van de volgende les.|Give Friday at seven in the evening as the time of the next lesson.|زمان کلاس بعدی را جمعه ساعت هفت عصر بیان کن.'
        ],
        'writing': [
            'Bevestig vrijdag om zeven uur in de avond als lesmoment.|Confirm Friday at seven in the evening as the lesson time.|جمعه ساعت هفت عصر را به‌عنوان زمان کلاس تأیید کن.',
            'Zeg dat je water meebrengt.|Say that you will bring water.|بگو آب همراهت می‌آوری.'
        ]
    },
    'silent-waiter': {
        'speaking': [
            'Bestel als klant één koffie met een beleefde korte zin.|Order one coffee as the customer using a polite short phrase.|در نقش مشتری با جمله‌ای کوتاه و مؤدبانه یک قهوه سفارش بده.',
            'Vraag toestemming om de zin twee keer te oefenen.|Ask permission to practise the line twice.|اجازه بخواه جمله را دو بار تمرین کنی.'
        ],
        'writing': [
            'Leg uit dat Adam na de pauze de klant speelt.|Explain that Adam plays the customer after the break.|توضیح بده آدم بعد از استراحت نقش مشتری را بازی می‌کند.',
            'Vermeld dat de scène twee keer wordt geoefend.|Mention that the scene is practised twice.|بیان کن صحنه دو بار تمرین می‌شود.'
        ]
    },
    'anniversary-cake': {
        'speaking': [
            'Controleer dat je dochter bij haar grootouders slaapt en morgen om tien uur in de voormiddag thuiskomt.|Check that your daughter sleeps at her grandparents’ home and returns tomorrow at ten in the morning.|بررسی کن دخترت پیش پدربزرگ و مادربزرگش می‌خوابد و فردا ساعت ده صبح برمی‌گردد.',
            'Bedank de grootmoeder en zeg dat jullie je dochter vanavond niet ophalen.|Thank the grandmother and say that you will not collect your daughter tonight.|از مادربزرگ تشکر کن و بگو امشب دنبال دخترت نمی‌روید.'
        ],
        'writing': [
            'Bevestig dat je dochter bij haar grootouders blijft slapen.|Confirm that your daughter stays overnight at her grandparents’ home.|تأیید کن دخترت شب را پیش پدربزرگ و مادربزرگش می‌ماند.',
            'Bevestig morgen om tien uur in de voormiddag als thuiskomst en zeg dat ophalen vanavond niet nodig is.|Confirm tomorrow at ten in the morning as the return time and say that collection tonight is unnecessary.|فردا ساعت ده صبح را برای بازگشت تأیید کن و بگو امشب نیازی به دنبال او رفتن نیست.'
        ]
    },
    'sour-cherries': {
        'speaking': [
            'Bevestig zondag om tien uur in de voormiddag voor het telefoongesprek.|Confirm Sunday at ten in the morning for the telephone conversation.|یکشنبه ساعت ده صبح را برای گفت‌وگوی تلفنی تأیید کن.',
            'Respecteer dat de ruzie later besproken wordt en vraag eerst iets over haar nieuwe leven.|Respect that the argument will be discussed later and first ask something about her new life.|به صحبت دربارهٔ دعوا در زمانی دیگر احترام بگذار و ابتدا دربارهٔ زندگی تازه‌اش چیزی بپرس.'
        ],
        'writing': [
            'Bevestig zondag om tien uur in de voormiddag.|Confirm Sunday at ten in the morning.|یکشنبه ساعت ده صبح را تأیید کن.',
            'Zeg dat je geen druk wilt zetten en stel een vraag over Gent of haar nieuwe buurt.|Say that you do not want to pressure her and ask a question about Ghent or her new neighbourhood.|بگو نمی‌خواهی به او فشار بیاوری و دربارهٔ خنت یا محلهٔ تازه‌اش سؤالی بپرس.'
        ]
    },
    'portrait-scar': {
        'speaking': [
            'Kies A4 voor twintig euro en blijf binnen het budget van vijfentwintig euro.|Choose A4 at twenty euros and stay within the twenty-five-euro budget.|A4 بیست‌یورویی را انتخاب کن و از بودجهٔ بیست‌وپنج یورو بیشتر خرج نکن.',
            'Geef toestemming voor de afdruk met alleen een lichtere achtergrond en behoud het gezicht en litteken.|Authorise printing with only a lighter background while keeping the face and scar unchanged.|اجازهٔ چاپ با تنها تغییرِ روشن‌تر شدن پس‌زمینه را بده و چهره و جای زخم را بدون تغییر نگه دار.'
        ],
        'writing': [
            'Bevestig één afdruk op A4 voor twintig euro binnen het budget.|Confirm one A4 print at twenty euros within the budget.|یک چاپ A4 به قیمت بیست یورو را در محدودهٔ بودجه تأیید کن.',
            'Leg vast dat alleen de achtergrond lichter mag worden en geef onder die voorwaarde toestemming voor de afdruk.|Specify that only the background may be lightened and authorise printing on that condition.|مشخص کن فقط پس‌زمینه اجازه دارد روشن‌تر شود و به این شرط اجازهٔ چاپ بده.'
        ]
    }
}

for _unit in UNITS:
    _unit['speaking_criteria'] = TASK_CRITERIA[_unit['id']]['speaking']
    _unit['writing_criteria'] = TASK_CRITERIA[_unit['id']]['writing']
    _unit['word_classes'] = ['noun', 'verb', 'adjective', 'adverb']
