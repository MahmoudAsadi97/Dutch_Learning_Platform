import type { Copy } from "@/lib/ui-copy";

/** The library entry points distinguish the course bank from each learner's saved material. */
export const libraryHubsCopy = {
  storiesTitle: {
    nl: "Verhalen op jouw niveau",
    en: "Stories at your level",
    fa: "داستان‌های متناسب با سطح تو",
  },
  storiesIntro: {
    nl: "Kies je niveau en een verhaal. Luister, ontdek woorden en gebruik ze zelf.",
    en: "Choose your level and a story. Listen, discover words and use them yourself.",
    fa: "سطح و داستانی انتخاب کن. گوش بده، واژه‌ها را کشف کن و خودت به کار ببر.",
  },
  wordsTitle: {
    nl: "Woorden leren en gebruiken",
    en: "Learn and use words",
    fa: "واژه‌ها را یاد بگیر و به کار ببر",
  },
  wordsIntro: {
    nl: "Ontdek woordkaarten per niveau, oefen met voorbeelden en herhaal je eigen bewaarde woorden.",
    en: "Explore word cards by level, practise examples and review your own saved words.",
    fa: "کارت‌های واژه را بر اساس سطح ببین، با مثال تمرین کن و واژه‌های ذخیره‌شده‌ات را مرور کن.",
  },
  courseStories: { nl: "Verhalen per niveau", en: "Stories by level", fa: "داستان‌ها بر اساس سطح" },
  personalStories: { nl: "Mijn afleveringen", en: "My episodes", fa: "قسمت‌های من" },
  courseWords: { nl: "Woordkaarten per niveau", en: "Word cards by level", fa: "کارت‌های واژه بر اساس سطح" },
  personalWords: { nl: "Mijn herhaling", en: "My review", fa: "مرور من" },
  personalStoriesNote: {
    nl: "Dit zijn je persoonlijke vervolgverhalen. Ze staan los van de verhalenbank per niveau.",
    en: "These are your personal serial stories. They are separate from the story bank for each level.",
    fa: "این‌ها داستان‌های دنباله‌دار شخصی تو هستند و از مجموعهٔ داستان‌های هر سطح جدا هستند.",
  },
  personalWordsNote: {
    nl: "Hier herhaal je alleen woorden die je zelf bewaarde. De volledige woordenbank vind je bij Woordkaarten per niveau.",
    en: "Review only the words you saved here. Find the complete bank under Word cards by level.",
    fa: "اینجا فقط واژه‌هایی را که خودت ذخیره کردی مرور می‌کنی. مجموعهٔ کامل در کارت‌های واژه بر اساس سطح است.",
  },
  level: { nl: "Kies je niveau", en: "Choose your level", fa: "سطحت را انتخاب کن" },
  openLevel: { nl: "Alles op dit niveau", en: "Everything at this level", fa: "همهٔ بخش‌های این سطح" },
  loading: { nl: "Niveaus ophalen…", en: "Loading levels…", fa: "در حال بارگذاری سطح‌ها…" },
  failed: {
    nl: "De niveaus konden niet worden geladen.",
    en: "The levels could not be loaded.",
    fa: "سطح‌ها بارگذاری نشدند.",
  },
  retry: { nl: "Opnieuw proberen", en: "Try again", fa: "دوباره امتحان کن" },
  wordsCount: {
    nl: "{words} woordkaarten · {core} kernwoorden",
    en: "{words} word cards · {core} core words",
    fa: "{words} کارت واژه · {core} واژهٔ اصلی",
  },
  storiesCount: {
    nl: "{stories} uitgewerkte verhalen · doel: {target}",
    en: "{stories} developed stories · target: {target}",
    fa: "{stories} داستان کامل · هدف: {target}",
  },
  shortTexts: {
    nl: "Daarnaast {count} korte oefenteksten. Die tellen niet mee voor dit verhalendoel.",
    en: "Plus {count} short practice texts. These do not count toward this story target.",
    fa: "همچنین {count} متن تمرینی کوتاه وجود دارد که در این هدف داستانی محاسبه نمی‌شوند.",
  },
  reviewNote: {
    nl: "De inhoud wacht nog op controle door een taalexpert.",
    en: "The content is still awaiting a language specialist's review.",
    fa: "این محتوا هنوز در انتظار بازبینی متخصص زبان است.",
  },
  speakingTitle: {
    nl: "Oefen een gesprek op jouw niveau",
    en: "Practise a conversation at your level",
    fa: "در سطح خودت گفت‌وگو تمرین کن",
  },
  speakingIntro: {
    nl: "Kies een niveau, vind een situatie en zeg wat je wilt bereiken. Elk niveau heeft eigen spreekopdrachten.",
    en: "Choose a level, find a situation and say what you want to achieve. Each level has its own speaking tasks.",
    fa: "سطح و موقعیتی انتخاب کن و بگو چه هدفی داری. هر سطح تمرین‌های گفتاری خودش را دارد.",
  },
  speakingTopics: {
    nl: "{count} spreekonderwerpen",
    en: "{count} speaking topics",
    fa: "{count} موضوع گفتاری",
  },
  speakingOpen: {
    nl: "Kies een spreekonderwerp",
    en: "Choose a speaking topic",
    fa: "موضوع گفتاری انتخاب کن",
  },
  speakingLoop: {
    nl: "Bekijk de situatie → spreek → lees je transcript → probeer het opnieuw.",
    en: "Explore the situation → speak → read your transcript → try again.",
    fa: "موقعیت را ببین ← صحبت کن ← متن گفتارت را بخوان ← دوباره امتحان کن.",
  },
  shortConversations: {
    nl: "Korte gesprekken met een gesprekspartner",
    en: "Short conversations with a partner",
    fa: "گفت‌وگوهای کوتاه با یک هم‌صحبت",
  },
  conversationsNote: {
    nl: "Deze extra gesprekken zijn beschikbaar voor de onderstaande onderwerpen. De volledige spreekbank staat bij je gekozen niveau.",
    en: "These extra conversations are available for the topics below. The full speaking bank is available at your selected level.",
    fa: "این گفت‌وگوهای تکمیلی برای موضوع‌های زیر موجودند. مجموعهٔ کامل گفتاری در سطح انتخابی تو است.",
  },
  conversationsEmpty: {
    nl: "Voor dit niveau staan hier nog geen extra gesprekken. De spreekopdrachten zijn wel beschikbaar.",
    en: "There are no extra conversations here for this level yet. The speaking tasks are available.",
    fa: "هنوز برای این سطح گفت‌وگوی تکمیلی اینجا نیست، اما تمرین‌های گفتاری در دسترس هستند.",
  },
  conversationsFailed: {
    nl: "De extra gesprekken konden niet worden geladen.",
    en: "The extra conversations could not be loaded.",
    fa: "گفت‌وگوهای تکمیلی بارگذاری نشدند.",
  },
  conversationsLoading: {
    nl: "Gesprekken ophalen…",
    en: "Loading conversations…",
    fa: "در حال بارگذاری گفت‌وگوها…",
  },
  studioTitle: { nl: "Microfoon controleren", en: "Check your microphone", fa: "میکروفونت را بررسی کن" },
  studioNote: {
    nl: "Neem een zin op en vergelijk met een luistervoorbeeld. Dit geeft geen uitspraakscore.",
    en: "Record a sentence and compare it with an audio example. This does not produce a pronunciation score.",
    fa: "جمله‌ای ضبط کن و با نمونهٔ صوتی مقایسه کن. این بخش نمرهٔ تلفظ نمی‌دهد.",
  },
  studioOpen: { nl: "Open de spraakstudio", en: "Open the speech studio", fa: "استودیوی گفتار را باز کن" },
} as const satisfies Record<string, Copy>;
