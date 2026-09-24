/** Original introductory examples; source distinctions checked, voice and language review pending. */
export type AlphabetLetter = {
  letter: string;
  name: string;
  speech: string;
  example: { nl: string; en: string; fa: string };
};
export const ALPHABET_REVIEW_STATUS = "unreviewed" as const;
export const ALPHABET_REFERENCES = [
  "https://taaladvies.net/ij-alfabetisering/",
  "https://www.vlaanderen.be/team-taaladvies/spellingregels/basisbegrippen-in-verband-met-spelling-taalkundige-termen",
  "https://www.vlaanderen.be/team-taaladvies/taaladviezen/ei-ij",
];

// Use Dutch letter names, never browser-inferred English names. Letter names are not word sounds.
const letterRows = [
  ["A", "aa", "appel", "apple", "سیب"],
  ["B", "bee", "boek", "book", "کتاب"],
  ["C", "see", "citroen", "lemon", "لیمو"],
  ["D", "dee", "deur", "door", "در"],
  ["E", "ee", "eten", "food; to eat", "غذا؛ خوردن"],
  ["F", "ef", "fiets", "bicycle", "دوچرخه"],
  ["G", "gee", "goed", "good", "خوب"],
  ["H", "haa", "huis", "house", "خانه"],
  ["I", "ie", "ik", "I", "من"],
  ["J", "jee", "jas", "coat", "کاپشن"],
  ["K", "kaa", "kat", "cat", "گربه"],
  ["L", "el", "lamp", "lamp", "چراغ"],
  ["M", "em", "maan", "moon", "ماه"],
  ["N", "en", "naam", "name", "نام"],
  ["O", "oo", "oog", "eye", "چشم"],
  ["P", "pee", "pen", "pen", "خودکار"],
  ["Q", "kuu", "quiz", "quiz", "مسابقهٔ پرسش و پاسخ"],
  ["R", "er", "rood", "red", "قرمز"],
  ["S", "es", "stoel", "chair", "صندلی"],
  ["T", "tee", "tafel", "table", "میز"],
  ["U", "uu", "uur", "hour", "ساعت"],
  ["V", "vee", "vis", "fish", "ماهی"],
  ["W", "wee", "water", "water", "آب"],
  ["X", "iks", "taxi", "taxi", "تاکسی"],
  ["Y", "ypsilon", "yoghurt", "yoghurt", "ماست"],
  ["Z", "zet", "zon", "sun", "خورشید"],
] as const;
export const DUTCH_ALPHABET: AlphabetLetter[] = letterRows.map(([letter, name, nl, en, fa]) => ({ letter, name, speech: name, example: { nl, en, fa } }));

export const DUTCH_LETTER_PAIRS = [
  { letters: "aa", example: { nl: "maan", en: "moon", fa: "ماه" } },
  { letters: "ee", example: { nl: "been", en: "leg", fa: "پا" } },
  { letters: "oo", example: { nl: "boot", en: "boat", fa: "قایق" } },
  { letters: "uu", example: { nl: "muur", en: "wall", fa: "دیوار" } },
  { letters: "ie", example: { nl: "fiets", en: "bicycle", fa: "دوچرخه" } },
  { letters: "oe", example: { nl: "boek", en: "book", fa: "کتاب" } },
  { letters: "eu", example: { nl: "neus", en: "nose", fa: "بینی" } },
  { letters: "ui", example: { nl: "huis", en: "house", fa: "خانه" } },
  { letters: "ij", example: { nl: "ijs", en: "ice", fa: "یخ" } },
  { letters: "ei", example: { nl: "trein", en: "train", fa: "قطار" } },
  { letters: "ou", example: { nl: "koud", en: "cold", fa: "سرد" } },
  { letters: "au", example: { nl: "pauw", en: "peacock", fa: "طاووس" } },
  { letters: "ch", example: { nl: "lach", en: "laugh", fa: "خنده" } },
  { letters: "sch", example: { nl: "school", en: "school", fa: "مدرسه" } },
];

/** Every letter is visited once in 26 rounds; four distinct options include the answer. */
export function letterQuestion(round: number): { target: AlphabetLetter; options: AlphabetLetter[] } {
  const index = ((Math.max(0, Math.floor(round)) * 7 + 3) % DUTCH_ALPHABET.length);
  const offsets = [0, 5, 11, 17];
  const options = offsets.map(offset => DUTCH_ALPHABET[(index + offset) % DUTCH_ALPHABET.length]);
  const shift = round % options.length;
  return { target: DUTCH_ALPHABET[index], options: [...options.slice(shift), ...options.slice(0, shift)] };
}
