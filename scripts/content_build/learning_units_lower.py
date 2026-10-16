"""Original short narrative units; translations and level placement await language review."""

UNITS = []


def unit(stage, slug, title, focus, lines, listening, reading_q, listening_q,
         speaking, spoken_sample, writing, written_sample, bounds, words):
    UNITS.append({"stage": stage, "id": slug, "title": title, "focus": focus,
                      "genre": "Een klein verhaal|A little story|یک داستان کوتاه", "lines": lines,
                      "listening": listening, "reading_q": reading_q, "listening_q": listening_q,
                      "speaking": speaking, "spoken_sample": spoken_sample, "writing": writing,
                      "written_sample": written_sample, "speaking_bounds": bounds,
                      "writing_bounds": bounds, "criteria": [focus], "words": words})


unit('pre-a1', 'blue-envelope', 'De blauwe envelop|The blue envelope|پاکت آبی',
     'Herken een naam en een kleur. Zeg voor wie iets is.|Recognise a name and a colour. Say who something is for.|یک نام و یک رنگ را تشخیص بده. بگو چیزی برای چه کسی است.', [
    'Dit is Noor.|This is Noor.|این نور است.',
    'Noor heeft een envelop.|Noor has an envelope.|نور یک پاکت دارد.',
    'De envelop is blauw.|The envelope is blue.|پاکت آبی است.',
    'Op de envelop staat Sara.|The envelope says Sara.|روی پاکت نوشته شده سارا.',
    'Daar is Sara.|There is Sara.|سارا آنجاست.',
    'Noor zegt: Dag Sara!|Noor says: Hello, Sara!|نور می‌گوید: سلام سارا!',
    'Sara kijkt naar de envelop.|Sara looks at the envelope.|سارا به پاکت نگاه می‌کند.',
    'Noor zegt: Voor jou.|Noor says: For you.|نور می‌گوید: برای تو.',
    'Sara opent de envelop.|Sara opens the envelope.|سارا پاکت را باز می‌کند.',
    'Een hartje! Sara lacht.|A little heart! Sara smiles.|یک قلب کوچک! سارا لبخند می‌زند.'
], 'Ik ben Sam. Mijn envelop is geel. Hij is voor Noor.|I am Sam. My envelope is yellow. It is for Noor.|من سام هستم. پاکت من زرد است. برای نور است.', [
    ('Voor wie is de blauwe envelop?|Who is the blue envelope for?|پاکت آبی برای چه کسی است؟', 'Voor Sara.|For Sara.|برای سارا.', 'Voor Sam.|For Sam.|برای سام.', 'Sara staat op de envelop.|Sara is written on the envelope.|روی پاکت نوشته شده سارا.'),
    ('Wat zit in de envelop?|What is inside the envelope?|داخل پاکت چیست؟', 'Een hartje.|A little heart.|یک قلب کوچک.', 'Een sleutel.|A key.|یک کلید.', 'Sara ziet een hartje.|Sara sees a little heart.|سارا یک قلب کوچک می‌بیند.')
], [
    ('Wie spreekt?|Who is speaking?|چه کسی صحبت می‌کند؟', 'Sam.|Sam.|سام.', 'Sara.|Sara.|سارا.', 'De spreker zegt: Ik ben Sam.|The speaker says: I am Sam.|گوینده می‌گوید: من سام هستم.'),
    ('Welke kleur heeft Sams envelop?|What colour is Sam’s envelope?|پاکت سام چه رنگی است؟', 'Geel.|Yellow.|زرد.', 'Blauw.|Blue.|آبی.', 'Sam zegt dat zijn envelop geel is.|Sam says his envelope is yellow.|سام می‌گوید پاکتش زرد است.')
], 'Geef een envelop aan Noor. Zeg: voor jou.|Give an envelope to Noor. Say: for you.|پاکتی به نور بده. بگو: برای تو.',
     'Dag Noor! Voor jou.|Hello, Noor! For you.|سلام نور! برای تو.',
     'Schrijf je naam en de kleur van je envelop.|Write your name and your envelope’s colour.|نام خودت و رنگ پاکتت را بنویس.',
     'Ik ben Sam. Mijn envelop is geel.|I am Sam. My envelope is yellow.|من سام هستم. پاکت من زرد است.', (2, 15), [
    ('de envelop', 'Een papieren omslag voor een brief.|A paper cover for a letter.|پوششی کاغذی برای نامه.', 'De envelop is blauw.|The envelope is blue.|پاکت آبی است.'),
    ('openen', 'Iets openmaken.|To open something.|باز کردن چیزی.', 'Sara opent de envelop.|Sara opens the envelope.|سارا پاکت را باز می‌کند.'),
    ('blauw', 'Een kleur.|A colour.|یک رنگ.', 'Mijn envelop is blauw.|My envelope is blue.|پاکت من آبی است.'),
    ('daar', 'Op die plaats.|In that place.|در آنجا.', 'Daar is Sara.|There is Sara.|سارا آنجاست.')
])

