import { Link, useParams } from "react-router";
import {
  ArrowLeft, Play, Pause, Flag, Loader2, AlertTriangle as AlertTriangleIcon,
  RefreshCw, SkipBack, SkipForward,
  Volume2, VolumeX, CheckCircle2, Clock, XCircle,
  TrendingUp, TrendingDown, Minus, MessageSquare, ShieldAlert, BarChart2, Brain,
} from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";
import {
  getInteractionDetail, getAudioUrl, reprocessInteraction,
  getInteractionProcessingStatus,
  type InteractionDetail, type ProcessingStatusResult,
} from "../../services/api";
import { EvidenceAnchoredExplainabilityPanel } from "./EvidenceAnchoredExplainabilityPanel";
import { EmotionComparisonPanel } from "./EmotionComparisonPanel";

// ── Score helpers ──────────────────────────────────────────────────────────────

function getScoreColor(score: number): string {
  if (score >= 85) return "var(--success)";
  if (score >= 70) return "var(--primary)";
  if (score >= 50) return "var(--warning)";
  return "var(--destructive)";
}

function getScoreTailwind(score: number): string {
  if (score >= 85) return "bg-success/10 text-success";
  if (score >= 70) return "bg-primary/10 text-primary";
  if (score >= 50) return "bg-warning/10 text-warning";
  return "bg-destructive/10 text-destructive";
}

function ScoreTrendIcon({ score }: { score: number }) {
  if (score >= 70) return <TrendingUp className="w-3 h-3" aria-hidden="true" />;
  if (score >= 50) return <Minus className="w-3 h-3" aria-hidden="true" />;
  return <TrendingDown className="w-3 h-3" aria-hidden="true" />;
}

