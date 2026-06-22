/** Remove trailing inline evidence lists when structured citations are shown separately. */
export function stripRedundantEvidenceNarrative(
  rootCause: string | undefined | null,
  hasStructuredEvidence: boolean,
): string {
  if (!rootCause || !hasStructuredEvidence) return rootCause || "";
  return rootCause
    .replace(/\s*Evidence\s*[:\u2014-]\s*.+$/is, "")
    .replace(/\s*Supporting quotes?\s*[:\u2014-]\s*.+$/is, "")
    .trim();
}

/**
 * Clean speaker-attributed derived text for manager display: strips the LLM
 * "[Focus window …]" debug block that older cached reports embedded in the
 * customer context, while preserving line breaks for whitespace-pre-wrap.
 */
export function cleanDisplayText(value?: string | null): string {
  return (value || "")
    .replace(/\r/g, "")
    .replace(/\n*-{2,}\s*\[Focus window[\s\S]*$/i, "")
    .replace(/\[Focus window[^\]]*\]/gi, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/** Deduplicate citation/quote lists by normalized quote text. */
export function uniqueByQuote<T extends { quote?: string | null }>(items: T[]): T[] {
  const seen = new Set<string>();
  const out: T[] = [];
  for (const item of items) {
    const key = (item.quote || "").trim().toLowerCase();
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(item);
  }
  return out;
}
