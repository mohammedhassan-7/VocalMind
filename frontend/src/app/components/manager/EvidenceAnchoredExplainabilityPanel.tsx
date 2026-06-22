import { useMemo, useState, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type {
  ClaimProvenance,
  EvidenceAnchoredExplainability,
  TriggerAttribution,
  UtteranceData,
} from "../../services/api";
import { resolveJumpSeconds } from "../../utils/utteranceNavigation";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "../ui/accordion";

const verdictTheme: Record<string, string> = {
  Supported: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  "Partial Attempt": "bg-amber-500/10 text-amber-500 border-amber-500/20",
  Neutral: "bg-muted text-muted-foreground border-border",
  Contradiction: "bg-red-500/10 text-red-400 border-red-500/20",
  "Cross-Modal Mismatch": "bg-purple-500/10 text-purple-400 border-purple-500/20",
  "No Trigger": "bg-sky-500/10 text-sky-400 border-sky-500/20",
  "Insufficient Evidence": "bg-muted text-muted-foreground border-border",
};

// Emotion attributions that did not actually fire add no review value to this
// supervisor deck and duplicate the always-on Emotion Analysis tab. We keep
// emotion cards only when they represent a real finding.
const NON_FIRING_EMOTION_VERDICTS = new Set(["No Trigger", "Neutral", "Insufficient Evidence"]);

function formatPercent(value?: number | null): string {
  const numeric = Number(value);
  if (value == null || !Number.isFinite(numeric)) return "N/A";
  return `${Math.round(Math.max(0, Math.min(1, numeric)) * 100)}%`;
}

function cleanEvidenceText(value?: string | null): string {
  return (value || "")
    .replace(/\r/g, "")
    .replace(/^\s*#{1,6}\s*/gm, "")
    .replace(/<!--.*?-->/gs, " ")
    .replace(/\[Focus window.*?\]\s*/gi, "")
    .replace(/^(agent|customer):\s*/gi, "")
    .replace(/\s*Ã¢â‚¬Â¢\s*/g, " / ")
    .replace(/\s*â€¢\s*/g, " / ")
    .replace(/\|{2,}/g, " / ")
    .replace(/[-|]{4,}/g, " ")
    .replace(/^\s*[-*]\s+/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
}

const isDelimiterRow = (line: string) => /^\s*\|(?:\s*:?-{1,}:?\s*\|)+\s*$/.test(line);
const tableCells = (line: string) =>
  line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());

// Build a valid GFM table from grouped rows (header + delimiter + body), padding
// short rows to the widest column count so remark-gfm parses every row.
function buildMarkdownTable(rows: string[][]): string {
  const colCount = Math.max(...rows.map((r) => r.length));
  const pad = (r: string[]) => {
    const padded = [...r];
    while (padded.length < colCount) padded.push("");
    return padded;
  };
  const lines = [`| ${pad(rows[0]).join(" | ")} |`, `|${" --- |".repeat(colCount)}`];
  for (let i = 1; i < rows.length; i++) lines.push(`| ${pad(rows[i]).join(" | ")} |`);
  return lines.join("\n");
}

// Retrieved policy clauses are stored as GFM pipe tables, but the chunking that
// produced them mangles the structure two ways: it drops the `| --- | --- |`
// delimiter row, and it often flattens the whole table onto one line so that the
// row boundary survives only as an empty `| |` cell. Either way remark-gfm
// renders literal "| ID | Rule |" text. Reconstruct a valid table so it renders.
// Non-table clauses (which don't start with `|`) are returned untouched.
function normalizePolicyMarkdown(value?: string | null): string {
  const source = (value || "").replace(/\r/g, "").trim();
  if (!source.startsWith("|") || !source.includes("|")) return source;

  // Flattened single-line table: split on cells, group rows on empty cells.
  if (!source.includes("\n")) {
    const rows: string[][] = [];
    let current: string[] = [];
    for (const cell of tableCells(source)) {
      if (cell === "") {
        if (current.length) rows.push(current);
        current = [];
      } else {
        current.push(cell);
      }
    }
    if (current.length) rows.push(current);
    return rows.length >= 2 ? buildMarkdownTable(rows) : source;
  }

  // Multi-line table: inject a delimiter after the header row if missing.
  const lines = source.split("\n");
  const isRow = (line: string) => /^\s*\|.*\|\s*$/.test(line);
  const out: string[] = [];
  for (let i = 0; i < lines.length; i++) {
    out.push(lines[i]);
    const prevIsRow = i > 0 && isRow(lines[i - 1]);
    const isHeader = isRow(lines[i]) && !isDelimiterRow(lines[i]) && !prevIsRow;
    if (isHeader && (lines[i + 1] === undefined || !isDelimiterRow(lines[i + 1]))) {
      out.push(`|${" --- |".repeat(tableCells(lines[i]).length)}`);
    }
  }
  return out.join("\n");
}

// Renders a retrieved SOP/policy/KB clause, reconstructing any mangled pipe table
// into a styled GFM table. Shared by the claim-provenance and trigger-attribution
// cards so both render clauses identically.
function PolicyClauseMarkdown({ clause }: { clause?: string | null }) {
  return (
    <div className="text-[13px] leading-relaxed text-foreground/80">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ children }) => (
            <div className="overflow-x-auto rounded-lg border border-border my-2">
              <table className="w-full text-[12px] border-collapse">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-muted/50">{children}</thead>,
          tbody: ({ children }) => <tbody>{children}</tbody>,
          tr: ({ children }) => <tr className="border-t border-border">{children}</tr>,
          th: ({ children }) => (
            <th className="px-3 py-2 text-left text-[11px] font-bold uppercase tracking-wider text-muted-foreground whitespace-nowrap">
              {children}
            </th>
          ),
          td: ({ children }) => <td className="px-3 py-2 text-foreground/80 align-top">{children}</td>,
          p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
          code: ({ children }) => (
            <code className="px-1 py-0.5 rounded bg-muted/50 text-[11px] font-mono">{children}</code>
          ),
        }}
      >
        {normalizePolicyMarkdown(clause)}
      </ReactMarkdown>
    </div>
  );
}

