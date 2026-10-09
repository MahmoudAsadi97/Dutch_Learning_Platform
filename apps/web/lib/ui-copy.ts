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
    offline: { nl: "Geen verbinding", en: "No connection", fa: "اتصال نیست" },
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
      fa: "به هدف روزانه رسیدی. هر چه بیشتر بخوانی، اضافه است.",
    },
    streak: { nl: "{days} dagen op rij", en: "{days} days in a row", fa: "{days} روز پشت سر هم" },
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
      en: "Here you learn Dutch as it is spoken in Belgium: a piece of story every day, words you keep, and speaking and writing with explanations.",
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
      en: "You only choose a starting point. It does not pass you for anything, and you can always change it later.",
      fa: "فقط نقطه‌ی شروع را انتخاب می‌کنی. با این انتخاب هیچ مرحله‌ای را قبول نمی‌شوی و بعداً همیشه می‌توانی عوضش کنی.",
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
      fa: "خرید، قرار گذاشتن، تعریف کردن از روزت.",
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
      fa: "برای دوره‌ی ادغام (inburgering)",
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
      fa: "برای آنچه می‌گویی و می‌نویسی توضیح می‌گیری، هرگز نمره‌ای برای تلفظت.",
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
      nl: "Je eerste aflevering verschijnt op Vandaag zodra ze klaar is.",
      en: "Your first episode appears on Today as soon as it is ready.",
      fa: "اولین قسمتت به‌محض آماده شدن در «امروز» نمایش داده می‌شود.",
    },
    alphabetTitle: { nl: "Het alfabet", en: "The alphabet", fa: "الفبا" },
    wordsTitle: { nl: "Je eerste woorden", en: "Your first words", fa: "اولین واژه‌هایت" },
    wordsIntro: {
      nl: "Kies de woorden die je wilt bewaren. Je herhaalt ze later onder Woorden.",
      en: "Choose the words you want to keep. You review them later under Words.",
      fa: "واژه‌هایی را که می‌خواهی نگه داری انتخاب کن. بعداً در بخش «واژه‌ها» مرورشان می‌کنی.",
    },
    wordsSave: { nl: "Bewaar {count} woorden", en: "Keep {count} words", fa: "{count} واژه را نگه دار" },
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
      fa: "یک مدل زبانی این متن را نوشته است. رایانه طول، سطح و انسجام آن را بررسی کرده، اما هنوز یک معلم زبان آن را بازبینی نکرده است. اشتباه‌های کوچک ممکن است.",
    },
    videoLabel: {
      nl: "Taalmodel en computerstem",
      en: "Language model and computer voice",
      fa: "مدل زبانی و صدای رایانه‌ای",
    },
    video: {
      nl: "Een taalmodel schrijft het script; de stem en de presentator maakt de computer, het is geen echte persoon. De ondertitels komen uit de gesproken tekst. Een taaldocent heeft het script nog niet nagekeken.",
      en: "A language model writes the script; the computer makes the voice and the presenter, it is not a real person. The subtitles come from the spoken text. A language teacher has not reviewed the script yet.",
      fa: "یک مدل زبانی متن را می‌نویسد؛ صدا و مجری را رایانه می‌سازد و شخص واقعی نیست. زیرنویس‌ها از متن گفته‌شده می‌آیند. هنوز یک معلم زبان متن را بازبینی نکرده است.",
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
      fa: "این بازخورد از یک مدل زبانی می‌آید و معلمی آن را بررسی نکرده است. درباره‌ی چیزی است که نوشتی یا گفتی، هرگز درباره‌ی تلفظت، و نمره‌ای نمی‌دهد.",
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
      en: "How what you read, hear and practise in Taalstudio is made, and what it does and does not say.",
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
      nl: "Je verhalen, de scripts van je video's en de feedback op je teksten komen van een taalmodel. De computer controleert lengte, niveau en woordenschat; een docent kijkt ze niet na. Kleine fouten zijn mogelijk.",
      en: "Your stories, the scripts of your videos and the feedback on your texts come from a language model. The computer checks length, level and vocabulary; a teacher does not review them. Small mistakes are possible.",
      fa: "داستان‌هایت، متن ویدیوهایت و بازخورد نوشته‌هایت از یک مدل زبانی می‌آیند. رایانه طول، سطح و واژگان را بررسی می‌کند؛ معلمی آن‌ها را بازبینی نمی‌کند. اشتباه‌های کوچک ممکن است.",
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
} as const satisfies Record<string, Record<string, Copy>>;

export type UiCopyGroup = keyof typeof uiCopy;
export type UiCopyKey<G extends UiCopyGroup> = keyof (typeof uiCopy)[G];

/** Which batch every entry belongs to, and which entry a filled copy came from (for the Persian review). */
const batches = new WeakMap<object, string>();
const origins = new WeakMap<object, Copy>();

/** Records the batch name of each entry; lib/client/persian-review.ts registers every batch once. */
export function registerBatch(name: string, entries: Record<string, Copy>): void {
  for (const copy of Object.values(entries)) batches.set(copy, name);
}

/** The batch a copy entry (or a copy made from one with `fill`) belongs to. */
export function batchOf(copy: Copy): string | undefined {
  return batches.get(copy) ?? batches.get(origins.get(copy) ?? {});
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
