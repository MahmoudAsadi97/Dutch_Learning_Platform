import type { Copy } from "@/lib/ui-copy";

/** Interface copy of word review (components/WordReview.tsx), in Dutch with English and Persian. */
export const wordsCopy = {
  loading: { nl: "Woorden laden…", en: "Loading words…", fa: "در حال بارگذاری واژه‌ها…" },
  loadFailed: {
    nl: "Je woorden konden niet worden geladen.",
    en: "Your words could not be loaded.",
    fa: "واژه‌هایت بارگذاری نشدند.",
  },
  gradeFailed: {
    nl: "Je antwoord kon niet worden bewaard.",
    en: "Your answer could not be saved.",
    fa: "پاسخت ذخیره نشد.",
  },
  listFailed: {
    nl: "De lijst kon niet worden geladen.",
    en: "The list could not be loaded.",
    fa: "فهرست بارگذاری نشد.",
  },
  eyebrow: { nl: "WOORDEN", en: "Words", fa: "واژه‌ها" },
  titleReview: {
    nl: "Herhaal wat je bewaarde.",
    en: "Review what you saved.",
    fa: "آنچه را نگه داشتی مرور کن.",
  },
  titleDone: { nl: "Klaar voor vandaag.", en: "Done for today.", fa: "برای امروز تمام شد." },
  titleNothing: { nl: "Niets te herhalen.", en: "Nothing to review.", fa: "چیزی برای مرور نیست." },
  stats: {
    nl: "{total} woorden bewaard · {learned} stevig onthouden · {due} vandaag te herhalen",
    en: "{total} words saved · {learned} firmly learned · {due} to review today",
    fa: "{total} واژه‌ی ذخیره‌شده · {learned} واژه‌ی تثبیت‌شده · {due} واژه برای مرور امروز",
  },
  statsWithDone: {
    nl: "{total} woorden bewaard · {learned} stevig onthouden · {due} vandaag te herhalen · {done} gedaan",
    en: "{total} words saved · {learned} firmly learned · {due} to review today · {done} done",
    fa: "{total} واژه‌ی ذخیره‌شده · {learned} واژه‌ی تثبیت‌شده · {due} واژه برای مرور امروز · {done} انجام‌شده",
  },
  cardsOne: {
    nl: "{count} KAART IN DEZE RONDE",
    en: "{count} card in this round",
    fa: "{count} کارت در این دور",
  },
  cardsMany: {
    nl: "{count} KAARTEN IN DEZE RONDE",
    en: "{count} cards in this round",
    fa: "{count} کارت در این دور",
  },
  gradeQuestion: {
    nl: "Hoe goed kende je dit woord?",
    en: "How well did you know this word?",
    fa: "این واژه را چقدر خوب بلد بودی؟",
  },
  gradeAgain: { nl: "Nog eens", en: "Again", fa: "دوباره" },
  gradeAgainHint: { nl: "straks opnieuw", en: "again soon", fa: "کمی بعد دوباره" },
  gradeHard: { nl: "Moeilijk", en: "Hard", fa: "سخت" },
  gradeHardHint: { nl: "kort interval", en: "short interval", fa: "فاصله‌ی کوتاه" },
  gradeGood: { nl: "Goed", en: "Good", fa: "خوب" },
  gradeGoodHint: { nl: "normaal interval", en: "normal interval", fa: "فاصله‌ی معمولی" },
  gradeEasy: { nl: "Makkelijk", en: "Easy", fa: "آسان" },
  gradeEasyHint: { nl: "langer interval", en: "longer interval", fa: "فاصله‌ی طولانی‌تر" },
  intervalNote: {
    nl: "Het interval groeit als je een woord goed kent en krimpt als je het vergeet. Het zegt niets over je niveau, alleen over wanneer je dit woord weer ziet.",
    en: "The interval grows when you know a word well and shrinks when you forget it. It says nothing about your level, only about when you see this word again.",
    fa: "این فاصله وقتی واژه‌ای را خوب بلدی بیشتر می‌شود و وقتی فراموشش می‌کنی کمتر. چیزی درباره‌ی سطح تو نمی‌گوید، فقط اینکه کی دوباره این واژه را می‌بینی.",
  },
  emptyDoneTitle: {
    nl: "Alles herhaald voor vandaag",
    en: "Everything reviewed for today",
    fa: "همه‌چیز برای امروز مرور شد",
  },
  emptyDoneText: {
    nl: "Lees een aflevering en bewaar nieuwe woorden; ze komen hier terug.",
    en: "Read an episode and save new words; they come back here.",
    fa: "یک قسمت بخوان و واژه‌های تازه را ذخیره کن؛ اینجا دوباره می‌آیند.",
  },
  emptyNoneTitle: {
    nl: "Nog niets te herhalen",
    en: "Nothing to review yet",
    fa: "هنوز چیزی برای مرور نیست",
  },
  emptyNoneText: {
    nl: "Bewaar woorden uit de verhalen met de knop Bewaar, of voeg hieronder zelf een woord toe.",
    en: "Save words from the stories with the Bewaar button, or add a word yourself below.",
    fa: "واژه‌های داستان‌ها را با دکمه‌ی Bewaar ذخیره کن، یا خودت در پایین یک واژه اضافه کن.",
  },
  toStories: { nl: "Naar de verhalen", en: "To the stories", fa: "برو به داستان‌ها" },
  addTitle: { nl: "Zelf een woord toevoegen", en: "Add a word yourself", fa: "خودت یک واژه اضافه کن" },
  fieldWord: { nl: "Woord", en: "Word", fa: "واژه" },
  fieldEnglish: { nl: "Engels", en: "English", fa: "انگلیسی" },
  fieldPersian: { nl: "Perzisch", en: "Persian", fa: "فارسی" },
  /** The example in the three fields: the Dutch word, its English and its Persian meaning. */
  example: { nl: "de buurvrouw", en: "the neighbour", fa: "همسایه" },
  savedNew: { nl: '"{term}" is bewaard.', en: '"{term}" is saved.', fa: "«{term}» ذخیره شد." },
  savedAlready: {
    nl: '"{term}" stond er al.',
    en: '"{term}" was already there.',
    fa: "«{term}» از قبل در فهرست بود.",
  },
  saveFailed: { nl: "Bewaren lukte niet.", en: "Saving did not work.", fa: "ذخیره نشد." },
  hideList: { nl: "Verberg de lijst", en: "Hide the list", fa: "فهرست را پنهان کن" },
  showList: { nl: "Toon al mijn woorden", en: "Show all my words", fa: "همه‌ی واژه‌هایم را نشان بده" },
  statusLearned: { nl: "stevig", en: "learned", fa: "تثبیت‌شده" },
  statusDue: { nl: "nu te herhalen", en: "to review now", fa: "وقت مرورش رسیده" },
  backInDay: { nl: "terug over {days} dag", en: "back in {days} day", fa: "{days} روز دیگر برمی‌گردد" },
  backInDays: { nl: "terug over {days} dagen", en: "back in {days} days", fa: "{days} روز دیگر برمی‌گردد" },
  remove: { nl: "Verwijder", en: "Remove", fa: "حذف کن" },
  removeFailed: { nl: "Verwijderen lukte niet.", en: "Removing did not work.", fa: "حذف نشد." },
} as const satisfies Record<string, Copy>;
