import type { StudyCopy, StudyStep } from "@/lib/client/study";

/** Interface copy for the guided Dutch/English learning journey. */
export const studyCopy = {
  wordReference: {
    nl: "Woordenlijst",
    en: "Word reference",
  },
  whatWouldYouLikeToLearn: {
    nl: "Waar wil je over leren?",
    en: "What would you like to learn about?",
  },
  topic: {
    nl: "Onderwerp",
    en: "Topic",
  },
  wordsYouCanUseStraightAway: {
    nl: "Woorden om meteen te gebruiken",
    en: "Words you can use straight away",
  },
  iMReadyToPractise: {
    nl: "Ik ben klaar om te oefenen",
    en: "I’m ready to practise",
  },
  whatWouldYouLikeToSay: {
    nl: "Wat wil je vandaag kunnen zeggen?",
    en: "What would you like to say today?",
  },
  chooseOneTopicLearnUsefulWords: {
    nl: "Kies één onderwerp. Leer de woorden, oefen in een echte situatie en maak je antwoord steeds duidelijker.",
    en: "Choose one topic. Learn useful words, practise in context and make your answer clearer.",
  },
  chooseAnotherLevel: {
    nl: "Kies een ander niveau",
    en: "Choose another level",
  },
  chooseWhereToBeginEveryLevel: {
    nl: "Je kiest zelf waar je begint. Alle niveaus zijn open.",
    en: "Choose where to begin. Every level is open.",
  },
  aClearNextStepEveryTime: {
    nl: "Een duidelijke stap, elke keer",
    en: "A clear next step, every time",
  },
  chooseYourLevel: {
    nl: "Kies je niveau",
    en: "Choose your level",
  },
  everyLevelHasTheSameFour: {
    nl: "Elk niveau heeft dezelfde vier vaardigheden. Kies daarna een onderwerp dat je aanspreekt.",
    en: "Every level has the same four skills. Then choose a topic that interests you.",
  },
  thePreLevelsAreBridgeStages: {
    nl: "De pre-niveaus zijn tussenstappen binnen dit leerpad. Oefenmateriaal en niveau-indeling wachten op deskundige taalbeoordeling.",
    en: "The pre-levels are bridge stages within this course. Content and level placement await specialist language review.",
  },
  retry: {
    nl: "Opnieuw proberen",
    en: "Try again",
  },
  moreExamples: {
    nl: "Meer voorbeelden",
    en: "More examples",
  },
  wordReferenceRegion: {
    nl: "Woordenlijst van dit niveau",
    en: "Word reference for this level",
  },
  searchWordPlaceholder: {
    nl: "Zoek een woord of voorbeeld…",
    en: "Find a word or example…",
  },
  searchWordLabel: {
    nl: "Zoek in de woordenlijst",
    en: "Search the word reference",
  },
  previous: {
    nl: "Vorige",
    en: "Previous",
  },
  nextWords: {
    nl: "Volgende woorden",
    en: "Next words",
  },
  browseTopics: {
    nl: "Bladeren door onderwerpen",
    en: "Browse topics",
  },
  nextTopics: {
    nl: "Volgende",
    en: "Next",
  },
  noWords: {
    nl: "Geen woorden gevonden. Probeer een kortere zoekterm.",
    en: "No words found. Try a shorter search.",
  },
  loadingWords: {
    nl: "De woorden laden…",
    en: "Loading words…",
  },
  breadcrumb: {
    nl: "Je plek in het leerpad",
    en: "Your place in the learning path",
  },
  dashboard: {
    nl: "Dashboard",
    en: "Dashboard",
  },
  levels: {
    nl: "Niveaus",
    en: "Levels",
  },
  topics: {
    nl: "Onderwerpen",
    en: "Topics",
  },
  level: {
    nl: "Niveau",
    en: "Level",
  },
  grammar: {
    nl: "Grammatica",
    en: "Grammar",
  },
  alphabetNumbers: {
    nl: "Alfabet & getallen",
    en: "Alphabet and numbers",
  },
  chooseSkill: {
    nl: "Kies een vaardigheid",
    en: "Choose a skill",
  },
  referenceHeading: {
    nl: "Woordenlijst ·",
    en: "Word reference ·",
  },
  savedWords: {
    nl: "Mijn bewaarde woorden",
    en: "My saved words",
  },
  personalStories: {
    nl: "Mijn persoonlijke verhalen",
    en: "My personal stories",
  },
  grammarInUse: {
    nl: "Grammatica in gebruik",
    en: "Grammar in use",
  },
  close: {
    nl: "Sluiten",
    en: "Close",
  },
  firstWordsSounds: {
    nl: "Eerste woorden en klanken",
    en: "First words and sounds",
  },
  topicSearchPlaceholder: {
    nl: "Zoek bijvoorbeeld familie, sport of werk…",
    en: "Try family, sport or work…",
  },
  topicSearchLabel: {
    nl: "Zoek een onderwerp",
    en: "Search topics",
  },
  filterTheme: {
    nl: "Filter op thema",
    en: "Filter by theme",
  },
  allThemes: {
    nl: "Alle thema’s",
    en: "All themes",
  },
  openPersonalStories: {
    nl: "Mijn persoonlijke verhalen openen",
    en: "Open my personal stories",
  },
  loadingTopics: {
    nl: "Je onderwerpen laden…",
    en: "Loading your topics…",
  },
  noTopics: {
    nl: "Geen onderwerp gevonden",
    en: "No topic found",
  },
  changeTopicSearch: {
    nl: "Probeer een andere zoekterm of kies alle thema’s.",
    en: "Try a different search or choose all themes.",
  },
  clearFilters: {
    nl: "Wis filters",
    en: "Clear filters",
  },
  includePlanned: {
    nl: "Ook onderwerpen in voorbereiding tonen",
    en: "Show topics still in preparation",
  },
  loadingLesson: {
    nl: "Je oefening laden…",
    en: "Loading your activity…",
  },
  reviewPending: {
    nl: "Taalreview in voorbereiding",
    en: "Language review pending",
  },
  exerciseSteps: {
    nl: "Stappen van de oefening",
    en: "Activity steps",
  },
  prepareInvitation: {
    nl: "Luister, bekijk het voorbeeld en maak zelf een korte zin.",
    en: "Listen, look at the example and make your own short sentence.",
  },
  skillParts: {
    nl: "Onderdelen van deze vaardigheid",
    en: "Parts of this skill",
  },
  keepWordsOpen: {
    nl: "Woorden erbij",
    en: "Keep the words nearby",
  },
  temporaryScore: {
    nl: "Je oefenscore verdwijnt als je deze pagina verlaat.",
    en: "Your practice score disappears when you leave this page.",
  },
  context: {
    nl: "De situatie",
    en: "The situation",
  },
  fictionalAnswer: {
    nl: "Je mag een voorbeeld verzinnen. Je hoeft geen persoonlijke informatie te delen.",
    en: "You may invent an example. You do not need to share personal information.",
  },
  listenSituation: {
    nl: "Luister naar de hele situatie",
    en: "Listen to the complete situation",
  },
  listenInstructions: {
    nl: "Lees eerst de vragen. De antwoorden volgen de opname.",
    en: "Read the questions first. The answers follow the recording.",
  },
  continuousAudio: {
    nl: "Doorlopende luisteropname",
    en: "Continuous listening recording",
  },
  testAudio: {
    nl: "Testtoon; dit is geen uitspraakvoorbeeld.",
    en: "Test tone; this is not a pronunciation example.",
  },
  revealTranscript: {
    nl: "Bekijk de tekst na je poging",
    en: "View the text after your attempt",
  },
  story: {
    nl: "Verhaal",
    en: "Story",
  },
  anotherShortQuestion: {
    nl: "Andere korte vraag",
    en: "Another short question",
  },
  exampleHelp: {
    nl: "Gebruik het als hulp. Probeer daarna je eigen antwoord.",
    en: "Use it as support. Then try your own answer.",
  },
  playOwnRecording: {
    nl: "Je eigen opname terugluisteren",
    en: "Listen to your own recording",
  },
  words: {
    nl: "woorden",
    en: "words",
  },
  nextPart: {
    nl: "Volgend onderdeel",
    en: "Next part",
  },
  temporaryFeedback: {
    nl: "Tijdelijke oefenfeedback",
    en: "Temporary practice feedback",
  },
  feedbackKicker: {
    nl: "OEFENFEEDBACK · ALLEEN OP DEZE PAGINA",
    en: "PRACTICE FEEDBACK · ONLY ON THIS PAGE",
  },
  noReliableScore: {
    nl: "Geen betrouwbare score beschikbaar",
    en: "No reliable score available",
  },
  reviseAnswer: {
    nl: "Verbeter mijn antwoord",
    en: "Improve my answer",
  },
  dashboardKicker: {
    nl: "JOUW NEDERLANDS. STAP VOOR STAP.",
    en: "YOUR DUTCH. STEP BY STEP.",
  },
  startingPoint: {
    nl: "Je startpunt",
    en: "Your starting point",
  },
  fourSkills: {
    nl: "Lezen · Luisteren · Spreken · Schrijven",
    en: "Reading · Listening · Speaking · Writing",
  },
  routeKicker: {
    nl: "ZO WERKT JE LEERROUTE",
    en: "HOW YOUR LEARNING PATH WORKS",
  },
  skillKicker: {
    nl: "KIES JE VAARDIGHEID",
    en: "CHOOSE YOUR SKILL",
  },
  allLevels: {
    nl: "Alle niveaus",
    en: "All levels",
  },
  directoryKicker: {
    nl: "JOUW STARTPUNT",
    en: "YOUR STARTING POINT",
  },
  optionalCoach: {
    nl: "Hulp bij je volgende oefening",
    en: "Help choosing your next practice",
  },
  situationConversations: {
    nl: "Situatiegesprekken",
    en: "Situation conversations",
  },
  conversationInvitation: {
    nl: "Wil je verder oefenen? Kies een kort gesprek waarin je om de beurt antwoordt.",
    en: "Want to practise further? Choose a short conversation and take turns answering.",
  },
  openConversations: {
    nl: "Kies een situatiegesprek",
    en: "Choose a situation conversation",
  },
  extendedPractice: {
    nl: "Verder oefenen",
    en: "Further practice",
  },
  backToTopicPractice: {
    nl: "Terug naar de onderwerpen",
    en: "Back to topic practice",
  },
  savedConversationNotice: {
    nl: "Dit is een aparte oefening met bewaarde gespreksgeschiedenis, zodat je later kunt verdergaan. Er wordt geen oefenscore gegeven.",
    en: "This separate practice keeps conversation history so you can continue later. It does not award a practice score.",
  },
  savedPracticeNotice: {
    nl: "Deze extra oefening bewaart je voortgang en kladtekst. De tijdelijke oefenscores in het gewone onderwerp blijven apart.",
    en: "This extra practice keeps your progress and draft. Temporary scores in the main topic practice remain separate.",
  },
  noConversations: {
    nl: "Voor dit niveau zijn er nog geen situatiegesprekken. Je kunt wel de gewone spreekonderwerpen oefenen.",
    en: "Situation conversations are not available at this level yet. You can practise the main speaking topics.",
  },
  chooseConversation: {
    nl: "Kies een gesprek dat je wilt oefenen.",
    en: "Choose a conversation you would like to practise.",
  },
  stopBeforeLeaving: {
    nl: "Stop eerst je opname voordat je verdergaat.",
    en: "Stop recording before moving on.",
  },
  waitBeforeLeaving: {
    nl: "Je antwoord wordt nog bekeken. Wacht even voordat je verdergaat.",
    en: "Your answer is still being reviewed. Wait a moment before moving on.",
  },
  tapPlayAgain: {
    nl: "Tik nog eens op afspelen om de audio te starten.",
    en: "Tap play again to start the audio.",
  },
  fillGap: {
    nl: "Vul het ontbrekende woord in",
    en: "Fill in the missing word",
  },
  shortAnswer: {
    nl: "Schrijf een kort antwoord",
    en: "Write a short answer",
  },
  stopRecording: {
    nl: "Stop opname",
    en: "Stop recording",
  },
  recordAnswer: {
    nl: "Neem je antwoord op",
    en: "Record your answer",
  },
  microphoneOn: {
    nl: "Je microfoon staat aan. Tik om te stoppen.",
    en: "Your microphone is on. Tap to stop.",
  },
  recordingPrivate: {
    nl: "Je opname wordt niet bewaard. Je kunt ook typen.",
    en: "Your recording is not saved. You can also type.",
  },
  speechPlaceholder: {
    nl: "Neem je stem op, of typ je antwoord…",
    en: "Record your voice, or type your answer…",
  },
  writingPlaceholder: {
    nl: "Schrijf hier in het Nederlands…",
    en: "Write here in Dutch…",
  },
  prepareAudio: {
    nl: "Audio voorbereiden…",
    en: "Preparing audio…",
  },
  startRecordingAudio: {
    nl: "Start de opname",
    en: "Start the recording",
  },
  understandingTitle: {
    nl: "Wat heb je begrepen?",
    en: "What did you understand?",
  },
  clearerAnswer: {
    nl: "Zo maak je je antwoord duidelijker",
    en: "How to make your answer clearer",
  },
  wellUnderstood: {
    nl: "Goed begrepen",
    en: "Well understood",
  },
  reviewAgain: {
    nl: "Bekijk dit nog eens",
    en: "Review this again",
  },
  practiceDisclaimer: {
    nl: "Oefenfeedback, geen officieel examenresultaat. Er wordt niets aan je voortgang toegevoegd.",
    en: "Practice feedback, not an official exam result. Nothing is added to your progress.",
  },
  firstPractice: {
    nl: "Begin met een kleine stap",
    en: "Start with a small step",
  },
  chooseActivity: {
    nl: "Kies een",
    en: "Choose a",
  },
} satisfies Record<string, StudyCopy>;

