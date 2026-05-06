import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useNavigate } from "react-router";
import { parse, isValid } from "date-fns";
import {
  Search,
  ArrowDown,
  ArrowUp,
  Loader2,
  AlertTriangle,
  RefreshCw,
  UploadCloud,
  MoreHorizontal,
  Trash2,
  ChevronRight,
  X,
} from "lucide-react";
import {
  createInteraction,
  deleteInteraction,
  getAgents,
  getInteractionDetail,
  getInteractions,
  reprocessInteraction,
  type AgentSummary,
  type InteractionSummary,
} from "../../services/api";

function getFailurePreview(row: InteractionSummary): string {
  const failures = row.processingFailures || [];
  if (!failures.length) {
    return String(row.status).toLowerCase() === "failed"
      ? "Processing failed (no error text stored)."
      : "";
  }

  const grouped = new Map<string, { message: string; stages: string[] }>();
  for (const failure of failures) {
    const stage = (failure.stage || "unknown").trim() || "unknown";
    const message = (failure.errorMessage || "Unknown error").trim() || "Unknown error";
    const key = message.toLowerCase();
    const current = grouped.get(key);
    if (current) {
      current.stages.push(stage);
      continue;
    }
    grouped.set(key, { message, stages: [stage] });
  }

  return Array.from(grouped.values())
    .map((group) =>
      group.stages.length > 1
        ? `${group.stages.join(", ")}: ${group.message}`
        : `${group.stages[0]}: ${group.message}`,
    )
    .join(" | ");
}

function isFailedStatus(row: InteractionSummary): boolean {
  return String(row.status || "").toLowerCase() === "failed";
}

