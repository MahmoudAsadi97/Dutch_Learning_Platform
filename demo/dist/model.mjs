export const LEVELS = [
  { id: 'pre-a1', name: 'Pre-A1', label: 'Start with sounds and everyday words', nl: 'Begin met klanken en alledaagse woorden', status: 'CEFR descriptor band' },
  { id: 'a1', name: 'A1', label: 'Introduce yourself and ask simple questions', nl: 'Stel jezelf voor en stel eenvoudige vragen', status: 'CEFR level' },
  { id: 'pre-a2', name: 'Pre-A2', label: 'Connect simple sentences in familiar situations', nl: 'Verbind eenvoudige zinnen in vertrouwde situaties', status: 'Internal bridge to A2' },
  { id: 'a2', name: 'A2', label: 'Manage everyday plans and explain a simple problem', nl: 'Maak dagelijkse afspraken en leg een eenvoudig probleem uit', status: 'CEFR level' },
  { id: 'pre-b1', name: 'Pre-B1', label: 'Build independence when a plan changes', nl: 'Reageer zelfstandiger wanneer een plan verandert', status: 'Internal bridge to B1' },
  { id: 'b1', name: 'B1', label: 'Explain experiences and negotiate familiar situations', nl: 'Vertel over ervaringen en bespreek vertrouwde situaties', status: 'CEFR level' },
  { id: 'pre-b2', name: 'Pre-B2', label: 'Develop arguments and handle less familiar topics', nl: 'Bouw een argument op en bespreek minder vertrouwde onderwerpen', status: 'Internal bridge to B2' },
  { id: 'b2', name: 'B2', label: 'Discuss complex ideas with clarity and detail', nl: 'Bespreek complexe ideeën duidelijk en gedetailleerd', status: 'CEFR level' },
  { id: 'pre-c1', name: 'Pre-C1', label: 'Refine register, nuance and extended expression', nl: 'Verfijn register, nuance en langere bijdragen', status: 'Internal bridge to C1' },
  { id: 'c1', name: 'C1', label: 'Use language flexibly in demanding contexts', nl: 'Gebruik taal flexibel in veeleisende situaties', status: 'CEFR level' },
  { id: 'pre-c2', name: 'Pre-C2', label: 'Practise subtle meaning and precise reformulation', nl: 'Oefen subtiele betekenis en nauwkeurige herformulering', status: 'Internal bridge to C2' },
  { id: 'c2', name: 'C2', label: 'Communicate with precision across complex contexts', nl: 'Communiceer nauwkeurig in complexe situaties', status: 'CEFR level' },
];

export const SCENARIO = {
  duration: 30,
  current: { day: '2026-10-06', start: 600 },
  learnerBusy: [
    { day: '2026-10-06', start: 540, end: 660, reason: 'les' },
    { day: '2026-10-06', start: 855, end: 900, reason: 'werk' },
  ],
  opening: [{ day: '2026-10-06', start: 540, end: 1020 }, { day: '2026-10-07', start: 540, end: 960 }],
  offers: [
    { id: 'tue-14', day: '2026-10-06', start: 840, nl: 'Dinsdag 6 oktober · 14.00 uur', en: 'Tuesday 6 October · 14:00', fa: 'سه‌شنبه ۶ اکتبر · ساعت ۱۴' },
    { id: 'wed-14', day: '2026-10-07', start: 840, nl: 'Woensdag 7 oktober · 14.00 uur', en: 'Wednesday 7 October · 14:00', fa: 'چهارشنبه ۷ اکتبر · ساعت ۱۴' },
    { id: 'wed-16', day: '2026-10-07', start: 960, nl: 'Woensdag 7 oktober · 16.00 uur', en: 'Wednesday 7 October · 16:00', fa: 'چهارشنبه ۷ اکتبر · ساعت ۱۶' },
  ],
};

export function validateSlot(id, scenario = SCENARIO) {
  const slot = scenario.offers.find((offer) => offer.id === id);
  if (!slot) return { valid: false, reason: 'unknown' };
  const end = slot.start + scenario.duration;
  if (scenario.learnerBusy.some((busy) => busy.day === slot.day && slot.start < busy.end && end > busy.start)) return { valid: false, reason: 'overlap', slot, end };
  if (!scenario.opening.some((hours) => hours.day === slot.day && slot.start >= hours.start && end <= hours.end)) return { valid: false, reason: 'closed', slot, end };
  return { valid: true, slot, end };
}

export const HINTS = [
  { nl: 'Controleer je agenda én de openingsuren. De afspraak duurt dertig minuten.', en: 'Check your calendar and the opening hours. The appointment lasts thirty minutes.', fa: 'تقویم خود و ساعت کاری را بررسی کنید. قرار سی دقیقه طول می‌کشد.' },
  { nl: 'Dinsdag begint je werk om 14.15 uur. Woensdag sluit de praktijk om 16.00 uur.', en: 'Your work begins Tuesday at 14:15. The practice closes Wednesday at 16:00.', fa: 'سه‌شنبه کار شما ساعت ۱۴:۱۵ آغاز می‌شود. مطب چهارشنبه ساعت ۱۶ بسته می‌شود.' },
  { nl: 'Woensdag om 14.00 uur past. Vraag: “Past woensdag om twee uur in de namiddag?”', en: 'Wednesday at 14:00 works. Ask: “Would Wednesday at two in the afternoon work?”', fa: 'چهارشنبه ساعت ۱۴ مناسب است. بپرسید: «چهارشنبه ساعت دو بعدازظهر مناسب است؟»' },
];