unit('a1', 'window-plant', 'Een plant aan het raam|A plant at the window|گیاهی کنار پنجره',
     'Beschrijf een plaats en bied eenvoudige hulp aan.|Describe a place and offer simple help.|یک مکان را توصیف کن و کمکی ساده پیشنهاد بده.', [
    'Mina woont naast Jonas.|Mina lives next door to Jonas.|مینا همسایهٔ یوناس است.',
    'Elke ochtend ziet ze zijn lege raam.|Every morning she sees his empty window.|هر صبح پنجرهٔ خالی او را می‌بیند.',
    'Vandaag koopt ze een kleine plant.|Today she buys a small plant.|امروز گیاه کوچکی می‌خرد.',
    'Ze zet de plant voor zijn deur.|She puts the plant outside his door.|گیاه را جلوی در او می‌گذارد.',
    'Op een kaart schrijft ze: Voor je raam.|On a card she writes: For your window.|روی کارتی می‌نویسد: برای پنجره‌ات.',
    'Jonas vindt de plant na zijn werk.|Jonas finds the plant after work.|یوناس بعد از کار گیاه را پیدا می‌کند.',
    'Hij leest de kaart en belt bij Mina aan.|He reads the card and rings Mina’s doorbell.|کارت را می‌خواند و زنگ در مینا را می‌زند.',
    'Hij vraagt: Waar staat een plant het best?|He asks: Where is the best place for a plant?|می‌پرسد: بهترین جا برای گیاه کجاست؟',
    'Mina wijst naar de lichte vensterbank.|Mina points to the bright windowsill.|مینا به لبهٔ روشن پنجره اشاره می‌کند.',
    'Nu drinken ze aan de tafel samen thee.|Now they drink tea together at the table.|حالا پشت میز با هم چای می‌نوشند.'
], 'Dag Mina, met Jonas. De plant staat nu op mijn tafel. Het raam is dicht. Kom je om drie uur thee drinken?|Hello, Mina, Jonas here. The plant is on my table now. The window is closed. Will you come for tea at three?|سلام مینا، یوناس هستم. گیاه حالا روی میز من است. پنجره بسته است. ساعت سه برای نوشیدن چای می‌آیی؟', [
    ('Waarom geeft Mina de plant?|Why does Mina give the plant?|چرا مینا گیاه را هدیه می‌دهد؟', 'Voor het lege raam van Jonas.|For Jonas’s empty window.|برای پنجرهٔ خالی یوناس.', 'Voor haar werk.|For her work.|برای کار خودش.', 'Op de kaart staat: Voor je raam.|The card says: For your window.|روی کارت نوشته شده: برای پنجره‌ات.'),
    ('Waar wijst Mina naar?|What does Mina point to?|مینا به کجا اشاره می‌کند؟', 'De vensterbank.|The windowsill.|لبهٔ پنجره.', 'De straat.|The street.|خیابان.', 'Ze wijst naar de lichte vensterbank.|She points to the bright windowsill.|به لبهٔ روشن پنجره اشاره می‌کند.')
], [
    ('Waar staat de plant nu?|Where is the plant now?|گیاه حالا کجاست؟', 'Op de tafel.|On the table.|روی میز.', 'Voor de deur.|Outside the door.|جلوی در.', 'Jonas noemt zijn tafel.|Jonas mentions his table.|یوناس از میز خود می‌گوید.'),
    ('Hoe laat is Mina welkom?|What time is Mina invited for?|مینا چه ساعتی دعوت شده است؟', 'Om drie uur.|At three.|ساعت سه.', 'Om twee uur.|At two.|ساعت دو.', 'Jonas vraagt haar om drie uur te komen.|Jonas asks her to come at three.|یوناس می‌خواهد او ساعت سه بیاید.')
], 'Je buur krijgt een plant. Zeg waar de plant kan staan en nodig je buur uit voor thee.|Your neighbour receives a plant. Say where it can go and invite your neighbour for tea.|همسایه‌ات گیاهی هدیه می‌گیرد. بگو آن را کجا بگذارد و همسایه‌ات را به چای دعوت کن.',
     'De plant kan op de tafel staan. Kom je om drie uur thee drinken?|The plant can go on the table. Will you come for tea at three?|گیاه می‌تواند روی میز باشد. ساعت سه برای چای می‌آیی؟',
     'Antwoord op Jonas. Zeg of je om drie uur kunt komen.|Reply to Jonas. Say whether you can come at three.|به یوناس پاسخ بده. بگو آیا می‌توانی ساعت سه بیایی.',
     'Dag Jonas, dank je. Ik kan om drie uur komen. Tot straks!|Hello, Jonas, thank you. I can come at three. See you soon!|سلام یوناس، ممنون. می‌توانم ساعت سه بیایم. تا بعد!', (6, 40), [
    ('de vensterbank', 'De rand onder een raam.|The ledge below a window.|لبهٔ زیر پنجره.', 'De plant staat op de vensterbank.|The plant is on the windowsill.|گیاه روی لبهٔ پنجره است.'),
    ('aanbellen', 'Op de bel bij een deur drukken.|To ring a doorbell.|زنگ در را زدن.', 'Jonas belt bij Mina aan.|Jonas rings Mina’s doorbell.|یوناس زنگ در مینا را می‌زند.'),
    ('klein', 'Niet groot.|Small.|کوچک.', 'De plant is klein.|The plant is small.|گیاه کوچک است.'),
    ('samen', 'Met elkaar.|Together.|با هم.', 'Ze drinken samen thee.|They drink tea together.|آن‌ها با هم چای می‌نوشند.')
])