function VerdictBadge({ verdict }: { verdict: string }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider ${
      verdictTheme[verdict] || verdictTheme.Neutral
    }`}>
      {verdict}
    </span>
  );
}

function JumpButton({
  timestamp, startSeconds, utteranceIndex, utterances, onJumpTo,
}: {
  timestamp?: string | null;
  startSeconds?: number | null;
  utteranceIndex?: number | null;
  utterances: UtteranceData[];
  onJumpTo?: (seconds: number) => void;
}) {
  const jumpSeconds = resolveJumpSeconds(utterances, { utteranceIndex, startSeconds, timestamp });
  if (!onJumpTo || jumpSeconds == null) {
    return timestamp ? <span className="text-[11px] font-bold text-muted-foreground">{timestamp}</span> : null;
  }
  return (
    <button type="button" onClick={() => onJumpTo(jumpSeconds)}
      className="rounded-full border border-border bg-card px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground transition-colors hover:border-primary hover:text-primary cursor-pointer">
      {timestamp || "Jump"}
    </button>
  );
}

function Pager({ count, index, onChange }: { count: number; index: number; onChange: (next: number) => void }) {
  if (count <= 1) return null;
  return (
    <div className="flex items-center gap-2">
      <button type="button" onClick={() => onChange(Math.max(0, index - 1))} disabled={index === 0}
        className="rounded-full border border-border bg-card px-3 py-1 text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground disabled:opacity-40">
        Prev
      </button>
      <span className="text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground">
        {index + 1} / {count}
      </span>
      <button type="button" onClick={() => onChange(Math.min(count - 1, index + 1))} disabled={index === count - 1}
        className="rounded-full border border-border bg-card px-3 py-1 text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground disabled:opacity-40">
        Next
      </button>
    </div>
  );
}

function TriggerCard({ attribution, utterances, onJumpTo }: { attribution: TriggerAttribution; utterances: UtteranceData[]; onJumpTo?: (seconds: number) => void }) {
  return (
    <article className="rounded-xl border border-border bg-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-extrabold uppercase tracking-[0.24em] text-muted-foreground">
            {cleanEvidenceText(attribution.triggerType)}
          </p>
          <h4 className="mt-1 text-base font-extrabold text-foreground">
            {cleanEvidenceText(attribution.title)}
          </h4>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-muted px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground">
            Confidence {formatPercent(attribution.confidence)}
          </span>
          <VerdictBadge verdict={attribution.verdict} />
        </div>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-3">
          {attribution.evidenceSpan && (
            <div className="rounded-lg border border-border bg-muted/30 p-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
                  Evidence Span{attribution.evidenceSpan.speaker ? ` - ${cleanEvidenceText(attribution.evidenceSpan.speaker)}` : ""}
                </p>
                <JumpButton
                  timestamp={attribution.evidenceSpan.timestamp}
                  startSeconds={attribution.evidenceSpan.startSeconds}
                  utteranceIndex={attribution.evidenceSpan.utteranceIndex}
                  utterances={utterances}
                  onJumpTo={onJumpTo}
                />
              </div>
              <p className="mt-2 text-[13px] italic leading-relaxed text-foreground/80">
                &ldquo;{cleanEvidenceText(attribution.evidenceSpan.quote)}&rdquo;
              </p>
            </div>
          )}

          {attribution.policyReference && (() => {
            const src = attribution.policyReference.source;
            const label = src === "kb" ? "Knowledge Base Reference" : src === "sop" ? "SOP Clause" : "Policy Clause";
            const accent = src === "kb" ? "text-indigo-400" : "text-orange-400";
            const bgAccent = src === "kb" ? "bg-indigo-500/5 border-indigo-500/15" : "bg-orange-500/5 border-orange-500/15";
            return (
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="policy" className={`rounded-lg border px-3 py-1 border-b-0 ${bgAccent}`}>
                  <AccordionTrigger className={`text-[11px] font-extrabold uppercase tracking-wider py-2 hover:no-underline ${accent}`}>
                    <div className="flex items-center justify-between w-full pr-2 text-left">
                       <div className="flex items-center gap-2">
                         <span>{label}</span>
                         {attribution.policyReference.severity && (
                           <span className={`px-1.5 py-0.5 rounded text-[9px] uppercase tracking-wider ${
                             attribution.policyReference.severity === 'critical' ? 'bg-red-500/20 text-red-500' :
                             attribution.policyReference.severity === 'major' ? 'bg-amber-500/20 text-amber-500' :
                             'bg-blue-500/20 text-blue-500'
                           }`}>
                             {attribution.policyReference.severity}
                           </span>
                         )}
                       </div>
                       <span className="text-[10px] text-muted-foreground normal-case font-medium">{cleanEvidenceText(attribution.policyReference.reference)}</span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="pt-2 pb-3 border-t border-border/40">
                    <div className="mt-2">
                      <PolicyClauseMarkdown clause={attribution.policyReference.clause} />
                    </div>
                    {attribution.policyReference.provenance && (
                      <p className="mt-2 text-[11px] font-medium text-muted-foreground">{cleanEvidenceText(attribution.policyReference.provenance)}</p>
                    )}
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            );
          })()}
        </div>

        <div className="space-y-3">
          <div className="rounded-lg border border-border bg-card p-3">
            <p className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">Reasoning</p>
            <div className="mt-2 max-h-[15rem] overflow-y-auto pr-1 scrollbar-thin text-[13px] leading-relaxed text-foreground/80">
              {cleanEvidenceText(attribution.reasoning)}
            </div>
          </div>

          {attribution.evidenceChain.length > 0 && (
            <div className="rounded-lg border border-border bg-muted/30 p-3">
              <p className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">Evidence Chain</p>
              <ol className="mt-3">
                {attribution.evidenceChain.map((step, i) => (
                  <li key={step} className="relative flex gap-3 pb-3 last:pb-0">
                    {i < attribution.evidenceChain.length - 1 && (
                      <span className="absolute left-[11px] top-7 bottom-0 w-px bg-border" aria-hidden />
                    )}
                    <span className="z-10 mt-0.5 flex h-6 w-6 flex-none items-center justify-center rounded-full border border-primary/30 bg-primary/10 text-[10px] font-extrabold text-primary">
                      {i + 1}
                    </span>
                    <div className="flex-1 rounded-lg bg-card px-3 py-2 text-[12px] font-medium leading-relaxed text-foreground/80">
                      {cleanEvidenceText(step)}
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

function ClaimCard({ claim, utterances, onJumpTo }: { claim: ClaimProvenance; utterances: UtteranceData[]; onJumpTo?: (seconds: number) => void }) {
  return (
    <article className="rounded-xl border border-teal-500/20 bg-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-extrabold uppercase tracking-[0.24em] text-teal-400">Claim Provenance</p>
          <h4 className="mt-1 text-base font-extrabold text-foreground">{cleanEvidenceText(claim.claimText)}</h4>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-teal-500/10 px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider text-teal-400">
            Similarity {formatPercent(claim.semanticSimilarity)}
          </span>
          <VerdictBadge verdict={claim.nliVerdict} />
        </div>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-3">
          {claim.claimSpan && (
            <div className="rounded-lg border border-border bg-muted/30 p-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">Agent Claim</p>
                <JumpButton
                  timestamp={claim.claimSpan.timestamp}
                  startSeconds={claim.claimSpan.startSeconds}
                  utteranceIndex={claim.claimSpan.utteranceIndex}
                  utterances={utterances}
                  onJumpTo={onJumpTo}
                />
              </div>
              <p className="mt-2 text-[13px] italic leading-relaxed text-foreground/80">
                &ldquo;{cleanEvidenceText(claim.claimSpan.quote)}&rdquo;
              </p>
            </div>
          )}

          {claim.retrievedPolicy && (
            <Accordion type="single" collapsible defaultValue="policy" className="w-full">
              <AccordionItem value="policy" className="rounded-lg border border-teal-500/15 bg-teal-500/5 px-3 py-1 border-b-0">
                <AccordionTrigger className="text-[11px] font-extrabold uppercase tracking-wider py-2 hover:no-underline text-teal-400">
                  <div className="flex items-center justify-between w-full pr-2 text-left">
                     <span>Retrieved Policy</span>
                     <span className="text-[10px] text-muted-foreground normal-case font-medium">{cleanEvidenceText(claim.retrievedPolicy.reference)}</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pt-2 pb-3 border-t border-border/40">
                  <div className="mt-2">
                    <PolicyClauseMarkdown clause={claim.retrievedPolicy.clause} />
                  </div>
                  <p className="mt-4 text-[11px] font-medium text-muted-foreground">{cleanEvidenceText(claim.provenance)}</p>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}
        </div>

        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">Reasoning</p>
          <div className="mt-2 max-h-[15rem] overflow-y-auto pr-1 scrollbar-thin text-[13px] leading-relaxed text-foreground/80">
            {cleanEvidenceText(claim.reasoning)}
          </div>
          <p className="mt-4 text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
            Confidence {formatPercent(claim.confidence)}
          </p>
        </div>
      </div>
    </article>
  );
}

function PagedSection({
  sectionKey, title, accent, count, index, onChange, cardKey, children,
}: {
  sectionKey: string; title: string; accent: string; count: number;
  index: number; onChange: (next: number) => void; cardKey: string; children: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border/50 bg-muted/10 p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className={`text-[11px] font-extrabold uppercase tracking-[0.24em] ${accent}`}>{title}</p>
        <Pager count={count} index={index} onChange={onChange} />
      </div>
      <div key={`${sectionKey}-${cardKey}`} style={{ animation: "evidenceCardTurn 320ms cubic-bezier(0.22, 1, 0.36, 1)" }}>
        {children}
      </div>
    </div>
  );
}

export function EvidenceAnchoredExplainabilityPanel({
  explainability, utterances, onJumpTo,
}: {
  explainability?: EvidenceAnchoredExplainability | null;
  utterances?: UtteranceData[];
  onJumpTo?: (seconds: number) => void;
}) {
  const transcriptUtterances = utterances ?? [];
  const triggerAttributions = (explainability?.triggerAttributions ?? []).filter(
    (item) => item.family !== "emotion" || !NON_FIRING_EMOTION_VERDICTS.has(item.verdict),
  );
  const claimProvenance = explainability?.claimProvenance ?? [];
  const [pages, setPages] = useState<Record<string, number>>({});
  const [activeSection, setActiveSection] = useState<string>("");

  const grouped = useMemo(() => ({
    sop: triggerAttributions.filter((item) => item.family === "sop"),
    policy: triggerAttributions.filter((item) => item.family === "policy"),
    emotion: triggerAttributions.filter((item) => item.family === "emotion"),
    claims: claimProvenance,
  }), [claimProvenance, triggerAttributions]);

  const sections = useMemo(() =>
    [
      { key: "sop", title: "SOP Violations", accent: "text-orange-400", items: grouped.sop, kind: "trigger" as const },
      { key: "policy", title: "Policy Findings", accent: "text-red-400", items: grouped.policy, kind: "trigger" as const },
      { key: "emotion", title: "Span-Level Trigger Attribution", accent: "text-purple-400", items: grouped.emotion, kind: "trigger" as const },
      { key: "claims", title: "Retrieval Provenance Scoring", accent: "text-teal-400", items: grouped.claims, kind: "claim" as const },
    ].filter((section) => section.items.length > 0),
  [grouped]);

  if (!triggerAttributions.length && !claimProvenance.length) return null;

  const getIndex = (key: string, count: number) => Math.min(pages[key] ?? 0, Math.max(0, count - 1));
  const setIndex = (key: string, next: number) => setPages((current) => ({ ...current, [key]: next }));
  const currentSection = sections.find((section) => section.key === activeSection) || sections[0];
  const currentIndex = getIndex(currentSection.key, currentSection.items.length);
  const currentItem = currentSection.items[currentIndex];

  return (
    <section className="rounded-xl border border-border bg-card p-5">
      <style>{`
        @keyframes evidenceCardTurn {
          0% { opacity: 0; transform: perspective(1100px) rotateY(-10deg) translateY(8px) scale(0.985); }
          100% { opacity: 1; transform: perspective(1100px) rotateY(0deg) translateY(0) scale(1); }
        }
      `}</style>

      <div className="flex flex-wrap items-start justify-between gap-4 mb-5">
        <div>
          <p className="text-[11px] font-extrabold uppercase tracking-[0.26em] text-primary">
            Evidence-Anchored Explainability
          </p>
          <h3 className="mt-1.5 text-lg font-extrabold text-foreground">Claim to evidence to verdict</h3>
          <p className="mt-1 max-w-2xl text-[12px] leading-relaxed text-muted-foreground">
            Findings grouped by type as a compact review deck for supervisor evidence review.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-[10px] font-extrabold uppercase tracking-wider ${
            triggerAttributions.length === 0
              ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-400"
              : "border-primary/20 bg-primary/5 text-primary"
          }`}>
            <span className="text-sm leading-none">{triggerAttributions.length}</span> Triggers
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-teal-500/20 bg-teal-500/5 px-3 py-2 text-[10px] font-extrabold uppercase tracking-wider text-teal-400">
            <span className="text-sm leading-none">{claimProvenance.length}</span> Provenance
          </span>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {sections.map((section) => {
            const isActive = section.key === currentSection.key;
            return (
              <button key={section.key} type="button" onClick={() => setActiveSection(section.key)}
                className={`rounded-full border px-3 py-1.5 text-[11px] font-extrabold uppercase tracking-[0.18em] transition-colors ${
                  isActive
                    ? "border-primary/30 bg-primary/10 text-primary"
                    : "border-border bg-muted/30 text-muted-foreground hover:border-primary/20 hover:text-foreground"
                }`}>
                {section.title} ({section.items.length})
              </button>
            );
          })}
        </div>

        <PagedSection
          sectionKey={currentSection.key} title={currentSection.title} accent={currentSection.accent}
          count={currentSection.items.length} index={currentIndex}
          onChange={(next) => setIndex(currentSection.key, next)} cardKey={`${currentSection.key}-${currentIndex}`}>
          {currentSection.kind === "claim"
            ? <ClaimCard claim={currentItem as ClaimProvenance} utterances={transcriptUtterances} onJumpTo={onJumpTo} />
            : <TriggerCard attribution={currentItem as TriggerAttribution} utterances={transcriptUtterances} onJumpTo={onJumpTo} />}
        </PagedSection>
      </div>
    </section>
  );
}
