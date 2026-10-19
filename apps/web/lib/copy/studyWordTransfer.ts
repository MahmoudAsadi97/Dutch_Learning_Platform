export const studyWordTransferCopy = {
  moreUses: {
    nl: "Gebruik in een andere situatie",
    en: "Use in another situation",
  },
  formsOnly: {
    nl: "Bekijk andere woordvormen",
    en: "See other word forms",
  },
  forms: {
    nl: "Vormen en voorbeelden",
    en: "Forms and examples",
  },
  plural: {
    nl: "Meervoud",
    en: "Plural",
  },
  tryFirst: {
    nl: "Probeer zelf een zin. Bekijk daarna een mogelijk voorbeeld.",
    en: "Try a sentence yourself. Then look at one possible example.",
  },
  showExample: {
    nl: "Toon een mogelijk voorbeeld",
    en: "Show one possible example",
  },
  hideExample: {
    nl: "Verberg het voorbeeld",
    en: "Hide the example",
  },
  example: {
    nl: "Een mogelijk voorbeeld",
    en: "One possible example",
  },
  anotherSituation: {
    nl: "Volgende situatie",
    en: "Next situation",
  },
  temporaryDraft: {
    nl: "Je oefenzin wordt niet bewaard of beoordeeld.",
    en: "Your practice sentence is not saved or assessed.",
  },
} as const;

export function wordTransferResponseLabel(term: string) {
  return {
    nl: `Jouw zin met ‘${term}’`,
    en: `Your sentence with ‘${term}’`,
  };
}

export function wordTransferPosition(position: number, total: number) {
  return {
    nl: `Situatie ${position} van ${total}`,
    en: `Situation ${position} of ${total}`,
  };
}
