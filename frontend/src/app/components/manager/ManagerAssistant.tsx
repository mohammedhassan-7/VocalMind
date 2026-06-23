import { useEffect, useMemo, useRef, useState } from "react";
import { Check, Copy, Download, Lightbulb, MessageSquare, Mic, MoreHorizontal, Pencil, Plus, Send, Sparkles, Trash2 } from "lucide-react";

import { AssistantResponse, ChatSession, deleteAssistantSession, getAssistantHistory, renameAssistantSession, sendAssistantQuery } from "../../services/api";
import { useAuth } from "../../contexts/AuthContext";

/** Example questions shown to managers who don't know what they can ask. */
const SUGGESTED_QUESTIONS: readonly string[] = [
  "Who are my top 5 agents by overall score?",
  "How many calls were not resolved in the last 30 days?",
  "List all policy violations",
  "What are the most common customer emotions?",
  "Which agent has the lowest resolution rate?",
  "Show agents ranked by empathy score",
];

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Columns whose boolean values read naturally as a resolved/compliant outcome. */
const POSITIVE_BOOLEAN_COLUMNS = new Set(["was_resolved", "is_compliant", "is_active", "resolved", "compliant"]);

function isScoreColumn(key: string): boolean {
  return /score|empathy|resolution|policy|compliance|rating/i.test(key);
}

/** Format a numeric cell: whole numbers stay as-is, decimals round to 1 place. */
function formatNumber(val: number): string {
  return val % 1 === 0 ? String(val) : val.toFixed(1);
}

function buildCsv(rows: Record<string, unknown>[]): string {
  if (!rows.length) return "";
  const keys = Object.keys(rows[0]);
  const escape = (value: unknown): string => {
    const s = value == null ? "" : String(value);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const header = keys.join(",");
  const body = rows.map((row) => keys.map((k) => escape(row[k])).join(",")).join("\n");
  return `${header}\n${body}`;
}

function downloadCsv(rows: Record<string, unknown>[]): void {
  const csv = buildCsv(rows);
  if (!csv) return;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `assistant-results-${Date.now()}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

interface AssistantMessage extends Partial<AssistantResponse> {
  id: string;
  type: "user" | "ai";
  content: string;
  mode: string;
}


interface ModalState {
  type: "rename" | "delete";
  chatId: string;
}

interface ChatMenuState {
  chatId: string;
  x: number;
  y: number;
}

function uid(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

function formatMessageTime(iso?: string): string | null {
  if (!iso) return null;
  try {
    return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));
  } catch {
    return null;
  }
}

function deriveTitle(content: string): string {
  const normalized = content.replace(/\s+/g, " ").trim();
  if (!normalized) return "New chat";
  return normalized.length > 42 ? `${normalized.slice(0, 42)}...` : normalized;
}

/** Render a single result cell in manager-friendly form (badges, scores, short IDs). */
function ResultCell({ columnKey, value }: { columnKey: string; value: unknown }) {
  if (typeof value === "boolean") {
    const isOutcome = POSITIVE_BOOLEAN_COLUMNS.has(columnKey.toLowerCase());
    const label = isOutcome ? (value ? "Yes" : "No") : value ? "True" : "False";
    return (
      <span
        className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ${value ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400" : "bg-rose-500/15 text-rose-600 dark:text-rose-400"}`}
      >
        {label}
      </span>
    );
  }

  if (typeof value === "number") {
    const text = formatNumber(value);
    if (isScoreColumn(columnKey) && value >= 0 && value <= 10) {
      const tone = value >= 7 ? "text-emerald-600 dark:text-emerald-400" : value >= 4 ? "text-amber-600 dark:text-amber-400" : "text-rose-600 dark:text-rose-400";
      return <span className={`font-semibold tabular-nums ${tone}`}>{text}</span>;
    }
    return <span className="tabular-nums text-foreground">{text}</span>;
  }

  const str = String(value ?? "");
  if (UUID_RE.test(str)) {
    return (
      <span className="font-mono text-xs text-muted-foreground" title={str}>
        {str.slice(0, 8)}…
      </span>
    );
  }
  return <span className="text-foreground">{str}</span>;
}