export const studySteps: { id: StudyStep; title: StudyCopy }[] = [
  { id: "prepare", title: { nl: "Voorbereiden", en: "Prepare" } },
  { id: "practise", title: { nl: "Oefenen", en: "Practise" } },
  { id: "check", title: { nl: "Zelf proberen", en: "Try it yourself" } },
];

export const studyWordClasses: Record<string, string> = {
  noun: "zelfstandig naamwoord",
  verb: "werkwoord",
  adjective: "bijvoeglijk naamwoord",
  adverb: "bijwoord",
  expression: "uitdrukking",
  other: "woord",
};

export const studyStageDescriptions: Record<string, { nl: string; en: string }> = {
  "pre-a1": {
    nl: "Letters, getallen, tijd en je eerste kennismaking.",
    en: "Letters, numbers, time and first introductions.",
  },
  a1: {
    nl: "Eenvoudige vragen en herkenbare dagelijkse situaties.",
    en: "Simple questions and familiar daily situations.",
  },
  "pre-a2": {
    nl: "Verbind korte zinnen en vertel iets over jezelf.",
    en: "Connect short sentences and talk about yourself.",
  },
  a2: {
    nl: "Maak afspraken, geef een reden en schrijf een kort bericht.",
    en: "Make arrangements, give a reason and write a short message.",
  },
  "pre-b1": {
    nl: "Vertel wat er gebeurde en vraag door als iets onduidelijk is.",
    en: "Explain what happened and ask for clarification.",
  },
  b1: {
    nl: "Vertel ervaringen en geef een begrijpelijke mening.",
    en: "Share experiences and explain your opinion.",
  },
  "pre-b2": {
    nl: "Vergelijk mogelijkheden en bouw je uitleg verder uit.",
    en: "Compare options and develop your explanation.",
  },
  b2: {
    nl: "Bespreek voor- en nadelen in het dagelijks leven, werk en studie.",
    en: "Discuss advantages and disadvantages in life, work and study.",
  },
  "pre-c1": {
    nl: "Verfijn je argumenten, woordkeuze en toon.",
    en: "Refine your reasoning, word choice and tone.",
  },
  c1: {
    nl: "Begrijp nuance en communiceer nauwkeurig in complexe situaties.",
    en: "Understand nuance and communicate precisely in complex situations.",
  },
  "pre-c2": {
    nl: "Verbind perspectieven en pas je stijl doelgericht aan.",
    en: "Connect perspectives and adapt your style purposefully.",
  },
  c2: {
    nl: "Interpreteer impliciete betekenissen en formuleer met precisie.",
    en: "Interpret implied meaning and express yourself precisely.",
  },
};

