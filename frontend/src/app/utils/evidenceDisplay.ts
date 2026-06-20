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
