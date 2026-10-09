import type { Copy } from "@/lib/ui-copy";

/** Interface copy of the speech studio (components/SpeechCheck.tsx, app/speech-check), in Dutch with English and Persian. */
export const speechCopy = {
  pageEyebrow: { nl: "EERST EVEN PROBEREN", en: "First, a quick try", fa: "اول یک امتحان کوتاه" },
  pageTitle: {
    nl: "Jouw stem. Jouw Nederlands.",
    en: "Your voice. Your Dutch.",
    fa: "صدای تو. هلندیِ تو.",
  },
  pageIntro: {
    nl: "Test je microfoon, bekijk de transcriptie en luister naar een gesproken voorbeeld.",
    en: "Test your microphone, look at the transcription and listen to a spoken example.",
    fa: "میکروفونت را امتحان کن، متن پیاده‌شده را ببین و به یک نمونه‌ی گفتاری گوش بده.",
  },
  pageBadge: { nl: "Microfoontest", en: "Microphone test", fa: "آزمایش میکروفون" },
  quietPlaceTitle: {
    nl: "Een rustige plek maakt het verschil.",
    en: "A quiet place makes all the difference.",
    fa: "یک جای آرام همه‌چیز را بهتر می‌کند.",
  },
  quietPlaceBody: {
    nl: "Geef je browser toegang tot de microfoon. Gebruik bij voorkeur een hoofdtelefoon. Deze test geeft geen uitspraakscore en beoordeelt je accent niet.",
    en: "Give your browser access to the microphone. Headphones work best. This test gives no pronunciation score and does not judge your accent.",
    fa: "به مرورگرت اجازه بده به میکروفون دسترسی داشته باشد. بهتر است از هدفون استفاده کنی. این آزمایش به تلفظت نمره نمی‌دهد و لهجه‌ات را قضاوت نمی‌کند.",
  },
  recordEyebrow: { nl: "01 · JOUW STEM", en: "01 · Your voice", fa: "01 · صدای تو" },
  recordTitle: { nl: "Opnemen en transcriberen", en: "Record and transcribe", fa: "ضبط و تبدیل به متن" },
  recordIntro: {
    nl: "Houd de knop ingedrukt en zeg een Nederlandse zin, bijvoorbeeld:",
    en: "Hold the button down and say a Dutch sentence, for example:",
    fa: "دکمه را نگه دار و یک جمله‌ی هلندی بگو، برای نمونه:",
  },
  formatTitle: { nl: "Opnameformaat", en: "Recording format", fa: "قالب ضبط" },
  formatChecking: { nl: "controleren…", en: "checking…", fa: "در حال بررسی…" },
  formatUnsupported: { nl: "niet ondersteund", en: "not supported", fa: "پشتیبانی نمی‌شود" },
  formatDefault: {
    nl: "standaardformaat van de browser",
    en: "the browser's default format",
    fa: "قالب پیش‌فرض مرورگر",
  },
  talkRecording: {
    nl: "Opname loopt… laat los om te stoppen",
    en: "Recording… let go to stop",
    fa: "در حال ضبط… برای توقف رها کن",
  },
  talkProcessing: { nl: "Verwerken…", en: "Processing…", fa: "در حال پردازش…" },
  talkHold: { nl: "Houd ingedrukt om te spreken", en: "Hold to speak", fa: "برای صحبت کردن نگه دار" },
  phaseIdle: { nl: "Klaar om op te nemen.", en: "Ready to record.", fa: "آماده‌ی ضبط." },
  phaseRecording: { nl: "Opname loopt.", en: "Recording.", fa: "در حال ضبط." },
  phaseUploading: {
    nl: "Uploaden, converteren en transcriberen…",
    en: "Uploading, converting and transcribing…",
    fa: "در حال بارگذاری، تبدیل و نوشتن متن…",
  },
  phaseDone: { nl: "Klaar.", en: "Done.", fa: "تمام شد." },
  phaseUnsupported: {
    nl: "Deze browser ondersteunt MediaRecorder niet.",
    en: "This browser does not support MediaRecorder.",
    fa: "این مرورگر از MediaRecorder پشتیبانی نمی‌کند.",
  },
  phaseError: { nl: "Er ging iets mis.", en: "Something went wrong.", fa: "مشکلی پیش آمد." },
  ownRecordingTitle: { nl: "Jouw opname", en: "Your recording", fa: "صدای ضبط‌شده‌ی تو" },
  ownRecordingListen: {
    nl: "Luister naar je eigen opname",
    en: "Listen to your own recording",
    fa: "به صدای ضبط‌شده‌ی خودت گوش بده",
  },
  ownRecordingNote: {
    nl: "Alleen in dit tabblad beschikbaar. De opname wordt voor deze microfoontest niet in de opslag bewaard.",
    en: "Only available in this tab. The recording for this microphone test is not kept in storage.",
    fa: "فقط در همین زبانه در دسترس است. ضبط این آزمایش میکروفون در فضای ذخیره‌سازی نگه داشته نمی‌شود.",
  },
  transcriptTitle: { nl: "Transcriptie", en: "Transcription", fa: "متن پیاده‌شده" },
  transcriptEmpty: { nl: "(leeg)", en: "(empty)", fa: "(خالی)" },
  transcriptCompare: {
    nl: "Vergelijk de tekst met wat je zei. Een transcriptie kan fouten bevatten.",
    en: "Compare the text with what you said. A transcription can contain mistakes.",
    fa: "متن را با آنچه گفتی مقایسه کن. متن پیاده‌شده ممکن است اشتباه داشته باشد.",
  },
  synthesisEyebrow: {
    nl: "02 · LUISTER EN VERGELIJK",
    en: "02 · Listen and compare",
    fa: "02 · گوش بده و مقایسه کن",
  },
  synthesisTitle: { nl: "Synthetische stem", en: "Synthetic voice", fa: "صدای مصنوعی" },
  synthesisIntro: {
    nl: "Een kunstmatige stem als luistervoorbeeld, altijd gelabeld. Geen menselijke opname of uitspraakbeoordeling.",
    en: "An artificial voice as a listening example, always labelled. No human recording and no pronunciation assessment.",
    fa: "یک صدای مصنوعی به‌عنوان نمونه‌ی شنیداری، همیشه با برچسب. نه ضبط صدای انسان است و نه ارزیابی تلفظ.",
  },
  synthesisTextLabel: { nl: "Tekst om uit te spreken", en: "Text to speak", fa: "متنی که باید گفته شود" },
  synthesisBusy: { nl: "Bezig…", en: "Working…", fa: "در حال انجام…" },
  synthesisPlay: { nl: "Speel af", en: "Play", fa: "پخش کن" },
  uploadFailed: {
    nl: "Je opname kon niet worden verwerkt. Probeer opnieuw.",
    en: "Your recording could not be processed. Try again.",
    fa: "صدای ضبط‌شده‌ات پردازش نشد. دوباره امتحان کن.",
  },
  synthesisFailed: { nl: "Synthese mislukt.", en: "Speech synthesis failed.", fa: "ساخت صدا انجام نشد." },
  playbackFailed: {
    nl: "Afspelen mislukt; gebruik de afspeelknop van de speler.",
    en: "Playback failed; use the player's play button.",
    fa: "پخش انجام نشد؛ از دکمه‌ی پخشِ پخش‌کننده استفاده کن.",
  },
  playbackBlocked: {
    nl: "Automatisch afspelen is geblokkeerd; gebruik de afspeelknop van de speler.",
    en: "Automatic playback is blocked; use the player's play button.",
    fa: "پخش خودکار مسدود است؛ از دکمه‌ی پخشِ پخش‌کننده استفاده کن.",
  },
} as const satisfies Record<string, Copy>;