export const studyRoute = [
  {
    icon: "flag",
    nl: "Kies je niveau",
    en: "Choose your level",
    hint: {
      nl: "Van je eerste woorden tot een genuanceerd gesprek.",
      en: "From your first words to a nuanced conversation.",
    },
  },
  {
    icon: "book",
    nl: "Verken een onderwerp",
    en: "Explore a topic",
    hint: {
      nl: "Leer woorden en zinnen die je meteen kunt gebruiken.",
      en: "Learn words and phrases you can use straight away.",
    },
  },
  {
    icon: "message",
    nl: "Probeer het zelf",
    en: "Try it yourself",
    hint: {
      nl: "Lees, luister, spreek of schrijf in een herkenbare situatie.",
      en: "Read, listen, speak or write in a familiar situation.",
    },
  },
  {
    icon: "refresh",
    nl: "Verbeter je antwoord",
    en: "Improve your answer",
    hint: {
      nl: "Bekijk de uitleg en probeer het nog eens zonder voorbeeld.",
      en: "Read the explanation and try again without the example.",
    },
  },
] as const;

export const studyDimensions = {
  task: { nl: "Inhoud", en: "Content" },
  grammar: { nl: "Grammatica", en: "Grammar" },
  vocabulary: { nl: "Woordkeuze", en: "Word choice" },
  organisation: { nl: "Opbouw", en: "Organisation" },
} satisfies Record<string, StudyCopy>;

