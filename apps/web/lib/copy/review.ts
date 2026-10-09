/**
 * Which batches of interface Persian a fluent reader has checked (owner decision O2). Until a batch is
 * marked true here, its Persian stays hidden and learners who chose English still see English; the
 * Dutch is always shown. Review a batch at /dev/copy, then set it to true in the same change.
 */
export const PERSIAN_REVIEWED: Record<string, boolean> = {
  nav: false,
  action: false,
  state: false,
  today: false,
  honesty: false,
  welcome: false,
  chip: false,
  about: false,
  episode: false,
  video: false,
  words: false,
  missions: false,
  speech: false,
};