# These observable criteria describe the actual output task, rather than asking
# the assessor to infer a rubric from the unit's broad communication goal.
CRITERIA = {
    'blue-envelope': (
        ['Spreek Noor aan.|Address Noor.|نور را خطاب قرار بده.', 'Zeg dat de envelop voor haar is.|Say the envelope is for her.|بگو پاکت برای اوست.'],
        ['Noem je eigen naam.|Give your own name.|نام خودت را بگو.', 'Noem de kleur van je envelop.|Give your envelope’s colour.|رنگ پاکتت را بگو.']),
    'window-plant': (
        ['Noem een plaats voor de plant.|Give a place for the plant.|جایی برای گیاه مشخص کن.', 'Nodig de buur uit voor thee.|Invite the neighbour for tea.|همسایه را به چای دعوت کن.'],
        ['Zeg of je kunt komen.|Say whether you can come.|بگو می‌توانی بیایی یا نه.', 'Reageer op de uitnodiging voor drie uur.|Respond to the invitation for three.|به دعوت ساعت سه پاسخ بده.']),
    'recipe-stain': (
        ['Vraag naar de ontbrekende kooktijd.|Ask for the missing cooking time.|زمان پخت جاافتاده را بپرس.', 'Bevestig de gehoorde dertig minuten.|Confirm the thirty minutes you heard.|سی دقیقه‌ای را که شنیدی تأیید کن.'],
        ['Noem de pompoen en dertig minuten.|Mention the pumpkin and thirty minutes.|کدوحلوایی و سی دقیقه را ذکر کن.', 'Voeg de room pas na het koken toe.|Add the cream only after cooking.|خامه را فقط بعد از پخت اضافه کن.']),
    'two-tickets': (
        ['Bevestig dat jullie zaterdag gaan.|Confirm that you will go on Saturday.|تأیید کن که شنبه می‌روید.', 'Vraag waar jullie afspreken.|Ask where to meet.|بپرس کجا قرار می‌گذارید.'],
        ['Bevestig zaterdag en de geruilde dienst.|Confirm Saturday and the swapped shift.|شنبه و عوض شدن شیفت را تأیید کن.', 'Leg uit dat zondag niet meer nodig is.|Explain that Sunday is no longer needed.|توضیح بده یکشنبه دیگر لازم نیست.']),
    'silent-radio': (
        ['Leg uit wat is hersteld en wat nog kraakt.|Explain what was repaired and what still crackles.|بگو چه چیزی تعمیر شده و چه چیزی هنوز خش‌خش می‌کند.', 'Bespreek de keuze om tot vrijdag te wachten.|Discuss the choice to wait until Friday.|دربارهٔ انتخاب منتظر ماندن تا جمعه صحبت کن.'],
        ['Kies ophalen of wachten.|Choose collection or waiting.|تحویل گرفتن یا منتظر ماندن را انتخاب کن.', 'Geef een reden uit Lucs bericht.|Give a reason from Luc’s message.|از پیام لوک دلیلی بیاور.']),
    'unfinished-mural': (
        ['Noem een voordeel en een bezwaar.|Give an advantage and a concern.|یک مزیت و یک نگرانی بگو.', 'Stel een concrete volgende stap voor.|Propose a concrete next step.|قدم بعدی مشخصی پیشنهاد بده.'],
        ['Nodig uit voor zaterdag.|Invite people for Saturday.|برای شنبه دعوت کن.', 'Leg het gewichtsprobleem en de veertig euro uit.|Explain the weight problem and the forty euros.|مشکل وزن و چهل یورو را توضیح بده.', 'Zeg dat het voorstel nog niet is goedgekeurd.|Say the proposal has not been approved yet.|بگو پیشنهاد هنوز تصویب نشده است.']),
}


unit('pre-a2', 'recipe-stain', 'De vlek op het recept|The stain on the recipe|لکهٔ روی دستور پخت',
     'Vraag om ontbrekende informatie en geef een volgorde aan.|Ask for missing information and give a sequence.|اطلاعات جاافتاده را بپرس و ترتیب کار را بیان کن.', [
    'Rosa wil soep maken voor haar vader.|Rosa wants to make soup for her father.|روزا می‌خواهد برای پدرش سوپ درست کند.',
    'Ze gebruikt een oud recept van haar moeder.|She uses an old recipe from her mother.|از دستور پخت قدیمی مادرش استفاده می‌کند.',
    'Er zit een grote vlek op het papier.|There is a large stain on the paper.|روی کاغذ لکهٔ بزرگی است.',
    'De groenten kan ze lezen, maar de kooktijd niet.|She can read the vegetables, but not the cooking time.|نام سبزی‌ها را می‌تواند بخواند، اما زمان پخت را نه.',
    'Ze belt haar moeder en vraagt om hulp.|She calls her mother and asks for help.|به مادرش زنگ می‌زند و کمک می‌خواهد.',
    'Eerst snijd je de wortels, zegt haar moeder.|First you cut the carrots, her mother says.|مادرش می‌گوید: اول هویج‌ها را خرد می‌کنی.',
    'Dan kook je alles twintig minuten.|Then you cook everything for twenty minutes.|بعد همه‌چیز را بیست دقیقه می‌پزی.',
    'Rosa schrijft de tijd naast de vlek.|Rosa writes the time beside the stain.|روزا زمان را کنار لکه می‌نویسد.',
    'Haar vader proeft de soep en glimlacht.|Her father tastes the soup and smiles.|پدرش سوپ را می‌چشد و لبخند می‌زند.',
    'De soep smaakt net als vroeger.|The soup tastes just like it used to.|مزهٔ سوپ درست مثل گذشته است.'
], 'Rosa, voor pompoensoep is het anders. Snijd eerst de pompoen. Kook de soep dertig minuten. Voeg daarna een beetje room toe.|Rosa, pumpkin soup is different. Cut the pumpkin first. Cook the soup for thirty minutes. Add a little cream afterwards.|روزا، سوپ کدوحلوایی فرق دارد. اول کدوحلوایی را خرد کن. سوپ را سی دقیقه بپز. بعد کمی خامه اضافه کن.', [
    ('Wat kan Rosa niet lezen?|What can Rosa not read?|روزا چه چیزی را نمی‌تواند بخواند؟', 'De kooktijd.|The cooking time.|زمان پخت.', 'De groenten.|The vegetables.|سبزی‌ها.', 'De vlek bedekt de kooktijd.|The stain covers the cooking time.|لکه زمان پخت را پوشانده است.'),
    ('Hoe lang kookt de soep uit het oude recept?|How long does the soup in the old recipe cook?|سوپ دستور قدیمی چقدر می‌پزد؟', 'Twintig minuten.|Twenty minutes.|بیست دقیقه.', 'Dertig minuten.|Thirty minutes.|سی دقیقه.', 'Haar moeder zegt twintig minuten.|Her mother says twenty minutes.|مادرش می‌گوید بیست دقیقه.')
], [
    ('Hoe lang kookt de pompoensoep?|How long does the pumpkin soup cook?|سوپ کدوحلوایی چقدر می‌پزد؟', 'Dertig minuten.|Thirty minutes.|سی دقیقه.', 'Twintig minuten.|Twenty minutes.|بیست دقیقه.', 'De nieuwe instructie noemt dertig minuten.|The new instruction says thirty minutes.|دستور تازه سی دقیقه را بیان می‌کند.'),
    ('Wat voeg je daarna toe?|What do you add afterwards?|بعد چه چیزی اضافه می‌کنی؟', 'Een beetje room.|A little cream.|کمی خامه.', 'Een wortel.|A carrot.|یک هویج.', 'Room komt na het koken.|Cream is added after cooking.|خامه بعد از پخت اضافه می‌شود.')
], 'Je kunt een stap op een recept niet lezen. Vraag om hulp en herhaal de kooktijd die je hoort.|You cannot read a recipe step. Ask for help and repeat the cooking time you hear.|یکی از مراحل دستور را نمی‌توانی بخوانی. کمک بخواه و زمان پختی را که می‌شنوی تکرار کن.',
     'Ik kan de tijd niet lezen. Hoe lang moet de soep koken? Dertig minuten, juist?|I cannot read the time. How long should the soup cook? Thirty minutes, right?|زمان را نمی‌توانم بخوانم. سوپ چقدر باید بپزد؟ سی دقیقه، درست است؟',
     'Schrijf drie stappen voor de pompoensoep uit het luisterbericht.|Write three steps for the pumpkin soup from the audio message.|از پیام شنیداری، سه مرحلهٔ سوپ کدوحلوایی را بنویس.',
     'Snijd eerst de pompoen. Kook de soep dertig minuten. Voeg daarna een beetje room toe.|Cut the pumpkin first. Cook the soup for thirty minutes. Add a little cream afterwards.|اول کدوحلوایی را خرد کن. سوپ را سی دقیقه بپز. بعد کمی خامه اضافه کن.', (8, 55), [
    ('de vlek', 'Een vuile of verkleurde plek.|A dirty or discoloured mark.|لکه یا جای تغییررنگ‌داده.', 'De vlek zit op het recept.|The stain is on the recipe.|لکه روی دستور پخت است.'),
    ('toevoegen', 'Er iets bij doen.|To add something.|چیزی اضافه کردن.', 'Voeg een beetje room toe.|Add a little cream.|کمی خامه اضافه کن.'),
    ('oud', 'Al lang bestaand.|Existing for a long time.|قدیمی.', 'Rosa gebruikt een oud recept.|Rosa uses an old recipe.|روزا از دستور پخت قدیمی استفاده می‌کند.'),
    ('daarna', 'Na dat moment.|After that.|پس از آن.', 'Daarna voegt ze room toe.|Afterwards she adds cream.|بعد خامه اضافه می‌کند.')
])

