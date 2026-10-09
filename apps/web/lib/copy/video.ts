import type { Copy } from "@/lib/ui-copy";

/** Interface copy of the video player (components/VideoPlayer.tsx), in Dutch with English and Persian. */
export const videoCopy = {
  backToVideos: { nl: "Naar de video's", en: "To the videos", fa: "برو به ویدیوها" },
  loading: { nl: "Video laden…", en: "Loading video…", fa: "در حال بارگذاری ویدیو…" },
  failedTitle: {
    nl: "Deze video is niet gelukt.",
    en: "This video did not work out.",
    fa: "ساختن این ویدیو ناموفق بود.",
  },
  makingTitle: {
    nl: "Deze video wordt nog gemaakt.",
    en: "This video is still being made.",
    fa: "این ویدیو هنوز در حال ساخته شدن است.",
  },
  makingBody: {
    nl: "Het script wordt geschreven en de video opgenomen. Dat duurt een paar minuten.",
    en: "The script is being written and the video recorded. That takes a few minutes.",
    fa: "متن در حال نوشته شدن و ویدیو در حال ضبط است. این کار چند دقیقه طول می‌کشد.",
  },
  checkStatus: {
    nl: "Ga terug naar de video's om de stand te zien.",
    en: "Go back to the videos to see how it is going.",
    fa: "به ویدیوها برگرد تا ببینی کار به کجا رسیده است.",
  },
  wordCount: { nl: "{count} WOORDEN", en: "{count} words", fa: "{count} واژه" },
  topic: { nl: "Onderwerp: {topic}", en: "Topic: {topic}", fa: "موضوع: {topic}" },
  subtitleTrack: { nl: "Nederlands", en: "Dutch", fa: "هلندی" },
  noVideoSupport: {
    nl: "Je browser kan deze video niet afspelen.",
    en: "Your browser cannot play this video.",
    fa: "مرورگرت نمی‌تواند این ویدیو را پخش کند.",
  },
  subtitles: { nl: "Ondertitels", en: "Subtitles", fa: "زیرنویس" },
  presenterAvatar: {
    nl: "Virtuele presentator en synthetische stem ({voice}). Geen echte persoon.",
    en: "Virtual presenter and synthetic voice ({voice}). Not a real person.",
    fa: "مجری مجازی و صدای مصنوعی ({voice}). شخص واقعی نیست.",
  },
  presenterCards: {
    nl: "Scènekaarten en synthetische stem ({voice}). Geen echte persoon.",
    en: "Scene cards and synthetic voice ({voice}). Not a real person.",
    fa: "کارت‌های صحنه و صدای مصنوعی ({voice}). شخص واقعی نیست.",
  },
  finishWatching: { nl: "Klaar met kijken", en: "Done watching", fa: "تماشا را تمام کردم" },
  questionsFollow: {
    nl: "Daarna volgen een paar vragen over de video.",
    en: "A few questions about the video come next.",
    fa: "بعد چند سؤال درباره‌ی ویدیو می‌آید.",
  },
  ratingGroup: { nl: "Was deze video goed?", en: "Was this video good?", fa: "این ویدیو خوب بود؟" },
  ratingPrompt: { nl: "Was dit een goede video?", en: "Was this a good video?", fa: "ویدیوی خوبی بود؟" },
  ratingYes: { nl: "Ja", en: "Yes", fa: "بله" },
  ratingNo: { nl: "Niet echt", en: "Not really", fa: "نه چندان" },
  anotherVideo: { nl: "Vraag nog een video", en: "Ask for another video", fa: "یک ویدیوی دیگر بخواه" },
  transcriptEyebrow: { nl: "TRANSCRIPT", en: "Transcript", fa: "متن گفتار" },
  readAlong: { nl: "Lees mee", en: "Read along", fa: "همراهش بخوان" },
  sceneHint: {
    nl: "Klik op een scène om daar te kijken.",
    en: "Click a scene to watch from there.",
    fa: "روی یک صحنه کلیک کن تا از همان‌جا تماشا کنی.",
  },
  goToScene: { nl: "Ga naar scène {number}", en: "Go to scene {number}", fa: "برو به صحنه‌ی {number}" },
  sceneName: { nl: "scène {number}", en: "scene {number}", fa: "صحنه‌ی {number}" },
  newWordsEyebrow: { nl: "NIEUWE WOORDEN", en: "New words", fa: "واژه‌های تازه" },
  glossaryTitle: {
    nl: "Bewaar wat je wilt onthouden",
    en: "Save what you want to remember",
    fa: "چیزی را که می‌خواهی به خاطر بسپاری ذخیره کن",
  },
  glossaryCount: { nl: "{count} woorden", en: "{count} words", fa: "{count} واژه" },
  wordSaved: {
    nl: '"{term}" staat in je woordenlijst en komt terug op het juiste moment.',
    en: '"{term}" is in your word list and will come back at the right moment.',
    fa: "«{term}» در فهرست واژه‌هایت است و در زمان مناسب دوباره می‌آید.",
  },
  wordKnown: {
    nl: '"{term}" stond al in je woordenlijst.',
    en: '"{term}" was already in your word list.',
    fa: "«{term}» از قبل در فهرست واژه‌هایت بود.",
  },
  comprehensionEyebrow: { nl: "BEGRIP", en: "Comprehension", fa: "درک مطلب" },
  score: {
    nl: "{correct} van {total} juist",
    en: "{correct} of {total} correct",
    fa: "{correct} از {total} درست",
  },
  questionsTwo: {
    nl: "Twee vragen over de video",
    en: "Two questions about the video",
    fa: "دو سؤال درباره‌ی ویدیو",
  },
  questionsThree: {
    nl: "Drie vragen over de video",
    en: "Three questions about the video",
    fa: "سه سؤال درباره‌ی ویدیو",
  },
  checkAnswers: { nl: "Controleer mijn antwoorden", en: "Check my answers", fa: "پاسخ‌هایم را بررسی کن" },
  evidence: {
    nl: "In de video: “{evidence}”",
    en: "In the video: “{evidence}”",
    fa: "در ویدیو: «{evidence}»",
  },
  notFound: { nl: "Deze video bestaat niet.", en: "This video does not exist.", fa: "این ویدیو وجود ندارد." },
  loadFailed: {
    nl: "De video kon niet worden geladen.",
    en: "The video could not be loaded.",
    fa: "ویدیو بارگذاری نشد.",
  },
  watchFailed: {
    nl: "Je kijkbeurt kon niet worden bewaard.",
    en: "Your viewing could not be saved.",
    fa: "تماشای تو ثبت نشد.",
  },
  saveFailed: { nl: "Bewaren lukte niet.", en: "Saving did not work.", fa: "ذخیره نشد." },
  answersFailed: {
    nl: "Je antwoorden konden niet worden bewaard.",
    en: "Your answers could not be saved.",
    fa: "پاسخ‌هایت ذخیره نشد.",
  },
  libraryLoadFailed: {
    nl: "De video's konden niet worden geladen.",
    en: "The videos could not be loaded.",
    fa: "ویدیوها بارگذاری نشدند.",
  },
  requestStarted: {
    nl: "De schrijver is begonnen. De video verschijnt hier zodra ze klaar is; dat duurt een paar minuten.",
    en: "The writer has started. The video appears here as soon as it is ready; that takes a few minutes.",
    fa: "نویسنده شروع کرده است. ویدیو به‌محض آماده شدن اینجا نمایش داده می‌شود؛ این کار چند دقیقه طول می‌کشد.",
  },
  retryStarted: { nl: "Nieuwe poging gestart.", en: "New attempt started.", fa: "تلاش تازه شروع شد." },
  retryFailed: {
    nl: "Opnieuw proberen lukte niet.",
    en: "Trying again did not work.",
    fa: "تلاش دوباره انجام نشد.",
  },
} as const satisfies Record<string, Copy>;
