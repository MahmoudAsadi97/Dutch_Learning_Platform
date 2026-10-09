import type { Copy } from "@/lib/ui-copy";

/** Interface copy of the practice conversations (MissionCatalog, LessonShell and the step components), in Dutch with English and Persian. */
export const missionsCopy = {
  // app/missions/page.tsx
  pageTitle: { nl: "Oefenmissies", en: "Practice missions", fa: "مأموریت‌های تمرینی" },
  pageEyebrow: { nl: "SPREKEN", en: "SPEAKING", fa: "صحبت کردن" },
  pageHeading: { nl: "Praktijkgesprekken", en: "Real-life conversations", fa: "گفت‌وگوهای کاربردی" },
  pageIntro: {
    nl: "Kies een situatie en oefen op je eigen tempo.",
    en: "Choose a situation and practise at your own pace.",
    fa: "یک موقعیت انتخاب کن و با سرعت خودت تمرین کن.",
  },

  // MissionCatalog
  catalogEyebrow: {
    nl: "NEDERLANDS IN HET DAGELIJKS LEVEN",
    en: "DUTCH IN EVERYDAY LIFE",
    fa: "هلندی در زندگی روزمره",
  },
  catalogTitle: {
    nl: "Wat wil je vandaag oefenen?",
    en: "What do you want to practise today?",
    fa: "امروز می‌خواهی چه چیزی را تمرین کنی؟",
  },
  catalogIntro: {
    nl: "Elke missie combineert lezen, luisteren, spreken en schrijven.",
    en: "Every mission combines reading, listening, speaking and writing.",
    fa: "هر مأموریت خواندن، شنیدن، صحبت کردن و نوشتن را با هم ترکیب می‌کند.",
  },
  catalogFailed: {
    nl: "De oefeningen konden niet worden geladen.",
    en: "The exercises could not be loaded.",
    fa: "تمرین‌ها بارگذاری نشدند.",
  },
  catalogLoading: { nl: "Oefeningen laden…", en: "Loading exercises…", fa: "در حال بارگذاری تمرین‌ها…" },
  catalogEmpty: {
    nl: "Er zijn nog geen oefeningen beschikbaar.",
    en: "No exercises are available yet.",
    fa: "هنوز تمرینی در دسترس نیست.",
  },
  catalogBadge: {
    nl: "{level}-oefendoelen · 4 vaardigheden",
    en: "{level} practice goals · 4 skills",
    fa: "هدف‌های تمرینی {level} · ۴ مهارت",
  },
  catalogPractise: { nl: "Oefen {title}", en: "Practise {title}", fa: "{title} را تمرین کن" },

  // LessonShell
  missionLoading: { nl: "Missie laden…", en: "Loading mission…", fa: "در حال بارگذاری مأموریت…" },
  stepsLabel: { nl: "Stappen", en: "Steps", fa: "مرحله‌ها" },
  lessonMeta: {
    nl: "{level}-oefendoelen · {count} stappen",
    en: "{level} practice goals · {count} steps",
    fa: "هدف‌های تمرینی {level} · {count} مرحله",
  },
  independent: { nl: "Zelfstandig", en: "On your own", fa: "مستقل" },
  sessionTitle: { nl: "Sessie", en: "Session", fa: "جلسه" },
  sessionSaved: {
    nl: "Je werk wordt tijdens het oefenen bewaard.",
    en: "Your work is saved while you practise.",
    fa: "کارت هنگام تمرین ذخیره می‌شود.",
  },
  sessionStart: {
    nl: "Start een oefensessie",
    en: "Start a practice session",
    fa: "یک جلسه‌ی تمرین شروع کن",
  },
  sessionStarted: { nl: "Sessie gestart.", en: "Session started.", fa: "جلسه شروع شد." },
  sessionResumed: { nl: "Sessie hervat.", en: "Session resumed.", fa: "جلسه از سر گرفته شد." },
  sessionRestarted: { nl: "Nieuwe sessie gestart.", en: "New session started.", fa: "جلسه‌ی تازه شروع شد." },
  skillsTitle: { nl: "Vaardigheden", en: "Skills", fa: "مهارت‌ها" },
  noRecords: { nl: "nog geen records", en: "no records yet", fa: "هنوز سابقه‌ای نیست" },
  stepNoView: {
    nl: "Deze stap ({type}) heeft nog geen weergave.",
    en: "This step ({type}) has no view yet.",
    fa: "این مرحله ({type}) هنوز نمایشی ندارد.",
  },

  // SpeakingStep: what a turn did in the conversation
  actionStateNeed: { nl: "vraag uitgelegd", en: "request explained", fa: "درخواستت توضیح داده شد" },
  actionChooseOption: { nl: "keuze gemaakt", en: "choice made", fa: "انتخاب انجام شد" },
  actionStateReason: { nl: "reden gegeven", en: "reason given", fa: "دلیل گفته شد" },
  actionAcceptSlot: { nl: "nieuw moment gekozen", en: "new time chosen", fa: "زمان تازه انتخاب شد" },
  actionConfirm: { nl: "bevestigd", en: "confirmed", fa: "تأیید شد" },
  actionProposeSlot: { nl: "moment voorgesteld", en: "time proposed", fa: "زمانی پیشنهاد شد" },
  actionAskRepeat: { nl: "om herhaling gevraagd", en: "asked for a repeat", fa: "تکرار خواسته شد" },
  actionCancel: { nl: "geannuleerd", en: "cancelled", fa: "لغو شد" },
  actionNone: { nl: "geen actie", en: "no action", fa: "بدون اقدام" },
  actionNotRecognised: { nl: "geen actie herkend", en: "no action recognised", fa: "اقدامی تشخیص داده نشد" },
  actionNotAccepted: { nl: "niet aanvaard", en: "not accepted", fa: "پذیرفته نشد" },

  // SpeakingStep
  checkpointRules: {
    nl: "zelfstandige controle: alleen spreken, geen hulp, één poging",
    en: "independent check: speaking only, no help, one attempt",
    fa: "آزمون مستقل: فقط صحبت کردن، بدون کمک، یک بار تلاش",
  },
  goalTitle: { nl: "Doel", en: "Goal", fa: "هدف" },
  startCallWith: {
    nl: "Start een sessie om met {name} te bellen.",
    en: "Start a session to call {name}.",
    fa: "یک جلسه شروع کن تا با {name} تماس بگیری.",
  },
  startCallDefault: {
    nl: "Start een sessie om met de medewerker te bellen.",
    en: "Start a session to call the staff member.",
    fa: "یک جلسه شروع کن تا با کارمند تماس بگیری.",
  },
  busy: { nl: "Bezig…", en: "Working…", fa: "در حال انجام…" },
  startCheck: {
    nl: "Start de controle (één poging)",
    en: "Start the check (one attempt)",
    fa: "آزمون را شروع کن (یک بار تلاش)",
  },
  startConversation: { nl: "Start het gesprek", en: "Start the conversation", fa: "گفت‌وگو را شروع کن" },
  conversationWith: { nl: "Gesprek met {name}", en: "Conversation with {name}", fa: "گفت‌وگو با {name}" },
  recordingPlaceholder: { nl: "(opname)", en: "(recording)", fa: "(ضبط صدا)" },
  pendingSpeech: {
    nl: "Uploaden, herkennen en antwoord opstellen…",
    en: "Uploading, recognising and writing a reply…",
    fa: "در حال بارگذاری، تشخیص و نوشتن پاسخ…",
  },
  pendingTyped: { nl: "Antwoord opstellen…", en: "Writing a reply…", fa: "در حال نوشتن پاسخ…" },
  cancel: { nl: "Annuleren", en: "Cancel", fa: "لغو کن" },
  statusNoSession: { nl: "Nog geen sessie.", en: "No session yet.", fa: "هنوز جلسه‌ای نیست." },
  statusCheckDone: {
    nl: "Controle afgerond: het doel is bereikt.",
    en: "Check finished: the goal is reached.",
    fa: "آزمون تمام شد: هدف به دست آمد.",
  },
  statusEnded: {
    nl: "De beurten zijn opgebruikt; de controle is afgesloten.",
    en: "The turns are used up; the check is closed.",
    fa: "نوبت‌ها تمام شده‌اند؛ آزمون بسته شد.",
  },
  statusAbandoned: {
    nl: "Deze sessie is afgebroken.",
    en: "This session was stopped.",
    fa: "این جلسه نیمه‌کاره متوقف شد.",
  },
  statusTypedOnly: {
    nl: "Doel bereikt met getypte tekst. Dat telt niet als spreekoefening: start een nieuwe oefensessie en spreek de beurten in.",
    en: "Goal reached with typed text. That does not count as speaking practice: start a new practice session and speak your turns.",
    fa: "با متن تایپ‌شده به هدف رسیدی. این تمرین صحبت کردن به حساب نمی‌آید: یک جلسه‌ی تمرین تازه شروع کن و نوبت‌ها را با صدای خودت بگو.",
  },
  statusGoalReached: {
    nl: "Doel bereikt. Je kunt verder naar de volgende stap.",
    en: "Goal reached. You can go on to the next step.",
    fa: "به هدف رسیدی. می‌توانی به مرحله‌ی بعد بروی.",
  },
  statusTurnsLeft: {
    nl: "{left} van {max} beurten over.",
    en: "{left} of {max} turns left.",
    fa: "{left} از {max} نوبت باقی مانده است.",
  },
  restartSession: {
    nl: "Nieuwe oefensessie (de huidige wordt afgesloten)",
    en: "New practice session (ends the current one)",
    fa: "جلسه‌ی تمرین تازه (جلسه‌ی فعلی بسته می‌شود)",
  },
  audioLabel: { nl: "audio: {label}", en: "audio: {label}", fa: "صدا: {label}" },
  audioMissing: {
    nl: "Geen audio voor dit antwoord; lees de tekst.",
    en: "No audio for this reply; read the text.",
    fa: "این پاسخ صدا ندارد؛ متن را بخوان.",
  },
  replyPlaybackFailed: {
    nl: "Afspelen mislukt; lees de tekst van het antwoord.",
    en: "Playback failed; read the text of the reply.",
    fa: "پخش نشد؛ متن پاسخ را بخوان.",
  },
  replyPlaybackBlocked: {
    nl: "Automatisch afspelen is geblokkeerd; druk op “speel af” bij het antwoord.",
    en: "Automatic playback is blocked; press “speel af” next to the reply.",
    fa: "پخش خودکار مسدود شده است؛ کنار پاسخ روی «speel af» بزن.",
  },
  talkRecording: {
    nl: "Opname loopt… laat los om te versturen",
    en: "Recording… let go to send",
    fa: "در حال ضبط… رها کن تا فرستاده شود",
  },
  talkHold: { nl: "Houd ingedrukt om te spreken", en: "Hold to speak", fa: "برای صحبت کردن نگه دار" },
  recordingUnsupported: {
    nl: "Deze browser ondersteunt geen opname.",
    en: "This browser does not support recording.",
    fa: "این مرورگر از ضبط صدا پشتیبانی نمی‌کند.",
  },
  typedLabel: {
    nl: "Of typ je zin (wordt als getypte tekst opgeslagen, niet als spraak)",
    en: "Or type your sentence (saved as typed text, not as speech)",
    fa: "یا جمله‌ات را تایپ کن (به‌صورت متن تایپ‌شده ذخیره می‌شود، نه گفتار)",
  },
  typedSend: { nl: "Verstuur getypt", en: "Send typed text", fa: "متن تایپ‌شده را بفرست" },
  typedNotAllowed: {
    nl: "Typen is in deze stap niet toegestaan.",
    en: "Typing is not allowed in this step.",
    fa: "در این مرحله تایپ کردن مجاز نیست.",
  },
  yourConversation: { nl: "Je gesprek", en: "Your conversation", fa: "گفت‌وگوی تو" },
  appointment: { nl: "Afspraak", en: "Appointment", fa: "قرار ملاقات" },
  choiceLine: { nl: "keuze:", en: "choice:", fa: "انتخاب:" },
  newMomentLine: { nl: "nieuw moment:", en: "new time:", fa: "زمان تازه:" },
  conversationCancelled: { nl: "gesprek geannuleerd", en: "conversation cancelled", fa: "گفت‌وگو لغو شد" },
  choicesList: { nl: "Keuzes: {list}", en: "Choices: {list}", fa: "گزینه‌ها: {list}" },
  slotsList: {
    nl: "Beschikbare momenten: {list}",
    en: "Available times: {list}",
    fa: "زمان‌های آزاد: {list}",
  },
  turnCount: {
    nl: "Gespreksbeurten {used}/{max}",
    en: "Conversation turns {used}/{max}",
    fa: "نوبت‌های گفت‌وگو {used}/{max}",
  },
  help: { nl: "Hulp", en: "Help", fa: "کمک" },
  spokenTranscript: {
    nl: "gesproken · transcriptie",
    en: "spoken · transcript",
    fa: "گفته‌شده · متن پیاده‌شده",
  },
  typedSaved: {
    nl: "getypt · als getypte tekst opgeslagen",
    en: "typed · saved as typed text",
    fa: "تایپ‌شده · به‌صورت متن تایپ‌شده ذخیره شد",
  },
  turnFailed: { nl: "mislukt", en: "failed", fa: "ناموفق" },
  recordingWarning: {
    nl: "Je tekst is bewaard. De geluidsopname kon niet worden opgeslagen.",
    en: "Your text is saved. The sound recording could not be stored.",
    fa: "متنت ذخیره شد. صدای ضبط‌شده ذخیره نشد.",
  },
  playing: { nl: "speelt", en: "playing", fa: "در حال پخش" },
  play: { nl: "speel af", en: "play", fa: "پخش کن" },

  // WritingStep
  assignment: { nl: "Opdracht", en: "Task", fa: "تکلیف" },
  wordRange: { nl: "{min}–{max} woorden", en: "{min}–{max} words", fa: "{min} تا {max} واژه" },
  wordRangeUse: {
    nl: "{min}–{max} woorden · gebruik: {words}",
    en: "{min}–{max} words · use: {words}",
    fa: "{min} تا {max} واژه · به کار ببر: {words}",
  },
  yourMessage: { nl: "Je bericht", en: "Your message", fa: "پیامت" },
  messageLabel: { nl: "Je bericht in het Nederlands", en: "Your message in Dutch", fa: "پیامت به هلندی" },
  wordCount: { nl: "{count} woorden", en: "{count} words", fa: "{count} واژه" },
  wordCountNeeded: {
    nl: "{count} woorden ({min}–{max} nodig)",
    en: "{count} words ({min}–{max} needed)",
    fa: "{count} واژه ({min} تا {max} لازم است)",
  },
  stillToUse: {
    nl: "nog te gebruiken: {words}",
    en: "still to use: {words}",
    fa: "هنوز باید به کار ببری: {words}",
  },
  allRequiredWords: { nl: "alle vereiste woorden", en: "all required words", fa: "همه‌ی واژه‌های لازم" },
  autosaving: { nl: "wijzigingen bewaren…", en: "saving changes…", fa: "در حال ذخیره‌ی تغییرها…" },
  savedAt: { nl: "bewaard {time}", en: "saved {time}", fa: "ذخیره شد {time}" },
  notSavedYet: { nl: "nog niet bewaard", en: "not saved yet", fa: "هنوز ذخیره نشده" },
  saveAgain: { nl: "Opnieuw bewaren", en: "Save again", fa: "دوباره ذخیره کن" },
  textStays: {
    nl: "Je tekst blijft hier staan. Bewaar voordat je verdergaat.",
    en: "Your text stays here. Save before you go on.",
    fa: "متنت همین‌جا می‌ماند. پیش از ادامه دادن ذخیره‌اش کن.",
  },
  submitting: { nl: "Indienen…", en: "Submitting…", fa: "در حال فرستادن…" },
  resubmit: { nl: "Opnieuw indienen", en: "Submit again", fa: "دوباره بفرست" },
  submit: { nl: "Dien in", en: "Submit", fa: "بفرست" },
  messageSaved: { nl: "bericht opgeslagen", en: "message saved", fa: "پیام ذخیره شد" },
  submittedMissing: {
    nl: "Ingediend: {count} woorden. Ontbreekt nog: {missing}.",
    en: "Submitted: {count} words. Still missing: {missing}.",
    fa: "فرستاده شد: {count} واژه. هنوز کم است: {missing}.",
  },
  submittedComplete: {
    nl: "Ingediend: {count} woorden. Alle vereiste woorden staan erin.",
    en: "Submitted: {count} words. All required words are in it.",
    fa: "فرستاده شد: {count} واژه. همه‌ی واژه‌های لازم در آن هست.",
  },
  submittedReread: {
    nl: "Ingediend: {count} woorden. Lees je bericht na en vraag feedback.",
    en: "Submitted: {count} words. Read your message again and ask for feedback.",
    fa: "فرستاده شد: {count} واژه. پیامت را دوباره بخوان و بازخورد بخواه.",
  },

  // ListeningStep
  listenTitle: { nl: "Beluister de boodschap", en: "Listen to the message", fa: "به پیام گوش بده" },
  clipPlaying: { nl: "Speelt…", en: "Playing…", fa: "در حال پخش…" },
  listenAgain: { nl: "Nog eens beluisteren", en: "Listen again", fa: "دوباره گوش بده" },
  listen: { nl: "Beluister", en: "Listen", fa: "گوش بده" },
  playCount: { nl: "{count}× beluisterd", en: "listened {count}×", fa: "{count} بار گوش دادی" },
  syntheticVoice: {
    nl: "Synthetische luisterstem",
    en: "Synthetic listening voice",
    fa: "صدای شنیداری مصنوعی",
  },
  listenWhenNeeded: {
    nl: "Luister opnieuw wanneer je dat nodig hebt.",
    en: "Listen again whenever you need to.",
    fa: "هر وقت لازم داشتی دوباره گوش بده.",
  },
  clipPlaybackFailed: { nl: "Afspelen mislukt.", en: "Playback failed.", fa: "پخش نشد." },
  clipPlaybackBlocked: {
    nl: "Afspelen werd geblokkeerd; klik nog eens op de knop.",
    en: "Playback was blocked; click the button again.",
    fa: "پخش مسدود شد؛ دوباره روی دکمه بزن.",
  },
  hideText: { nl: "Verberg de tekst", en: "Hide the text", fa: "متن را پنهان کن" },
  showText: { nl: "Toon de tekst", en: "Show the text", fa: "متن را نشان بده" },
  transcriptFailed: {
    nl: "De tekst is nog niet getoond: hulp kon niet worden opgeslagen. Probeer opnieuw.",
    en: "The text is not shown yet: the help could not be saved. Try again.",
    fa: "متن هنوز نشان داده نشده است: کمک ذخیره نشد. دوباره امتحان کن.",
  },

  // ReadingStep
  readingText: { nl: "Tekst", en: "Text", fa: "متن" },
  readingTextAudio: { nl: "De leestekst", en: "The reading text", fa: "متن خواندنی" },
  vocabulary: { nl: "Woordenschat", en: "Vocabulary", fa: "واژگان" },
  columnDutch: { nl: "Nederlands", en: "Dutch", fa: "هلندی" },
  columnMeaning: { nl: "Betekenis", en: "Meaning", fa: "معنی" },
  columnNote: { nl: "Opmerking", en: "Note", fa: "یادداشت" },
  translationFailed: {
    nl: "De vertaling is nog niet getoond: hulp kon niet worden opgeslagen. Probeer opnieuw.",
    en: "The translation is not shown yet: the help could not be saved. Try again.",
    fa: "ترجمه هنوز نشان داده نشده است: کمک ذخیره نشد. دوباره امتحان کن.",
  },

  // FeedbackPanel
  feedbackIntro: {
    nl: "Wat gaat goed en wat kun je verder oefenen?",
    en: "What is going well and what can you practise further?",
    fa: "چه چیزی خوب پیش می‌رود و چه چیزی را می‌توانی بیشتر تمرین کنی؟",
  },
  feedbackBusy: {
    nl: "Feedback wordt opgesteld…",
    en: "Writing feedback…",
    fa: "در حال آماده کردن بازخورد…",
  },
  feedbackAgain: { nl: "Vraag nieuwe feedback", en: "Ask for new feedback", fa: "بازخورد تازه بخواه" },
  feedbackAsk: { nl: "Vraag feedback", en: "Ask for feedback", fa: "بازخورد بخواه" },

  // HelpLadder
  helpAllShown: { nl: "Alle hulp is getoond.", en: "All help is shown.", fa: "همه‌ی کمک‌ها نشان داده شد." },
  helpSaveFailed: {
    nl: "Hulp kon niet worden opgeslagen. Probeer opnieuw; de tip is nog niet getoond.",
    en: "The help could not be saved. Try again; the tip is not shown yet.",
    fa: "کمک ذخیره نشد. دوباره امتحان کن؛ راهنمایی هنوز نشان داده نشده است.",
  },
  loadFailed: {
    nl: "De missie kon niet worden geladen.",
    en: "The mission could not be loaded.",
    fa: "مأموریت بارگذاری نشد.",
  },
  sessionStartFailed: {
    nl: "Kon geen sessie starten.",
    en: "Could not start a session.",
    fa: "جلسه شروع نشد.",
  },
  sessionRestartFailed: {
    nl: "Kon geen nieuwe sessie starten.",
    en: "Could not start a new session.",
    fa: "جلسه‌ی تازه شروع نشد.",
  },
  turnNotProcessed: {
    nl: "Je antwoord kon niet worden verwerkt. Probeer opnieuw.",
    en: "Your answer could not be processed. Try again.",
    fa: "پاسخت پردازش نشد. دوباره امتحان کن.",
  },
  feedbackUnavailable: {
    nl: "Feedback is tijdelijk niet beschikbaar. Probeer opnieuw.",
    en: "Feedback is temporarily unavailable. Try again.",
    fa: "بازخورد موقتاً در دسترس نیست. دوباره امتحان کن.",
  },
  draftNotSaved: {
    nl: "Niet bewaard. Je tekst blijft hier staan; probeer het zo opnieuw.",
    en: "Not saved. Your text stays here; try again in a moment.",
    fa: "ذخیره نشد. متنت همین‌جا می‌ماند؛ کمی بعد دوباره امتحان کن.",
  },
  submitFailed: {
    nl: "Indienen lukte niet. Je tekst blijft staan; probeer het opnieuw.",
    en: "Submitting did not work. Your text stays here; try again.",
    fa: "ارسال انجام نشد. متنت سر جایش می‌ماند؛ دوباره امتحان کن.",
  },
  audioUnavailable: { nl: "Audio niet beschikbaar.", en: "Audio not available.", fa: "صدا در دسترس نیست." },
  answersFailed: {
    nl: "Antwoorden konden niet worden opgeslagen.",
    en: "The answers could not be saved.",
    fa: "پاسخ‌ها ذخیره نشدند.",
  },
} as const satisfies Record<string, Copy>;