unit('a2', 'two-tickets', 'Twee kaartjes, één verrassing|Two tickets, one surprise|دو بلیت، یک غافلگیری',
     'Vertel wat er gebeurd is en stel een nieuw plan voor.|Explain what happened and propose a new plan.|بگو چه اتفاقی افتاده و برنامه‌ای تازه پیشنهاد بده.', [
    'Lena heeft twee kaartjes voor een concert gekocht.|Lena has bought two concert tickets.|لنا دو بلیت کنسرت خریده است.',
    'Ze wil haar vriend Milan verrassen.|She wants to surprise her boyfriend Milan.|می‌خواهد دوست‌پسرش میلان را غافلگیر کند.',
    'Ze heeft de kaartjes in een kookboek gelegd.|She has put the tickets in a cookbook.|بلیت‌ها را داخل کتاب آشپزی گذاشته است.',
    'Op vrijdag bakt Milan een taart uit dat boek.|On Friday Milan bakes a cake from that book.|جمعه میلان از روی همان کتاب کیک می‌پزد.',
    'Hij vindt de kaartjes en denkt dat het oude kaartjes zijn.|He finds the tickets and thinks they are old ones.|بلیت‌ها را پیدا می‌کند و فکر می‌کند قدیمی هستند.',
    'Gelukkig vraagt hij het voordat hij ze weggooit.|Fortunately he asks before throwing them away.|خوشبختانه پیش از دور انداختنشان سؤال می‌کند.',
    'Lena vertelt hem over het concert van zaterdag.|Lena tells him about Saturday’s concert.|لنا دربارهٔ کنسرت شنبه به او می‌گوید.',
    'Milan moet zaterdagavond werken.|Milan has to work on Saturday evening.|میلان باید شنبه‌شب کار کند.',
    'Samen zoeken ze een concert op zondag.|Together they look for a concert on Sunday.|با هم دنبال کنسرتی در روز یکشنبه می‌گردند.',
    'De verrassing is weg, maar hun nieuwe plan is beter.|The surprise is gone, but their new plan is better.|غافلگیری از بین رفته، اما برنامهٔ تازه‌شان بهتر است.'
], 'Dag Lena, ik heb geruild met een collega. Zaterdagavond ben ik toch vrij. Het concert op zondag is uitverkocht. Laten we de twee kaartjes voor zaterdag houden.|Hello, Lena, I have swapped shifts with a colleague. I am free on Saturday evening after all. Sunday’s concert is sold out. Let’s keep the two tickets for Saturday.|سلام لنا، شیفتم را با همکارم عوض کرده‌ام. بالاخره شنبه‌شب آزاد هستم. بلیت‌های کنسرت یکشنبه تمام شده است. بیا دو بلیت شنبه را نگه داریم.', [
    ('Waar vindt Milan de kaartjes?|Where does Milan find the tickets?|میلان بلیت‌ها را کجا پیدا می‌کند؟', 'In een kookboek.|In a cookbook.|داخل کتاب آشپزی.', 'In zijn jas.|In his coat.|داخل کتش.', 'Lena heeft ze in het kookboek gelegd.|Lena has put them in the cookbook.|لنا آن‌ها را داخل کتاب آشپزی گذاشته است.'),
    ('Waarom zoeken ze eerst een concert op zondag?|Why do they initially look for a Sunday concert?|چرا ابتدا دنبال کنسرت یکشنبه می‌گردند؟', 'Milan moet zaterdagavond werken.|Milan has to work on Saturday evening.|میلان باید شنبه‌شب کار کند.', 'Lena houdt niet van muziek.|Lena does not like music.|لنا موسیقی دوست ندارد.', 'Zijn werk botst met het eerste plan.|His work conflicts with the first plan.|کار او با برنامهٔ اول تداخل دارد.')
], [
    ('Wat is er veranderd?|What has changed?|چه چیزی تغییر کرده است؟', 'Milan is zaterdagavond vrij.|Milan is free on Saturday evening.|میلان شنبه‌شب آزاد است.', 'Lena moet zaterdag werken.|Lena has to work on Saturday.|لنا باید شنبه کار کند.', 'Milan heeft zijn dienst geruild.|Milan has swapped his shift.|میلان شیفتش را عوض کرده است.'),
    ('Welke kaartjes willen ze houden?|Which tickets do they want to keep?|کدام بلیت‌ها را می‌خواهند نگه دارند؟', 'De kaartjes voor zaterdag.|The Saturday tickets.|بلیت‌های شنبه.', 'De kaartjes voor zondag.|The Sunday tickets.|بلیت‌های یکشنبه.', 'Het zondagconcert is uitverkocht.|The Sunday concert is sold out.|بلیت‌های کنسرت یکشنبه تمام شده است.')
], 'Je vriend kan na een wijziging toch mee. Bevestig het nieuwe plan en vraag waar jullie afspreken.|Your friend can come after a change. Confirm the new plan and ask where to meet.|دوستت پس از تغییری می‌تواند بیاید. برنامهٔ تازه را تأیید کن و بپرس کجا قرار می‌گذارید.',
     'Fijn dat je zaterdag vrij bent! Dan houden we de kaartjes voor zaterdag. Waar spreken we af?|It’s good that you are free on Saturday! Then we will keep the Saturday tickets. Where shall we meet?|خوب شد شنبه آزادی! پس بلیت‌های شنبه را نگه می‌داریم. کجا قرار بگذاریم؟',
     'Antwoord op Milans bericht. Bevestig de dag en leg uit waarom zondag niet meer nodig is.|Reply to Milan’s message. Confirm the day and explain why Sunday is no longer needed.|به پیام میلان پاسخ بده. روز را تأیید کن و توضیح بده چرا یکشنبه دیگر لازم نیست.',
     'Dag Milan, wat fijn! We gaan zaterdag naar het concert, want je hebt je dienst geruild. We hoeven geen kaartjes voor zondag te zoeken. Zullen we om zeven uur aan de ingang afspreken?|Hello, Milan, that’s great! We will go to the concert on Saturday because you have swapped your shift. We do not need to look for Sunday tickets. Shall we meet at the entrance at seven?|سلام میلان، چه خوب! شنبه به کنسرت می‌رویم، چون شیفتت را عوض کرده‌ای. لازم نیست دنبال بلیت یکشنبه بگردیم. ساعت هفت جلوی ورودی قرار بگذاریم؟', (15, 65), [
    ('verrassen', 'Iemand iets onverwachts en leuks geven of laten beleven.|To give someone an unexpected pleasant experience.|کسی را با اتفاقی خوشایند و غیرمنتظره غافلگیر کردن.', 'Lena wil Milan verrassen.|Lena wants to surprise Milan.|لنا می‌خواهد میلان را غافلگیر کند.'),
    ('weggooien', 'Iets bij het afval doen.|To throw something away.|چیزی را دور انداختن.', 'Hij gooit de kaartjes niet weg.|He does not throw the tickets away.|بلیت‌ها را دور نمی‌اندازد.'),
    ('uitverkocht', 'Zonder beschikbare kaartjes of producten.|Sold out.|تمام‌شده از نظر موجودی یا بلیت.', 'Het concert is uitverkocht.|The concert is sold out.|بلیت‌های کنسرت تمام شده است.'),
    ('gelukkig', 'Tot ons geluk.|Fortunately.|خوشبختانه.', 'Gelukkig vraagt hij het eerst.|Fortunately he asks first.|خوشبختانه اول سؤال می‌کند.')
])

