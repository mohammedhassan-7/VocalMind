import type { UtteranceData } from "../services/api";

/** Parse mm:ss or h:mm:ss labels into seconds. */
export function parseTimestampLabel(label?: string | null): number | null {
  if (!label) return null;
  const parts = label.trim().split(":").map((part) => Number(part.trim()));
  if (!parts.length || parts.some((n) => Number.isNaN(n))) return null;
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  return null;
}

export function resolveJumpSeconds(
  utterances: UtteranceData[],
  opts: {
    utteranceIndex?: number | null;
    startSeconds?: number | null;
    timestamp?: string | null;
  },
): number | null {
  if (opts.startSeconds != null && Number.isFinite(opts.startSeconds)) {
    return opts.startSeconds;
  }
  const fromUtterance = startSecondsForUtteranceIndex(utterances, opts.utteranceIndex);
  if (fromUtterance != null) return fromUtterance;
  return parseTimestampLabel(opts.timestamp);
}

/** Resolve citation utteranceIndex (sequence index) to the matching utterance row. */
export function findUtteranceByIndex(
  utterances: UtteranceData[],
  utteranceIndex?: number | null,
): UtteranceData | null {
  if (utteranceIndex == null || Number.isNaN(utteranceIndex)) {
    return null;
  }
  const bySequence = utterances.find((u) => u.sequenceIndex === utteranceIndex);
  if (bySequence) {
    return bySequence;
  }
  return utterances[utteranceIndex] ?? null;
}

export function startSecondsForUtteranceIndex(
  utterances: UtteranceData[],
  utteranceIndex?: number | null,
): number | null {
  const utterance = findUtteranceByIndex(utterances, utteranceIndex);
  return utterance?.startTime ?? null;
}

/** Utterance active at playback time (half-open interval [start, next.start)). */
export function activeUtteranceAtTime(
  utterances: UtteranceData[],
  currentTime: number,
): UtteranceData | null {
  if (!utterances.length) {
    return null;
  }
  for (let i = 0; i < utterances.length; i++) {
    const utterance = utterances[i];
    const nextStart = utterances[i + 1]?.startTime ?? Number.POSITIVE_INFINITY;
    if (currentTime >= utterance.startTime && currentTime < nextStart) {
      return utterance;
    }
  }
  return null;
}

/** Parse interaction duration labels like "12:34" into seconds. */
export function parseDurationLabel(label?: string | null): number {
  if (!label) return 0;
  const parts = label.trim().split(":").map((part) => Number(part.trim()));
  if (parts.length >= 2 && parts.every((n) => Number.isFinite(n))) {
    return parts[0] * 60 + parts[1];
  }
  return 0;
}
