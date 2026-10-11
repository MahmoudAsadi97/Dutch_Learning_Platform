import type { Copy } from "@/lib/ui-copy";

/** Interface copy of a practice topic's start and task (components/SkillTopicPractice), Dutch with glosses. */
export const topicsCopy = {
  reviewOf: { nl: "Herhaling van {stage}", en: "Review of {stage}", fa: "مرور {stage}" },
  reviewLead: {
    nl: "Dit kwam al voor bij {stage}. Nog eens oefenen helpt je het vlot te begrijpen.",
    en: "This already came up at {stage}. Practising it again helps you understand it with ease.",
    fa: "این پیش‌تر در {stage} آمده بود. تمرین دوباره کمک می‌کند آن را راحت بفهمی.",
  },
  startTitle: { nl: "Zo werkt het", en: "How it works", fa: "این‌طور کار می‌کند" },
  stepRead: {
    nl: "Je leest een korte tekst. Je kunt elke zin laten voorlezen.",
    en: "You read a short text. You can have each sentence read aloud.",
    fa: "یک متن کوتاه می‌خوانی. می‌توانی هر جمله را بشنوی.",
  },
  stepListen: {
    nl: "Je luistert naar een kort fragment, zo vaak als je wilt.",
    en: "You listen to a short fragment, as often as you like.",
    fa: "به یک قطعه‌ی کوتاه گوش می‌دهی، هر چند بار که بخواهی.",
  },
  stepQuestionsRead: {
    nl: "Daarna beantwoord je de vragen één voor één; de tekst blijft erbij staan.",
    en: "Then you answer the questions one at a time; the text stays with you.",
    fa: "بعد به سؤال‌ها یکی‌یکی پاسخ می‌دهی؛ متن کنارت می‌ماند.",
  },
  stepQuestionsListen: {
    nl: "Daarna beantwoord je de vragen één voor één; je kunt opnieuw luisteren.",
    en: "Then you answer the questions one at a time; you can listen again.",
    fa: "بعد به سؤال‌ها یکی‌یکی پاسخ می‌دهی؛ می‌توانی دوباره گوش بدهی.",
  },
  stepRevealRead: {
    nl: "Als alle vragen beantwoord zijn, kun je de vertaling lezen.",
    en: "Once every question is answered, you can read the translation.",
    fa: "وقتی به همه‌ی سؤال‌ها پاسخ دادی، می‌توانی ترجمه را بخوانی.",
  },
  stepRevealListen: {
    nl: "Als alle vragen beantwoord zijn, kun je meelezen met wat er gezegd werd.",
    en: "Once every question is answered, you can read along with what was said.",
    fa: "وقتی به همه‌ی سؤال‌ها پاسخ دادی، می‌توانی آنچه گفته شد را بخوانی.",
  },
  countsReceptive: {
    nl: "Je eerste antwoord op elke vraag telt voor dit onderwerp. Een tweede poging is extra oefening.",
    en: "Your first answer to each question counts for this topic. A second try is extra practice.",
    fa: "پاسخ اولت به هر سؤال برای این موضوع حساب می‌شود. تلاش دوم تمرین اضافه است.",
  },
  stepWarmUp: {
    nl: "Eerst oefen je een paar woorden uit deze situatie. Dat telt niet mee, maar levert wel punten op.",
    en: "First you practise a few words from this situation. That does not count, but it does earn points.",
    fa: "اول چند واژه از این موقعیت را تمرین می‌کنی. این حساب نمی‌شود، ولی امتیاز می‌گیری.",
  },
  stepTask: {
    nl: "Daarna doe je de opdracht. Die telt voor dit onderwerp, en je krijgt feedback.",
    en: "Then you do the task. That counts for this topic, and you get feedback.",
    fa: "بعد تکلیف را انجام می‌دهی. آن برای این موضوع حساب می‌شود و بازخورد می‌گیری.",
  },
  alreadyDone: {
    nl: "Dit onderwerp telt al als geoefend. Nog eens oefenen kan altijd.",
    en: "This topic already counts as practised. You can always practise again.",
    fa: "این موضوع از قبل تمرین‌شده حساب می‌شود. همیشه می‌توانی دوباره تمرین کنی.",
  },
  beginReading: { nl: "Begin met lezen", en: "Start reading", fa: "خواندن را شروع کن" },
  beginListening: { nl: "Begin met luisteren", en: "Start listening", fa: "گوش دادن را شروع کن" },
  warmUp: { nl: "Oefen eerst de woorden", en: "Practise the words first", fa: "اول واژه‌ها را تمرین کن" },
  skipToTask: {
    nl: "Ga meteen naar de opdracht",
    en: "Go straight to the task",
    fa: "مستقیم برو سراغ تکلیف",
  },
  toTask: { nl: "Naar de opdracht", en: "To the task", fa: "برو به تکلیف" },
  taskTitle: { nl: "Jouw opdracht", en: "Your task", fa: "تکلیف تو" },
  toTopics: { nl: "Kies een ander onderwerp", en: "Choose another topic", fa: "موضوع دیگری انتخاب کن" },
} as const satisfies Record<string, Copy>;