unit('pre-b1', 'silent-radio', 'De stille radio|The silent radio|رادیوی خاموش',
     'Vertel een gebeurtenis in het verleden en bespreek een oplossing.|Tell a past event and discuss a solution.|رویدادی در گذشته را تعریف کن و دربارهٔ راه‌حل گفت‌وگو کن.', [
    'Toen haar grootvader verhuisde, kreeg Aya zijn oude radio.|When her grandfather moved, Aya received his old radio.|وقتی پدربزرگ آیا اسباب‌کشی کرد، رادیوی قدیمی‌اش را به او داد.',
    'Ze herinnerde zich de muziek tijdens hun zondagse ontbijt.|She remembered the music during their Sunday breakfasts.|موسیقی صبحانه‌های یکشنبه‌شان را به یاد می‌آورد.',
    'Thuis draaide ze aan de knop, maar ze hoorde niets.|At home she turned the knob, but heard nothing.|در خانه پیچ رادیو را چرخاند، اما چیزی نشنید.',
    'Een nieuwe batterij hielp niet.|A new battery did not help.|باتری تازه هم کمکی نکرد.',
    'Daarom nam ze de radio mee naar een herstelatelier.|So she took the radio to a repair workshop.|برای همین رادیو را به کارگاه تعمیر برد.',
    'Vrijwilliger Luc ontdekte een los draadje.|Volunteer Luc discovered a loose wire.|لوک، داوطلب کارگاه، سیمی شل پیدا کرد.',
    'Aya mocht kijken terwijl hij het voorzichtig vastmaakte.|Aya could watch while he carefully secured it.|آیا اجازه داشت نگاه کند، درحالی‌که او بااحتیاط سیم را محکم می‌کرد.',
    'Plots klonk een lied dat ze meteen herkende.|Suddenly a song played that she recognised immediately.|ناگهان آهنگی پخش شد که فوراً شناخت.',
    'Ze belde haar grootvader en hield de telefoon bij de radio.|She called her grandfather and held the phone beside the radio.|به پدربزرگش زنگ زد و تلفن را کنار رادیو گرفت.',
    'Aan de andere kant begon hij zacht mee te zingen.|At the other end he began to sing along softly.|آن‌سوی خط، او آهسته با آهنگ هم‌صدا شد.'
], 'Aya, met Luc. Het draadje zit nu goed vast, maar de luidspreker kraakt. Je kunt de radio vandaag ophalen of hem tot vrijdag hier laten voor een tweede controle. Die controle is gratis.|Aya, Luc here. The wire is secure now, but the speaker crackles. You can collect the radio today or leave it here until Friday for a second check. That check is free.|آیا، لوک هستم. سیم حالا محکم است، اما بلندگو خش‌خش می‌کند. می‌توانی رادیو را امروز تحویل بگیری یا تا جمعه برای بررسی دوم اینجا بگذاری. این بررسی رایگان است.', [
    ('Waarom is de radio belangrijk voor Aya?|Why is the radio important to Aya?|چرا رادیو برای آیا مهم است؟', 'Hij herinnert haar aan ontbijt met haar grootvader.|It reminds her of breakfast with her grandfather.|او را به یاد صبحانه با پدربزرگش می‌اندازد.', 'Ze heeft hem net in een winkel gekocht.|She has just bought it in a shop.|همین حالا آن را از فروشگاه خریده است.', 'Ze herinnert zich hun zondagse muziek.|She remembers their Sunday music.|موسیقی یکشنبه‌هایشان را به یاد دارد.'),
    ('Wat herstelt Luc eerst?|What does Luc repair first?|لوک ابتدا چه چیزی را تعمیر می‌کند؟', 'Een los draadje.|A loose wire.|سیمی شل.', 'Een gebroken knop.|A broken knob.|پیچی شکسته.', 'Hij maakt het draadje vast.|He secures the wire.|سیم را محکم می‌کند.')
], [
    ('Welk probleem blijft er nog?|What problem remains?|چه مشکلی هنوز باقی است؟', 'De luidspreker kraakt.|The speaker crackles.|بلندگو خش‌خش می‌کند.', 'De batterij ontbreekt.|The battery is missing.|باتری وجود ندارد.', 'Luc hoort gekraak in de luidspreker.|Luc hears crackling in the speaker.|لوک از بلندگو خش‌خش می‌شنود.'),
    ('Tot wanneer kan de radio voor controle blijven?|Until when can the radio stay for a check?|رادیو برای بررسی تا چه روزی می‌تواند بماند؟', 'Tot vrijdag.|Until Friday.|تا جمعه.', 'Tot maandag.|Until Monday.|تا دوشنبه.', 'Luc biedt een controle tegen vrijdag aan.|Luc offers a check by Friday.|لوک بررسی تا جمعه را پیشنهاد می‌کند.')
], 'Leg aan je grootvader uit wat er met de radio gebeurd is. Bespreek of je op de tweede controle wilt wachten.|Explain to your grandfather what happened to the radio. Discuss whether you want to wait for the second check.|به پدربزرگت توضیح بده چه اتفاقی برای رادیو افتاده است. دربارهٔ منتظر ماندن برای بررسی دوم صحبت کن.',
     'Luc heeft het draadje vastgemaakt. De radio speelt weer, maar de luidspreker kraakt nog. Ik wil tot vrijdag wachten op de gratis controle. Dan weten we beter of het probleem opgelost is.|Luc has secured the wire. The radio plays again, but the speaker still crackles. I want to wait until Friday for the free check. Then we will know better whether the problem is solved.|لوک سیم را محکم کرده است. رادیو دوباره کار می‌کند، اما بلندگو هنوز خش‌خش می‌کند. می‌خواهم تا جمعه منتظر بررسی رایگان بمانم. آن‌وقت بهتر می‌فهمیم مشکل حل شده یا نه.',
     'Schrijf Luc terug. Kies ophalen of wachten en geef een reden op basis van zijn bericht.|Write back to Luc. Choose collection or waiting and give a reason based on his message.|به لوک پاسخ بده. تحویل گرفتن یا منتظر ماندن را انتخاب کن و بر اساس پیامش دلیل بیاور.',
     'Dag Luc, bedankt voor de herstelling. Ik laat de radio graag tot vrijdag bij jullie, want de luidspreker kraakt nog. Het is een cadeau van mijn grootvader en ik wil hem blijven gebruiken. Laat je weten wanneer de tweede controle klaar is? Vriendelijke groeten, Aya.|Hello, Luc, thank you for the repair. I would like to leave the radio with you until Friday because the speaker still crackles. It is a gift from my grandfather and I want to keep using it. Will you let me know when the second check is finished? Kind regards, Aya.|سلام لوک، از تعمیرت ممنونم. ترجیح می‌دهم رادیو تا جمعه پیش شما بماند، چون بلندگو هنوز خش‌خش می‌کند. هدیهٔ پدربزرگم است و می‌خواهم همچنان از آن استفاده کنم. خبر می‌دهی بررسی دوم چه زمانی تمام می‌شود؟ با احترام، آیا.', (25, 90), [
    ('vastmaken', 'Zorgen dat iets niet meer los zit.|To fasten something securely.|محکم کردن چیزی.', 'Luc maakt het draadje vast.|Luc secures the wire.|لوک سیم را محکم می‌کند.'),
    ('herkennen', 'Weten wat of wie iets of iemand is doordat je het eerder zag of hoorde.|To recognise something or someone encountered before.|شناختن چیزی یا کسی که قبلاً دیده یا شنیده‌ای.', 'Aya herkent het lied.|Aya recognises the song.|آیا آهنگ را می‌شناسد.'),
    ('voorzichtig', 'Zonder onnodige risico’s.|Careful.|بااحتیاط.', 'Luc werkt voorzichtig.|Luc works carefully.|لوک بااحتیاط کار می‌کند.'),
    ('plots', 'Onverwacht en opeens.|Suddenly.|ناگهان.', 'Plots klinkt muziek.|Suddenly music plays.|ناگهان موسیقی پخش می‌شود.')
])

