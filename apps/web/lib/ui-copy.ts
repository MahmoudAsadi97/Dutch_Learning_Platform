/**
 * Interface copy with its glosses. Every key carries Dutch (the interface language), English and Persian;
 * the unit test refuses a missing language, mismatched {placeholders} and formal "u" in the Dutch.
 * Practice content is not here: it stays formal and lives in the content files.
 */
export interface Copy {
  nl: string;
  en: string;
  fa: string;
}

export const uiCopy = {
  nav: {
    today: { nl: "Vandaag", en: "Today", fa: "امروز" },
    learn: { nl: "Leren", en: "Learn", fa: "یادگیری" },
    stories: { nl: "Verhalen", en: "Stories", fa: "داستان‌ها" },
    speak: { nl: "Spreken", en: "Speaking", fa: "صحبت کردن" },
    words: { nl: "Woorden", en: "Words", fa: "واژه‌ها" },
    progress: { nl: "Voortgang", en: "Progress", fa: "پیشرفت" },
    settings: { nl: "Instellingen", en: "Settings", fa: "تنظیمات" },
    videos: { nl: "Video's", en: "Videos", fa: "ویدیوها" },
    account: { nl: "Mijn account en instellingen", en: "My account and settings", fa: "حساب و تنظیمات من" },
    skip: { nl: "Naar de inhoud", en: "Skip to content", fa: "برو به محتوا" },
  },
  action: {
    continue: { nl: "Ga verder", en: "Continue", fa: "ادامه بده" },
    start: { nl: "Start", en: "Start", fa: "شروع" },
    check: { nl: "Controleer", en: "Check", fa: "بررسی کن" },
    next: { nl: "Volgende", en: "Next", fa: "بعدی" },
    back: { nl: "Terug", en: "Back", fa: "برگرد" },
    save: { nl: "Bewaar", en: "Save", fa: "ذخیره کن" },
    retry: { nl: "Opnieuw proberen", en: "Try again", fa: "دوباره تلاش کن" },
    close: { nl: "Sluiten", en: "Close", fa: "بستن" },
    listen: { nl: "Luister", en: "Listen", fa: "گوش بده" },
    record: { nl: "Neem op", en: "Record", fa: "ضبط کن" },
    showMeaning: { nl: "Toon de betekenis", en: "Show the meaning", fa: "معنی را نشان بده" },
  },
  state: {
    loading: { nl: "Bezig met laden", en: "Loading", fa: "در حال بارگذاری" },
    saved: { nl: "Bewaard", en: "Saved", fa: "ذخیره شد" },
    offline: { nl: "Geen verbinding", en: "No connection", fa: "اتصال برقرار نیست" },
    correct: { nl: "Juist", en: "Correct", fa: "درست" },
    almost: { nl: "Bijna", en: "Almost", fa: "تقریباً" },
    notHeard: { nl: "Niet gehoord", en: "Not heard", fa: "شنیده نشد" },
  },
  today: {
    goalLeft: {
      nl: "Nog {points} punten tot je dagdoel.",
      en: "{points} more points to your daily goal.",
      fa: "{points} امتیاز دیگر تا هدف روزانه‌ات.",
    },
    goalMet: {
      nl: "Dagdoel gehaald. Alles wat je nu nog doet, is extra.",
      en: "Daily goal reached. Anything more is a bonus.",
      fa: "به هدف روزانه‌ات رسیدی. هر کاری که از حالا انجام بدهی، فراتر از هدفت است.",
    },
    streak: { nl: "{days} dagen op rij", en: "{days} days in a row", fa: "{days} روز پشت سر هم" },
    loadFailed: {
      nl: "Je overzicht kon niet worden geladen.",
      en: "Your overview could not be loaded.",
      fa: "نمای کلی‌ات بارگذاری نشد.",
    },
    retryStarted: {
      nl: "De schrijver begint opnieuw.",
      en: "The writer is starting again.",
      fa: "نویسنده دوباره شروع می‌کند.",
    },
    wishQueued: {
      nl: "Je wens staat in de wachtrij. De aflevering verschijnt hierboven zodra ze klaar is.",
      en: "Your wish is in the queue. The episode appears above as soon as it is ready.",
      fa: "خواسته‌ات در صف است. قسمت به‌محض آماده شدن در بالا نمایش داده می‌شود.",
    },
  },
  honesty: {
    generated: {
      nl: "Geschreven door een taalmodel, nog niet door een taaldocent nagekeken.",
      en: "Written by a language model, not yet checked by a language teacher.",
      fa: "نوشته‌ی یک مدل زبانی؛ هنوز معلم زبان آن را بررسی نکرده است.",
    },
    noScore: {
      nl: "Punten belonen oefenen, nooit je Nederlands.",
      en: "Points reward practice, never your Dutch.",
      fa: "امتیازها به تمرین پاداش می‌دهند، نه به هلندی‌ات.",
    },
  },
  welcome: {
    title: { nl: "Welkom bij Taalstudio", en: "Welcome to Taalstudio", fa: "به Taalstudio خوش آمدی" },
    intro: {
      nl: "Hier leer je Nederlands zoals het in België gesproken wordt: elke dag een stukje verhaal, woorden die je bewaart, en spreken en schrijven met uitleg.",
      en: "Here you learn Dutch as it is spoken in Belgium: part of a story every day, words you keep, and speaking and writing with explanations.",
      fa: "اینجا هلندی را همان‌طور که در بلژیک صحبت می‌شود یاد می‌گیری: هر روز بخشی از یک داستان، واژه‌هایی که نگه می‌داری، و صحبت کردن و نوشتن همراه با توضیح.",
    },
    stepLanguage: { nl: "Taal", en: "Language", fa: "زبان" },
    stepLevel: { nl: "Niveau", en: "Level", fa: "سطح" },
    stepGoal: { nl: "Doel", en: "Goal", fa: "هدف" },
    stepHow: { nl: "Zo werkt het", en: "How it works", fa: "روش کار" },
    stepStart: { nl: "Eerste oefening", en: "First practice", fa: "اولین تمرین" },
    languageQuestion: {
      nl: "In welke taal wil je hulp?",
      en: "Which language would you like help in?",
      fa: "به چه زبانی کمک می‌خواهی؟",
    },
    languageNote: {
      nl: "De knoppen blijven Nederlands. Onder de Nederlandse tekst zie je een korte vertaling.",
      en: "The buttons stay in Dutch. Under the Dutch text you see a short translation.",
      fa: "دکمه‌ها هلندی می‌مانند. زیر متن هلندی ترجمه‌ی کوتاهی می‌بینی.",
    },
    languageNoteFaPending: {
      nl: "De knoppen blijven Nederlands. Perzische hulp komt zodra een lezer ze heeft nagekeken; kies Perzisch en Engels als je nu al een vertaling wilt.",
      en: "The buttons stay in Dutch. Persian help comes once a reader has checked it; choose Persian and English if you want a translation now.",
      fa: "دکمه‌ها هلندی می‌مانند. کمک فارسی وقتی می‌آید که یک خواننده آن را بررسی کرده باشد؛ اگر همین حالا ترجمه می‌خواهی، فارسی و انگلیسی را انتخاب کن.",
    },
    supportEn: {
      nl: "Nederlands met Engelse hulp",
      en: "Dutch with English help",
      fa: "هلندی با کمک انگلیسی",
    },
    supportFa: {
      nl: "Nederlands met Perzische hulp",
      en: "Dutch with Persian help",
      fa: "هلندی با کمک فارسی",
    },
    supportBoth: {
      nl: "Nederlands met Perzische en Engelse hulp",
      en: "Dutch with Persian and English help",
      fa: "هلندی با کمک فارسی و انگلیسی",
    },
    levelQuestion: {
      nl: "Hoeveel Nederlands ken je al?",
      en: "How much Dutch do you know already?",
      fa: "چقدر هلندی بلدی؟",
    },
    levelNote: {
      nl: "Je kiest alleen een startpunt. Je slaagt hiermee voor niets, en je kunt het later altijd veranderen.",
      en: "You only choose a starting point. It does not mean you have passed anything, and you can always change it later.",
      fa: "فقط نقطه‌ی شروع را انتخاب می‌کنی. این انتخاب به معنای قبول شدن در هیچ مرحله‌ای نیست و بعداً همیشه می‌توانی عوضش کنی.",
    },
    levelZero: { nl: "Ik begin bij nul", en: "I am starting from zero", fa: "از صفر شروع می‌کنم" },
    levelZeroDetail: {
      nl: "Letters, klanken en je eerste woorden.",
      en: "Letters, sounds and your first words.",
      fa: "حروف، صداها و اولین واژه‌هایت.",
    },
    levelFew: { nl: "Ik ken een paar woorden", en: "I know a few words", fa: "چند واژه بلدم" },
    levelFewDetail: {
      nl: "Jezelf voorstellen, getallen, korte zinnen.",
      en: "Introducing yourself, numbers, short sentences.",
      fa: "معرفی خودت، عددها، جمله‌های کوتاه.",
    },
    levelSimple: {
      nl: "Ik red me in eenvoudige gesprekken",
      en: "I can manage simple conversations",
      fa: "از پس گفت‌وگوهای ساده برمی‌آیم",
    },
    levelSimpleDetail: {
      nl: "Boodschappen, afspraken, over je dag vertellen.",
      en: "Shopping, appointments, talking about your day.",
      fa: "خرید، قرار گذاشتن، حرف زدن درباره‌ی روزت.",
    },
    levelFair: {
      nl: "Ik spreek al redelijk Nederlands",
      en: "I already speak fairly good Dutch",
      fa: "هلندی را نسبتاً خوب صحبت می‌کنم",
    },
    levelFairDetail: {
      nl: "Je mening geven, iets uitleggen, langere teksten lezen.",
      en: "Giving your opinion, explaining something, reading longer texts.",
      fa: "نظر دادن، توضیح دادن، خواندن متن‌های طولانی‌تر.",
    },
    levelOther: {
      nl: "Of kies zelf een niveau",
      en: "Or choose a level yourself",
      fa: "یا خودت سطحی را انتخاب کن",
    },
    goalQuestion: {
      nl: "Waarom leer je Nederlands?",
      en: "Why are you learning Dutch?",
      fa: "چرا هلندی یاد می‌گیری؟",
    },
    reasonWork: { nl: "Voor mijn werk", en: "For my work", fa: "برای کارم" },
    reasonStudy: { nl: "Voor mijn studie", en: "For my studies", fa: "برای تحصیلم" },
    reasonDaily: { nl: "Voor het dagelijks leven", en: "For everyday life", fa: "برای زندگی روزمره" },
    reasonIntegration: {
      nl: "Voor inburgering",
      en: "For the civic integration course",
      fa: "برای دوره‌ی ادغام اجتماعی (inburgering)",
    },
    reasonSelf: { nl: "Gewoon voor mezelf", en: "Just for myself", fa: "فقط برای خودم" },
    paceQuestion: {
      nl: "Hoeveel wil je per dag oefenen?",
      en: "How much do you want to practise each day?",
      fa: "روزی چقدر می‌خواهی تمرین کنی؟",
    },
    paceShort: {
      nl: "Kort · ongeveer 10 minuten",
      en: "Short · about 10 minutes",
      fa: "کوتاه · حدود ۱۰ دقیقه",
    },
    paceUsual: {
      nl: "Gewoon · ongeveer 20 minuten",
      en: "Usual · about 20 minutes",
      fa: "معمولی · حدود ۲۰ دقیقه",
    },
    paceLong: {
      nl: "Stevig · ongeveer 30 minuten",
      en: "Solid · about 30 minutes",
      fa: "جدی · حدود ۳۰ دقیقه",
    },
    paceNote: {
      nl: "Je kunt dit later aanpassen in Instellingen.",
      en: "You can change this later in Settings.",
      fa: "بعداً می‌توانی این را در تنظیمات تغییر بدهی.",
    },
    begin: { nl: "Start met leren", en: "Start learning", fa: "یادگیری را شروع کن" },
    saving: { nl: "Even bewaren…", en: "Saving…", fa: "در حال ذخیره…" },
    saveFailed: {
      nl: "Bewaren lukte niet. Probeer het opnieuw.",
      en: "Saving did not work. Please try again.",
      fa: "ذخیره انجام نشد. دوباره امتحان کن.",
    },
    howTitle: { nl: "Zo werkt Taalstudio", en: "How Taalstudio works", fa: "Taalstudio چطور کار می‌کند" },
    howStoryTitle: { nl: "Elke dag een aflevering", en: "An episode every day", fa: "هر روز یک قسمت" },
    howStory: {
      nl: "Een doorlopend verhaal op jouw niveau, met vragen en woorden die je kunt bewaren.",
      en: "An ongoing story at your level, with questions and words you can keep.",
      fa: "داستانی ادامه‌دار در سطح خودت، با پرسش‌ها و واژه‌هایی که می‌توانی نگه داری.",
    },
    howWordsTitle: { nl: "Woorden die blijven", en: "Words that stick", fa: "واژه‌هایی که در یادت می‌مانند" },
    howWords: {
      nl: "Bewaar woorden en herhaal ze op het juiste moment.",
      en: "Keep words and review them at the right moment.",
      fa: "واژه‌ها را نگه دار و درست به‌موقع مرورشان کن.",
    },
    howSpeakTitle: { nl: "Spreken en schrijven", en: "Speaking and writing", fa: "صحبت کردن و نوشتن" },
    howSpeak: {
      nl: "Je krijgt uitleg bij wat je zegt en schrijft, nooit een score voor je uitspraak.",
      en: "You get explanations for what you say and write, never a score for your pronunciation.",
      fa: "برای آنچه می‌گویی و می‌نویسی توضیح می‌گیری، اما هرگز برای تلفظت نمره نمی‌گیری.",
    },
    howGoalTitle: { nl: "Een doel per dag", en: "A goal for each day", fa: "هدفی برای هر روز" },
    howGoal: {
      nl: "Punten belonen oefenen, nooit je Nederlands. Een dag overslaan is geen ramp.",
      en: "Points reward practice, never your Dutch. Missing a day is no disaster.",
      fa: "امتیازها به تمرین پاداش می‌دهند، نه به هلندی‌ات. جا انداختن یک روز فاجعه نیست.",
    },
    startTitle: {
      nl: "Je eerste aflevering wordt geschreven",
      en: "Your first episode is being written",
      fa: "اولین قسمتت در حال نوشته شدن است",
    },
    startIntro: {
      nl: "Dat duurt één tot drie minuten. Oefen intussen al even.",
      en: "That takes one to three minutes. Practise a little in the meantime.",
      fa: "این یک تا سه دقیقه طول می‌کشد. در این فاصله کمی تمرین کن.",
    },
    startTitleNeutral: { nl: "Oefen alvast even", en: "Practise for a moment", fa: "کمی تمرین کن" },
    alreadyChosen: {
      nl: "Je had je start al gekozen. Je niveau en dagdoel pas je aan in Instellingen.",
      en: "You had already chosen your start. Change your level and daily goal in Settings.",
      fa: "شروعت را قبلاً انتخاب کرده بودی. سطح و هدف روزانه‌ات را در «تنظیمات» تغییر بده.",
    },
    writerQueued: {
      nl: "De schrijver begint zo.",
      en: "The writer starts shortly.",
      fa: "نویسنده به‌زودی شروع می‌کند.",
    },
    writerBusy: {
      nl: "Aflevering {number} wordt geschreven…",
      en: "Episode {number} is being written…",
      fa: "قسمت {number} در حال نوشته شدن است…",
    },
    writerReady: {
      nl: "Aflevering {number} staat klaar.",
      en: "Episode {number} is ready.",
      fa: "قسمت {number} آماده است.",
    },
    writerRead: { nl: "Lees aflevering {number}", en: "Read episode {number}", fa: "قسمت {number} را بخوان" },
    writerFailed: {
      nl: "Het schrijven lukte niet. Op Vandaag kun je het opnieuw proberen.",
      en: "Writing did not work. You can try again on Today.",
      fa: "نوشتن انجام نشد. در «امروز» می‌توانی دوباره امتحان کنی.",
    },
    writerLater: {
      nl: "Je aflevering verschijnt op Vandaag zodra ze klaar is.",
      en: "Your episode appears on Today as soon as it is ready.",
      fa: "قسمتت به‌محض آماده شدن در «امروز» نمایش داده می‌شود.",
    },
    alphabetTitle: { nl: "Het alfabet", en: "The alphabet", fa: "الفبا" },
    wordsTitle: { nl: "Je eerste woorden", en: "Your first words", fa: "اولین واژه‌هایت" },
    wordsIntro: {
      nl: "Kies de woorden die je wilt bewaren. Je herhaalt ze later onder Woorden.",
      en: "Choose the words you want to keep. You review them later under Words.",
      fa: "واژه‌هایی را که می‌خواهی نگه داری انتخاب کن. بعداً در بخش «واژه‌ها» مرورشان می‌کنی.",
    },
    wordsChoose: {
      nl: "Kies woorden om te bewaren",
      en: "Choose words to keep",
      fa: "واژه‌هایی برای نگه داشتن انتخاب کن",
    },
    wordsSaveOne: { nl: "Bewaar 1 woord", en: "Keep 1 word", fa: "یک واژه را نگه دار" },
    wordsSave: { nl: "Bewaar {count} woorden", en: "Keep {count} words", fa: "{count} واژه را نگه دار" },
    wordsSavedOne: { nl: "1 woord bewaard.", en: "1 word kept.", fa: "یک واژه نگه داشته شد." },
    wordsSaved: {
      nl: "{count} woorden bewaard.",
      en: "{count} words kept.",
      fa: "{count} واژه نگه داشته شد.",
    },
    wordsPractise: { nl: "Oefen ze meteen", en: "Practise them right away", fa: "همین حالا تمرینشان کن" },
    wordsUnavailable: {
      nl: "De woordenlijst kon niet worden geladen.",
      en: "The word list could not be loaded.",
      fa: "فهرست واژه‌ها بارگذاری نشد.",
    },
    toToday: { nl: "Naar Vandaag", en: "Go to Today", fa: "برو به «امروز»" },
    back: { nl: "Vorige stap", en: "Previous step", fa: "مرحله‌ی قبل" },
    next: { nl: "Volgende stap", en: "Next step", fa: "مرحله‌ی بعد" },
  },
  chip: {
    generatedLabel: {
      nl: "Taalmodel · niet nagekeken",
      en: "Language model · not reviewed",
      fa: "مدل زبانی · بازبینی‌نشده",
    },
    generated: {
      nl: "Een taalmodel schreef deze tekst. De computer controleerde lengte, niveau en samenhang, maar een taaldocent heeft hem nog niet nagekeken. Kleine fouten zijn mogelijk.",
      en: "A language model wrote this text. The computer checked its length, level and coherence, but a language teacher has not reviewed it yet. Small mistakes are possible.",
      fa: "یک مدل زبانی این متن را نوشته است. رایانه طول، سطح و انسجام آن را بررسی کرده، اما هنوز یک معلم زبان آن را بازبینی نکرده است. ممکن است اشتباه‌های کوچکی در آن باشد.",
    },
    videoLabel: {
      nl: "Taalmodel en computerstem",
      en: "Language model and computer voice",
      fa: "مدل زبانی و صدای رایانه‌ای",
    },
    video: {
      nl: "Een taalmodel schrijft het script en de vertalingen; de stem en het beeld maakt de computer. Wie je ziet of hoort, is geen echte persoon. De ondertitels komen uit de gesproken tekst. Een taaldocent heeft het script nog niet nagekeken.",
      en: "A language model writes the script and the translations; the computer makes the voice and the picture. Whoever you see or hear is not a real person. The subtitles come from the spoken text. A language teacher has not reviewed the script yet.",
      fa: "یک مدل زبانی متن و ترجمه‌ها را می‌نویسد؛ صدا و تصویر را رایانه می‌سازد. کسی که می‌بینی یا می‌شنوی شخص واقعی نیست. زیرنویس‌ها از متن گفتار ساخته می‌شوند. هنوز یک معلم زبان متن را بازبینی نکرده است.",
    },
    unreviewedLabel: { nl: "Nog niet nagekeken", en: "Not reviewed yet", fa: "هنوز بازبینی نشده" },
    unreviewed: {
      nl: "Deze les is voor Taalstudio geschreven, maar een taaldocent heeft ze nog niet nagekeken.",
      en: "This lesson was written for Taalstudio, but a language teacher has not reviewed it yet.",
      fa: "این درس برای Taalstudio نوشته شده، اما هنوز یک معلم زبان آن را بازبینی نکرده است.",
    },
    feedbackLabel: { nl: "Automatische feedback", en: "Automatic feedback", fa: "بازخورد خودکار" },
    feedback: {
      nl: "Deze feedback komt van een taalmodel en is niet door een docent nagekeken. Ze gaat over wat je schreef of zei, nooit over je uitspraak, en geeft geen score.",
      en: "This feedback comes from a language model and has not been checked by a teacher. It is about what you wrote or said, never about your pronunciation, and gives no score.",
      fa: "این بازخورد از یک مدل زبانی می‌آید و معلمی آن را بررسی نکرده است. درباره‌ی چیزی است که نوشتی یا گفتی، هرگز درباره‌ی تلفظت نیست و نمره‌ای هم نمی‌دهد.",
    },
    voiceLabel: { nl: "Computerstem", en: "Computer voice", fa: "صدای رایانه‌ای" },
    voice: {
      nl: "De luistervoorbeelden spreekt de computer uit. Zeg de woorden daarna zelf: dit is oefening, geen beoordeling van je uitspraak.",
      en: "The computer speaks the listening examples. Say the words yourself afterwards: this is practice, not an assessment of your pronunciation.",
      fa: "نمونه‌های شنیداری را رایانه می‌گوید. بعد خودت واژه‌ها را بگو: این تمرین است، نه ارزیابی تلفظ تو.",
    },
    checkLabel: {
      nl: "Oefenleerpad · geen certificaat",
      en: "Practice path · no certificate",
      fa: "مسیر تمرینی · بدون گواهی",
    },
    check: {
      nl: "Taalstudio is een oefenleerpad. De toetsen meten je voortgang hier en geven geen erkend certificaat. De lessen wachten nog op een review door een taaldocent.",
      en: "Taalstudio is a practice path. The checks measure your progress here and give no recognised certificate. The lessons are still waiting for a review by a language teacher.",
      fa: "Taalstudio یک مسیر تمرینی است. آزمون‌ها پیشرفتت را در همین‌جا می‌سنجند و گواهی رسمی نمی‌دهند. درس‌ها هنوز منتظر بازبینی یک معلم زبان هستند.",
    },
    more: { nl: "Meer over de inhoud", en: "More about the content", fa: "بیشتر درباره‌ی محتوا" },
    details: { nl: "Voor ontwikkelaars", en: "For developers", fa: "برای توسعه‌دهندگان" },
  },
  about: {
    title: { nl: "Over de inhoud", en: "About the content", fa: "درباره‌ی محتوا" },
    intro: {
      nl: "Zo ontstaat wat je in Taalstudio leest, hoort en oefent, en wat het wel en niet zegt.",
      en: "How everything you read, hear and practise in Taalstudio is made, and what it does and does not say.",
      fa: "آنچه در Taalstudio می‌خوانی، می‌شنوی و تمرین می‌کنی چگونه ساخته می‌شود، و چه می‌گوید و چه نمی‌گوید.",
    },
    lessonsTitle: { nl: "Lessen en onderwerpen", en: "Lessons and topics", fa: "درس‌ها و موضوع‌ها" },
    lessons: {
      nl: "De lessen, onderwerpen en toetsen zijn voor Taalstudio geschreven in Standaardnederlands met een Belgische context. Een taaldocent heeft ze nog niet nagekeken.",
      en: "The lessons, topics and checks were written for Taalstudio in standard Dutch with a Belgian context. A language teacher has not reviewed them yet.",
      fa: "درس‌ها، موضوع‌ها و آزمون‌ها برای Taalstudio به هلندی معیار با زمینه‌ی بلژیکی نوشته شده‌اند. هنوز یک معلم زبان آن‌ها را بازبینی نکرده است.",
    },
    modelTitle: {
      nl: "Wat een taalmodel schrijft",
      en: "What a language model writes",
      fa: "آنچه یک مدل زبانی می‌نویسد",
    },
    model: {
      nl: "Je verhalen, de scripts van je video's, hun vertalingen en de feedback op je teksten komen van een taalmodel. De computer controleert lengte, niveau en woordenschat; een docent kijkt ze niet na. Kleine fouten zijn mogelijk.",
      en: "Your stories, the scripts of your videos, their translations and the feedback on your texts come from a language model. The computer checks length, level and vocabulary; a teacher does not review them. Small mistakes are possible.",
      fa: "داستان‌هایت، متن ویدیوهایت، ترجمه‌های آن‌ها و بازخورد درباره‌ی نوشته‌هایت از یک مدل زبانی می‌آیند. رایانه طول، سطح و واژگان را بررسی می‌کند؛ معلمی آن‌ها را بازبینی نمی‌کند. ممکن است اشتباه‌های کوچکی در آن‌ها باشد.",
    },
    voiceTitle: { nl: "Stemmen", en: "Voices", fa: "صداها" },
    voices: {
      nl: "Wat je hoort, spreekt de computer uit met een Belgische stem. De presentator in een video is geen echte persoon.",
      en: "What you hear is spoken by the computer with a Belgian voice. The presenter in a video is not a real person.",
      fa: "آنچه می‌شنوی را رایانه با صدایی بلژیکی می‌گوید. مجری ویدیو شخص واقعی نیست.",
    },
    measureTitle: { nl: "Wat we niet meten", en: "What we do not measure", fa: "آنچه نمی‌سنجیم" },
    measure: {
      nl: "Taalstudio geeft geen score voor je uitspraak en geen totaalniveau. Punten belonen oefenen, nooit je Nederlands. De toetsen meten je voortgang hier en geven geen erkend certificaat.",
      en: "Taalstudio gives no score for your pronunciation and no overall level. Points reward practice, never your Dutch. The checks measure your progress here and give no recognised certificate.",
      fa: "Taalstudio برای تلفظت نمره نمی‌دهد و سطح کلی تعیین نمی‌کند. امتیازها به تمرین پاداش می‌دهند، نه به هلندی‌ات. آزمون‌ها پیشرفتت را در همین‌جا می‌سنجند و گواهی رسمی نمی‌دهند.",
    },
    dataTitle: { nl: "Wat we bewaren", en: "What we keep", fa: "آنچه نگه می‌داریم" },
    data: {
      nl: "We bewaren je antwoorden, je teksten en opnames, je bewaarde woorden en je voortgang, zodat je verder kunt waar je stopte.",
      en: "We keep your answers, your texts and recordings, your saved words and your progress, so you can continue where you stopped.",
      fa: "پاسخ‌ها، نوشته‌ها و ضبط‌های صدایت، واژه‌های ذخیره‌شده و پیشرفتت را نگه می‌داریم تا از همان‌جا که ماندی ادامه بدهی.",
    },
  },
  errors: {
    generic: {
      nl: "Dit lukte even niet. Probeer het opnieuw.",
      en: "That did not work just now. Please try again.",
      fa: "این کار فعلاً انجام نشد. دوباره امتحان کن.",
    },
    genericKept: {
      nl: "Dit lukte even niet. Je invoer blijft staan. Probeer het opnieuw.",
      en: "That did not work just now. What you entered stays here. Please try again.",
      fa: "این کار فعلاً انجام نشد. چیزی که وارد کردی سر جایش می‌ماند. دوباره امتحان کن.",
    },
    offline: {
      nl: "De verbinding viel weg. Probeer het zo opnieuw.",
      en: "The connection dropped. Try again in a moment.",
      fa: "اتصال قطع شد. کمی بعد دوباره امتحان کن.",
    },
    offlineKept: {
      nl: "De verbinding viel weg. Je invoer blijft staan; probeer het zo opnieuw.",
      en: "The connection dropped. What you entered stays here; try again in a moment.",
      fa: "اتصال قطع شد. چیزی که وارد کردی سر جایش می‌ماند؛ کمی بعد دوباره امتحان کن.",
    },
    serverAway: {
      nl: "De server antwoordt even niet. Probeer het zo opnieuw.",
      en: "The server is not answering right now. Try again in a moment.",
      fa: "سرور فعلاً پاسخ نمی‌دهد. کمی بعد دوباره امتحان کن.",
    },
    serverAwayKept: {
      nl: "De server antwoordt even niet. Je invoer blijft staan; probeer het zo opnieuw.",
      en: "The server is not answering right now. What you entered stays here; try again in a moment.",
      fa: "سرور فعلاً پاسخ نمی‌دهد. چیزی که وارد کردی سر جایش می‌ماند؛ کمی بعد دوباره امتحان کن.",
    },
    session: {
      nl: "Je sessie is verlopen. Meld je opnieuw aan en probeer verder te gaan.",
      en: "Your session has expired. Sign in again and carry on.",
      fa: "نشست تو تمام شده است. دوباره وارد شو و ادامه بده.",
    },
    forbidden: {
      nl: "Je hebt nog geen toegang tot deze actie.",
      en: "You do not have access to this action yet.",
      fa: "هنوز به این کار دسترسی نداری.",
    },
    checkLocked: {
      nl: "Je hebt nog geen toegang tot deze actie. Oefen voor een eindtoets eerst de vier vaardigheden van dit niveau.",
      en: "You do not have access to this action yet. Before a final check, first practise the four skills of this level.",
      fa: "هنوز به این کار دسترسی نداری. پیش از آزمون پایانی، اول چهار مهارت این سطح را تمرین کن.",
    },
    notFound: {
      nl: "Dit bestaat niet meer of nog niet. Ga terug en kies opnieuw.",
      en: "This no longer exists, or does not exist yet. Go back and choose again.",
      fa: "این مورد دیگر وجود ندارد یا هنوز ساخته نشده است. برگرد و دوباره انتخاب کن.",
    },
    tooLarge: {
      nl: "Dit is te groot om te versturen. Maak het korter en probeer opnieuw.",
      en: "This is too large to send. Make it shorter and try again.",
      fa: "این برای ارسال خیلی بزرگ است. کوتاه‌ترش کن و دوباره امتحان کن.",
    },
    invalid: {
      nl: "Controleer je invoer en probeer het opnieuw.",
      en: "Check what you entered and try again.",
      fa: "چیزی را که وارد کردی بررسی کن و دوباره امتحان کن.",
    },
    checkIncomplete: {
      nl: "Controleer of je alle onderdelen hebt ingevuld en een nieuwe opname hebt gemaakt.",
      en: "Check that you filled in every part and made a new recording.",
      fa: "بررسی کن که همه‌ی بخش‌ها را پر کرده‌ای و ضبط تازه‌ای انجام داده‌ای.",
    },
    limit: {
      nl: "Je oefenlimiet is bereikt. Probeer het later opnieuw.",
      en: "You have reached your practice limit. Try again later.",
      fa: "به سقف تمرینت رسیده‌ای. بعداً دوباره امتحان کن.",
    },
    limitKept: {
      nl: "Je oefenlimiet is bereikt. Je invoer blijft staan; probeer het later opnieuw.",
      en: "You have reached your practice limit. What you entered stays here; try again later.",
      fa: "به سقف تمرینت رسیده‌ای. چیزی که وارد کردی سر جایش می‌ماند؛ بعداً دوباره امتحان کن.",
    },
    modelAway: {
      nl: "De taalhulp is even niet bereikbaar. Probeer het zo opnieuw.",
      en: "The language help cannot be reached right now. Try again in a moment.",
      fa: "کمک زبانی فعلاً در دسترس نیست. کمی بعد دوباره امتحان کن.",
    },
    modelAwayKept: {
      nl: "De taalhulp is even niet bereikbaar. Je invoer blijft staan. Probeer het zo opnieuw.",
      en: "The language help cannot be reached right now. What you entered stays here. Try again in a moment.",
      fa: "کمک زبانی فعلاً در دسترس نیست. چیزی که وارد کردی سر جایش می‌ماند. کمی بعد دوباره امتحان کن.",
    },
    episodesBusy: {
      nl: "Er worden al twee afleveringen geschreven. Lees er eerst een.",
      en: "Two episodes are already being written. Read one of them first.",
      fa: "دو قسمت در حال نوشته شدن است. اول یکی از آن‌ها را بخوان.",
    },
    videosBusy: {
      nl: "Er worden al twee video's gemaakt. Bekijk er eerst een.",
      en: "Two videos are already being made. Watch one of them first.",
      fa: "دو ویدیو در حال ساخته شدن است. اول یکی از آن‌ها را ببین.",
    },
    notReady: {
      nl: "Dit is nog niet klaar. Probeer het zo opnieuw.",
      en: "This is not ready yet. Try again in a moment.",
      fa: "این هنوز آماده نیست. کمی بعد دوباره امتحان کن.",
    },
    alreadyAnswered: {
      nl: "Je hebt deze vragen al beantwoord.",
      en: "You have already answered these questions.",
      fa: "به این سؤال‌ها قبلاً پاسخ داده‌ای.",
    },
    sessionClosed: {
      nl: "Deze oefensessie is al afgesloten. Begin een nieuwe sessie.",
      en: "This practice session is already closed. Start a new session.",
      fa: "این جلسه‌ی تمرین قبلاً بسته شده است. یک جلسه‌ی تازه شروع کن.",
    },
    turnLimit: {
      nl: "Je hebt het maximum aantal beurten voor deze stap bereikt.",
      en: "You have reached the maximum number of turns for this step.",
      fa: "به بیشترین تعداد نوبت برای این مرحله رسیده‌ای.",
    },
    noRetry: {
      nl: "Deze toets kun je maar één keer doen. Je eerste poging telt.",
      en: "You can take this check only once. Your first attempt counts.",
      fa: "این آزمون را فقط یک بار می‌توانی بدهی. تلاش اولت حساب می‌شود.",
    },
    nothingToRetry: {
      nl: "Er is geen gemiste vraag meer om opnieuw te oefenen.",
      en: "There is no missed question left to practise again.",
      fa: "دیگر سؤال جاافتاده‌ای برای تمرین دوباره نمانده است.",
    },
    inProgress: {
      nl: "Je antwoord wordt nog verwerkt. Probeer het zo opnieuw.",
      en: "Your answer is still being processed. Try again in a moment.",
      fa: "پاسخت هنوز در حال بررسی است. کمی بعد دوباره امتحان کن.",
    },
    usageUnavailable: {
      nl: "Deze oefening kan tijdelijk niet starten. Probeer het straks opnieuw.",
      en: "This exercise cannot start right now. Please try again later.",
      fa: "این تمرین فعلاً نمی‌تواند شروع شود. کمی بعد دوباره امتحان کن.",
    },
    paidAlreadyStarted: {
      nl: "Deze poging is al gestart en kan niet nog eens worden verstuurd. Wacht even voordat je een nieuwe poging begint.",
      en: "This attempt has already started and cannot be sent again. Wait a moment before starting a new attempt.",
      fa: "این تلاش قبلاً شروع شده و نمی‌توان آن را دوباره فرستاد. پیش از شروع تلاش تازه کمی صبر کن.",
    },
    profilePending: {
      nl: "Je profiel wordt nog klaargezet. Vernieuw de pagina en probeer het opnieuw.",
      en: "Your profile is still being prepared. Refresh the page and try again.",
      fa: "نمایه‌ات هنوز در حال آماده شدن است. صفحه را تازه کن و دوباره امتحان کن.",
    },
    loadFailed: {
      nl: "Dit kon niet worden geladen. Probeer het zo opnieuw.",
      en: "This could not be loaded. Try again in a moment.",
      fa: "این بارگذاری نشد. کمی بعد دوباره امتحان کن.",
    },
    evidenceShort: {
      nl: "Maak eerst deze oefening om feedback te krijgen.",
      en: "Do this exercise first to get feedback.",
      fa: "اول این تمرین را انجام بده تا بازخورد بگیری.",
    },
  },
  failures: {
    episodeAllowanceTitle: {
      nl: "De schrijver heeft vandaag genoeg geschreven.",
      en: "The writer has written enough for today.",
      fa: "نویسنده امروز به اندازه‌ی کافی نوشته است.",
    },
    episodeQualityTitle: {
      nl: "Deze aflevering haalde de controle niet.",
      en: "This episode did not pass the check.",
      fa: "این قسمت در بررسی قبول نشد.",
    },
    episodeAwayTitle: {
      nl: "De schrijver is even niet bereikbaar.",
      en: "The writer cannot be reached right now.",
      fa: "نویسنده فعلاً در دسترس نیست.",
    },
    episodeQuality: {
      nl: "De tekst haalde de automatische controle niet, ook niet na een tweede poging. Een nieuwe poging gebruikt dezelfde personages.",
      en: "The text did not pass the automatic check, not even on a second attempt. A new attempt uses the same characters.",
      fa: "متن حتی پس از تلاش دوم هم در بررسی خودکار قبول نشد. تلاش تازه از همان شخصیت‌ها استفاده می‌کند.",
    },
    episodeAllowance: {
      nl: "Je dagelijkse limiet voor modelgebruik is bereikt. Probeer het morgen opnieuw of herhaal vandaag je woorden.",
      en: "You have reached your daily limit for the language model. Try again tomorrow, or review your words today.",
      fa: "به سقف روزانه‌ی استفاده از مدل زبانی رسیده‌ای. فردا دوباره امتحان کن یا امروز واژه‌هایت را مرور کن.",
    },
    paidNotApproved: {
      nl: "Betaald modelgebruik is in deze omgeving niet ingeschakeld.",
      en: "Paid model use is not switched on in this environment.",
      fa: "استفاده‌ی پولی از مدل در این محیط فعال نیست.",
    },
    writerAway: {
      nl: "De schrijver was even niet bereikbaar. Probeer het opnieuw.",
      en: "The writer could not be reached just now. Please try again.",
      fa: "نویسنده لحظه‌ای در دسترس نبود. دوباره امتحان کن.",
    },
    writerAwayDeveloper: {
      nl: "Controleer of het taalmodel draait (Instellingen › Technische ondersteuning) en probeer opnieuw.",
      en: "Check that the language model is running (Settings › Technical support) and try again.",
      fa: "بررسی کن که مدل زبانی در حال اجرا باشد (تنظیمات › پشتیبانی فنی) و دوباره امتحان کن.",
    },
    writerLimit: {
      nl: "Je dagelijkse limiet voor de schrijver is bereikt. Morgen schrijft hij verder.",
      en: "You have reached your daily limit for the writer. It will continue writing tomorrow.",
      fa: "به سقف روزانه‌ی نویسنده رسیده‌ای. فردا دوباره می‌نویسد.",
    },
    videoAllowance: {
      nl: "De schrijver heeft vandaag genoeg geschreven. Probeer het morgen opnieuw.",
      en: "The writer has written enough for today. Try again tomorrow.",
      fa: "نویسنده امروز به اندازه‌ی کافی نوشته است. فردا دوباره امتحان کن.",
    },
    videoTime: {
      nl: "Je dagelijkse videotijd is op. Morgen kan er weer een video gemaakt worden.",
      en: "Your daily video time is used up. A new video can be made tomorrow.",
      fa: "زمان روزانه‌ات برای ساخت ویدیو تمام شده است. فردا دوباره می‌شود ویدیو ساخت.",
    },
    videoQuality: {
      nl: "Het script haalde de automatische controle niet, ook niet na een tweede poging.",
      en: "The script did not pass the automatic check, not even on a second attempt.",
      fa: "متن ویدیو حتی پس از تلاش دوم هم در بررسی خودکار قبول نشد.",
    },
    videoRender: {
      nl: "Het maken van de video is mislukt. Het script is bewaard; een nieuwe poging gebruikt het opnieuw.",
      en: "Making the video failed. The script is kept; a new attempt uses it again.",
      fa: "ساختن ویدیو انجام نشد. متن ذخیره شده است؛ تلاش تازه دوباره از آن استفاده می‌کند.",
    },
    videoTooLong: {
      nl: "Het script was te lang voor één video.",
      en: "The script was too long for one video.",
      fa: "متن برای یک ویدیو خیلی طولانی بود.",
    },
    videoAway: {
      nl: "De schrijver of de videodienst was even niet bereikbaar.",
      en: "The writer or the video service could not be reached just now.",
      fa: "نویسنده یا سرویس ویدیو لحظه‌ای در دسترس نبود.",
    },
  },
} as const satisfies Record<string, Record<string, Copy>>;

