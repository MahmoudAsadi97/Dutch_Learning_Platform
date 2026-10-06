/**
 * Query keys, built in one place so that invalidation after a mutation names the same key the readers use.
 * Keys are arrays: the first element is the domain, the rest narrows (stage, skill, id).
 */
export const queryKeys = {
  me: () => ["me"] as const,
  today: () => ["today"] as const,
  usage: () => ["usage"] as const,
  progress: () => ["progress"] as const,
  curriculum: {
    all: () => ["curriculum"] as const,
    catalog: () => ["curriculum", "catalog"] as const,
    stage: (stageId: string) => ["curriculum", "stage", stageId] as const,
    topics: (stageId: string, skill: string) => ["curriculum", "topics", stageId, skill] as const,
    topic: (stageId: string, skill: string, topicId: string) =>
      ["curriculum", "topic", stageId, skill, topicId] as const,
  },
  words: {
    all: () => ["words"] as const,
    due: (limit: number) => ["words", "due", limit] as const,
    list: () => ["words", "list"] as const,
  },
  stories: {
    library: () => ["stories", "library"] as const,
    episode: (episodeId: string) => ["stories", "episode", episodeId] as const,
  },
  videos: {
    library: () => ["videos", "library"] as const,
    video: (videoId: string) => ["videos", "video", videoId] as const,
  },
  missions: {
    catalog: () => ["missions", "catalog"] as const,
    mission: (missionId: string) => ["missions", "mission", missionId] as const,
  },
} as const;