unit('b1', 'unfinished-mural', 'De lege plek op de muur|The empty space on the wall|جای خالی روی دیوار',
     'Bespreek verschillende wensen en onderbouw een gezamenlijk besluit.|Discuss different wishes and justify a shared decision.|خواسته‌های متفاوت را بررسی کن و برای تصمیم مشترک دلیل بیاور.', [
    'De bewoners van een straat in Kortrijk maken samen een muurschildering.|The residents of a street in Kortrijk are creating a mural together.|ساکنان خیابانی در کورتریک با هم نقاشی دیواری می‌کشند.',
    'Iedereen mag iets schilderen dat bij de buurt past.|Everyone may paint something that belongs to the neighbourhood.|هرکس می‌تواند چیزی متناسب با محله نقاشی کند.',
    'Bilal schildert de bakkerij waar hij zijn eerste baan vond.|Bilal paints the bakery where he found his first job.|بلال نانوایی‌ای را می‌کشد که اولین کارش را آنجا پیدا کرد.',
    'Emma tekent de boom waaronder haar ouders elkaar leerden kennen.|Emma draws the tree under which her parents first met.|اما درختی را می‌کشد که پدر و مادرش زیر آن با هم آشنا شدند.',
    'Alleen in het midden blijft een groot wit vlak over.|Only a large white area in the middle remains empty.|فقط بخش سفید بزرگی در وسط خالی می‌ماند.',
    'Sommige buren willen daar de naam van de straat zetten.|Some neighbours want to put the street’s name there.|بعضی همسایه‌ها می‌خواهند نام خیابان را آنجا بنویسند.',
    'Anderen willen ruimte laten voor bewoners die later komen.|Others want to leave room for residents who arrive later.|دیگران می‌خواهند برای ساکنان آینده جا بگذارند.',
    'Na een gesprek stellen ze voor om er losse panelen te hangen.|After a discussion they propose hanging removable panels there.|پس از گفت‌وگو پیشنهاد می‌کنند آنجا صفحه‌های جداشدنی نصب کنند.',
    'Zo kan het midden veranderen zonder de rest te overschilderen.|This lets the centre change without painting over the rest.|این‌طوری بخش میانی بدون پوشاندن بقیهٔ نقاشی تغییر می‌کند.',
    'Emma schrijft de eerste uitnodiging voor de nieuwe buren.|Emma writes the first invitation for the new neighbours.|اما اولین دعوت‌نامه را برای همسایه‌های تازه می‌نویسد.'
], 'Dag iedereen, de panelen zijn te zwaar voor de bevestiging die we hebben. Een vrijwilliger stelt lichte houten kaders voor. Die kosten samen veertig euro. We kunnen de naam van de straat bovenaan houden en de tekeningen in de kaders verwisselen. Beslissen we daar zaterdag samen over?|Hello, everyone, the panels are too heavy for the fastening we have. A volunteer suggests lightweight wooden frames. Together they cost forty euros. We can keep the street’s name at the top and change the pictures in the frames. Shall we decide together on Saturday?|سلام به همه، صفحه‌ها برای اتصالی که داریم بیش از حد سنگین هستند. داوطلبی قاب‌های چوبی سبک پیشنهاد می‌کند. در مجموع چهل یورو هزینه دارند. می‌توانیم نام خیابان را بالا نگه داریم و تصویرهای داخل قاب‌ها را عوض کنیم. شنبه با هم درباره‌اش تصمیم بگیریم؟', [
    ('Waarom willen sommige buren ruimte vrijhouden?|Why do some neighbours want to leave space?|چرا بعضی همسایه‌ها می‌خواهند جایی خالی بماند؟', 'Voor bewoners die later komen.|For residents who arrive later.|برای ساکنان آینده.', 'Omdat niemand kan schilderen.|Because nobody can paint.|چون هیچ‌کس نقاشی بلد نیست.', 'Ook nieuwe bewoners moeten kunnen bijdragen.|New residents should be able to contribute too.|ساکنان تازه هم باید بتوانند مشارکت کنند.'),
    ('Wat is het voordeel van losse panelen?|What is the advantage of removable panels?|مزیت صفحه‌های جداشدنی چیست؟', 'Het midden kan veranderen.|The centre can change.|بخش میانی می‌تواند تغییر کند.', 'De hele muur moet telkens opnieuw geschilderd worden.|The whole wall must be repainted each time.|هربار باید کل دیوار دوباره نقاشی شود.', 'De rest hoeft niet overschilderd te worden.|The rest does not need painting over.|لازم نیست روی بقیه دوباره رنگ بزنند.')
], [
    ('Waarom wordt een ander materiaal voorgesteld?|Why is another material suggested?|چرا مادهٔ دیگری پیشنهاد می‌شود؟', 'De panelen zijn te zwaar.|The panels are too heavy.|صفحه‌ها بیش از حد سنگین هستند.', 'De straat krijgt een nieuwe naam.|The street is getting a new name.|نام خیابان عوض می‌شود.', 'De bestaande bevestiging kan het gewicht niet dragen.|The existing fastening cannot support the weight.|اتصال موجود تحمل وزن را ندارد.'),
    ('Is het voorstel al definitief goedgekeurd?|Has the proposal already received final approval?|آیا پیشنهاد به‌طور نهایی تصویب شده است؟', 'Nee, er volgt zaterdag een gezamenlijk besluit.|No, a joint decision follows on Saturday.|نه، شنبه تصمیم مشترک گرفته می‌شود.', 'Ja, de kaders zijn al gekocht.|Yes, the frames have already been bought.|بله، قاب‌ها قبلاً خریده شده‌اند.', 'Het bericht vraagt nog om een besluit.|The message still asks for a decision.|پیام هنوز درخواست تصمیم‌گیری می‌کند.')
], 'Bespreek het voorstel voor lichte kaders met een buur. Noem een voordeel en een bezwaar en stel een volgende stap voor.|Discuss the lightweight-frame proposal with a neighbour. Give one advantage and one concern, then propose a next step.|پیشنهاد قاب‌های سبک را با همسایه بررسی کن. یک مزیت و یک نگرانی بگو و قدم بعد را پیشنهاد بده.',
     'Lichte kaders lijken me handig, want we kunnen de tekeningen later veranderen. Ik weet alleen niet of het hout tegen regen kan. Zullen we dat voor zaterdag aan de vrijwilliger vragen? Dan kunnen we met de juiste informatie over de veertig euro beslissen.|Lightweight frames seem useful because we can change the pictures later. I just do not know whether the wood can withstand rain. Shall we ask the volunteer before Saturday? Then we can decide about the forty euros with the right information.|قاب‌های سبک به‌نظرم کاربردی هستند، چون بعداً می‌توانیم تصویرها را تغییر بدهیم. فقط نمی‌دانم چوب در برابر باران دوام دارد یا نه. قبل از شنبه از داوطلب بپرسیم؟ آن‌وقت با اطلاعات درست دربارهٔ چهل یورو تصمیم می‌گیریم.',
     'Schrijf een uitnodiging voor het overleg van zaterdag. Leg uit wat veranderde, noem de kosten en maak duidelijk dat er nog geen definitief besluit is.|Write an invitation to Saturday’s discussion. Explain what changed, give the cost and make clear that no final decision has been made.|برای جلسهٔ شنبه دعوت‌نامه بنویس. تغییر را توضیح بده، هزینه را بگو و روشن کن هنوز تصمیم نهایی گرفته نشده است.',
     'Beste buren, zaterdag bespreken we hoe we het midden van de muurschildering kunnen gebruiken. De panelen blijken te zwaar voor onze bevestiging. Daarom stelt een vrijwilliger lichte houten kaders voor. Die kosten samen veertig euro. De tekeningen blijven dan verwisselbaar en de straatnaam kan bovenaan staan. We hebben dit nog niet definitief goedgekeurd. Kom dus mee nadenken en breng je vragen over het materiaal en de kosten mee. Tot zaterdag!|Dear neighbours, on Saturday we will discuss how to use the centre of the mural. The panels turn out to be too heavy for our fastening. A volunteer therefore suggests lightweight wooden frames. Together they cost forty euros. The pictures would remain interchangeable and the street’s name could stay at the top. We have not given this final approval yet. Please join the discussion and bring your questions about the material and the cost. See you on Saturday!|همسایه‌های عزیز، شنبه دربارهٔ استفاده از بخش میانی نقاشی دیواری گفت‌وگو می‌کنیم. مشخص شده صفحه‌ها برای اتصال ما بیش از حد سنگین هستند. بنابراین داوطلبی قاب‌های چوبی سبک پیشنهاد می‌کند. در مجموع چهل یورو هزینه دارند. تصویرها قابل تعویض می‌مانند و نام خیابان می‌تواند بالا باشد. هنوز این پیشنهاد را نهایی تصویب نکرده‌ایم. لطفاً در گفت‌وگو شرکت کنید و پرسش‌هایتان دربارهٔ جنس و هزینه را بیاورید. تا شنبه!', (30, 100), [
    ('overschilderen', 'Nieuwe verf over een geschilderd oppervlak aanbrengen.|To paint over a painted surface.|روی سطح نقاشی‌شده دوباره رنگ زدن.', 'We willen de boom niet overschilderen.|We do not want to paint over the tree.|نمی‌خواهیم روی درخت دوباره رنگ بزنیم.'),
    ('bijdragen', 'Een aandeel leveren aan iets gemeenschappelijks.|To contribute to something shared.|در کاری مشترک مشارکت کردن.', 'Ook nieuwe buren kunnen bijdragen.|New neighbours can contribute too.|همسایه‌های تازه هم می‌توانند مشارکت کنند.'),
    ('verwisselbaar', 'Vervangbaar door een ander exemplaar.|Interchangeable.|قابل تعویض.', 'De tekeningen zijn verwisselbaar.|The pictures are interchangeable.|تصویرها قابل تعویض هستند.'),
    ('bovenaan', 'Aan de bovenkant.|At the top.|در بالا.', 'De straatnaam staat bovenaan.|The street’s name is at the top.|نام خیابان بالاست.')
])


GENRES = {
    'blue-envelope': 'Romantiek|Romance|عاشقانه',
    'window-plant': 'Een ontmoeting|An encounter|یک آشنایی',
    'recipe-stain': 'Familie|Family|خانوادگی',
    'two-tickets': 'Romantiek en humor|Romance and humour|عاشقانه و طنز',
    'silent-radio': 'Herinneringen|Memories|خاطره‌ها',
    'unfinished-mural': 'Een buurtverhaal|A neighbourhood story|داستان محله',
}

for _unit in UNITS:
    _unit['genre'] = GENRES[_unit['id']]
    _unit['speaking_criteria'], _unit['writing_criteria'] = CRITERIA[_unit['id']]
    _unit['word_classes'] = (['verb', 'verb', 'adjective', 'adverb'] if _unit['stage'] in ('a2', 'pre-b1', 'b1')
                             else ['noun', 'verb', 'adjective', 'adverb'])
