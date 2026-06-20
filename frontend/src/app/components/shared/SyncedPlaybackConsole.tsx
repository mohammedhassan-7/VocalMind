import { useMemo, type KeyboardEvent, type MouseEvent } from "react";
import { SkipBack, SkipForward, Play, Pause } from "lucide-react";

// ── Emotion → valence mapping (shared with the timeline + markers) ───────────
const EMOTION_VALENCE: Record<string, number> = {
  angry: -1, frustrated: -0.5, sad: -0.35, neutral: 0, happy: 0.85,
};
const EMOTION_ALIASES: Record<string, string> = {
  fearful: "frustrated", surprised: "neutral", disgusted: "angry",
};
function normalizeEmotion(raw: string): string {
  const k = (raw || "").toLowerCase();
  return EMOTION_ALIASES[k] ?? k;
}
export function emotionVar(raw: string): string {
  const e = normalizeEmotion(raw);
  return EMOTION_VALENCE[e] !== undefined ? `var(--${e})` : "var(--neutral)";
}
function valenceOf(raw: string): number {
  return EMOTION_VALENCE[normalizeEmotion(raw)] ?? 0;
}

function formatSeconds(s: number): string {
  const m = Math.floor(Math.max(0, s) / 60);
  const sec = Math.floor(Math.max(0, s) % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

interface CurvePoint {
  startTime: number;
  emotion: string;
  speaker: string;
}

export interface TimelineMarker {
  time: number;
  emotion: string;
  label: string;
  onJump: () => void;
}

interface SyncedPlaybackConsoleProps {
  utterances: CurvePoint[];
  markers: TimelineMarker[];
  duration: number;
  currentTime: number;
  isPlaying: boolean;
  rate: number;
  onTogglePlay: () => void;
  onSkip: (delta: number) => void;
  onSeek: (seconds: number) => void;
  onRate: (rate: number) => void;
}

const W = 1000;
const H = 150;
const SAMPLES = 90;
const RATES = [1, 1.25, 1.5, 2];

// Map a valence in [-1, 1] to a vertical % position inside the chart band.
function yPct(v: number): number {
  const pad = 18;
  const span = H - 36;
  const y = pad + (1 - (v + 1) / 2) * span;
  return (y / H) * 100;
}

function buildKeyframes(utterances: CurvePoint[], speaker: "agent" | "customer"): [number, number][] {
  const pts = utterances
    .filter((u) => u.speaker === speaker)
    .sort((a, b) => a.startTime - b.startTime)
    .map((u): [number, number] => [u.startTime, valenceOf(u.emotion)]);
  return pts.length ? pts : [[0, 0]];
}

function interp(kf: [number, number][], t: number): number {
  if (t <= kf[0][0]) return kf[0][1];
  for (let i = 0; i < kf.length - 1; i++) {
    const [ax, ay] = kf[i];
    const [bx, by] = kf[i + 1];
    if (t >= ax && t <= bx) {
      const f = bx === ax ? 0 : (t - ax) / (bx - ax);
      return ay + (by - ay) * f;
    }
  }
  return kf[kf.length - 1][1];
}

/**
 * The signature VocalMind playback console: an emotion-valence area timeline
 * (customer sentiment) with a dashed agent line, AI-shift jump markers, a live
 * playhead driven by real audio time, and the transport controls.
 */
export function SyncedPlaybackConsole({
  utterances, markers, duration, currentTime, isPlaying, rate,
  onTogglePlay, onSkip, onSeek, onRate,
}: SyncedPlaybackConsoleProps) {
  const dur = duration || 1;

  const { areaPath, linePath, agentPath } = useMemo(() => {
    const custKf = buildKeyframes(utterances, "customer");
    const agentKf = buildKeyframes(utterances, "agent");
    let lp = "";
    let agp = "";
    for (let i = 0; i <= SAMPLES; i++) {
      const t = (i / SAMPLES) * dur;
      const y = (yPct(interp(custKf, t)) / 100) * H;
      const x = (i / SAMPLES) * W;
      lp += (i ? " L" : "M") + x.toFixed(1) + "," + y.toFixed(1);
    }
    for (let j = 0; j <= SAMPLES; j++) {
      const t = (j / SAMPLES) * dur;
      const y = (yPct(interp(agentKf, t)) / 100) * H;
      const x = (j / SAMPLES) * W;
      agp += (j ? " L" : "M") + x.toFixed(1) + "," + y.toFixed(1);
    }
    return { areaPath: `${lp} L${W},${H} L0,${H} Z`, linePath: lp, agentPath: agp };
  }, [utterances, dur]);

  const custKf = useMemo(() => buildKeyframes(utterances, "customer"), [utterances]);
  const playPct = Math.max(0, Math.min(1, currentTime / dur));
  const dotTop = yPct(interp(custKf, currentTime));

  const seekFromEvent = (e: MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    onSeek(Math.max(0, Math.min(dur, x * dur)));
  };
  const timelineKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "ArrowLeft") { e.preventDefault(); onSkip(-5); }
    else if (e.key === "ArrowRight") { e.preventDefault(); onSkip(5); }
    else if (e.key === " " || e.code === "Space") { e.preventDefault(); onTogglePlay(); }
  };

  const ctrlBtn = "inline-flex items-center justify-center w-9 h-9 rounded-[9px] border border-[var(--border)] bg-[var(--surface-2)] text-[var(--text-muted)] hover:text-[var(--text)] transition-colors";

  return (
    <section
      className="sticky top-2 z-30 mt-4 rounded-2xl border border-[var(--border)] bg-card p-4 sm:p-5"
      style={{ boxShadow: "var(--shadow-md)" }}
    >
      <div className="flex items-center gap-3 mb-3">
        <div className="text-[13px] font-semibold text-foreground">Synced Playback</div>
        <span className="inline-flex items-center gap-1.5 h-[22px] px-2 rounded-full text-[11px] font-semibold"
          style={{ background: "var(--accent-soft)", color: "var(--accent-ink)" }}>
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--primary)" }} />
          Transcript &amp; timeline locked to audio
        </span>
        <div className="flex-1" />
        <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] text-[var(--text-faint)]">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ background: "var(--primary)" }} />Customer sentiment
        </span>
        <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] text-[var(--text-faint)]">
          <span className="w-3.5 border-t-2 border-dashed" style={{ borderColor: "var(--text-muted)" }} />Agent
        </span>
      </div>

      {/* Emotion timeline */}
      <div
        role="slider" tabIndex={0}
        aria-label="Emotion timeline scrubber"
        aria-valuemin={0} aria-valuemax={Math.floor(dur)} aria-valuenow={Math.floor(currentTime)}
        onClick={seekFromEvent} onKeyDown={timelineKey}
        className="relative h-[148px] rounded-xl border border-[var(--border)] overflow-hidden cursor-pointer"
        style={{ background: "var(--surface-2)" }}
      >
        {["POSITIVE", "NEUTRAL", "NEGATIVE"].map((lbl, i) => (
          <div key={lbl}
            className="absolute left-2 px-1.5 rounded text-[9px] font-semibold tracking-wide text-[var(--text-faint)]"
            style={{ background: "var(--surface)", top: i === 0 ? 6 : i === 1 ? "50%" : undefined, bottom: i === 2 ? 6 : undefined, transform: i === 1 ? "translateY(-50%)" : undefined }}>
            {lbl}
          </div>
        ))}
        <svg width="100%" height="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="absolute inset-0">
          <defs>
            <linearGradient id="vmEmo" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--happy)" stopOpacity="0.28" />
              <stop offset="48%" stopColor="var(--primary)" stopOpacity="0.12" />
              <stop offset="100%" stopColor="var(--angry)" stopOpacity="0.26" />
            </linearGradient>
          </defs>
          <line x1="0" y1="18" x2={W} y2="18" stroke="var(--border)" strokeWidth="1" strokeDasharray="3 5" />
          <line x1="0" y1="75" x2={W} y2="75" stroke="var(--border-strong)" strokeWidth="1" />
          <line x1="0" y1="132" x2={W} y2="132" stroke="var(--border)" strokeWidth="1" strokeDasharray="3 5" />
          <path d={agentPath} fill="none" stroke="var(--text-muted)" strokeWidth="1.6" strokeDasharray="4 4" strokeOpacity="0.55" vectorEffect="non-scaling-stroke" />
          <path d={areaPath} fill="url(#vmEmo)" />
          <path d={linePath} fill="none" stroke="var(--primary)" strokeWidth="2.4" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
        </svg>
        {markers.map((m, i) => (
          <button key={i} type="button"
            onClick={(e) => { e.stopPropagation(); m.onJump(); }}
            aria-label={m.label}
            className="absolute w-4 h-4 rounded-full p-0 cursor-pointer"
            style={{
              left: `${(m.time / dur) * 100}%`,
              top: `${yPct(interp(custKf, m.time))}%`,
              transform: "translate(-50%,-50%)",
              border: "2.5px solid var(--surface)",
              background: emotionVar(m.emotion),
              boxShadow: "var(--shadow-sm)",
            }} />
        ))}
        <div className="absolute top-0 bottom-0 w-0.5 pointer-events-none" style={{ left: `${playPct * 100}%`, background: "var(--text)" }} />
        <div className="absolute w-[11px] h-[11px] rounded-full pointer-events-none"
          style={{ left: `${playPct * 100}%`, top: `${dotTop}%`, transform: "translate(-50%,-50%)", background: "var(--text)", border: "2px solid var(--surface)", boxShadow: "var(--shadow-sm)" }} />
      </div>

      {/* Transport */}
      <div className="flex items-center gap-3 sm:gap-3.5 mt-3.5">
        <button type="button" onClick={() => onSkip(-10)} aria-label="Back 10 seconds" className={ctrlBtn}>
          <SkipBack className="w-[18px] h-[18px]" />
        </button>
        <button type="button" onClick={onTogglePlay} aria-label="Play or pause"
          className="inline-flex items-center justify-center w-[46px] h-[46px] rounded-full text-[var(--on-accent)]"
          style={{ background: "var(--primary)", boxShadow: "var(--shadow-sm)" }}>
          {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
        </button>
        <button type="button" onClick={() => onSkip(10)} aria-label="Forward 10 seconds" className={ctrlBtn}>
          <SkipForward className="w-[18px] h-[18px]" />
        </button>
        <div className={`${isPlaying ? "vm-eq-on" : ""} hidden sm:flex items-end gap-0.5 h-5 w-[22px]`} aria-hidden="true">
          {[0, 1, 2, 3].map((i) => (
            <span key={i} className="flex-1 rounded-[1px] origin-bottom" style={{ background: "var(--primary)", height: "100%" }} />
          ))}
        </div>
        <div className="flex-1 flex items-center gap-2.5">
          <span className="font-mono text-[12px] text-foreground min-w-[38px]">{formatSeconds(currentTime)}</span>
          <div onClick={seekFromEvent} className="relative flex-1 h-1.5 rounded-full cursor-pointer" style={{ background: "var(--surface-3)" }}>
            <div className="absolute left-0 top-0 bottom-0 rounded-full" style={{ width: `${playPct * 100}%`, background: "var(--primary)" }} />
          </div>
          <span className="font-mono text-[12px] text-[var(--text-faint)] min-w-[38px] text-right">{formatSeconds(dur)}</span>
        </div>
        <div className="hidden sm:flex items-center gap-0.5 p-0.5 rounded-[9px] border border-[var(--border)]" style={{ background: "var(--surface-2)" }}>
          {RATES.map((r) => {
            const on = Math.abs(r - rate) < 0.01;
            return (
              <button key={r} type="button" onClick={() => onRate(r)}
                className="h-6 px-2 rounded-md text-[11px] font-semibold transition-colors"
                style={on
                  ? { background: "var(--surface)", color: "var(--accent-ink)", boxShadow: "var(--shadow-sm)" }
                  : { background: "none", color: "var(--text-faint)" }}>
                {r}×
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