function ResultTable({ rows }: { rows: Record<string, unknown>[] }) {
  const columns = Object.keys(rows[0]);
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <div className="overflow-x-auto scrollbar-thin">
        <table className="min-w-full divide-y divide-border text-sm">
          <thead className="bg-muted/60">
            <tr>
              {columns.map((key) => (
                <th
                  key={key}
                  className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground capitalize"
                >
                  {key.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row, idx) => (
              <tr key={idx} className="hover:bg-muted/40 transition-colors">
                {columns.map((key) => (
                  <td key={key} className="px-3 py-2 whitespace-nowrap text-[13px]">
                    <ResultCell columnKey={key} value={row[key]} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable; no-op */
    }
  };
  return (
    <button
      type="button"
      onClick={onCopy}
      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
    >
      {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

export function ManagerAssistant() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  const [sessions, setSessions] = useState<Record<string, ChatSession>>({});
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [isDraftNewChat, setIsDraftNewChat] = useState(false);

  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [menuState, setMenuState] = useState<ChatMenuState | null>(null);
  const [modalState, setModalState] = useState<ModalState | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (modalState) {
      const original = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = original;
      };
    }
    return;
  }, [modalState]);

  useEffect(() => {
    const closeMenu = () => setMenuState(null);
    window.addEventListener("click", closeMenu);
    return () => window.removeEventListener("click", closeMenu);
  }, []);

  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated || user?.role !== "manager") {
      setHistoryLoading(false);
      setHistoryError(null);
      setSessions({});
      setSelectedChatId(null);
      return;
    }

    let cancelled = false;
    setHistoryLoading(true);
    setHistoryError(null);

    getAssistantHistory()
      .then((historySessions) => {
        if (cancelled) return;
        if (!historySessions?.length) return;
        const newSessions: Record<string, ChatSession> = {};
        for (const s of historySessions) {
            newSessions[s.id] = s as any;
        }
        setSessions(newSessions);
      })
      .catch((err) => {
        console.error("Failed to load chat history:", err);
        if (!cancelled) {
          setHistoryError("Could not load saved conversation. Your session may have expired - try logging in again.");
        }
      })
      .finally(() => {
        if (!cancelled) setHistoryLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [authLoading, isAuthenticated, user?.id, user?.role]);

  const chatList = useMemo(() => {
    const list = Object.values(sessions).filter((s) => !s.deleted);
    return list.sort((a, b) => a.id.localeCompare(b.id)).reverse();
  }, [sessions]);

  useEffect(() => {
    if (isDraftNewChat) return;
    if (selectedChatId && sessions[selectedChatId] && !sessions[selectedChatId].deleted) return;
    if (chatList.length > 0) setSelectedChatId(chatList[0].id);
    else setSelectedChatId(null);
  }, [chatList, selectedChatId, sessions, isDraftNewChat]);

  const selectedSession = selectedChatId ? sessions[selectedChatId] : null;
  const visibleMessages = selectedSession?.messages ?? [];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [visibleMessages, isLoading]);

  const createNewChat = () => {
    setIsDraftNewChat(true);
    setSelectedChatId(null);
    setInput("");
    setHistoryError(null);
  };

  const openChat = (chatId: string) => {
    setIsDraftNewChat(false);
    setSelectedChatId(chatId);
  };

  const openRenameModal = (chatId: string) => {
    setRenameValue(sessions[chatId]?.title || "");
    setModalState({ type: "rename", chatId });
    setMenuState(null);
  };

  const openDeleteModal = (chatId: string) => {
    setModalState({ type: "delete", chatId });
    setMenuState(null);
  };

  const confirmRename = async () => {
    if (!modalState || modalState.type !== "rename") return;
    const next = renameValue.trim();
    if (!next) return;
    
    try {
      await renameAssistantSession(modalState.chatId, next);
      setSessions((prev) => ({ ...prev, [modalState.chatId]: { ...prev[modalState.chatId], title: next } }));
    } catch (e) {
      console.error(e);
    }
    setModalState(null);
  };

  const confirmDelete = async () => {
    if (!modalState || modalState.type !== "delete") return;
    try {
      await deleteAssistantSession(modalState.chatId);
      setSessions((prev) => {
        const next = { ...prev };
        delete next[modalState.chatId];
        return next;
      });
      if (selectedChatId === modalState.chatId) setSelectedChatId(null);
    } catch (e) {
      console.error(e);
    }
    setModalState(null);
    setIsDraftNewChat(false);
  };

  const appendToSession = (chatId: string, message: AssistantMessage) => {
    setSessions((prev) => {
      const existing = prev[chatId];
      if (!existing) return prev;
      return {
        ...prev,
        [chatId]: {
          ...existing,
          messages: [...existing.messages, message],
        },
      };
    });
  };

  const handleSend = async (questionOverride?: string) => {
    const queryText = questionOverride ?? input;
    if (!queryText.trim()) return;

    const isNew = !selectedChatId || isDraftNewChat;
    const tempChatId = isNew ? uid("temp") : selectedChatId!;
    
    if (isNew) {
      const newSession: ChatSession = {
        id: tempChatId,
        title: deriveTitle(queryText),
        messages: [],
        deleted: false,
      } as any;
      setSessions((prev) => ({ ...prev, [tempChatId]: newSession }));
      setSelectedChatId(tempChatId);
      setIsDraftNewChat(false);
    }

    const userMessage: AssistantMessage = {
      id: `msg_${Date.now()}`,
      type: "user",
      content: queryText,
      mode: "chat",
    };
    appendToSession(tempChatId, userMessage);

    setInput("");
    setIsLoading(true);

    try {
      const response = await sendAssistantQuery(queryText, "chat", isNew ? undefined : tempChatId);
      const returnedSessionId = (response as any).session_id;
      
      if (isNew && returnedSessionId && returnedSessionId !== tempChatId) {
        setSessions((prev) => {
           const next = { ...prev };
           const s = next[tempChatId];
           if (s) {
              s.id = returnedSessionId;
              next[returnedSessionId] = s;
              delete next[tempChatId];
           }
           return next;
        });
        setSelectedChatId(returnedSessionId);
        
        const aiMessage: AssistantMessage = {
          ...response,
          id: response.id ?? `msg_ai_${Date.now()}`,
          type: "ai",
        };
        appendToSession(returnedSessionId, aiMessage);
      } else {
        const aiMessage: AssistantMessage = {
          ...response,
          id: response.id ?? `msg_ai_${Date.now()}`,
          type: "ai",
        };
        appendToSession(tempChatId, aiMessage);
      }
    } catch {
      appendToSession(tempChatId, {
        id: `msg_err_${Date.now()}`,
        type: "ai",
        content: "I'm sorry, I'm having trouble connecting to the service. Please make sure the backend is running.",
        success: false,
        mode: "chat",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const suggestionChips = (
    <div className="mt-6 w-full max-w-md">
      <div className="flex items-center justify-center gap-1.5 text-xs font-medium text-muted-foreground mb-3">
        <Lightbulb className="w-3.5 h-3.5" />
        Try asking
      </div>
      <div className="flex flex-col gap-2">
        {SUGGESTED_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => handleSend(q)}
            disabled={isLoading}
            className="group flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-left text-sm text-foreground hover:border-primary/50 hover:bg-accent transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5 shrink-0 text-primary/70 group-hover:text-primary" />
            <span>{q}</span>
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="h-[64px] px-5 border-b border-border bg-card flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-primary" />
          </div>
          <div>
            <div className="text-sm font-bold text-foreground">Manager Assistant</div>
            <div className="text-[11px] text-muted-foreground">New chat and recent chats</div>
          </div>
        </div>
        <button type="button" onClick={createNewChat} className="inline-flex items-center gap-1.5 h-9 px-3 rounded-lg border border-border text-xs font-semibold text-foreground hover:bg-accent">
          <Plus className="w-4 h-4" />
          New chat
        </button>
      </div>

      <div className="flex flex-1 min-h-0">
        <aside className="w-[290px] shrink-0 border-r border-border bg-card/40 hidden lg:flex flex-col min-h-0">
          <div className="h-12 px-3 border-b border-border/70 flex items-center">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Recent chats</span>
          </div>
          <div className="p-2 overflow-y-auto min-h-0 space-y-1 scrollbar-thin">
            {chatList.map((chat) => (
              <div key={chat.id} className="relative">
                <button
                  type="button"
                  onClick={() => openChat(chat.id)}
                  className={`w-full text-left rounded-md px-2.5 py-2 text-xs pr-8 ${selectedChatId === chat.id && !isDraftNewChat ? "bg-primary/15 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}
                >
                  <span className="block truncate">{chat.title}</span>
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    const rect = (e.currentTarget as HTMLButtonElement).getBoundingClientRect();
                    setMenuState((prev) =>
                      prev?.chatId === chat.id
                        ? null
                        : {
                            chatId: chat.id,
                            x: Math.max(8, rect.right - 128),
                            y: rect.bottom + 6,
                          }
                    );
                  }}
                  className="absolute top-1/2 -translate-y-1/2 right-1 w-6 h-6 rounded hover:bg-accent flex items-center justify-center text-muted-foreground"
                >
                  <MoreHorizontal className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </aside>

        <div className="flex-1 min-w-0 min-h-0 flex flex-col">
          <div className="flex-1 overflow-y-auto p-5 space-y-4 min-h-0 scrollbar-thin">
            {historyError && <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive" role="alert">{historyError}</div>}

            {historyLoading ? (
              <div className="flex flex-col items-center justify-center h-full gap-3" data-cy="assistant-history-loading">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
                <p className="text-sm text-muted-foreground font-medium">Loading conversation...</p>
              </div>
            ) : isDraftNewChat ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-3">
                  <MessageSquare className="w-6 h-6 text-primary" />
                </div>
                <h2 className="text-2xl font-bold text-foreground mb-1">How can I help?</h2>
                <p className="text-sm text-muted-foreground max-w-sm">Ask about agent performance, call outcomes, policy compliance, or customer emotions — in plain English.</p>
                {suggestionChips}
              </div>
            ) : !selectedSession ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <h2 className="text-2xl font-bold text-foreground mb-1">No chat selected</h2>
                <p className="text-sm text-muted-foreground">Select a recent chat or click New chat.</p>
                {suggestionChips}
              </div>
            ) : visibleMessages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <h2 className="text-2xl font-bold text-foreground mb-1">{selectedSession.title}</h2>
                <p className="text-sm text-muted-foreground">This chat is empty. Ask your first question below.</p>
                {suggestionChips}
              </div>
            ) : (
              <>
                {visibleMessages.map((message) => {
                  const timeLabel = formatMessageTime(message.created_at);
                  return (
                    <div key={message.id} className={`flex flex-col gap-1 ${message.type === "user" ? "items-end" : "items-start"}`}>
                      <div className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
                        {message.type === "user" ? (
                          <div className="max-w-[520px] bg-primary text-primary-foreground rounded-[18px_18px_4px_18px] px-4 py-3"><p className="text-sm">{message.content}</p></div>
                        ) : (
                          <div className={`max-w-[92%] md:max-w-[680px] rounded-[18px_18px_18px_4px] px-4 py-3 space-y-3 shadow-sm border ${message.success === false ? "bg-destructive/10 border-destructive/30" : "bg-card border-border"}`}>
                            <p className={`text-sm font-medium leading-relaxed whitespace-pre-line ${message.success === false ? "text-destructive" : "text-foreground"}`}>{message.content}</p>
                            {message.success && message.data && message.data.length > 0 && (
                              <div className="space-y-2">
                                <div className="flex items-center justify-between gap-2">
                                  <span className="text-[11px] font-medium text-muted-foreground">{message.data.length} result{message.data.length === 1 ? "" : "s"}</span>
                                  <div className="flex items-center gap-1">
                                    <CopyButton text={message.content} />
                                    <button
                                      type="button"
                                      onClick={() => downloadCsv(message.data as Record<string, unknown>[])}
                                      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                                    >
                                      <Download className="w-3 h-3" /> Export CSV
                                    </button>
                                  </div>
                                </div>
                                <ResultTable rows={message.data as Record<string, unknown>[]} />
                              </div>
                            )}
                            <div className="flex items-center gap-2 flex-wrap">
                              {(message.execution_time ?? message.executionTime) && <span className="inline-flex px-2 py-1 bg-muted text-muted-foreground rounded text-[10px] font-medium border border-border">Executed in {message.execution_time ?? message.executionTime}</span>}
                              {message.sql && (
                                <details className="cursor-pointer">
                                  <summary className="text-[11px] text-muted-foreground hover:text-foreground transition-colors select-none">Show generated SQL</summary>
                                  <div className="mt-2 bg-muted rounded-lg p-3 overflow-x-auto" style={{ fontFamily: "var(--font-mono)" }}>
                                    <pre className="text-[10px] text-emerald-600 dark:text-emerald-400 whitespace-pre-wrap">{message.sql}</pre>
                                  </div>
                                </details>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                      {timeLabel && <span className={`text-[10px] text-muted-foreground/80 px-1 ${message.type === "user" ? "text-right" : "text-left"}`}>{timeLabel}</span>}
                    </div>
                  );
                })}
                {isLoading && (
                  <div className="flex justify-start" data-cy="assistant-loading"><div className="bg-card border border-border rounded-[18px_18px_18px_4px] px-4 py-3"><div className="flex gap-1"><div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} /><div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} /><div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} /></div></div></div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="bg-card border-t border-border px-5 py-4 shrink-0">
            <div className="flex items-center gap-2 bg-input border border-border rounded-full p-1 shadow-inner focus-within:ring-1 focus-within:ring-primary/40 transition-all">
              <button type="button" disabled title="Voice input coming soon" className="w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-xl transition-all text-muted-foreground opacity-50 cursor-not-allowed"><Mic className="w-5 h-5" /></button>
              <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSend()} placeholder="Ask about scores, violations, agent trends..." disabled={isLoading} className="flex-1 h-10 px-2 bg-transparent text-foreground placeholder-muted-foreground text-sm focus:outline-none disabled:opacity-50" />
              <button type="button" aria-label="Send message" onClick={() => handleSend()} disabled={isLoading || !input.trim()} className={`w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-full transition-all ${input.trim() ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" : "bg-muted text-muted-foreground opacity-50"}`}><Send className="w-4 h-4" /></button>
            </div>
          </div>
        </div>
      </div>

      {menuState && (
        <div
          className="fixed z-40 w-32 rounded-md border border-border bg-popover shadow-lg p-1"
          style={{ top: menuState.y, left: menuState.x }}
        >
          <button className="w-full text-left text-xs px-2 py-1.5 rounded hover:bg-accent flex items-center gap-1.5" onClick={() => openRenameModal(menuState.chatId)}>
            <Pencil className="w-3.5 h-3.5" /> Rename
          </button>
          <button className="w-full text-left text-xs px-2 py-1.5 rounded hover:bg-destructive/10 text-destructive flex items-center gap-1.5" onClick={() => openDeleteModal(menuState.chatId)}>
            <Trash2 className="w-3.5 h-3.5" /> Delete
          </button>
        </div>
      )}

      {modalState && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-[1px] flex items-center justify-center p-4">
          <div className="w-full max-w-sm rounded-xl border border-border bg-card shadow-2xl p-4 space-y-3">
            {modalState.type === "rename" ? (
              <>
                <h3 className="text-sm font-semibold text-foreground">Rename chat</h3>
                <input value={renameValue} onChange={(e) => setRenameValue(e.target.value)} className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary/40" autoFocus />
                <div className="flex justify-end gap-2"><button className="h-9 px-3 text-xs rounded-lg border border-border hover:bg-accent" onClick={() => setModalState(null)}>Cancel</button><button className="h-9 px-3 text-xs rounded-lg bg-primary text-primary-foreground hover:opacity-90" onClick={confirmRename}>Save</button></div>
              </>
            ) : (
              <>
                <h3 className="text-sm font-semibold text-foreground">Delete chat?</h3>
                <p className="text-xs text-muted-foreground">Are you sure you want to delete this chat?</p>
                <div className="flex justify-end gap-2"><button className="h-9 px-3 text-xs rounded-lg border border-border hover:bg-accent" onClick={() => setModalState(null)}>Cancel</button><button className="h-9 px-3 text-xs rounded-lg bg-destructive text-destructive-foreground hover:opacity-90" onClick={confirmDelete}>Delete</button></div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
