import { grammarCopy } from "@/lib/copy/grammar";
import { episodeCopy } from "@/lib/copy/episode";
import { storyLearningCopy } from "@/lib/copy/storyLearning";
import { alignmentCopy } from "@/lib/copy/alignment";
import { exerciseCopy } from "@/lib/copy/exercise";
import { missionsCopy } from "@/lib/copy/missions";
import { PERSIAN_REVIEWED } from "@/lib/copy/review";
import { speechCopy } from "@/lib/copy/speech";
import { topicsCopy } from "@/lib/copy/topics";
import { videoCopy } from "@/lib/copy/video";
import { wordsCopy } from "@/lib/copy/words";
import { batchOf, registerBatch, uiCopy, type Copy } from "@/lib/ui-copy";

/** Every batch of interface copy, by name: the catalogue's groups and the per-screen modules. */
export const COPY_BATCHES: Record<string, Record<string, Copy>> = {
  ...uiCopy,
  grammar: grammarCopy,
  episode: episodeCopy,
  video: videoCopy,
  words: wordsCopy,
  missions: missionsCopy,
  speech: speechCopy,
  exercise: exerciseCopy,
  topics: topicsCopy,
  alignment: alignmentCopy,
  storyLearning: storyLearningCopy,
};

for (const [name, entries] of Object.entries(COPY_BATCHES)) registerBatch(name, entries);

/** True once a fluent reader has checked the Persian of the batch this copy belongs to (O2). */
export function persianReviewed(copy: Copy, reviewed: Record<string, boolean> = PERSIAN_REVIEWED): boolean {
  const batch = batchOf(copy);
  return batch !== undefined && reviewed[batch] === true;
}
