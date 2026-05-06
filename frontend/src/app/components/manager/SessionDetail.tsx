import { Link, useParams } from "react-router";
import {
  ArrowLeft, Play, Pause, Flag, Loader2, AlertTriangle as AlertTriangleIcon,
  RefreshCw, SkipBack, SkipForward,
  Volume2, VolumeX, CheckCircle2, Clock, XCircle,
} from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";
import {
  getInteractionDetail, getAudioUrl, reprocessInteraction,
  getInteractionProcessingStatus,
  type InteractionDetail, type ProcessingStatusResult,
} from "../../services/api";
import { EvidenceAnchoredExplainabilityPanel } from "./EvidenceAnchoredExplainabilityPanel";
import { EmotionComparisonPanel } from "./EmotionComparisonPanel";

function getScoreColor(score: number) {
  if (score >= 85) return "var(--success)";
  if (score >= 70) return "var(--primary)";
  if (score >= 50) return "var(--warning)";
  return "var(--destructive)";
}

function getScoreBg(score: number) {
  if (score >= 85) return "rgba(16,185,129,0.08)";
  if (score >= 70) return "rgba(59,130,246,0.08)";
  if (score >= 50) return "rgba(245,158,11,0.08)";
  return "rgba(239,68,68,0.08)";
}

function formatTime(s: number) {
  if (!isFinite(s) || s < 0) return "0:00";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

const STAGE_LABELS: Record<string, string> = {
  diarization: "Speaker Detection",
  stt: "Transcription",
  emotion: "Emotion Analysis",
  reasoning: "LLM Evaluation",
  scoring: "Scoring",
  rag_eval: "RAG Compliance",
};

function PipelineStatus({ status }: { status: ProcessingStatusResult }) {
  return (
    <div className="bg-card rounded-[14px] border border-border p-5">
      <h3 className="text-[14px] font-bold text-foreground mb-3">Pipeline Progress</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
        {status.jobs.map((job) => {
          const label = STAGE_LABELS[job.stage] || job.stage;
          const isCompleted = job.status === "completed";
          const isRunning = job.status === "running" || job.status === "processing";
          const isFailed = job.status === "failed";
          return (
            <div key={job.stage} className="flex flex-col items-center gap-1.5 text-center">
              {isCompleted && <CheckCircle2 className="w-5 h-5 text-success" />}
              {isRunning && <Loader2 className="w-5 h-5 text-primary animate-spin" />}
              {isFailed && <XCircle className="w-5 h-5 text-destructive" />}
              {!isCompleted && !isRunning && !isFailed && <Clock className="w-5 h-5 text-muted-foreground/50" />}
              <span className="text-[10px] font-semibold text-muted-foreground leading-tight">{label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
}

function ScoreRing({ score, size = 90, strokeWidth = 7 }: ScoreRingProps) {
  const r = (size - strokeWidth) / 2;
  const c = size / 2;
  const circumference = 2 * Math.PI * r;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90">
        <circle cx={c} cy={c} r={r} fill="none" stroke="var(--border)" strokeWidth={strokeWidth} />
        <circle
          cx={c} cy={c} r={r} fill="none"
          stroke={getScoreColor(score)} strokeWidth={strokeWidth} strokeLinecap="round"
          strokeDasharray={`${(score / 100) * circumference} ${circumference}`}
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-[20px] font-bold" style={{ color: getScoreColor(score) }}>
          {score}%
        </span>
      </div>
    </div>
  );
}

interface ScoreCardProps {
  label: string;
  value: number;
  suffix?: string;
}

function ScoreCard({ label, value, suffix = "%" }: ScoreCardProps) {
  const displayVal = suffix === "s" ? (isNaN(value) ? 0 : value) : value;
  const color = suffix === "s" ? "var(--muted-foreground)" : getScoreColor(displayVal);
  const bg = suffix === "s" ? "var(--muted)" : getScoreBg(displayVal);
  return (
    <div className="rounded-xl p-3 text-center border border-border/50" style={{ backgroundColor: bg }}>
      <div className="text-[11px] text-muted-foreground mb-1 uppercase tracking-wider font-bold">{label}</div>
      <div className="text-[18px] font-bold" style={{ color }}>{displayVal}{suffix}</div>
      {suffix !== "s" && (
        <div className="mt-1.5 h-1 rounded-full bg-border/30 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(displayVal, 100)}%`, backgroundColor: color }}
          />
        </div>
      )}
    </div>
  );
}

interface AudioPlayerProps {
  src: string | null;
  audioRef: React.RefObject<HTMLAudioElement | null>;
}

function AudioPlayer({ src, audioRef }: AudioPlayerProps) {
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [muted, setMuted] = useState(false);
  const barRef = useRef<HTMLDivElement>(null);

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

  const seek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const el = audioRef.current;
    const bar = barRef.current;
    if (!el || !bar || !el.duration) return;
    const rect = bar.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    el.currentTime = pct * el.duration;
  }, [audioRef]);

  const toggleMute = useCallback(() => {
    const el = audioRef.current;
    if (!el) return;
    el.muted = !el.muted;
    setMuted(el.muted);
  }, [audioRef]);

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  if (!src) {
    return (
      <div className="flex items-center gap-2 py-3">
        <Loader2 className="w-4 h-4 text-muted-foreground animate-spin" />
        <span className="text-[12px] text-muted-foreground">Loading audio...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <audio ref={audioRef} src={src} preload="metadata" />

      <button type="button" onClick={() => skip(-10)} className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-colors">
        <SkipBack className="w-4 h-4" />
      </button>

      <button type="button" onClick={togglePlay} className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/90 transition-colors shadow-sm">
        {playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
      </button>

      <button type="button" onClick={() => skip(10)} className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-colors">
        <SkipForward className="w-4 h-4" />
      </button>

      <span className="text-[11px] font-mono text-muted-foreground w-[72px] text-center shrink-0">
        {formatTime(currentTime)} / {formatTime(duration)}
      </span>

      <div ref={barRef} onClick={seek} className="flex-1 h-6 flex items-center cursor-pointer group">
        <div className="w-full h-1.5 rounded-full bg-border/40 relative overflow-visible">
          <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${progress}%` }} />
          <div
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-primary shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
            style={{ left: `calc(${progress}% - 6px)` }}
          />
        </div>
      </div>

      <button type="button" onClick={toggleMute} className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-colors">
        {muted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
      </button>
    </div>
  );
}

function getNliColor(category: string) {
  switch (category) {
    case "Entailment": return { bg: "bg-success/10", text: "text-success" };
    case "Benign Deviation": return { bg: "bg-primary/10", text: "text-primary" };
    case "Contradiction": return { bg: "bg-destructive/10", text: "text-destructive" };
    case "Policy Hallucination": return { bg: "bg-warning/10", text: "text-warning" };
    default: return { bg: "bg-muted", text: "text-muted-foreground" };
  }
}

function getSeverityStyle(severity: string) {
  switch (severity.toLowerCase()) {
    case "high": return "bg-destructive/10 text-destructive border-destructive/20";
    case "medium": return "bg-warning/10 text-warning border-warning/20";
    case "low": return "bg-primary/10 text-primary border-primary/20";
    default: return "bg-muted text-muted-foreground border-border";
  }
}

export function SessionDetail() {
  const { id } = useParams();
  const [data, setData] = useState<InteractionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [flaggedEvents, setFlaggedEvents] = useState<string[]>([]);
  const [flaggedViolations, setFlaggedViolations] = useState<string[]>([]);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<string[]>([]);
  const [reprocessing, setReprocessing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [audioSrc, setAudioSrc] = useState<string | null>(null);
  const [audioEpoch, setAudioEpoch] = useState(0);
  const [pipelineStatus, setPipelineStatus] = useState<ProcessingStatusResult | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const audioObjectUrlRef = useRef<string | null>(null);

  const handleJumpTo = useCallback((seconds: number) => {
    const el = audioRef.current;
    if (!el) return;
    el.currentTime = seconds;
    el.play().catch(() => {});
  }, []);

  useEffect(() => {
    if (!id) return;
    getInteractionDetail(id)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!id || !data) return;
    const status = String(data.interaction.status || "").toLowerCase();
    if (status !== "pending" && status !== "processing") return;

    let cancelled = false;
    const poll = () => {
      if (cancelled) return;
      getInteractionProcessingStatus(id)
        .then((result) => {
          if (cancelled) return;
          setPipelineStatus(result);
          const allDone = result.jobs.every((j) => j.status === "completed" || j.status === "failed");
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
    if (!id) {
      setAudioSrc(null);
      return;
    }
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
      .catch(() => {
        if (!cancelled) setAudioSrc(null);
      });

    return () => {
      cancelled = true;
      revoke();
    };
  }, [id, audioEpoch]);

  const handleReprocess = async () => {
    if (!id || reprocessing) return;
    setActionError(null);
    setReprocessing(true);
    try {
      await reprocessInteraction(id, { force: true });
      const refreshed = await getInteractionDetail(id, { skipCache: true });
      setData(refreshed);
      setAudioEpoch((n) => n + 1);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to reprocess interaction";
      setActionError(message);
    } finally {
      setReprocessing(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6 animate-pulse">
        <div className="h-5 w-48 bg-muted rounded" />
        <div className="bg-card rounded-[14px] border border-border p-6 space-y-4">
          <div className="flex justify-between">
            <div className="space-y-2">
              <div className="h-4 w-24 bg-muted rounded" />
              <div className="h-6 w-40 bg-muted rounded" />
              <div className="h-3 w-56 bg-muted rounded" />
            </div>
            <div className="w-[90px] h-[90px] rounded-full bg-muted" />
          </div>
          <div className="grid grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-20 bg-muted rounded-xl" />
            ))}
          </div>
          <div className="h-10 bg-muted rounded-lg" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7 h-80 bg-muted rounded-[14px]" />
          <div className="lg:col-span-5 h-80 bg-muted rounded-[14px]" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertTriangleIcon className="w-10 h-10 text-warning mx-auto mb-3" />
          <p className="text-foreground text-sm">Failed to load session</p>
          <p className="text-muted-foreground/80 text-xs mt-1">{error}</p>
        </div>
      </div>
    );
  }

  const interaction = data.interaction;
  const utterances = data.utterances;
  const emotionEvents = data.emotionEvents;
  const isProcessing = ["pending", "processing"].includes(String(interaction.status || "").toLowerCase());

  const emotionAliases: Record<string, string> = {
    fearful: "frustrated",
    sad: "frustrated",
    surprised: "neutral",
    disgusted: "angry",
  };

  const normalizeEmotion = (raw: string) => emotionAliases[raw] ?? raw;

  const getEmotionStyle = (emotion: string) => {
    const e = normalizeEmotion(emotion);
    switch (e) {
      case "neutral":
        return { bg: "var(--muted)", text: "var(--muted-foreground)", label: "Neutral" };
      case "happy":
        return { bg: "rgba(16, 185, 129, 0.1)", text: "var(--success)", label: "Happy" };
      case "angry":
        return { bg: "rgba(239, 68, 68, 0.1)", text: "var(--destructive)", label: "Angry" };
      case "frustrated":
        return { bg: "rgba(245, 158, 11, 0.1)", text: "var(--warning)", label: "Frustrated" };
      default:
        return { bg: "var(--muted)", text: "var(--muted-foreground)", label: "Neutral" };
    }
  };

  const responseTimeVal = parseFloat(String(interaction.responseTime));

  return (
    <div className="p-6 space-y-6">
      {/* Back + Reprocess */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to="/manager/inspector"
          className="inline-flex items-center gap-2 text-[13px] font-semibold text-primary hover:underline"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Session Inspector
        </Link>
        <button
          type="button"
          onClick={() => void handleReprocess()}
          disabled={reprocessing}
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-border px-3 text-[12px] font-semibold text-foreground hover:bg-muted disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${reprocessing ? "animate-spin" : ""}`} />
          {reprocessing ? "Reprocessing..." : "Reprocess"}
        </button>
      </div>

      {actionError && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3 text-[12px] font-medium text-destructive">
          {actionError}
        </div>
      )}

      {data.processingFailures && data.processingFailures.length > 0 && (
        <div className="rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3 text-[12px] text-foreground">
          <p className="font-semibold text-destructive mb-2">Processing errors</p>
          <ul className="list-disc space-y-1 pl-4 text-muted-foreground">
            {data.processingFailures.map((f, i) => (
              <li key={`${f.stage}-${i}`}>
                <span className="font-mono text-[11px] text-foreground">{f.stage}</span>
                {f.errorMessage ? `: ${f.errorMessage}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Pipeline Status (shown while processing) */}
      {isProcessing && pipelineStatus && <PipelineStatus status={pipelineStatus} />}

      {/* Call Header Card */}
      <div className="bg-card rounded-[14px] border border-border p-6 transition-all">
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="text-label mb-2">CALL DETAIL</div>
            <h2 className="text-[22px] font-bold text-foreground mb-2">
              {interaction.agentName}
            </h2>
            <div className="text-[13px] text-muted-foreground mb-3">
              {interaction.date} · {interaction.time} · {interaction.duration} · {interaction.language}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold border ${interaction.resolved ? "bg-success/5 text-success border-success/20" : "bg-destructive/5 text-destructive border-destructive/20"}`}>
                {interaction.resolved ? "Resolved" : "Unresolved"}
              </span>
              {interaction.hasViolation && (
                <span className="px-2.5 py-1 rounded-full text-[11px] font-bold border bg-destructive/10 text-destructive border-destructive/20">
                  Policy Violation
                </span>
              )}
              {isProcessing && (
                <span className="px-2.5 py-1 rounded-full text-[11px] font-bold border bg-primary/10 text-primary border-primary/20">
                  Processing...
                </span>
              )}
            </div>
          </div>
          <ScoreRing score={interaction.overallScore} />
        </div>

        <div className="h-px bg-border mb-6" />

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <ScoreCard label="Empathy" value={interaction.empathyScore} />
          <ScoreCard label="Policy" value={interaction.policyScore} />
          <ScoreCard label="Resolution" value={interaction.resolutionScore} />
          <ScoreCard label="Resp. Time" value={isNaN(responseTimeVal) ? 0 : responseTimeVal} suffix="s" />
          <ScoreCard label="Overall" value={interaction.overallScore} />
        </div>

        <div className="mt-6 border-t border-border pt-6">
          <div className="text-label mb-3">Call Recording</div>
          <AudioPlayer src={audioSrc} audioRef={audioRef} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Transcript */}
        <div className="bg-card rounded-[14px] border border-border p-6 lg:col-span-7">
          <h3 className="text-[16px] font-bold text-foreground mb-1">Transcript</h3>
          <p className="text-[11px] italic text-muted-foreground mb-4">
            {utterances.length} utterance{utterances.length !== 1 ? "s" : ""}
          </p>
          {utterances.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <AlertTriangleIcon className="w-8 h-8 mb-2 opacity-40" />
              <span className="text-[13px]">
                {isProcessing ? "Transcription in progress..." : "No transcript data — try reprocessing"}
              </span>
            </div>
          ) : (
            <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
              {utterances.map((u) => {
                const isAgent = u.speaker === "agent";
                const displayEmotion = u.fusedEmotion || u.emotion;
                const displayConfidence = u.fusedConfidence ?? u.confidence;
                const emotionStyle = getEmotionStyle(displayEmotion);
                return (
                  <div key={u.id} className={`flex gap-3 ${isAgent ? "" : "flex-row-reverse"}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${isAgent ? "bg-primary/20 text-primary" : "bg-success/20 text-success"}`}>
                      {isAgent ? "A" : "C"}
                    </div>
                    <div className={`flex-1 p-3 rounded-2xl text-[13px] ${isAgent ? "bg-primary/5 rounded-tl-none" : "bg-success/5 rounded-tr-none"}`}>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-foreground/80">{isAgent ? interaction.agentName : "Customer"}</span>
                          <span
                            className="rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
                            style={{ backgroundColor: emotionStyle.bg, color: emotionStyle.text }}
                          >
                            {emotionStyle.label} {Math.round((displayConfidence || 0) * 100)}%
                          </span>
                          {u.fusedEmotion && u.fusedEmotion !== u.emotion && (
                            <span className="text-[9px] text-muted-foreground/60" title={`Acoustic: ${u.emotion}, Text: ${u.textEmotion || "—"}`}>
                              fused
                            </span>
                          )}
                        </div>
                        <button
                          type="button"
                          onClick={() => handleJumpTo(u.startTime)}
                          className="text-[10px] text-primary font-semibold hover:underline"
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
        </div>

        <div className="space-y-6 lg:col-span-5 lg:sticky lg:top-6 self-start">
          {/* Emotion Events */}
          <div className="bg-card rounded-[14px] border border-border p-6">
            <h3 className="text-[16px] font-bold text-foreground mb-1">Emotion Events</h3>
            <p className="text-[11px] italic text-muted-foreground mb-4">AI-detected emotional shifts</p>
            {emotionEvents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-muted-foreground">
                <span className="text-[13px]">
                  {isProcessing ? "Emotion analysis in progress..." : "No emotion events detected"}
                </span>
              </div>
            ) : (
              <div className="space-y-4 max-h-[360px] overflow-y-auto pr-1">
                {emotionEvents.map((e) => (
                  <div key={e.id} className="p-4 border border-border rounded-xl bg-muted/5 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-[12px] font-bold text-foreground capitalize">{e.fromEmotion} → {e.toEmotion}</span>
                        <span className="text-[11px] text-muted-foreground">Δ {e.delta}</span>
                        <span className="px-1.5 py-0.5 bg-muted/30 rounded text-[10px] font-bold uppercase">{e.speaker}</span>
                      </div>
                      <button
                        onClick={() => handleJumpTo(e.jumpToSeconds)}
                        className="text-[11px] font-bold text-primary hover:underline flex items-center gap-1"
                      >
                        <Play className="w-3 h-3 fill-current" />
                        Jump to {e.timestamp}
                      </button>
                    </div>
                    <p className="text-[12px] text-muted-foreground italic leading-relaxed">"{e.justification}"</p>
                    {flaggedEvents.includes(e.id) ? (
                      feedbackSubmitted.includes(e.id) ? (
                        <div className="text-[11px] text-success font-bold mt-2 pt-2 border-t border-border/50">
                          Feedback recorded
                        </div>
                      ) : (
                        <div className="flex flex-col gap-2 pt-2 border-t border-border/50 sm:flex-row sm:items-center sm:flex-wrap">
                          <span className="text-[11px] text-muted-foreground">
                            Does this AI emotion-shift match what happened on the call?
                          </span>
                          <div className="flex flex-wrap gap-2">
                            <button type="button" onClick={() => setFeedbackSubmitted(prev => [...prev, e.id])} className="text-[11px] font-bold text-success hover:underline">Yes, looks right</button>
                            <button type="button" onClick={() => setFeedbackSubmitted(prev => [...prev, e.id])} className="text-[11px] font-bold text-destructive hover:underline">No, wrong detection</button>
                          </div>
                        </div>
                      )
                    ) : (
                      <div className="flex items-center justify-end pt-2 border-t border-border/50">
                        <button type="button" onClick={() => setFlaggedEvents(prev => [...prev, e.id])} className="text-[11px] font-bold text-muted-foreground hover:text-foreground flex items-center gap-1">
                          <Flag className="w-3 h-3" /> Dispute AI finding
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Policy Violations */}
          <div className="bg-card rounded-[14px] border border-border p-6">
            <h3 className="text-[16px] font-bold text-foreground mb-1">Policy Violations</h3>
            <p className="text-[11px] italic text-muted-foreground mb-4">Non-compliant policy findings</p>
            {data.policyViolations.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-muted-foreground">
                <span className="text-[13px]">
                  {isProcessing ? "Policy evaluation in progress..." : "No policy violations found"}
                </span>
              </div>
            ) : (
              <div className="space-y-4 max-h-[320px] overflow-y-auto pr-1">
                {data.policyViolations.map((v) => (
                  <div key={v.id} className="p-4 bg-destructive/5 border border-destructive/10 rounded-xl space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-[14px] font-bold text-foreground">{v.policyTitle}</span>
                        {v.severity && (
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase border ${getSeverityStyle(v.severity)}`}>
                            {v.severity}
                          </span>
                        )}
                      </div>
                      <span className="text-[12px] font-bold" style={{ color: getScoreColor(v.score) }}>{v.score}%</span>
                    </div>
                    <p className="text-[12px] text-muted-foreground leading-relaxed">{v.reasoning}</p>
                    {flaggedViolations.includes(v.id) ? (
                      feedbackSubmitted.includes(v.id) ? (
                        <div className="text-[11px] text-success font-bold mt-2 pt-2 border-t border-destructive/10">
                          Feedback recorded
                        </div>
                      ) : (
                        <div className="flex flex-col gap-2 pt-2 border-t border-destructive/10 sm:flex-row sm:items-center sm:flex-wrap">
                          <span className="text-[11px] text-muted-foreground">
                            Does this policy violation call match the transcript?
                          </span>
                          <div className="flex flex-wrap gap-2">
                            <button type="button" onClick={() => setFeedbackSubmitted(prev => [...prev, v.id])} className="text-[11px] font-bold text-success hover:underline">Yes, fair finding</button>
                            <button type="button" onClick={() => setFeedbackSubmitted(prev => [...prev, v.id])} className="text-[11px] font-bold text-destructive hover:underline">No, unfair / wrong call</button>
                          </div>
                        </div>
                      )
                    ) : (
                      <div className="flex items-center justify-end pt-2 border-t border-destructive/10">
                        <button type="button" onClick={() => setFlaggedViolations(prev => [...prev, v.id])} className="text-[11px] font-bold text-muted-foreground hover:text-foreground flex items-center gap-1">
                          <Flag className="w-3 h-3" /> Dispute AI finding
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Emotion Comparison Panel */}
      {data.emotionComparison && data.emotionComparison.totalUtterances > 0 && (
        <EmotionComparisonPanel data={data.emotionComparison} />
      )}

      {/* RAG Compliance */}
      {data.ragCompliance && data.ragCompliance.available && (
        <div className="bg-card rounded-[14px] border border-border p-6 space-y-5">
          <h3 className="text-[16px] font-bold text-foreground">RAG Compliance</h3>

          {data.ragCompliance.processAdherence && (
            <div className="rounded-xl border border-border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-[14px] font-semibold text-foreground">SOP Adherence</h4>
                <span className="text-[11px] font-bold" style={{ color: getScoreColor(data.ragCompliance.processAdherence.efficiencyScore * 100) }}>
                  {Math.round(data.ragCompliance.processAdherence.efficiencyScore * 100)}% efficiency
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[12px] text-muted-foreground">Topic:</span>
                <span className="text-[12px] font-semibold text-foreground">{data.ragCompliance.processAdherence.detectedTopic}</span>
              </div>
              <p className="text-[12px] text-muted-foreground">{data.ragCompliance.processAdherence.justification}</p>
              {data.ragCompliance.processAdherence.missingSopSteps.length > 0 && (
                <div className="mt-2">
                  <p className="text-[11px] font-semibold text-destructive mb-1">Missing SOP Steps:</p>
                  <ul className="list-disc ml-5 text-[12px] text-muted-foreground space-y-1">
                    {data.ragCompliance.processAdherence.missingSopSteps.map((step, idx) => (
                      <li key={idx}>{step}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {data.ragCompliance.nliPolicy && (
            <div className="rounded-xl border border-border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-[14px] font-semibold text-foreground">Policy Verification (NLI)</h4>
                {data.ragCompliance.nliPolicy.policyAlignmentScore != null && (
                  <span className="text-[11px] font-bold" style={{ color: getScoreColor(data.ragCompliance.nliPolicy.policyAlignmentScore) }}>
                    {data.ragCompliance.nliPolicy.policyAlignmentScore}% alignment
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[12px] text-muted-foreground">Category:</span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${getNliColor(data.ragCompliance.nliPolicy.nliCategory).bg} ${getNliColor(data.ragCompliance.nliPolicy.nliCategory).text}`}>
                  {data.ragCompliance.nliPolicy.nliCategory}
                </span>
              </div>
              <p className="text-[12px] text-muted-foreground">{data.ragCompliance.nliPolicy.justification}</p>
            </div>
          )}

          {data.ragCompliance.explainability && (
            <EvidenceAnchoredExplainabilityPanel
              explainability={data.ragCompliance.explainability}
              onJumpTo={handleJumpTo}
            />
          )}
        </div>
      )}

      {/* LLM Triggers */}
      {data.llmTriggers && data.llmTriggers.available && (
        <div className="bg-card rounded-[14px] border border-border p-6 transition-all space-y-6">
          <h3 className="text-[16px] font-bold text-foreground mb-1">Automated Evaluation</h3>
          <p className="text-[11px] italic text-muted-foreground mb-4">LLM trigger analysis saved during processing</p>

          {data.llmTriggers.emotionShift && (
            <div className="rounded-xl border border-border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-[14px] font-semibold text-foreground">Emotion Trigger Reasoning</h4>
                {data.llmTriggers.emotionShift.confidenceScore != null && (
                  <span className="text-[11px] font-bold" style={{ color: getScoreColor(data.llmTriggers.emotionShift.confidenceScore * 100) }}>
                    {Math.round(data.llmTriggers.emotionShift.confidenceScore * 100)}% confidence
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[12px] text-muted-foreground">Dissonance:</span>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-warning/10 text-warning">{data.llmTriggers.emotionShift.dissonanceType}</span>
              </div>
              <p className="text-[12px] text-muted-foreground">{data.llmTriggers.emotionShift.rootCause}</p>
              {data.llmTriggers.emotionShift.counterfactualCorrection && (
                <div className="border-l-2 border-primary/40 pl-3 mt-2">
                  <p className="text-[12px] text-foreground italic">Counterfactual: {data.llmTriggers.emotionShift.counterfactualCorrection}</p>
                </div>
              )}
            </div>
          )}

          {data.llmTriggers.processAdherence && (
            <div className="rounded-xl border border-border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-[14px] font-semibold text-foreground">Process Adherence</h4>
                {data.llmTriggers.processAdherence.confidenceScore != null && (
                  <span className="text-[11px] font-bold" style={{ color: getScoreColor(data.llmTriggers.processAdherence.confidenceScore * 100) }}>
                    {Math.round(data.llmTriggers.processAdherence.confidenceScore * 100)}% confidence
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[12px] text-muted-foreground">Topic:</span>
                <span className="text-[12px] font-semibold text-foreground">{data.llmTriggers.processAdherence.detectedTopic}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[12px] text-muted-foreground">Status:</span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${data.llmTriggers.processAdherence.isResolved ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive"}`}>
                  {data.llmTriggers.processAdherence.isResolved ? "Resolved" : "Needs follow-up"}
                </span>
              </div>
              <p className="text-[12px] text-muted-foreground">{data.llmTriggers.processAdherence.justification}</p>
              {data.llmTriggers.processAdherence.missingSopSteps.length > 0 && (
                <ul className="list-disc ml-5 text-[12px] text-muted-foreground space-y-1">
                  {data.llmTriggers.processAdherence.missingSopSteps.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {data.llmTriggers.nliPolicy && (
            <div className="rounded-xl border border-border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-[14px] font-semibold text-foreground">Policy Inference</h4>
                {data.llmTriggers.nliPolicy.policyAlignmentScore != null && (
                  <span className="text-[11px] font-bold" style={{ color: getScoreColor(data.llmTriggers.nliPolicy.policyAlignmentScore) }}>
                    {data.llmTriggers.nliPolicy.policyAlignmentScore}% alignment
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[12px] text-muted-foreground">Category:</span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${getNliColor(data.llmTriggers.nliPolicy.nliCategory).bg} ${getNliColor(data.llmTriggers.nliPolicy.nliCategory).text}`}>
                  {data.llmTriggers.nliPolicy.nliCategory}
                </span>
              </div>
              <p className="text-[12px] text-muted-foreground">{data.llmTriggers.nliPolicy.justification}</p>
            </div>
          )}

          {data.llmTriggers.explainability && (
            <div className="mt-6">
              <EvidenceAnchoredExplainabilityPanel
                explainability={data.llmTriggers.explainability}
                onJumpTo={handleJumpTo}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
