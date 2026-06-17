import { useMemo, useState, type ReactNode } from "react";
import type {
  ClaimProvenance,
  EvidenceAnchoredExplainability,
  TriggerAttribution,
} from "../../services/api";

const verdictTheme: Record<string, string> = {
  Supported: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  "Partial Attempt": "bg-amber-500/10 text-amber-500 border-amber-500/20",
  Neutral: "bg-muted text-muted-foreground border-border",
  Contradiction: "bg-red-500/10 text-red-400 border-red-500/20",
  "Cross-Modal Mismatch": "bg-purple-500/10 text-purple-400 border-purple-500/20",
  "No Trigger": "bg-sky-500/10 text-sky-400 border-sky-500/20",
  "Insufficient Evidence": "bg-muted text-muted-foreground border-border",
};

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
    .replace(/\s*Ã¢â‚¬Â¢\s*/g, " / ")
    .replace(/\s*â€¢\s*/g, " / ")
    .replace(/\|{2,}/g, " / ")
    .replace(/[-|]{4,}/g, " ")
    .replace(/^\s*[-*]\s+/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
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
  timestamp, startSeconds, onJumpTo,
}: {
  timestamp?: string | null;
  startSeconds?: number | null;
  onJumpTo?: (seconds: number) => void;
}) {
  if (!onJumpTo || startSeconds == null) {
    return timestamp ? <span className="text-[11px] font-bold text-muted-foreground">{timestamp}</span> : null;
  }
  return (
    <button type="button" onClick={() => onJumpTo(startSeconds)}
      className="rounded-full border border-border bg-card px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground transition-colors hover:border-primary hover:text-primary">
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

function TriggerCard({ attribution, onJumpTo }: { attribution: TriggerAttribution; onJumpTo?: (seconds: number) => void }) {
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
                <JumpButton timestamp={attribution.evidenceSpan.timestamp} startSeconds={attribution.evidenceSpan.startSeconds} onJumpTo={onJumpTo} />
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
              <div className={`rounded-lg border p-3 ${bgAccent}`}>
                <p className={`text-[11px] font-extrabold uppercase tracking-wider ${accent}`}>{label}</p>
                <p className="mt-1 text-[12px] font-bold text-foreground">{cleanEvidenceText(attribution.policyReference.reference)}</p>
                <p className="mt-2 text-[13px] leading-relaxed text-foreground/80">{cleanEvidenceText(attribution.policyReference.clause)}</p>
                {attribution.policyReference.provenance && (
                  <p className="mt-2 text-[11px] font-medium text-muted-foreground">{cleanEvidenceText(attribution.policyReference.provenance)}</p>
                )}
              </div>
            );
          })()}
        </div>

        <div className="space-y-3">
          <div className="rounded-lg border border-border bg-card p-3">
            <p className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">Reasoning</p>
            <div className="mt-2 max-h-[15rem] overflow-y-auto pr-1 text-[13px] leading-relaxed text-foreground/80">
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

function ClaimCard({ claim, onJumpTo }: { claim: ClaimProvenance; onJumpTo?: (seconds: number) => void }) {
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
                <JumpButton timestamp={claim.claimSpan.timestamp} startSeconds={claim.claimSpan.startSeconds} onJumpTo={onJumpTo} />
              </div>
              <p className="mt-2 text-[13px] italic leading-relaxed text-foreground/80">
                &ldquo;{cleanEvidenceText(claim.claimSpan.quote)}&rdquo;
              </p>
            </div>
          )}

          {claim.retrievedPolicy && (
            <div className="rounded-lg border border-teal-500/15 bg-teal-500/5 p-3">
              <p className="text-[11px] font-extrabold uppercase tracking-wider text-teal-400">Retrieved Policy</p>
              <p className="mt-1 text-[12px] font-bold text-foreground">{cleanEvidenceText(claim.retrievedPolicy.reference)}</p>
              <p className="mt-2 text-[13px] leading-relaxed text-foreground/80">{cleanEvidenceText(claim.retrievedPolicy.clause)}</p>
              <p className="mt-2 text-[11px] font-medium text-muted-foreground">{cleanEvidenceText(claim.provenance)}</p>
            </div>
          )}
        </div>

        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">Reasoning</p>
          <div className="mt-2 max-h-[15rem] overflow-y-auto pr-1 text-[13px] leading-relaxed text-foreground/80">
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
  explainability, onJumpTo,
}: {
  explainability?: EvidenceAnchoredExplainability | null;
  onJumpTo?: (seconds: number) => void;
}) {
  const triggerAttributions = explainability?.triggerAttributions ?? [];
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
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-[10px] font-extrabold uppercase tracking-wider text-primary">
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
            ? <ClaimCard claim={currentItem as ClaimProvenance} onJumpTo={onJumpTo} />
            : <TriggerCard attribution={currentItem as TriggerAttribution} onJumpTo={onJumpTo} />}
        </PagedSection>
      </div>
    </section>
  );
}