export type UiCopyGroup = keyof typeof uiCopy;
export type UiCopyKey<G extends UiCopyGroup> = keyof (typeof uiCopy)[G];

/** Which batch every entry belongs to, and which entry a filled copy came from (for the Persian review). */
const batches = new WeakMap<object, string>();
const origins = new WeakMap<object, Copy>();
/** A server component hands its props to the client as copies, not the same objects; the text still matches. */
const byText = new Map<string, string>();
const textOf = (copy: Copy) => [copy.nl, copy.en, copy.fa].join("\u0000");

/** Records the batch name of each entry; lib/client/persian-review.ts registers every batch once. */
export function registerBatch(name: string, entries: Record<string, Copy>): void {
  for (const copy of Object.values(entries)) {
    batches.set(copy, name);
    if (!byText.has(textOf(copy))) byText.set(textOf(copy), name);
  }
}

/** The batch a copy entry (or a copy made from one with `fill`, or a serialized copy) belongs to. */
export function batchOf(copy: Copy): string | undefined {
  return batches.get(copy) ?? batches.get(origins.get(copy) ?? {}) ?? byText.get(textOf(copy));
}

/** Fills `{name}` placeholders in every language of a copy entry. */
export function fill(copy: Copy, values: Record<string, string | number>): Copy {
  const apply = (text: string) =>
    text.replace(/\{(\w+)\}/g, (match, name: string) => (name in values ? String(values[name]) : match));
  const filled = { nl: apply(copy.nl), en: apply(copy.en), fa: apply(copy.fa) };
  origins.set(filled, origins.get(copy) ?? copy);
  return filled;
}

/** Every entry as a flat list for tests and tooling. */
export function allCopy(): { key: string; copy: Copy }[] {
  return Object.entries(uiCopy).flatMap(([group, entries]) =>
    Object.entries(entries).map(([name, copy]) => ({ key: `${group}.${name}`, copy })),
  );
}

