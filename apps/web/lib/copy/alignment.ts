import type { Copy } from "@/lib/ui-copy";

export const alignmentCopy = {
  target: {
    nl: "Wat oefen je op dit niveau?",
    en: "What are you practising at this level?",
    fa: "در این سطح چه چیزی تمرین می‌کنید؟",
  },
  bridge: {
    nl: "Een tussenstap naar het volgende niveau",
    en: "A bridge to the next level",
    fa: "یک گام میانی به سوی سطح بعدی",
  },
  reference: {
    nl: "Leerdoelen met officiële referenties",
    en: "Learning goals with official references",
    fa: "هدف‌های یادگیری با منابع رسمی",
  },
  limits: {
    nl: "Deze doelen begeleiden je oefening. De inhoud is nog niet door een taalexpert op niveau gecontroleerd.",
    en: "These goals guide your practice. A language specialist has not yet checked the content's level.",
    fa: "این هدف‌ها راهنمای تمرین هستند. سطح محتوا هنوز توسط متخصص زبان بررسی نشده است.",
  },
  loading: {
    nl: "Je leerdoel laden…",
    en: "Loading your learning goal…",
    fa: "در حال بارگذاری هدف یادگیری…",
  },
  failed: {
    nl: "Het leerdoel kon niet worden geladen. Probeer opnieuw.",
    en: "The learning goal could not be loaded. Try again.",
    fa: "هدف یادگیری بارگذاری نشد. دوباره تلاش کنید.",
  },
  sources: { nl: "Bekijk de officiële bronnen", en: "View official sources", fa: "منابع رسمی را ببینید" },
  exams: {
    nl: "Kies je examenrichting",
    en: "Choose your exam direction",
    fa: "مسیر آزمون خود را انتخاب کنید",
  },
  examIntro: {
    nl: "Ontdek welk examen bij je doel past. Oefeningen in Taalstudio zijn voorbereiding, geen officieel examen of certificaat.",
    en: "Explore which exam matches your goal. Taalstudio activities are preparation, not an official exam or certificate.",
    fa: "ببینید کدام آزمون با هدف شما سازگار است. تمرین‌های تالشودیو آمادگی هستند، نه آزمون رسمی یا مدرک.",
  },
  format: {
    nl: "Hoe verschilt de voorbereiding?",
    en: "How does preparation differ?",
    fa: "آمادگی چه تفاوتی دارد؟",
  },
  cnavt: {
    nl: "Oefen informatie verwerken en communiceren: luisteren en schrijven, lezen en schrijven, en mondeling reageren. Kies het profiel dat bij je doel past.",
    en: "Practise processing information and communicating: listening and writing, reading and writing, and oral responses. Choose the profile that fits your goal.",
    fa: "پردازش اطلاعات و ارتباط را تمرین کنید: شنیدن و نوشتن، خواندن و نوشتن، و پاسخ شفاهی. نمایه مناسب هدف خود را انتخاب کنید.",
  },
  itna: {
    nl: "Oefen taal in gebruik, lezen en luisteren, gevolgd door een presentatie en argumentatie. De C1-route voegt voor geschikte kandidaten een schrijfproef toe.",
    en: "Practise language in use, reading and listening, followed by presentation and argumentation. The C1 route adds a writing test for eligible candidates.",
    fa: "زبان در کاربرد، خواندن و شنیدن را تمرین کنید و سپس ارائه و استدلال. مسیر C1 برای داوطلبان واجد شرایط آزمون نوشتن اضافه می‌کند.",
  },
  other: {
    nl: "Controleer de vier vaardigheden en volg de actuele instructies van je cursus of examenhouder.",
    en: "Check the four skills and follow your course or exam provider's current instructions.",
    fa: "چهار مهارت را بررسی کنید و دستورهای فعلی دوره یا برگزارکننده آزمون را دنبال کنید.",
  },
  noC2: {
    nl: "C2 heeft hier een CEFR-leerroute. Er is geen CNaVT- of ITNA-C2-profiel in deze referentiegids.",
    en: "C2 has a CEFR learning route here. This guide contains no CNaVT or ITNA C2 profile.",
    fa: "C2 در اینجا مسیر یادگیری CEFR دارد. این راهنما نمایه C2 برای CNaVT یا ITNA ندارد.",
  },
  reading: { nl: "Lezen", en: "Reading", fa: "خواندن" },
  listening: { nl: "Luisteren", en: "Listening", fa: "شنیدن" },
  speaking: { nl: "Spreken", en: "Speaking", fa: "گفتن" },
  writing: { nl: "Schrijven", en: "Writing", fa: "نوشتن" },
} satisfies Record<string, Copy>;
