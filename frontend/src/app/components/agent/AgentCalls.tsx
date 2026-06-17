import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import {
  AlertTriangle, CheckCircle2, Clock3, Loader2, PhoneCall, ShieldAlert, TrendingUp,
} from "lucide-react";
import { getInteractions, type InteractionSummary } from "../../services/api";

function scoreTone(score: number): string {
  if (score >= 85) return "text-success";
  if (score >= 75) return "text-primary";
  return "text-warning";
}

function StatCard({
  label, value, icon: Icon, accent,
}: {
  label: string;
  value: string | number;
  icon: typeof PhoneCall;
  accent: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl border border-border bg-card/40 p-4 shadow-sm transition-colors hover:border-primary/30">
      <div className="space-y-1">
        <p className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">{label}</p>
        <p className="text-2xl font-black text-foreground">{value}</p>
      </div>
      <div className={`rounded-xl p-3 ${accent}`}>
        <Icon className="h-5 w-5" />
      </div>
    </div>
  );
}

export function AgentCalls() {
  const [calls, setCalls] = useState<InteractionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCalls = async () => {
      try {
        setCalls(await getInteractions());
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load calls");
      } finally {
        setLoading(false);
      }
    };
    void loadCalls();
  }, []);

  const stats = useMemo(() => {
    const completed = calls.filter((c) => c.status === "completed").length;
    const reviewNeeded = calls.filter((c) => c.hasViolation).length;
    const scored = calls.filter((c) => typeof c.overallScore === "number");
    const avg = scored.length
      ? Math.round(scored.reduce((sum, c) => sum + c.overallScore, 0) / scored.length)
      : 0;
    return { completed, reviewNeeded, avg };
  }, [calls]);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-3 text-sm text-muted-foreground">Loading your calls…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="mx-auto mb-3 h-10 w-10 text-warning" />
          <p className="text-sm font-semibold text-foreground">Failed to load calls</p>
          <p className="mt-1 text-xs text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4 md:p-8">
      {/* Header */}
      <div>
        <p className="text-[11px] font-extrabold uppercase tracking-[0.24em] text-primary">MY CALLS</p>
        <h2 className="mt-1.5 text-2xl font-bold tracking-tight text-foreground">Review recent conversations</h2>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          This view only includes your own sessions. Open any call to review the transcript, emotion shifts,
          and AI coaching insights — and flag anything that looks wrong for your manager.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total" value={calls.length} icon={PhoneCall} accent="bg-primary/10 text-primary" />
        <StatCard label="Completed" value={stats.completed} icon={CheckCircle2} accent="bg-success/10 text-success" />
        <StatCard label="Need Review" value={stats.reviewNeeded} icon={ShieldAlert} accent="bg-warning/10 text-warning" />
        <StatCard label="Avg Score" value={`${stats.avg}%`} icon={TrendingUp} accent="bg-blue-500/10 text-blue-500" />
      </div>

      {/* Calls list */}
      <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
        <h3 className="text-[15px] font-bold text-foreground">Recent Calls</h3>
        <p className="mb-4 mt-0.5 text-[12px] text-muted-foreground">Personal sessions only, newest first.</p>

        {calls.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border bg-muted/20 px-6 py-12 text-center">
            <PhoneCall className="mx-auto mb-3 h-10 w-10 text-muted-foreground/60" />
            <h3 className="mb-1 text-[15px] font-semibold text-foreground">No calls yet</h3>
            <p className="text-[13px] text-muted-foreground">Once your sessions are processed, they will appear here.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {calls.map((call) => (
              <Link
                key={call.id}
                to={`/agent/calls/${call.id}`}
                className="group block rounded-2xl border border-border bg-background/40 p-4 transition-all hover:border-primary/40 hover:bg-muted/20 hover:shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[14px] font-bold text-foreground">{call.date}</span>
                      <span className="text-muted-foreground/50">•</span>
                      <span className="text-[13px] text-muted-foreground">{call.time}</span>
                      {call.hasViolation && (
                        <span className="inline-flex items-center gap-1 rounded-full border border-warning/30 bg-warning/10 px-2.5 py-0.5 text-[11px] font-bold text-warning">
                          <ShieldAlert className="h-3 w-3" />
                          Review needed
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px] text-muted-foreground">
                      <span>{call.duration}</span>
                      <span className="text-muted-foreground/40">•</span>
                      <span>{call.language}</span>
                      <span className="text-muted-foreground/40">•</span>
                      <span className="capitalize">{call.status}</span>
                      <span className="text-muted-foreground/40">•</span>
                      <span className="inline-flex items-center gap-1">
                        <Clock3 className="h-3.5 w-3.5" />
                        {call.responseTime}
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className={`text-3xl font-black leading-none ${scoreTone(call.overallScore)}`}>
                      {call.overallScore}%
                    </div>
                    <div className={`mt-1 text-[12px] font-bold ${call.resolved ? "text-success" : "text-destructive"}`}>
                      {call.resolved ? "Resolved" : "Unresolved"}
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