export const SAMPLE_DRAFT = 'Beste, ik wil mijn afspraak verplaatsen. Woensdag om 14.00 uur komt ik. Vriendelijke groeten, Sam';
export const REVISED_DRAFT = 'Beste, ik wil mijn afspraak verplaatsen. Woensdag om 14.00 uur kom ik. Vriendelijke groeten, Sam';

export function inspectWriting(text) {
  const issues = [];
  if (/\bkomt ik\b/i.test(text)) issues.push({ before: 'komt ik', after: 'kom ik', nl: 'Na de tijdsbepaling staat het werkwoord vóór het onderwerp. Bij “ik” gebruik je “kom”.', en: 'After the time phrase, the verb comes before the subject. With “ik”, use “kom”.', fa: 'پس از عبارت زمان، فعل قبل از فاعل می‌آید. برای «ik» از «kom» استفاده کنید.' });
  if (/\bafsprak\b/i.test(text)) issues.push({ before: 'afsprak', after: 'afspraak', nl: 'Schrijf “afspraak” met twee a’s.', en: 'Spell “afspraak” with two a’s.', fa: 'واژه «afspraak» با دو حرف a نوشته می‌شود.' });
  const timePresent = /woensdag/i.test(text) && /(?:14[.:]00|twee uur)/i.test(text);
  return { issues, timePresent, canRevise: issues.length > 0, fixtureOnly: true };
}

export function eligibleDelayedReview({ firstTry, assisted, overridden, originalSession, currentSession, observedAt, reviewAt }) {
  return firstTry && !assisted && !overridden && originalSession !== currentSession && reviewAt - observedAt >= 4 * 60 * 60 * 1000;
}

export const SKILLS = [
  { id: 'reading', name: 'Lezen', en: 'Reading', fa: 'خواندن', eyebrow: '01', title: 'Haal de juiste informatie uit een bericht.', detail: 'An appointment notice, a calendar, one useful decision.', faDetail: 'پیام قرار، تقویم و یک تصمیم کاربردی.', icon: 'book', color: 'blue' },
  { id: 'listening', name: 'Luisteren', en: 'Listening', fa: 'شنیدن', eyebrow: '02', title: 'Luister eerst. Kijk daarna pas naar de tekst.', detail: 'A short voicemail with optional support.', faDetail: 'پیام صوتی کوتاه با کمک اختیاری.', icon: 'headphones', color: 'amber' },
  { id: 'speaking', name: 'Spreken', en: 'Speaking', fa: 'صحبت کردن', eyebrow: '03', title: 'Leg het probleem uit. Vind samen een oplossing.', detail: 'A simulated exchange with a practical outcome.', faDetail: 'گفت‌وگوی نمونه با نتیجه‌ای کاربردی.', icon: 'message', color: 'teal' },
  { id: 'writing', name: 'Schrijven', en: 'Writing', fa: 'نوشتن', eyebrow: '04', title: 'Bevestig je nieuwe afspraak in een kort bericht.', detail: 'Notice an error, understand it, revise your own draft.', faDetail: 'اشتباه را ببینید، بفهمید و متن خود را اصلاح کنید.', icon: 'pen', color: 'purple' },
];

export const STORY = {
  title: 'De tas op de trein',
  en: 'The bag on the train',
  fa: 'کیف در قطار',
  paragraphs: [
    'Sam neemt de trein naar Gent. Op de stoel naast hem ligt een blauwe tas. De vrouw die daar zat, is net uitgestapt. Sam kijkt door het raam, maar hij ziet haar niet meer. Hij neemt de tas mee naar de treinbegeleider.',
    'In de tas zit een boek met een naam op de eerste bladzijde. De treinbegeleider belt naar het station. Een uur later krijgt Sam goed nieuws: de vrouw heeft haar tas terug. Zij stuurt een kort bericht: “Dank u wel! In dat boek staan de foto’s van mijn familie.”',
  ],
  translations: {
    en: ['Sam takes the train to Ghent. A blue bag is on the seat next to him. The woman who sat there has just got off. Sam looks through the window, but cannot see her anymore. He takes the bag to the train attendant.', 'There is a book in the bag, with a name on the first page. The attendant calls the station. An hour later, Sam receives good news: the woman has her bag back. She sends a short message: “Thank you! That book contains photos of my family.”'],
    fa: ['سام با قطار به گنت می‌رود. روی صندلی کناری یک کیف آبی است. زنی که آنجا نشسته بود، تازه پیاده شده است. سام از پنجره نگاه می‌کند، اما دیگر او را نمی‌بیند. کیف را نزد مأمور قطار می‌برد.', 'در کیف کتابی است که روی صفحه اولش نامی نوشته شده است. مأمور قطار به ایستگاه زنگ می‌زند. یک ساعت بعد سام خبر خوبی می‌گیرد: زن کیفش را پس گرفته است. او پیام کوتاهی می‌فرستد: «خیلی ممنون! عکس‌های خانواده‌ام در آن کتاب است.»'],
  },
};