export const studyLabels = {
  continueAt: (stage: string): StudyCopy => ({ nl: `Verder met ${stage}`, en: `Continue with ${stage}` }),
  practiseAt: (stage: string): StudyCopy => ({ nl: `Aan de slag op ${stage}`, en: `Practise at ${stage}` }),
  chooseActivity: (reading: boolean): StudyCopy => ({
    nl: reading ? "Kies een verhaal" : "Kies een situatie",
    en: reading ? "Choose a story" : "Choose a situation",
  }),
  example: (shown: boolean): StudyCopy => ({
    nl: shown ? "Voorbeeld verbergen" : "Bekijk een voorbeeldantwoord",
    en: shown ? "Hide example" : "Reveal an example answer",
  }),
  response: (speaking: boolean): StudyCopy => ({
    nl: speaking ? "Je herkende woorden" : "Jouw antwoord",
    en: speaking ? "Your recognised words" : "Your answer",
  }),
  review: (busy: boolean): StudyCopy => ({
    nl: busy ? "Je antwoord bekijken…" : "Bekijk mijn feedback",
    en: busy ? "Reviewing your answer…" : "Review my answer",
  }),
  questionFeedback: (n: number): StudyCopy => ({
    nl: `Begripsfeedback voor vraag ${n}`,
    en: `Comprehension feedback for question ${n}`,
  }),
  questionAnswer: (n: number) => `Antwoord op vraag ${n}`,
  wordGuideline: (min: number, max: number): StudyCopy => ({
    nl: min > 1 ? `Richtlijn: ${min}–${max} woorden` : `Korte zinnen zijn genoeg · maximaal ${max} woorden`,
    en: min > 1 ? `Guide: ${min}–${max} words` : `Short sentences are enough · up to ${max} words`,
  }),
  topicIntroduction: (reading: boolean): StudyCopy => ({
    nl: reading
      ? "Kies een onderwerp. Leer eerst de woorden en ontdek daarna een verhaal."
      : "Kies een onderwerp. Bereid je voor en probeer het daarna zelf.",
    en: "Choose a topic. Prepare useful language, practise in context, then try it yourself.",
  }),
  recordingLimit: (seconds: number): StudyCopy => ({
    nl: `Maximaal ${seconds} seconden per opname. Je kunt daarna opnieuw proberen. Er wordt geen uitspraakscore berekend.`,
    en: `Up to ${seconds} seconds per recording. You can try again afterwards. No pronunciation score is calculated.`,
  }),
};

