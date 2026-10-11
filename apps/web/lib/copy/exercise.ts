import type { Copy } from "@/lib/ui-copy";

/** Interface copy of practice sessions (components/exercise, app/oefenen), in Dutch with English and Persian. */
export const exerciseCopy = {
  // app/oefenen/page.tsx and the session frame
  pageTitle: { nl: "Oefenen", en: "Practice", fa: "تمرین" },
  progressLabel: { nl: "Voortgang van je oefening", en: "Progress of your practice", fa: "پیشرفت تمرینت" },
  progress: { nl: "{closed} van {total}", en: "{closed} of {total}", fa: "{closed} از {total}" },
  exit: { nl: "Stoppen", en: "Stop", fa: "توقف" },
  loading: {
    nl: "Je oefening wordt klaargezet.",
    en: "Your practice is being set up.",
    fa: "تمرینت آماده می‌شود.",
  },
  loadFailed: {
    nl: "Je oefening kon niet worden geladen.",
    en: "Your practice could not be loaded.",
    fa: "تمرینت بارگذاری نشد.",
  },
  notReady: {
    nl: "Op dit niveau is er nog te weinig om mee te oefenen.",
    en: "There is not enough to practise with at this level yet.",
    fa: "در این سطح هنوز مطلب کافی برای تمرین نیست.",
  },
  resumed: {
    nl: "Je gaat verder waar je gebleven was.",
    en: "You continue where you left off.",
    fa: "از همان جایی که مانده بودی ادامه می‌دهی.",
  },
  keysHint: {
    nl: "Kies met de toetsen 1 tot 4 en bevestig met Enter.",
    en: "Choose with the keys 1 to 4 and confirm with Enter.",
    fa: "با کلیدهای ۱ تا ۴ انتخاب کن و با Enter تأیید کن.",
  },

  // the questions
  askMeaning: {
    nl: "Wat betekent dit woord?",
    en: "What does this word mean?",
    fa: "این واژه چه معنایی دارد؟",
  },
  askTerm: {
    nl: "Welk Nederlands woord past bij deze betekenis?",
    en: "Which Dutch word fits this meaning?",
    fa: "کدام واژه‌ی هلندی با این معنا جور است؟",
  },
  askDefinition: {
    nl: "Welke uitleg past bij dit woord?",
    en: "Which explanation fits this word?",
    fa: "کدام توضیح با این واژه جور است؟",
  },
  askQuestion: {
    nl: "Kies het juiste antwoord.",
    en: "Choose the right answer.",
    fa: "پاسخ درست را انتخاب کن.",
  },
  askCloze: {
    nl: "Welk woord past in de zin?",
    en: "Which word fits in the sentence?",
    fa: "کدام واژه در جمله جا می‌افتد؟",
  },
  askOdd: {
    nl: "Welk woord hoort er niet bij?",
    en: "Which word does not belong?",
    fa: "کدام واژه به بقیه تعلق ندارد؟",
  },
  oddTopic: {
    nl: "Drie woorden horen bij dit onderwerp:",
    en: "Three words belong to this topic:",
    fa: "سه واژه به این موضوع تعلق دارند:",
  },
  blank: { nl: "open plek", en: "blank", fa: "جای خالی" },
  askPairs: {
    nl: "Welke betekenis hoort bij welk woord?",
    en: "Which meaning goes with which word?",
    fa: "کدام معنا به کدام واژه تعلق دارد؟",
  },
  pairsHint: {
    nl: "Kies een woord en daarna zijn betekenis. Kies een paar opnieuw om het te veranderen.",
    en: "Choose a word, then its meaning. Choose a pair again to change it.",
    fa: "یک واژه را انتخاب کن و بعد معنایش را. برای تغییر یک جفت، دوباره آن را انتخاب کن.",
  },
  words: { nl: "Woorden", en: "Words", fa: "واژه‌ها" },
  meanings: { nl: "Betekenissen", en: "Meanings", fa: "معناها" },
  goesWith: { nl: "hoort bij", en: "goes with", fa: "جفت است با" },
  askDeHet: { nl: "De of het?", en: "De or het?", fa: "de یا het؟" },
  askBuild: { nl: "Maak de zin.", en: "Build the sentence.", fa: "جمله را بساز." },
  buildHint: {
    nl: "Kies de stukjes in de goede volgorde. Kies een stukje in je zin om het terug te leggen.",
    en: "Choose the pieces in the right order. Choose a piece in your sentence to put it back.",
    fa: "تکه‌ها را به ترتیب درست انتخاب کن. برای برگرداندن یک تکه، آن را در جمله‌ات انتخاب کن.",
  },
  yourSentence: { nl: "Jouw zin", en: "Your sentence", fa: "جمله‌ی تو" },
  pieces: { nl: "Stukjes", en: "Pieces", fa: "تکه‌ها" },
  removePiece: { nl: "Leg {piece} terug", en: "Put {piece} back", fa: "{piece} را برگردان" },
  askOrder: {
    nl: "Zet de zinnen in de goede volgorde.",
    en: "Put the sentences in the right order.",
    fa: "جمله‌ها را به ترتیب درست بچین.",
  },
  moveUp: { nl: "Zet zin {n} hoger", en: "Move sentence {n} up", fa: "جمله‌ی {n} را بالاتر ببر" },
  moveDown: { nl: "Zet zin {n} lager", en: "Move sentence {n} down", fa: "جمله‌ی {n} را پایین‌تر ببر" },
  finishFirst: { nl: "Maak eerst alles af.", en: "Finish everything first.", fa: "اول همه را کامل کن." },
  rightOrder: { nl: "De goede volgorde", en: "The right order", fa: "ترتیب درست" },
  rightSentence: { nl: "De goede zin", en: "The right sentence", fa: "جمله‌ی درست" },
  tilesDiffer: { nl: "Hier ging het anders:", en: "Here it went another way:", fa: "از اینجا متفاوت شد:" },
  orderPlaced: { nl: "Stond op plaats {m}", en: "Was in place {m}", fa: "در جای {m} بود" },

  // answering
  skip: { nl: "Ik weet het niet", en: "I don't know", fa: "نمی‌دانم" },
  chooseFirst: {
    nl: "Kies eerst een antwoord.",
    en: "Choose an answer first.",
    fa: "اول یک پاسخ انتخاب کن.",
  },
  answerFailed: {
    nl: "Je antwoord kon niet worden verstuurd.",
    en: "Your answer could not be sent.",
    fa: "پاسخت فرستاده نشد.",
  },
  sendAgain: { nl: "Verstuur opnieuw", en: "Send again", fa: "دوباره بفرست" },

  // typed answers (typed cloze, typed recall, dictation)
  askClozeTyped: {
    nl: "Typ het woord dat in de zin past.",
    en: "Type the word that fits in the sentence.",
    fa: "واژه‌ای را که در جمله جا می‌افتد تایپ کن.",
  },
  askClozeTypedWords: {
    nl: "Typ de woorden die in de zin passen.",
    en: "Type the words that fit in the sentence.",
    fa: "واژه‌هایی را که در جمله جا می‌افتند تایپ کن.",
  },
  askRecall: { nl: "Typ het Nederlandse woord.", en: "Type the Dutch word.", fa: "واژه‌ی هلندی را تایپ کن." },
  askRecallWords: {
    nl: "Typ de Nederlandse woorden.",
    en: "Type the Dutch words.",
    fa: "واژه‌های هلندی را تایپ کن.",
  },
  askDictation: {
    nl: "Luister en typ wat je hoort.",
    en: "Listen and type what you hear.",
    fa: "گوش بده و آنچه را می‌شنوی تایپ کن.",
  },
  wordCount: { nl: "Aantal woorden: {n}", en: "Number of words: {n}", fa: "تعداد واژه‌ها: {n}" },
  showHint: { nl: "Toon een hint", en: "Show a hint", fa: "یک راهنمایی نشان بده" },
  hintWord: {
    nl: "Het begint met {first} en heeft {letters} letters.",
    en: "It starts with {first} and has {letters} letters.",
    fa: "با {first} شروع می‌شود و {letters} حرف دارد.",
  },
  hintWords: {
    nl: "Het begint met {first}. Het zijn {count} woorden, met {letters} letters.",
    en: "It starts with {first}. It is {count} words, with {letters} letters.",
    fa: "با {first} شروع می‌شود. {count} واژه است، با {letters} حرف.",
  },
  typeFirst: { nl: "Typ eerst een antwoord.", en: "Type an answer first.", fa: "اول یک پاسخ تایپ کن." },
  noteAccents: {
    nl: "De accenten waren anders; dat telt hier niet mee.",
    en: "The accents were different; that does not count here.",
    fa: "نشانه‌های تلفظ جا افتاده بود؛ این به حساب نمی‌آید.",
  },
  notePunctuation: {
    nl: "Leestekens tellen niet mee.",
    en: "Punctuation does not count.",
    fa: "علامت‌های نگارشی به حساب نمی‌آیند.",
  },
  noteArticleMissing: {
    nl: "Het lidwoord ontbrak; dat mag hier.",
    en: "The article was missing; that is fine here.",
    fa: "حرف تعریف جا افتاده بود؛ اینجا اشکالی ندارد.",
  },
  noteArticleExtra: {
    nl: "Er stond een lidwoord bij dat hier niet hoort.",
    en: "There was an article that does not belong here.",
    fa: "یک حرف تعریف اضافه بود که اینجا لازم نیست.",
  },
  noteArticle: {
    nl: "Het lidwoord is anders: let op de of het.",
    en: "The article is different: watch de or het.",
    fa: "حرف تعریف فرق دارد: به de یا het دقت کن.",
  },
  noteSpelling: { nl: "Een kleine tikfout.", en: "A small typo.", fa: "یک غلط تایپی کوچک." },
  noteMissingWord: {
    nl: "Er ontbreekt een klein woord.",
    en: "A small word is missing.",
    fa: "یک واژه‌ی کوچک جا افتاده است.",
  },
  noteExtraWord: {
    nl: "Er staat een klein woord te veel.",
    en: "There is one small word too many.",
    fa: "یک واژه‌ی کوچک اضافه است.",
  },
  diffMissing: { nl: "ontbreekt:", en: "missing:", fa: "جا افتاده:" },
  diffExtra: { nl: "te veel:", en: "too many:", fa: "اضافه:" },
  diffTyped: { nl: "jij typte:", en: "you typed:", fa: "تو تایپ کردی:" },
  diffRight: { nl: "juist:", en: "right:", fa: "درست:" },
  override: { nl: "Mijn antwoord klopt ook", en: "My answer is right too", fa: "پاسخ من هم درست است" },
  accepted: { nl: "Je antwoord telt", en: "Your answer counts", fa: "پاسخت حساب می‌شود" },
  overrideFailed: {
    nl: "Dat kon niet worden bewaard.",
    en: "That could not be saved.",
    fa: "این ذخیره نشد.",
  },

  // listening and speaking
  askListen: { nl: "Welk woord hoor je?", en: "Which word do you hear?", fa: "کدام واژه را می‌شنوی؟" },
  askShadow: {
    nl: "Luister en zeg het na.",
    en: "Listen and say it after the voice.",
    fa: "گوش بده و بعد از صدا تکرارش کن.",
  },
  audioPlay: { nl: "Luister", en: "Listen", fa: "گوش بده" },
  audioStop: { nl: "Stop", en: "Stop", fa: "توقف" },
  audioSignin: {
    nl: "Meld je opnieuw aan om te luisteren.",
    en: "Sign in again to listen.",
    fa: "برای شنیدن دوباره وارد حساب شو.",
  },
  audioLimit: {
    nl: "Je luistertijd is op. Kies 'Ik kan nu niet luisteren'.",
    en: "Your listening time is used up. Choose 'I can't listen now'.",
    fa: "زمان شنیدنت تمام شده است. «الان نمی‌توانم گوش بدهم» را انتخاب کن.",
  },
  audioBlocked: {
    nl: "Je browser vraagt nog een tik. Druk opnieuw op Luister.",
    en: "Your browser needs another tap. Press Listen again.",
    fa: "مرورگر به یک لمس دیگر نیاز دارد. دوباره «گوش بده» را بزن.",
  },
  audioUnavailable: {
    nl: "Het geluid speelt nu niet. Probeer opnieuw.",
    en: "The sound is not playing now. Try again.",
    fa: "صدا الان پخش نمی‌شود. دوباره تلاش کن.",
  },
  audioTestTone: {
    nl: "Testtoon: in deze omgeving spreekt nog geen echte stem.",
    en: "Test tone: no real voice speaks in this environment yet.",
    fa: "صدای آزمایشی: در این محیط هنوز صدای واقعی پخش نمی‌شود.",
  },
  cannotListen: { nl: "Ik kan nu niet luisteren", en: "I can't listen now", fa: "الان نمی‌توانم گوش بدهم" },
  cannotSpeak: { nl: "Ik kan nu niet spreken", en: "I can't speak now", fa: "الان نمی‌توانم صحبت کنم" },
  recordStart: { nl: "Neem op", en: "Record", fa: "ضبط کن" },
  recordStop: { nl: "Stop met opnemen", en: "Stop recording", fa: "ضبط را متوقف کن" },
  recordListening: { nl: "We luisteren…", en: "Listening…", fa: "در حال شنیدن…" },
  recordHow: {
    nl: "Druk op Neem op, zeg de zin en druk dan op stop. Met een koptelefoon gaat het het best.",
    en: "Press Record, say the sentence, then press stop. Headphones work best.",
    fa: "ضبط را بزن، جمله را بگو و بعد توقف را بزن. با هدفون بهتر کار می‌کند.",
  },
  recordFailed: {
    nl: "De microfoon werkt niet. Probeer opnieuw of kies 'Ik kan nu niet spreken'.",
    en: "The microphone is not working. Try again or choose 'I can't speak now'.",
    fa: "میکروفون کار نمی‌کند. دوباره تلاش کن یا «الان نمی‌توانم صحبت کنم» را انتخاب کن.",
  },
  recordUnsupported: {
    nl: "Deze browser kan niet opnemen. Kies 'Ik kan nu niet spreken'.",
    en: "This browser cannot record. Choose 'I can't speak now'.",
    fa: "این مرورگر نمی‌تواند ضبط کند. «الان نمی‌توانم صحبت کنم» را انتخاب کن.",
  },
  recordSendFailed: {
    nl: "Je opname kon niet worden verstuurd. Neem opnieuw op.",
    en: "Your recording could not be sent. Record again.",
    fa: "ضبطت فرستاده نشد. دوباره ضبط کن.",
  },
  weHeard: { nl: "Wat we hoorden", en: "What we heard", fa: "آنچه شنیدیم" },
  heardNothing: { nl: "nog niets", en: "nothing yet", fa: "هنوز هیچ" },
  heard: { nl: "Gehoord", en: "Heard", fa: "شنیده شد" },
  tryOnceMore: {
    nl: "Je mag het meteen nog een keer proberen.",
    en: "You can try once more right away.",
    fa: "می‌توانی همین حالا یک بار دیگر امتحان کنی.",
  },

  // the intro card
  introTitle: { nl: "Nieuwe woorden", en: "New words", fa: "واژه‌های تازه" },
  introLead: {
    nl: "Lees ze rustig. Daarna oefen je ermee.",
    en: "Read them calmly. Then you practise with them.",
    fa: "با حوصله بخوانشان. بعد با آن‌ها تمرین می‌کنی.",
  },
  introDone: { nl: "Begin met oefenen", en: "Start practising", fa: "تمرین را شروع کن" },

  // feedback
  incorrect: { nl: "Nog niet", en: "Not yet", fa: "هنوز نه" },
  skipped: { nl: "Overgeslagen", en: "Skipped", fa: "رد شد" },
  comesBack: {
    nl: "Deze vraag komt aan het einde nog één keer terug.",
    en: "This question comes back once more at the end.",
    fa: "این سؤال در پایان یک بار دیگر برمی‌گردد.",
  },
  rightAnswer: { nl: "Het juiste antwoord", en: "The right answer", fa: "پاسخ درست" },
  checkExpected: {
    nl: "Wat de controle verwachtte",
    en: "What the check expected",
    fa: "آنچه بررسی انتظار داشت",
  },
  yourAnswer: { nl: "Jouw antwoord", en: "Your answer", fa: "پاسخ تو" },
  oddBelongs: {
    nl: "Het andere woord hoort bij:",
    en: "The odd word belongs to:",
    fa: "واژه‌ی متفاوت مربوط است به:",
  },
  pointEarned: { nl: "+1 punt", en: "+1 point", fa: "+۱ امتیاز" },
  continue: { nl: "Verder", en: "Continue", fa: "ادامه" },

  // reporting an exercise
  report: { nl: "Meld een probleem", en: "Report a problem", fa: "گزارش یک مشکل" },
  reportTitle: { nl: "Klopt er iets niet?", en: "Something not right?", fa: "چیزی درست نیست؟" },
  reportLead: {
    nl: "Zeg wat er mis is met deze oefening. Je antwoord en je punten blijven gewoon staan.",
    en: "Say what is wrong with this exercise. Your answer and your points stay as they are.",
    fa: "بگو این تمرین چه مشکلی دارد. پاسخ و امتیازهایت همان‌طور که هست می‌ماند.",
  },
  reasonLegend: { nl: "Wat is er mis?", en: "What is wrong?", fa: "مشکل چیست؟" },
  reasonAnswerWrong: {
    nl: "Het juiste antwoord klopt niet",
    en: "The right answer is wrong",
    fa: "پاسخ درست، درست نیست",
  },
  reasonUnclear: { nl: "De vraag is niet duidelijk", en: "The question is unclear", fa: "سؤال روشن نیست" },
  reasonSound: {
    nl: "Het geluid is fout of onduidelijk",
    en: "The sound is wrong or unclear",
    fa: "صدا اشتباه یا نامفهوم است",
  },
  reasonOther: { nl: "Iets anders", en: "Something else", fa: "چیز دیگری" },
  reportNote: {
    nl: "Wil je nog iets toelichten? Dat mag leeg blijven.",
    en: "Anything to add? You may leave this empty.",
    fa: "توضیح دیگری داری؟ می‌توانی خالی بگذاری.",
  },
  reportSend: { nl: "Verstuur", en: "Send", fa: "بفرست" },
  reportSent: {
    nl: "Bedankt. We bekijken deze oefening.",
    en: "Thank you. We will look at this exercise.",
    fa: "ممنون. این تمرین را بررسی می‌کنیم.",
  },
  reportFailed: {
    nl: "Je melding kon niet worden verstuurd.",
    en: "Your report could not be sent.",
    fa: "گزارشت فرستاده نشد.",
  },

  // stopping
  exitTitle: { nl: "Stoppen met oefenen?", en: "Stop practising?", fa: "تمرین را متوقف می‌کنی؟" },
  exitLead: {
    nl: "Je antwoorden en punten zijn bewaard. Rond nu af om te zien wat je gedaan hebt, of ga terug naar Vandaag.",
    en: "Your answers and points are saved. Finish now to see what you have done, or go back to Today.",
    fa: "پاسخ‌ها و امتیازهایت ذخیره شده‌اند. همین حالا تمام کن تا ببینی چه کرده‌ای، یا به امروز برگرد.",
  },
  exitLater: { nl: "Naar Vandaag", en: "To Today", fa: "به امروز" },
  exitFinish: { nl: "Rond nu af", en: "Finish now", fa: "همین حالا تمام کن" },
  keepGoing: { nl: "Blijf oefenen", en: "Keep practising", fa: "به تمرین ادامه بده" },

  // the summary
  summaryTitle: { nl: "Je oefening is klaar", en: "Your practice is done", fa: "تمرینت تمام شد" },
  summaryAnswered: {
    nl: "Je hebt {answered} van de {total} vragen beantwoord.",
    en: "You answered {answered} of the {total} questions.",
    fa: "به {answered} سؤال از {total} سؤال پاسخ دادی.",
  },
  summaryFirstTry: { nl: "Meteen juist", en: "Right first time", fa: "همان بار اول درست" },
  summaryFixed: { nl: "Juist bij de tweede keer", en: "Right the second time", fa: "درست در بار دوم" },
  summaryPoints: { nl: "Punten verdiend", en: "Points earned", fa: "امتیازهای گرفته‌شده" },
  summaryBonus: {
    nl: "Waarvan {points} extra voor een hele sessie.",
    en: "Including {points} extra for a whole session.",
    fa: "شامل {points} امتیاز اضافه برای یک جلسه‌ی کامل.",
  },
  summaryMissed: {
    nl: "Deze oefen je best nog eens",
    en: "Worth practising again",
    fa: "بهتر است این‌ها را دوباره تمرین کنی",
  },
  summarySuggest: { nl: "Bewaar in je woorden", en: "Save to your words", fa: "در واژه‌هایت ذخیره کن" },
  summarySuggestLead: {
    nl: "Woorden die je nog niet kende. Bewaar je ze, dan komen ze terug bij Woorden.",
    en: "Words you did not know yet. Save them and they come back in Words.",
    fa: "واژه‌هایی که هنوز نمی‌دانستی. اگر ذخیره‌شان کنی، در بخش واژه‌ها برمی‌گردند.",
  },
  saveWord: { nl: "Bewaar {term}", en: "Save {term}", fa: "{term} را ذخیره کن" },
  saveFailed: { nl: "Bewaren lukte niet.", en: "Saving did not work.", fa: "ذخیره نشد." },
  finishFailed: {
    nl: "Je resultaat kon niet worden bewaard.",
    en: "Your result could not be saved.",
    fa: "نتیجه‌ات ذخیره نشد.",
  },
  again: { nl: "Nog een oefening", en: "Another practice", fa: "یک تمرین دیگر" },
  stoppedElsewhere: {
    nl: "Deze oefening is al gestopt, bijvoorbeeld in een ander venster.",
    en: "This practice has already stopped, for example in another window.",
    fa: "این تمرین پیش‌تر متوقف شده است، مثلاً در پنجره‌ای دیگر.",
  },
  backToday: { nl: "Terug naar Vandaag", en: "Back to Today", fa: "برگرد به امروز" },

  // the entry on Today while an episode is written
  waitTitle: { nl: "Oefen terwijl je wacht", en: "Practise while you wait", fa: "تا منتظری، تمرین کن" },
  waitLead: {
    nl: "Een paar korte vragen over woorden van je niveau, alleen tikken.",
    en: "A few short questions on words at your level, tapping only.",
    fa: "چند سؤال کوتاه درباره‌ی واژه‌های سطح تو، فقط با لمس.",
  },
} as const satisfies Record<string, Copy>;
