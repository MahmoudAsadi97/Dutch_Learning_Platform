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
} as const satisfies Record<string, Record<string, Copy>>;

export type UiCopyGroup = keyof typeof uiCopy;
export type UiCopyKey<G extends UiCopyGroup> = keyof (typeof uiCopy)[G];

/** Fills `{name}` placeholders in every language of a copy entry. */
export function fill(copy: Copy, values: Record<string, string | number>): Copy {
  const apply = (text: string) =>
    text.replace(/\{(\w+)\}/g, (match, name: string) => (name in values ? String(values[name]) : match));
  return { nl: apply(copy.nl), en: apply(copy.en), fa: apply(copy.fa) };
}

/** Every entry as a flat list for tests and tooling. */
export function allCopy(): { key: string; copy: Copy }[] {
  return Object.entries(uiCopy).flatMap(([group, entries]) =>
    Object.entries(entries).map(([name, copy]) => ({ key: `${group}.${name}`, copy })),
  );
}