function formatBytes(bytes: number): string {
  if (!bytes) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Backend sends `date` as YYYY-MM-DD and `time` as 12h (e.g. strftime "%I:%M %p"). */
function interactionDateMs(row: InteractionSummary): number {
  const datePart = (row.date || "").trim();
  const timePart = (row.time || "").trim();
  if (!datePart) return 0;

  if (timePart) {
    const combined = `${datePart} ${timePart}`;
    const withPaddedHour = parse(combined, "yyyy-MM-dd hh:mm a", new Date());
    if (isValid(withPaddedHour)) return withPaddedHour.getTime();
    const withHour = parse(combined, "yyyy-MM-dd h:mm a", new Date());
    if (isValid(withHour)) return withHour.getTime();
  }

  const dateOnly = parse(datePart, "yyyy-MM-dd", new Date());
  return isValid(dateOnly) ? dateOnly.getTime() : 0;
}

export function SessionInspector() {
  const navigate = useNavigate();
  const [interactions, setInteractions] = useState<InteractionSummary[]>([]);
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [reprocessingIds, setReprocessingIds] = useState<Set<string>>(new Set());
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
  const [uploading, setUploading] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState("");

  // Upload modal + drag-and-drop state.
  const [uploadOpen, setUploadOpen] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Row 3-dots menu open state (interaction id of currently-open row, or null).
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  // Confirm-delete modal state.
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");

  const [sortField, setSortField] = useState<"score" | "date" | "duration">("score");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    Promise.all([getInteractions(), getAgents()])
      .then(([interactionRows, agentRows]) => {
        setInteractions(interactionRows);
        setAgents(agentRows);
        setSelectedAgentId((current) => current || agentRows[0]?.id || "");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSort = (field: "score" | "date" | "duration") => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
    setCurrentPage(1);
  };

  const closeMenu = useCallback(() => setOpenMenuId(null), []);

  // Click-outside to close the row menu.
  useEffect(() => {
    if (!openMenuId) return;
    const handler = () => closeMenu();
    window.addEventListener("click", handler);
    return () => window.removeEventListener("click", handler);
  }, [openMenuId, closeMenu]);

  const handleReprocess = async (interactionId: string) => {
    closeMenu();
    setActionError(null);
    setReprocessingIds((prev) => new Set(prev).add(interactionId));
    try {
      await reprocessInteraction(interactionId);
      const refreshed = await getInteractions();
      setInteractions(refreshed);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to reprocess interaction";
      if (message.includes("409")) {
        try {
          await reprocessInteraction(interactionId, { force: true });
          const refreshed = await getInteractions();
          setInteractions(refreshed);
          return;
        } catch {
          setActionError("This interaction is already processing. Please wait and try again.");
        }
      } else {
        setActionError(message);
      }
    } finally {
      setReprocessingIds((prev) => {
        const next = new Set(prev);
        next.delete(interactionId);
        return next;
      });
    }
  };

  const handleDelete = async (interactionId: string) => {
    setActionError(null);
    setDeletingIds((prev) => new Set(prev).add(interactionId));
    try {
      await deleteInteraction(interactionId);
      setInteractions((current) => current.filter((row) => row.id !== interactionId));
      setConfirmDeleteId(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to delete interaction";
      setActionError(message);
    } finally {
      setDeletingIds((prev) => {
        const next = new Set(prev);
        next.delete(interactionId);
        return next;
      });
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      setActionError("Choose an audio file before uploading.");
      return;
    }
    if (!selectedAgentId) {
      setActionError("Choose the agent who handled this call.");
      return;
    }

    setActionError(null);
    setUploading(true);
    try {
      await createInteraction(uploadFile, selectedAgentId);
      setUploadFile(null);
      setUploadOpen(false);
      const refreshed = await getInteractions();
      setInteractions(refreshed);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to upload interaction");
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (file: File | null) => {
    if (!file) {
      setUploadFile(null);
      return;
    }
    if (!file.type.startsWith("audio/") && !/\.(wav|mp3|m4a|ogg|flac)$/i.test(file.name)) {
      setActionError("Please select an audio file (.wav, .mp3, .m4a, .ogg, .flac).");
      return;
    }
    setActionError(null);
    setUploadFile(file);
  };

  const onDrop = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0];
    if (file) handleFileSelect(file);
  };

  const confirmDeleteRow = useMemo(
    () => interactions.find((r) => r.id === confirmDeleteId) || null,
    [interactions, confirmDeleteId],
  );

  const filteredInteractions = interactions.filter((interaction) => {
    const searchLower = searchQuery.toLowerCase();
    return (
      interaction.agentName.toLowerCase().includes(searchLower) ||
      interaction.id.toLowerCase().includes(searchLower) ||
      interaction.date.toLowerCase().includes(searchLower)
    );
  });

  const sortedInteractions = [...filteredInteractions].sort((a, b) => {
    let comparison = 0;
    if (sortField === "score") {
      comparison = a.overallScore - b.overallScore;
    } else if (sortField === "date") {
      const dateA = interactionDateMs(a);
      const dateB = interactionDateMs(b);
      comparison = dateA - dateB;
      if (comparison === 0) {
        comparison = a.id.localeCompare(b.id);
      }
    } else if (sortField === "duration") {
      const [mA, sA] = a.duration.split(":").map(Number);
      const [mB, sB] = b.duration.split(":").map(Number);
      const durA = (mA || 0) * 60 + (sA || 0);
      const durB = (mB || 0) * 60 + (sB || 0);
      comparison = durA - durB;
    }
    return sortOrder === "asc" ? -comparison : comparison;
  });

  const totalItems = sortedInteractions.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / itemsPerPage));
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedInteractions = sortedInteractions.slice(startIndex, startIndex + itemsPerPage);

  const sortIndicator = (field: "score" | "date" | "duration") => {
    if (sortField !== field) return null;
    return sortOrder === "asc" ? (
      <ArrowUp className="ml-1 h-3.5 w-3.5" />
    ) : (
      <ArrowDown className="ml-1 h-3.5 w-3.5" />
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <span className="ml-3 text-muted-foreground text-sm">Loading interactions...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertTriangle className="w-10 h-10 text-destructive mx-auto mb-3" />
          <p className="text-foreground text-sm">Failed to load interactions</p>
          <p className="text-muted-foreground/80 text-xs mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 min-w-0 max-w-full">
      {actionError && (
        <div className="mb-4 flex items-start justify-between gap-3 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-[12px] font-medium text-destructive dark:bg-destructive/15">
          <span className="flex-1">{actionError}</span>
          <button
            type="button"
            onClick={() => setActionError(null)}
            className="text-destructive/70 hover:text-destructive"
            aria-label="Dismiss error"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Page header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-[22px] font-bold text-foreground mb-1">Session Inspector</h2>
          <p className="text-[13px] text-muted-foreground">
            {totalItems} interaction{totalItems !== 1 ? "s" : ""} · sorted by {sortField} ({sortOrder === "asc" ? "descending" : "ascending"})
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search agent, date, ID…"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              className="w-[220px] h-10 pl-9 pr-3 bg-background border border-border rounded-lg text-[13px] text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
            />
          </div>

          <div className="flex items-center border border-border rounded-lg overflow-hidden bg-background">
            {(["score", "date", "duration"] as const).map((field) => (
              <button
                key={field}
                type="button"
                onClick={() => handleSort(field)}
                className={`flex items-center px-3 h-10 text-[12px] font-semibold transition-colors capitalize ${
                  sortField === field
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                {field}
                {sortIndicator(field)}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={() => {
              setActionError(null);
              setUploadOpen(true);
            }}
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-[13px] font-semibold text-primary-foreground hover:bg-primary/90 shadow-sm"
          >
            <UploadCloud className="h-4 w-4" />
            Upload call
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[52rem] border-collapse">
            <thead>
              <tr className="bg-muted/40 border-b border-border">
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Agent</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Date &amp; Time</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Duration</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Score</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Empathy</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Policy</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Resolution</th>
                <th className="px-4 py-3 text-center text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Status</th>
                <th className="px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-wider text-muted-foreground w-44 sticky right-0 bg-muted/40 border-l border-border">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {paginatedInteractions.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-muted-foreground text-[13px]">
                    No interactions match your filters.
                  </td>
                </tr>
              )}
              {paginatedInteractions.map((row) => {
                const failed = isFailedStatus(row);
                const processing = ["processing", "pending"].includes(String(row.status || "").toLowerCase());
                const isReprocessing = reprocessingIds.has(row.id);
                const isDeleting = deletingIds.has(row.id);
                const failurePreview = getFailurePreview(row);
                return (
                  <tr
                    key={row.id}
                    className={`group transition-colors hover:bg-muted/30 ${failed ? "bg-destructive/[0.03]" : ""}`}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <span className="text-[14px] font-semibold text-foreground">{row.agentName}</span>
                        {row.hasViolation && (
                          <span className="px-2 py-0.5 bg-destructive/10 text-destructive rounded-full text-[10px] font-semibold">
                            Violation
                          </span>
                        )}
                      </div>
                      {failed && failurePreview && (
                        <div
                          className="mt-1 max-w-[28rem] truncate text-[11px] text-destructive/80"
                          title={failurePreview}
                        >
                          {failurePreview}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-[13px] text-muted-foreground">
                      <div className="text-foreground">{row.date}</div>
                      <div className="text-[11px] text-muted-foreground">{row.time}</div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-[13px] text-foreground tabular-nums">
                      {row.duration}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div
                        className="text-[18px] font-bold tabular-nums"
                        style={{
                          color:
                            row.overallScore >= 85
                              ? "var(--success)"
                              : row.overallScore >= 70
                                ? "var(--primary)"
                                : row.overallScore >= 50
                                  ? "var(--warning)"
                                  : "var(--destructive)",
                        }}
                      >
                        {row.overallScore}
                        <span className="text-[12px] font-medium text-muted-foreground">%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-[13px] text-foreground tabular-nums">{row.empathyScore}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-[13px] text-foreground tabular-nums">{row.policyScore}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-[13px] text-foreground tabular-nums">{row.resolutionScore}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                          failed
                            ? "bg-destructive/10 text-destructive"
                            : processing
                              ? "bg-primary/10 text-primary"
                              : row.resolved
                                ? "bg-success/15 text-success"
                                : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {failed ? "Failed" : processing ? "Processing" : row.resolved ? "Resolved" : "Unresolved"}
                      </span>
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap text-right sticky right-0 bg-card group-hover:bg-muted/30 border-l border-border">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          type="button"
                          disabled={processing}
                          onMouseEnter={() => {
                            void getInteractionDetail(row.id).catch(() => undefined);
                          }}
                          onClick={() => navigate(`/manager/inspector/${row.id}`)}
                          className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-primary/10 px-3 text-[12px] font-semibold text-primary hover:bg-primary/15 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          Inspect
                          <ChevronRight className="h-3.5 w-3.5" />
                        </button>
                        <div className="relative" onClick={(e) => e.stopPropagation()}>
                          <button
                            type="button"
                            onClick={() => setOpenMenuId((curr) => (curr === row.id ? null : row.id))}
                            disabled={isReprocessing || isDeleting}
                            className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background hover:bg-muted disabled:opacity-50 transition-colors"
                            aria-label="More actions"
                          >
                            {isReprocessing || isDeleting ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                            )}
                          </button>
                          {openMenuId === row.id && (
                            <div className="absolute right-0 top-9 z-40 w-44 overflow-hidden rounded-lg border border-border bg-popover shadow-lg">
                              <button
                                type="button"
                                onClick={() => void handleReprocess(row.id)}
                                className="flex w-full items-center gap-2 px-3 py-2 text-left text-[12px] font-medium text-foreground hover:bg-muted"
                              >
                                <RefreshCw className="h-3.5 w-3.5 text-muted-foreground" />
                                Reprocess
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  closeMenu();
                                  setConfirmDeleteId(row.id);
                                }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-left text-[12px] font-medium text-destructive hover:bg-destructive/10"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                                Delete
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-5 py-3 bg-muted/30 border-t border-border flex items-center justify-between">
          <div className="text-[12px] text-muted-foreground">
            Showing {totalItems === 0 ? 0 : startIndex + 1}–{Math.min(startIndex + itemsPerPage, totalItems)} of {totalItems}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="h-9 px-3 rounded-lg border border-border bg-background text-[12px] font-semibold text-foreground hover:bg-muted disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-[12px] text-muted-foreground tabular-nums">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages || totalItems === 0}
              className="h-9 px-3 rounded-lg border border-border bg-background text-[12px] font-semibold text-foreground hover:bg-muted disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Upload modal */}
      {uploadOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
          onClick={() => !uploading && setUploadOpen(false)}
        >
          <div
            className="w-full max-w-lg rounded-2xl bg-card border border-border shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <h3 className="text-[16px] font-bold text-foreground">Upload call audio</h3>
              <button
                type="button"
                onClick={() => !uploading && setUploadOpen(false)}
                disabled={uploading}
                className="text-muted-foreground hover:text-foreground disabled:opacity-50"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div>
                <label className="mb-1.5 block text-[12px] font-semibold text-foreground">
                  Agent
                </label>
                <select
                  value={selectedAgentId}
                  onChange={(event) => setSelectedAgentId(event.target.value)}
                  disabled={uploading}
                  className="h-10 w-full rounded-lg border border-border bg-background px-3 text-[13px] text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
                >
                  {agents.map((agent) => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-[12px] font-semibold text-foreground">
                  Audio file
                </label>
                <label
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragActive(true);
                  }}
                  onDragLeave={() => setDragActive(false)}
                  onDrop={onDrop}
                  className={`flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-8 cursor-pointer transition-colors ${
                    dragActive
                      ? "border-primary bg-primary/5"
                      : "border-border bg-muted/30 hover:bg-muted/50 hover:border-primary/40"
                  }`}
                >
                  <UploadCloud className="h-8 w-8 text-muted-foreground" />
                  {uploadFile ? (
                    <div className="text-center">
                      <div className="text-[13px] font-semibold text-foreground">{uploadFile.name}</div>
                      <div className="text-[11px] text-muted-foreground">
                        {formatBytes(uploadFile.size)} · click or drag to replace
                      </div>
                    </div>
                  ) : (
                    <div className="text-center">
                      <div className="text-[13px] font-medium text-foreground">
                        Click to choose or drop a file here
                      </div>
                      <div className="text-[11px] text-muted-foreground mt-0.5">
                        .wav, .mp3, .m4a, .ogg, .flac
                      </div>
                    </div>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="audio/*,.wav,.mp3,.m4a,.ogg,.flac"
                    className="hidden"
                    onChange={(event) => handleFileSelect(event.target.files?.[0] ?? null)}
                  />
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 px-5 py-4 border-t border-border bg-muted/20">
              <button
                type="button"
                onClick={() => setUploadOpen(false)}
                disabled={uploading}
                className="h-10 rounded-lg border border-border bg-background px-4 text-[13px] font-semibold text-foreground hover:bg-muted disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleUpload()}
                disabled={uploading || !uploadFile || !selectedAgentId}
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-[13px] font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <UploadCloud className="h-4 w-4" />}
                {uploading ? "Uploading…" : "Upload"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm-delete modal */}
      {confirmDeleteRow && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-card border border-border shadow-2xl p-5">
            <div className="flex items-start gap-3">
              <div className="rounded-full bg-destructive/15 p-2">
                <AlertTriangle className="h-5 w-5 text-destructive" />
              </div>
              <div className="flex-1">
                <h3 className="text-[15px] font-bold text-foreground">Delete this interaction?</h3>
                <p className="mt-1 text-[13px] text-muted-foreground">
                  Permanently removes <span className="font-semibold text-foreground">{confirmDeleteRow.agentName}</span> · {confirmDeleteRow.date} · {confirmDeleteRow.time}, including transcript, emotion events, scores, policy compliance and trigger cache. This cannot be undone.
                </p>
              </div>
            </div>
            <div className="mt-5 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setConfirmDeleteId(null)}
                disabled={deletingIds.has(confirmDeleteRow.id)}
                className="h-10 rounded-lg border border-border bg-background px-4 text-[13px] font-semibold text-foreground hover:bg-muted disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleDelete(confirmDeleteRow.id)}
                disabled={deletingIds.has(confirmDeleteRow.id)}
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-destructive px-4 text-[13px] font-semibold text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50"
              >
                {deletingIds.has(confirmDeleteRow.id) ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