function formatTime(s: number): string {
  if (!isFinite(s) || s < 0) return "0:00";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

// ── Pipeline Status ────────────────────────────────────────────────────────────

const STAGE_LABELS: Record<string, string> = {
  diarization: "Speaker Detection",
  stt: "Transcription",
  emotion: "Emotion Analysis",
  reasoning: "LLM Evaluation",
  scoring: "Scoring",
  rag_eval: "RAG Compliance",
};

interface PipelineStatusProps {
  status: ProcessingStatusResult;
}

function PipelineStatus({ status }: PipelineStatusProps) {
  return (
    <div className="bg-card rounded-xl border border-border p-5">
      <h3 className="text-sm font-bold text-foreground mb-3">Pipeline Progress</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3" role="list" aria-label="Processing stages">
        {status.jobs.map((job) => {
          const label = STAGE_LABELS[job.stage] ?? job.stage;
          const isCompleted = job.status === "completed";
          const isRunning = job.status === "running" || job.status === "processing";
          const isFailed = job.status === "failed";
          const stateLabel = isCompleted ? "Completed" : isRunning ? "Running" : isFailed ? "Failed" : "Pending";
          return (
            <div
              key={job.stage}
              role="listitem"
              aria-label={`${label}: ${stateLabel}`}
              className="flex flex-col items-center gap-1.5 text-center"
            >
              {isCompleted && <CheckCircle2 className="w-5 h-5 text-success" aria-hidden="true" />}
              {isRunning && <Loader2 className="w-5 h-5 text-primary animate-spin" aria-hidden="true" />}
              {isFailed && <XCircle className="w-5 h-5 text-destructive" aria-hidden="true" />}
              {!isCompleted && !isRunning && !isFailed && (
                <Clock className="w-5 h-5 text-muted-foreground/50" aria-hidden="true" />
              )}
              <span className="text-xs font-semibold text-muted-foreground leading-tight">{label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Score Ring ─────────────────────────────────────────────────────────────────

interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
}

function ScoreRing({ score, size = 96, strokeWidth = 8 }: ScoreRingProps) {
  const r = (size - strokeWidth) / 2;
  const c = size / 2;
  const circumference = 2 * Math.PI * r;
  const scoreLabel =
    score >= 85 ? "Excellent" : score >= 70 ? "Good" : score >= 50 ? "Fair" : "Needs Improvement";

  return (
    <div
      className="relative shrink-0"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Overall score: ${score}% — ${scoreLabel}`}
    >
      <svg className="w-full h-full -rotate-90" aria-hidden="true">
        <circle cx={c} cy={c} r={r} fill="none" stroke="var(--border)" strokeWidth={strokeWidth} />
        <circle
          cx={c} cy={c} r={r} fill="none"
          stroke={getScoreColor(score)}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${(score / 100) * circumference} ${circumference}`}
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5">
        <span className="text-xl font-bold leading-none" style={{ color: getScoreColor(score) }}>
          {score}%
        </span>
        <span className="text-xs text-muted-foreground font-medium">overall</span>
      </div>
    </div>
  );
}

// ── Score Card ─────────────────────────────────────────────────────────────────

interface ScoreCardProps {
  label: string;
  value: number;
  suffix?: string;
  description?: string;
}

function ScoreCard({ label, value, suffix = "%", description }: ScoreCardProps) {
  const displayVal = suffix === "s" ? (isNaN(value) ? 0 : value) : value;
  const isTime = suffix === "s";
  const colorClass = isTime ? "text-muted-foreground" : getScoreTailwind(displayVal);
  const ariaLabel = `${label}: ${displayVal}${suffix}${description ? `. ${description}` : ""}`;

  return (
    <div
      className={`rounded-xl p-3 text-center border border-border/50 ${isTime ? "bg-muted/40" : colorClass.split(" ")[0]}`}
      aria-label={ariaLabel}
    >
      <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wider font-bold">{label}</div>
      <div className={`text-lg font-bold flex items-center justify-center gap-1 ${isTime ? "text-muted-foreground" : colorClass.split(" ")[1]}`}>
        {!isTime && <ScoreTrendIcon score={displayVal} />}
        {displayVal}{suffix}
      </div>
      {!isTime && (
        <div className="mt-1.5 h-1 rounded-full bg-border/40 overflow-hidden" aria-hidden="true">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(displayVal, 100)}%`, backgroundColor: getScoreColor(displayVal) }}
          />
        </div>
      )}
    </div>
  );
}

// ── Audio Player ───────────────────────────────────────────────────────────────

interface AudioPlayerProps {
  src: string | null;
  audioRef: React.RefObject<HTMLAudioElement | null>;
  currentTime: number;
  setCurrentTime: React.Dispatch<React.SetStateAction<number>>;
}

function AudioPlayer({ src, audioRef, currentTime, setCurrentTime }: AudioPlayerProps) {
  const [playing, setPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [muted, setMuted] = useState(false);

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    const onTime = () => setCurrentTime(el.currentTime);
    const onMeta = () => { setDuration(el.duration); setCurrentTime(el.currentTime); };
    const onEnded = () => { setPlaying(false); setCurrentTime(0); };
    el.addEventListener("play", onPlay);
    el.addEventListener("pause", onPause);
    el.addEventListener("timeupdate", onTime);
    el.addEventListener("loadedmetadata", onMeta);
    el.addEventListener("ended", onEnded);
    return () => {
      el.removeEventListener("play", onPlay);
      el.removeEventListener("pause", onPause);
      el.removeEventListener("timeupdate", onTime);
      el.removeEventListener("loadedmetadata", onMeta);
      el.removeEventListener("ended", onEnded);
    };
  }, [audioRef, src]);

  const togglePlay = useCallback(() => {
    const el = audioRef.current;
    if (!el) return;
    if (el.paused) el.play().catch(() => {});
    else el.pause();
  }, [audioRef]);

  const skip = useCallback((delta: number) => {
    const el = audioRef.current;
    if (!el) return;
    el.currentTime = Math.max(0, Math.min(el.duration || 0, el.currentTime + delta));
  }, [audioRef]);

  const handleSeek = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const el = audioRef.current;
    if (!el) return;
    el.currentTime = Number(e.target.value);
    setCurrentTime(el.currentTime);
  }, [audioRef]);

  const toggleMute = useCallback(() => {
    const el = audioRef.current;
    if (!el) return;
    el.muted = !el.muted;
    setMuted(el.muted);
  }, [audioRef]);

  if (!src) {
    return (
      <div className="flex items-center gap-2 py-3" aria-live="polite">
        <Loader2 className="w-4 h-4 text-muted-foreground animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">Loading audio…</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3" role="group" aria-label="Audio player controls">
      <audio ref={audioRef} src={src} preload="metadata" />

      <button
        type="button"
        onClick={() => skip(-10)}
        aria-label="Skip back 10 seconds"
        className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors"
      >
        <SkipBack className="w-4 h-4" aria-hidden="true" />
      </button>

      <button
        type="button"
        onClick={togglePlay}
        aria-label={playing ? "Pause recording" : "Play recording"}
        className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/90 transition-colors shadow-sm shrink-0"
      >
        {playing
          ? <Pause className="w-4 h-4" aria-hidden="true" />
          : <Play className="w-4 h-4 ml-0.5" aria-hidden="true" />
        }
      </button>

      <button
        type="button"
        onClick={() => skip(10)}
        aria-label="Skip forward 10 seconds"
        className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors"
      >
        <SkipForward className="w-4 h-4" aria-hidden="true" />
      </button>

      <span className="text-xs font-mono text-muted-foreground w-[72px] text-center shrink-0" aria-live="off">
        {formatTime(currentTime)} / {formatTime(duration)}
      </span>

      <input
        type="range"
        min={0}
        max={duration || 0}
        step={0.1}
        value={currentTime}
        onChange={handleSeek}
        aria-label="Seek recording position"
        aria-valuetext={`${formatTime(currentTime)} of ${formatTime(duration)}`}
        className="flex-1 h-1.5 rounded-full accent-primary cursor-pointer"
        style={{ accentColor: "var(--primary)" }}
      />

      <button
        type="button"
        onClick={toggleMute}
        aria-label={muted ? "Unmute recording" : "Mute recording"}
        className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors"
      >
        {muted
          ? <VolumeX className="w-4 h-4" aria-hidden="true" />
          : <Volume2 className="w-4 h-4" aria-hidden="true" />
        }
      </button>
    </div>
  );
}

// ── NLI / Severity helpers ─────────────────────────────────────────────────────

function getNliClass(category: string): string {
  switch (category) {
    case "Entailment":         return "bg-success/10 text-success";
    case "Benign Deviation":   return "bg-primary/10 text-primary";
    case "Contradiction":      return "bg-destructive/10 text-destructive";
    case "Policy Hallucination": return "bg-warning/10 text-warning";
    default:                   return "bg-muted text-muted-foreground";
  }
}

function getSeverityClass(severity: string): string {
  switch (severity.toLowerCase()) {
    case "high":   return "bg-destructive/10 text-destructive border-destructive/20";
    case "medium": return "bg-warning/10 text-warning border-warning/20";
    case "low":    return "bg-primary/10 text-primary border-primary/20";
    default:       return "bg-muted text-muted-foreground border-border";
  }
}

// ── Emotion helpers ────────────────────────────────────────────────────────────

const EMOTION_ALIASES: Record<string, string> = {
  fearful: "frustrated",
  sad: "frustrated",
  surprised: "neutral",
  disgusted: "angry",
};

function normalizeEmotion(raw: string): string {
  return EMOTION_ALIASES[raw] ?? raw;
}

interface EmotionStyle {
  bgClass: string;
  textClass: string;
  label: string;
}

function getEmotionStyle(emotion: string): EmotionStyle {
  switch (normalizeEmotion(emotion)) {
    case "neutral":
      return { bgClass: "bg-muted", textClass: "text-muted-foreground", label: "Neutral" };
    case "happy":
      return { bgClass: "bg-success/10", textClass: "text-success", label: "Happy" };
    case "angry":
      return { bgClass: "bg-destructive/10", textClass: "text-destructive", label: "Angry" };
    case "frustrated":
      return { bgClass: "bg-warning/10", textClass: "text-warning", label: "Frustrated" };
    default:
      return { bgClass: "bg-muted", textClass: "text-muted-foreground", label: "Neutral" };
  }
}

// ── Speaker Avatar ─────────────────────────────────────────────────────────────

interface SpeakerAvatarProps {
  isAgent: boolean;
}

function SpeakerAvatar({ isAgent }: SpeakerAvatarProps) {
  return (
    <div
      aria-hidden="true"
      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
        isAgent ? "bg-primary/20 text-primary" : "bg-success/20 text-success"
      }`}
    >
      {isAgent ? "A" : "C"}
    </div>
  );
}

// ── Section Nav ────────────────────────────────────────────────────────────────

interface SectionNavProps {
  hasViolations: boolean;
  hasRag: boolean;
  hasLlm: boolean;
  hasEmotion: boolean;
}

const NAV_ITEMS = [
  { id: "overview",   label: "Overview",    icon: BarChart2 },
  { id: "transcript", label: "Transcript",  icon: MessageSquare },
  { id: "violations", label: "Violations",  icon: ShieldAlert },
  { id: "emotion",    label: "Emotion",     icon: TrendingUp },
  { id: "compliance", label: "Compliance",  icon: Flag },
  { id: "llm",        label: "LLM Analysis",icon: Brain },
] as const;

type SectionId = typeof NAV_ITEMS[number]["id"];

function SectionNav({ hasViolations, hasRag, hasLlm, hasEmotion }: SectionNavProps) {
  const [active, setActive] = useState<SectionId>("overview");

  const scrollTo = (id: SectionId) => {
    setActive(id);
    const el = document.getElementById(`section-${id}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const visibleItems = NAV_ITEMS.filter((item) => {
    if (item.id === "violations" && !hasViolations) return false;
    if (item.id === "emotion" && !hasEmotion) return false;
    if (item.id === "compliance" && !hasRag) return false;
    if (item.id === "llm" && !hasLlm) return false;
    return true;
  });

  return (
    <nav
      aria-label="Session detail sections"
      className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-border"
    >
      <div className="flex items-center gap-1 px-1 overflow-x-auto scrollbar-hide">
        {visibleItems.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => scrollTo(id)}
            aria-current={active === id ? "location" : undefined}
            className={`
              flex items-center gap-1.5 px-3 py-3 text-sm font-semibold whitespace-nowrap border-b-2 transition-colors shrink-0
              ${active === id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
              }
            `}
          >
            <Icon className="w-3.5 h-3.5" aria-hidden="true" />
            {label}
          </button>
        ))}
      </div>
    </nav>
  );
}

// ── Manager Annotation ─────────────────────────────────────────────────────────
// The agent dispute endpoint is agent-only (POST /emotion-events/{id}/dispute).
// In the manager view we capture an in-session annotation for reference.

type AnnotationState = "idle" | "prompted" | "submitted";

interface ManagerAnnotationProps {
  entityId: string;
  context: "emotion" | "violation";
  annotated: Record<string, AnnotationState>;
  onAnnotate: (id: string) => void;
  onSubmit: (id: string, verdict: "accurate" | "inaccurate") => void;
}

function ManagerAnnotation({ entityId, context, annotated, onAnnotate, onSubmit }: ManagerAnnotationProps) {
  const state = annotated[entityId] ?? "idle";
  const prompt = context === "emotion"
    ? "Does this AI emotion-shift match what happened on the call?"
    : "Does this policy violation accurately reflect the transcript?";

  if (state === "submitted") {
    return (
      <div className="flex items-center gap-1.5 pt-2 border-t border-border/50 text-xs text-success font-semibold">
        <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
        Annotation saved for this session
      </div>
    );
  }

  if (state === "prompted") {
    return (
      <div className="pt-2 border-t border-border/50 space-y-2">
        <p className="text-xs text-muted-foreground">{prompt}</p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => onSubmit(entityId, "accurate")}
            className="text-xs font-bold text-success hover:underline"
          >
            Yes, accurate
          </button>
          <button
            type="button"
            onClick={() => onSubmit(entityId, "inaccurate")}
            className="text-xs font-bold text-destructive hover:underline"
          >
            No, inaccurate
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-end pt-2 border-t border-border/50">
      <button
        type="button"
        onClick={() => onAnnotate(entityId)}
        className="flex items-center gap-1 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
        aria-label={`Add annotation for this ${context === "emotion" ? "emotion event" : "policy violation"}`}
      >
        <Flag className="w-3 h-3" aria-hidden="true" />
        Add annotation
      </button>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

export function SessionDetail() {
  const { id } = useParams();
  const [data, setData] = useState<InteractionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [annotations, setAnnotations] = useState<Record<string, AnnotationState>>({});
  const [reprocessing, setReprocessing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [audioSrc, setAudioSrc] = useState<string | null>(null);
  const [audioEpoch, setAudioEpoch] = useState(0);
  const [pipelineStatus, setPipelineStatus] = useState<ProcessingStatusResult | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);
  const audioObjectUrlRef = useRef<string | null>(null);

  // Refs to each utterance row so we can scroll the active one into view
  // smoothly as the audio plays. Keyed by utterance id.
  const utteranceRefs = useRef<Map<string, HTMLDivElement | null>>(new Map());
  const transcriptScrollRef = useRef<HTMLDivElement | null>(null);
  // Track id of the last utterance we scrolled to so we don't re-scroll on
  // every timeupdate tick (audio fires ~4×/s).
  const lastActiveIdRef = useRef<string | null>(null);
  // Auto-scroll on by default; user can pause it with the toggle.
  const [autoScroll, setAutoScroll] = useState(true);

  const handleJumpTo = useCallback((seconds: number) => {
    const el = audioRef.current;
    if (!el) return;
    el.currentTime = seconds;
    el.play().catch(() => {});
  }, []);

  const handleAnnotate = useCallback((id: string) => {
    setAnnotations((prev) => ({ ...prev, [id]: "prompted" }));
  }, []);

  const handleAnnotationSubmit = useCallback((id: string, _verdict: "accurate" | "inaccurate") => {
    setAnnotations((prev) => ({ ...prev, [id]: "submitted" }));
  }, []);

  useEffect(() => {
    if (!id) return;
    getInteractionDetail(id)
      .then(setData)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Unknown error"))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!id || !data) return;
    const status = String(data.interaction.status ?? "").toLowerCase();
    if (status !== "pending" && status !== "processing") return;

    let cancelled = false;
    const poll = () => {
      if (cancelled) return;
      getInteractionProcessingStatus(id)
        .then((result) => {
          if (cancelled) return;
          setPipelineStatus(result);
          const allDone = result.jobs.every(
            (j) => j.status === "completed" || j.status === "failed"
          );
          if (allDone) {
            getInteractionDetail(id, { skipCache: true }).then(setData).catch(() => {});
          } else {
            setTimeout(poll, 4000);
          }
        })
        .catch(() => {
          if (!cancelled) setTimeout(poll, 8000);
        });
    };
    poll();
    return () => { cancelled = true; };
  }, [id, data?.interaction.status]);

  useEffect(() => {
    if (!id) { setAudioSrc(null); return; }
    let cancelled = false;
    const revoke = () => {
      if (audioObjectUrlRef.current) {
        URL.revokeObjectURL(audioObjectUrlRef.current);
        audioObjectUrlRef.current = null;
      }
    };
    revoke();
    setAudioSrc(null);

    void fetch(getAudioUrl(id), { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error(`audio ${res.status}`);
        return res.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        audioObjectUrlRef.current = url;
        setAudioSrc(url);
      })
      .catch(() => { if (!cancelled) setAudioSrc(null); });

    return () => { cancelled = true; revoke(); };
  }, [id, audioEpoch]);

  // Auto-scroll the active utterance into view as audio plays. We only
  // scroll when the *active utterance id* changes (not on every timeupdate
  // tick) and only when autoScroll is enabled. Uses block:'center' so the
  // active line stays visually anchored in the middle of the panel.
  const utterancesRef = useRef(data?.utterances ?? []);
  utterancesRef.current = data?.utterances ?? [];
  useEffect(() => {
    if (!autoScroll) return;
    const list = utterancesRef.current;
    if (!list.length) return;
    const active = list.find(
      (u) => currentTime >= u.startTime && currentTime <= u.endTime,
    );
    const activeId = active?.id ?? null;
    if (!activeId || activeId === lastActiveIdRef.current) return;
    lastActiveIdRef.current = activeId;
    const node = utteranceRefs.current.get(activeId);
    if (node) {
      node.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [currentTime, autoScroll]);

  const handleReprocess = async () => {
    if (!id || reprocessing) return;
    setActionError(null);
    setReprocessing(true);
    try {
      await reprocessInteraction(id, { force: true });
      const refreshed = await getInteractionDetail(id, { skipCache: true });
      setData(refreshed);
      setAudioEpoch((n) => n + 1);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to reprocess interaction");
    } finally {
      setReprocessing(false);
    }
  };

  // ── Loading skeleton ─────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="p-6 space-y-6 animate-pulse" aria-busy="true" aria-label="Loading session details">
        <div className="h-5 w-48 bg-muted rounded" />
        <div className="bg-card rounded-xl border border-border p-6 space-y-4">
          <div className="flex justify-between">
            <div className="space-y-2">
              <div className="h-4 w-24 bg-muted rounded" />
              <div className="h-6 w-40 bg-muted rounded" />
              <div className="h-3 w-56 bg-muted rounded" />
            </div>
            <div className="w-24 h-24 rounded-full bg-muted" />
          </div>
          <div className="grid grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-20 bg-muted rounded-xl" />
            ))}
          </div>
          <div className="h-10 bg-muted rounded-lg" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7 h-80 bg-muted rounded-xl" />
          <div className="lg:col-span-5 h-80 bg-muted rounded-xl" />
        </div>
      </div>
    );
  }

  // ── Error state ──────────────────────────────────────────────────────────────
  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-96" role="alert">
        <div className="text-center">
          <AlertTriangleIcon className="w-10 h-10 text-warning mx-auto mb-3" aria-hidden="true" />
          <p className="text-foreground text-sm font-semibold">Failed to load session</p>
          <p className="text-muted-foreground text-xs mt-1">{error}</p>
        </div>
      </div>
    );
  }

  const interaction = data.interaction;
  const utterances = data.utterances;
  const emotionEvents = data.emotionEvents;
  const isProcessing = ["pending", "processing"].includes(
    String(interaction.status ?? "").toLowerCase()
  );
  const responseTimeVal = parseFloat(String(interaction.responseTime));
  const hasViolations = data.policyViolations.length > 0;
  const hasRag = Boolean(data.ragCompliance?.available);
  const hasLlm = Boolean(data.llmTriggers?.available);
  const hasEmotion = Boolean(
    data.emotionComparison && data.emotionComparison.totalUtterances > 0
  );

  return (
    <div className="space-y-0">
      {/* ── Top bar ──────────────────────────────────────────────────────────── */}
      <div className="px-6 pt-6 pb-4 flex flex-wrap items-center justify-between gap-3">
        <Link
          to="/manager/inspector"
          className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          Back to Session Inspector
        </Link>
        <button
          type="button"
          onClick={() => void handleReprocess()}
          disabled={reprocessing}
          aria-label={reprocessing ? "Reprocessing session…" : "Reprocess this session"}
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-border px-3 text-sm font-semibold text-foreground hover:bg-muted/40 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${reprocessing ? "animate-spin" : ""}`} aria-hidden="true" />
          {reprocessing ? "Reprocessing…" : "Reprocess"}
        </button>
      </div>

      {/* ── Error banners ─────────────────────────────────────────────────────── */}
      {actionError && (
        <div role="alert" className="mx-6 mb-4 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive">
          {actionError}
        </div>
      )}
      {data.processingFailures && data.processingFailures.length > 0 && (
        <div role="alert" className="mx-6 mb-4 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-foreground">
          <p className="font-semibold text-destructive mb-2">Processing errors</p>
          <ul className="list-disc space-y-1 pl-4 text-muted-foreground text-xs">
            {data.processingFailures.map((f, i) => (
              <li key={`${f.stage}-${i}`}>
                <span className="font-mono text-foreground">{f.stage}</span>
                {f.errorMessage ? `: ${f.errorMessage}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Pipeline status ───────────────────────────────────────────────────── */}
      {isProcessing && pipelineStatus && (
        <div className="px-6 mb-4">
          <PipelineStatus status={pipelineStatus} />
        </div>
      )}

      {/* ── Call header card ──────────────────────────────────────────────────── */}
      <div id="section-overview" className="mx-6 bg-card rounded-xl border border-border p-6" tabIndex={-1}>
        <div className="flex items-start justify-between mb-5">
          <div className="min-w-0">
            <div className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-1.5">
              Call Detail
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-1.5 truncate">
              {interaction.agentName}
            </h2>
            <p className="text-sm text-muted-foreground mb-3">
              {interaction.date} · {interaction.time} · {interaction.duration} · {interaction.language}
            </p>
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                  interaction.resolved
                    ? "bg-success/10 text-success border-success/20"
                    : "bg-destructive/10 text-destructive border-destructive/20"
                }`}
              >
                {interaction.resolved ? "✓ Resolved" : "✗ Unresolved"}
              </span>
              {interaction.hasViolation && (
                <span className="px-2.5 py-1 rounded-full text-xs font-bold border bg-destructive/10 text-destructive border-destructive/20">
                  ⚠ Policy Violation
                </span>
              )}
              {isProcessing && (
                <span className="px-2.5 py-1 rounded-full text-xs font-bold border bg-primary/10 text-primary border-primary/20 inline-flex items-center gap-1">
                  <Loader2 className="w-3 h-3 animate-spin" aria-hidden="true" /> Processing
                </span>
              )}
            </div>
          </div>
          <ScoreRing score={interaction.overallScore} />
        </div>

        <div className="h-px bg-border mb-5" />

        {/* Score cards — Overall is shown in the ring, excluded here */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <ScoreCard label="Empathy" value={interaction.empathyScore} description="Agent empathy score" />
          <ScoreCard label="Policy" value={interaction.policyScore} description="Policy adherence score" />
          <ScoreCard label="Resolution" value={interaction.resolutionScore} description="Issue resolution score" />
          <ScoreCard
            label="Response Time"
            value={isNaN(responseTimeVal) ? 0 : responseTimeVal}
            suffix="s"
            description="Average agent response time in seconds"
          />
        </div>

        <div className="mt-5 border-t border-border pt-5">
          <div className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">
            Call Recording
          </div>
          <AudioPlayer src={audioSrc} audioRef={audioRef} currentTime={currentTime} setCurrentTime={setCurrentTime} />
        </div>
      </div>

      {/* ── Section Navigation ────────────────────────────────────────────────── */}
      <div className="mt-4">
        <SectionNav
          hasViolations={hasViolations}
          hasRag={hasRag}
          hasLlm={hasLlm}
          hasEmotion={hasEmotion}
        />
      </div>

      {/* ── Transcript + Emotion Events ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 px-6 pt-6">

        {/* Transcript */}
        <section
          id="section-transcript"
          aria-labelledby="transcript-heading"
          className="bg-card rounded-xl border border-border p-6 lg:col-span-7"
          tabIndex={-1}
        >
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 id="transcript-heading" className="text-base font-bold text-foreground">Transcript</h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                {utterances.length} utterance{utterances.length !== 1 ? "s" : ""}
              </p>
            </div>
            {utterances.length > 0 && (
              <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  className="h-3.5 w-3.5 rounded border-border accent-primary"
                />
                Follow audio
              </label>
            )}
          </div>

          {utterances.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground" role="status">
              <AlertTriangleIcon className="w-8 h-8 mb-2 opacity-40" aria-hidden="true" />
              <span className="text-sm">
                {isProcessing ? "Transcription in progress…" : "No transcript data — try reprocessing"}
              </span>
            </div>
          ) : (
            <div
              ref={transcriptScrollRef}
              className="space-y-4 max-h-[520px] overflow-y-auto pr-2 scrollbar-thin"
            >
              {utterances.map((u) => {
                const isAgent = u.speaker === "agent";
                const displayEmotion = u.fusedEmotion ?? u.emotion;
                const displayConfidence = u.fusedConfidence ?? u.confidence;
                const emotionStyle = getEmotionStyle(displayEmotion);
                const isFused = Boolean(u.fusedEmotion && u.fusedEmotion !== u.emotion);
                const isActive = currentTime >= u.startTime && currentTime <= u.endTime;
                return (
                  <div
                    key={u.id}
                    ref={(node) => {
                      const map = utteranceRefs.current;
                      if (node) map.set(u.id, node);
                      else map.delete(u.id);
                    }}
                    data-active={isActive}
                    className={`flex gap-3 transition-all duration-300 ${isAgent ? "" : "flex-row-reverse"} ${
                      isActive ? "" : "opacity-80 hover:opacity-100"
                    }`}
                  >
                    <SpeakerAvatar isAgent={isAgent} />
                    <div
                      className={`flex-1 p-3 rounded-2xl text-sm transition-all duration-200 ${
                        isAgent ? "bg-primary/10 rounded-tl-none" : "bg-success/10 rounded-tr-none"
                      } ${
                        isActive
                          ? isAgent
                            ? "ring-2 ring-primary bg-primary/15 shadow-md shadow-primary/20"
                            : "ring-2 ring-success bg-success/20 shadow-md shadow-success/20"
                          : ""
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5 gap-2 flex-wrap">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span
                            className="font-semibold text-foreground/80"
                            aria-label={isAgent ? `Agent: ${interaction.agentName}` : "Customer"}
                          >
                            {isAgent ? interaction.agentName : "Customer"}
                          </span>
                          <span
                            className={`rounded-full px-1.5 py-0.5 text-xs font-semibold ${emotionStyle.bgClass} ${emotionStyle.textClass}`}
                            aria-label={`Emotion: ${emotionStyle.label}, confidence ${Math.round((displayConfidence || 0) * 100)}%`}
                          >
                            {emotionStyle.label} · {Math.round((displayConfidence || 0) * 100)}%
                          </span>
                          {isFused && (
                            <span
                              className="text-xs text-muted-foreground/60 border border-border/50 rounded px-1 py-px"
                              aria-label={`Fused from acoustic ${u.emotion} and text ${u.textEmotion ?? "—"}`}
                            >
                              fused
                            </span>
                          )}
                        </div>
                        <button
                          type="button"
                          onClick={() => handleJumpTo(u.startTime)}
                          aria-label={`Jump to ${u.timestamp} in recording`}
                          className="text-xs text-primary font-semibold hover:underline shrink-0"
                        >
                          {u.timestamp}
                        </button>
                      </div>
                      <p className="text-foreground leading-relaxed">{u.text}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Right sidebar — Emotion Events + Policy Violations */}
        <div className="space-y-6 lg:col-span-5">

          {/* Emotion Events */}
          <section
            aria-labelledby="emotion-events-heading"
            className="bg-card rounded-xl border border-border p-6"
          >
            <div className="mb-4">
              <h3 id="emotion-events-heading" className="text-base font-bold text-foreground">Emotion Events</h3>
              <p className="text-xs text-muted-foreground mt-0.5">AI-detected emotional shifts</p>
            </div>

            {emotionEvents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-muted-foreground" role="status">
                <span className="text-sm">
                  {isProcessing ? "Emotion analysis in progress…" : "No emotion events detected"}
                </span>
              </div>
            ) : (
              <div className="space-y-4">
                {emotionEvents.map((e) => (
                  <article key={e.id} className="p-4 border border-border rounded-xl bg-muted/30 space-y-3">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-bold text-foreground capitalize">
                          {e.fromEmotion} → {e.toEmotion}
                        </span>
                        <span className="text-xs text-muted-foreground">Δ {e.delta}</span>
                        <span className="px-1.5 py-0.5 bg-muted/40 rounded text-xs font-bold uppercase border border-border/50">
                          {e.speaker}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleJumpTo(e.jumpToSeconds)}
                        aria-label={`Jump to emotion shift at ${e.timestamp} in recording`}
                        className="text-xs font-bold text-primary hover:underline flex items-center gap-1 shrink-0"
                      >
                        <Play className="w-3 h-3 fill-current" aria-hidden="true" />
                        {e.timestamp}
                      </button>
                    </div>
                    <p className="text-xs text-muted-foreground italic leading-relaxed">
                      "{e.justification}"
                    </p>
                    <ManagerAnnotation
                      entityId={e.id}
                      context="emotion"
                      annotated={annotations}
                      onAnnotate={handleAnnotate}
                      onSubmit={handleAnnotationSubmit}
                    />
                  </article>
                ))}
              </div>
            )}
          </section>

          {/* Policy Violations */}
          {hasViolations && (
            <section
              id="section-violations"
              aria-labelledby="violations-heading"
              className="bg-card rounded-xl border border-border p-6"
              tabIndex={-1}
            >
              <div className="mb-4">
                <h3 id="violations-heading" className="text-base font-bold text-foreground">Policy Violations</h3>
                <p className="text-xs text-muted-foreground mt-0.5">Non-compliant policy findings</p>
              </div>

              <div className="space-y-4">
                {data.policyViolations.map((v) => (
                  <article key={v.id} className="p-4 bg-destructive/10 border border-destructive/30 rounded-xl space-y-2">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-bold text-foreground">{v.policyTitle}</span>
                        {v.severity && (
                          <span
                            className={`px-1.5 py-0.5 rounded text-xs font-bold uppercase border ${getSeverityClass(v.severity)}`}
                            aria-label={`Severity: ${v.severity}`}
                          >
                            {v.severity}
                          </span>
                        )}
                      </div>
                      <span
                        className="text-sm font-bold"
                        style={{ color: getScoreColor(v.score) }}
                        aria-label={`Compliance score: ${v.score}%`}
                      >
                        {v.score}%
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{v.reasoning}</p>
                    <ManagerAnnotation
                      entityId={v.id}
                      context="violation"
                      annotated={annotations}
                      onAnnotate={handleAnnotate}
                      onSubmit={handleAnnotationSubmit}
                    />
                  </article>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>

      {/* ── Emotion Comparison Panel (collapsed by default to free vertical space) */}
      {hasEmotion && (
        <section
          id="section-emotion"
          aria-labelledby="emotion-intelligence-heading"
          className="mx-6 mt-6 bg-card rounded-xl border border-border"
          tabIndex={-1}
        >
          <details className="group">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-xl px-6 py-4 hover:bg-muted/30 transition-colors">
              <div>
                <h3 id="emotion-intelligence-heading" className="text-base font-bold text-foreground">
                  Emotion Intelligence
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Acoustic vs text vs fused emotion comparison · agreement metrics
                </p>
              </div>
              <span className="text-xs font-semibold text-muted-foreground rounded-md border border-border px-2 py-1 group-open:bg-primary/10 group-open:text-primary group-open:border-primary/30">
                <span className="group-open:hidden">Show details</span>
                <span className="hidden group-open:inline">Hide</span>
              </span>
            </summary>
            <div className="px-6 pb-6">
              <EmotionComparisonPanel data={data.emotionComparison!} />
            </div>
          </details>
        </section>
      )}

      {/* ── RAG Compliance ────────────────────────────────────────────────────── */}
      {hasRag && (
        <section
          id="section-compliance"
          aria-labelledby="rag-compliance-heading"
          className="mx-6 mt-6 bg-card rounded-xl border border-border p-6 space-y-5"
          tabIndex={-1}
        >
          <h3 id="rag-compliance-heading" className="text-base font-bold text-foreground">
            RAG Compliance
          </h3>

          {data.ragCompliance!.processAdherence && (
            <div className="rounded-xl border border-border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-foreground">SOP Adherence</h4>
                <span
                  className="text-xs font-bold"
                  style={{ color: getScoreColor(data.ragCompliance!.processAdherence.efficiencyScore * 100) }}
                >
                  {Math.round(data.ragCompliance!.processAdherence.efficiencyScore * 100)}% efficiency
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Topic:</span>
                <span className="text-xs font-semibold text-foreground">
                  {data.ragCompliance!.processAdherence.detectedTopic}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{data.ragCompliance!.processAdherence.justification}</p>
              {data.ragCompliance!.processAdherence.missingSopSteps.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-semibold text-destructive mb-1">Missing SOP Steps:</p>
                  <ul className="list-disc ml-5 text-xs text-muted-foreground space-y-1">
                    {data.ragCompliance!.processAdherence.missingSopSteps.map((step, idx) => (
                      <li key={idx}>{step}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {data.ragCompliance!.nliPolicy && (
            <div className="rounded-xl border border-border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-foreground">Policy Verification (NLI)</h4>
                {data.ragCompliance!.nliPolicy.policyAlignmentScore != null && (
                  <span
                    className="text-xs font-bold"
                    style={{ color: getScoreColor(data.ragCompliance!.nliPolicy.policyAlignmentScore) }}
                  >
                    {data.ragCompliance!.nliPolicy.policyAlignmentScore}% alignment
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Category:</span>
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getNliClass(data.ragCompliance!.nliPolicy.nliCategory)}`}>
                  {data.ragCompliance!.nliPolicy.nliCategory}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{data.ragCompliance!.nliPolicy.justification}</p>
            </div>
          )}

          {data.ragCompliance!.explainability && (
            <EvidenceAnchoredExplainabilityPanel
              explainability={data.ragCompliance!.explainability}
              onJumpTo={handleJumpTo}
            />
          )}
        </section>
      )}

      {/* ── LLM Triggers / Automated Evaluation ──────────────────────────────── */}
      {hasLlm && (
        <section
          id="section-llm"
          aria-labelledby="llm-eval-heading"
          className="mx-6 mt-6 mb-6 bg-card rounded-xl border border-border p-6 space-y-5"
          tabIndex={-1}
        >
          <div>
            <h3 id="llm-eval-heading" className="text-base font-bold text-foreground">Automated Evaluation</h3>
            <p className="text-xs text-muted-foreground mt-0.5">LLM trigger analysis saved during processing</p>
          </div>

          {data.llmTriggers!.emotionShift && (
            <div className="rounded-xl border border-border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-foreground">Emotion Trigger Reasoning</h4>
                {data.llmTriggers!.emotionShift.confidenceScore != null && (
                  <span
                    className="text-xs font-bold"
                    style={{ color: getScoreColor(data.llmTriggers!.emotionShift.confidenceScore * 100) }}
                  >
                    {Math.round(data.llmTriggers!.emotionShift.confidenceScore * 100)}% confidence
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-muted-foreground">Dissonance:</span>
                <span className="px-2 py-0.5 rounded text-xs font-semibold bg-warning/10 text-warning">
                  {data.llmTriggers!.emotionShift.dissonanceType}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{data.llmTriggers!.emotionShift.rootCause}</p>
              {data.llmTriggers!.emotionShift.counterfactualCorrection && (
                <div className="border-l-2 border-primary/40 pl-3 mt-2">
                  <p className="text-xs text-foreground italic">
                    Counterfactual: {data.llmTriggers!.emotionShift.counterfactualCorrection}
                  </p>
                </div>
              )}
            </div>
          )}

          {data.llmTriggers!.processAdherence && (
            <div className="rounded-xl border border-border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-foreground">Process Adherence</h4>
                {data.llmTriggers!.processAdherence.confidenceScore != null && (
                  <span
                    className="text-xs font-bold"
                    style={{ color: getScoreColor(data.llmTriggers!.processAdherence.confidenceScore * 100) }}
                  >
                    {Math.round(data.llmTriggers!.processAdherence.confidenceScore * 100)}% confidence
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Topic:</span>
                <span className="text-xs font-semibold text-foreground">
                  {data.llmTriggers!.processAdherence.detectedTopic}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Status:</span>
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  data.llmTriggers!.processAdherence.isResolved
                    ? "bg-success/10 text-success"
                    : "bg-destructive/10 text-destructive"
                }`}>
                  {data.llmTriggers!.processAdherence.isResolved ? "✓ Resolved" : "Needs follow-up"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{data.llmTriggers!.processAdherence.justification}</p>
              {data.llmTriggers!.processAdherence.missingSopSteps.length > 0 && (
                <ul className="list-disc ml-5 text-xs text-muted-foreground space-y-1">
                  {data.llmTriggers!.processAdherence.missingSopSteps.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {data.llmTriggers!.nliPolicy && (
            <div className="rounded-xl border border-border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-foreground">Policy Inference</h4>
                {data.llmTriggers!.nliPolicy.policyAlignmentScore != null && (
                  <span
                    className="text-xs font-bold"
                    style={{ color: getScoreColor(data.llmTriggers!.nliPolicy.policyAlignmentScore) }}
                  >
                    {data.llmTriggers!.nliPolicy.policyAlignmentScore}% alignment
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Category:</span>
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getNliClass(data.llmTriggers!.nliPolicy.nliCategory)}`}>
                  {data.llmTriggers!.nliPolicy.nliCategory}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{data.llmTriggers!.nliPolicy.justification}</p>
            </div>
          )}

          {data.llmTriggers!.explainability && (
            <div className="mt-2">
              <EvidenceAnchoredExplainabilityPanel
                explainability={data.llmTriggers!.explainability}
                onJumpTo={handleJumpTo}
              />
            </div>
          )}
        </section>
      )}
    </div>
  );
}