export const studyReviewComparison: StudyCopy = {
  nl: "Vergelijk met het voorbeeld",
  en: "Compare with the reference answer",
};

export const studySemanticReviewCopy = {
  action: { nl: "Beoordeel mijn antwoord", en: "Review my answer" },
  explanation: {
    nl: "Laat dit antwoord apart op betekenis beoordelen. Dit gebruikt één feedbackaanvraag uit je toelage.",
    en: "Request a separate review of this answer's meaning. This uses one feedback request from your allowance.",
  },
  scope: {
    nl: "Deze score gaat alleen over het begrip in dit ene antwoord. Het is geen score voor de volledige oefening en beoordeelt je uitspraak niet.",
    en: "This score concerns comprehension in this answer only. It is not a score for the full activity and does not assess pronunciation.",
  },
} satisfies Record<string, StudyCopy>;

export const studyStarterTopics = [
  { topic: "personal-identity", title: { nl: "Je naam en adres", en: "Your name and address" } },
  { topic: "languages", title: { nl: "Woorden en klanken", en: "Words and sounds" } },
  { topic: "time-management", title: { nl: "Getallen en tijd", en: "Numbers and time" } },
  { topic: "family", title: { nl: "Jezelf en je familie", en: "You and your family" } },
  { topic: "cities-countries", title: { nl: "De weg vragen", en: "Asking for directions" } },
] as const;
