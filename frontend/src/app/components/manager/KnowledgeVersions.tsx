import { useEffect, useState } from "react";
import { History, RotateCcw, Check, Loader2, RefreshCw } from "lucide-react";
import {
  listKnowledgeVersions,
  activateKnowledgeVersion,
  reprocessAgainstVersion,
  type KnowledgeVersion,
} from "../../services/api";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../../components/ui/dialog";

function formatWhen(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleString();
}

export function KnowledgeVersions() {
  const [versions, setVersions] = useState<KnowledgeVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [pendingActivate, setPendingActivate] = useState<KnowledgeVersion | null>(null);

  async function reload() {
    setLoading(true);
    try {
      setVersions(await listKnowledgeVersions());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
  }, []);

  const activeNumber = versions.find((v) => v.isActive)?.versionNumber ?? null;

  async function handleActivate() {
    if (!pendingActivate) return;
    setBusy(true);
    setStatus(null);
    try {
      const res = await activateKnowledgeVersion(pendingActivate.id);
      setStatus(`Restored and activated version ${res.activeVersion}. Existing results keep their original tags — reprocess to apply.`);
      setPendingActivate(null);
      await reload();
    } catch {
      setStatus("Failed to activate version.");
    } finally {
      setBusy(false);
    }
  }

  async function handleReprocessStale() {
    setBusy(true);
    setStatus(null);
    try {
      const res = await reprocessAgainstVersion({ scope: "stale", target: "active" });
      const n = res.count ?? res.reprocessed ?? 0;
      setStatus(n > 0
        ? `Queued ${n} stale result${n === 1 ? "" : "s"} to reprocess against version ${activeNumber ?? ""}.`
        : "No stale results to reprocess — everything is on the active version.");
    } catch {
      setStatus("Failed to reprocess stale results.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-foreground">
          <History className="w-5 h-5 text-primary" />
          <div>
            <h3 className="text-[15px] font-bold">Knowledge Versions</h3>
            <p className="text-[12px] text-muted-foreground">
              Every knowledge change creates a version. Activate an earlier one to roll back; existing
              call results are preserved with the version they were judged against.
            </p>
          </div>
        </div>
        <Button variant="outline" onClick={handleReprocessStale} disabled={busy || loading} className="rounded-xl">
          <RefreshCw className="w-4 h-4 mr-2" />
          Reprocess stale results
        </Button>
      </div>

      {status && (
        <div className="text-[12px] rounded-xl border border-border bg-muted/40 px-4 py-2 text-foreground">
          {status}
        </div>
      )}

      {loading ? (
        <div className="flex items-center gap-2 text-muted-foreground text-[13px] py-8 justify-center">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading versions…
        </div>
      ) : (
        <div className="space-y-2">
          {versions.map((v) => (
            <div
              key={v.id}
              className="flex items-center justify-between gap-4 rounded-2xl border border-border bg-card px-4 py-3"
            >
              <div className="flex items-center gap-3 min-w-0">
                <Badge
                  variant={v.isActive ? "default" : "secondary"}
                  className="rounded-lg font-bold shrink-0"
                >
                  v{v.versionNumber}
                </Badge>
                <div className="min-w-0">
                  <p className="text-[13px] font-semibold text-foreground truncate">{v.summary || "Knowledge update"}</p>
                  <p className="text-[11px] text-muted-foreground">{formatWhen(v.createdAt)}</p>
                </div>
              </div>
              <div className="shrink-0">
                {v.isActive ? (
                  <span className="inline-flex items-center gap-1 text-[12px] font-semibold text-primary">
                    <Check className="w-4 h-4" /> Active
                  </span>
                ) : (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="rounded-lg text-[12px]"
                    onClick={() => setPendingActivate(v)}
                    disabled={busy}
                  >
                    <RotateCcw className="w-3.5 h-3.5 mr-1.5" /> Activate
                  </Button>
                )}
              </div>
            </div>
          ))}
          {versions.length === 0 && (
            <p className="text-[13px] text-muted-foreground py-8 text-center">No versions yet.</p>
          )}
        </div>
      )}

      <Dialog open={!!pendingActivate} onOpenChange={(open) => !open && setPendingActivate(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Activate version {pendingActivate?.versionNumber}?</DialogTitle>
            <DialogDescription>
              This restores the knowledge base to “{pendingActivate?.summary || "this version"}”. Existing
              call results are not changed — they keep the version they were originally judged against. New
              processing and reprocessing will use the activated version.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPendingActivate(null)} disabled={busy}>
              Cancel
            </Button>
            <Button onClick={handleActivate} disabled={busy}>
              {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RotateCcw className="w-4 h-4 mr-2" />}
              Activate v{pendingActivate?.versionNumber}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
