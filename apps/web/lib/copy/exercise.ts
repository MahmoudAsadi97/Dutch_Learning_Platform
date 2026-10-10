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
