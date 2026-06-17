import { useEffect, useRef, useState } from "react";
import { User, Bell, Shield, Key, Loader2, Check, AlertCircle } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { updateProfile, changePassword } from "../../services/api";

type Status = { kind: "idle" | "saving" | "ok" | "error"; message?: string };

const MAX_AVATAR_BYTES = 2 * 1024 * 1024; // 2 MB

function StatusLine({ status }: { status: Status }) {
  if (status.kind === "idle") return null;
  if (status.kind === "saving") {
    return (
      <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-muted-foreground">
        <Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving…
      </span>
    );
  }
  if (status.kind === "ok") {
    return (
      <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-emerald-500">
        <Check className="w-3.5 h-3.5" /> {status.message || "Saved"}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-destructive">
      <AlertCircle className="w-3.5 h-3.5" /> {status.message || "Something went wrong"}
    </span>
  );
}

export function ManagerSettings() {
  const { user, refreshUser } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [activeTab, setActiveTab] = useState<string>(() => {
    const hash = typeof window !== "undefined" ? window.location.hash.replace("#", "") : "";
    return ["profile", "notifications", "security", "api"].includes(hash) ? hash : "profile";
  });

  const [name, setName] = useState(user?.name ?? "");
  const [avatar, setAvatar] = useState<string | null | undefined>(user?.avatar_url);
  const [profileStatus, setProfileStatus] = useState<Status>({ kind: "idle" });

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwStatus, setPwStatus] = useState<Status>({ kind: "idle" });

  useEffect(() => {
    setName(user?.name ?? "");
    setAvatar(user?.avatar_url);
  }, [user?.name, user?.avatar_url]);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace("#", "");
      if (["profile", "notifications", "security", "api"].includes(hash)) {
        setActiveTab(hash);
      }
    };
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const displayName = name || user?.name || "Manager User";
  const displayEmail = user?.email || "manager@vocalmind.io";
  const initials =
    displayName
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0])
      .join("")
      .toUpperCase() || "MU";

  const profileDirty = name.trim() !== (user?.name ?? "") || avatar !== user?.avatar_url;

  const onPickAvatar = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setProfileStatus({ kind: "error", message: "Please choose an image file" });
      return;
    }
    if (file.size > MAX_AVATAR_BYTES) {
      setProfileStatus({ kind: "error", message: "Image must be under 2 MB" });
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setAvatar(reader.result as string);
      setProfileStatus({ kind: "idle" });
    };
    reader.readAsDataURL(file);
  };

  const onSaveProfile = async () => {
    setProfileStatus({ kind: "saving" });
    try {
      await updateProfile({ name: name.trim(), avatar_url: avatar ?? "" });
      await refreshUser();
      setProfileStatus({ kind: "ok", message: "Profile updated" });
    } catch (err) {
      setProfileStatus({ kind: "error", message: err instanceof Error ? err.message : "Update failed" });
    }
  };

  const onChangePassword = async () => {
    if (newPassword.length < 8) {
      setPwStatus({ kind: "error", message: "New password must be at least 8 characters" });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwStatus({ kind: "error", message: "Passwords do not match" });
      return;
    }
    setPwStatus({ kind: "saving" });
    try {
      await changePassword({ current_password: currentPassword || undefined, new_password: newPassword });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPwStatus({ kind: "ok", message: "Password changed" });
    } catch (err) {
      setPwStatus({ kind: "error", message: err instanceof Error ? err.message : "Change failed" });
    }
  };

  const tabs = [
    { key: "profile", label: "Profile", icon: User },
    { key: "notifications", label: "Notifications", icon: Bell },
    { key: "security", label: "Privacy & Security", icon: Shield },
    { key: "api", label: "API Keys", icon: Key },
  ];

  const inputCls =
    "w-full h-11 px-3 bg-background border border-border rounded-xl text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors";

  return (
    <div className="p-4 md:p-8 bg-background min-h-screen transition-colors duration-300">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground">Settings &amp; Preferences</h2>
          <p className="text-muted-foreground text-sm mt-1">Manage your account settings and application preferences.</p>
        </div>

        <div className="bg-card rounded-2xl border border-border shadow-sm overflow-hidden flex flex-col md:flex-row transition-all duration-300">
          {/* Sidebar Tabs */}
          <div className="w-full md:w-64 border-r border-border bg-muted/20 p-4 space-y-1">
            {tabs.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => { setActiveTab(key); window.location.hash = key; }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 font-semibold rounded-xl text-sm transition-colors ${
                  activeTab === key ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted"
                }`}
              >
                <Icon className="w-4 h-4" /> {label}
              </button>
            ))}
          </div>

          {/* Content Area */}
          <div className="flex-1 p-6 md:p-8">
            {activeTab === "profile" && (
              <>
                <h3 className="text-lg font-bold text-foreground border-b border-border pb-4 mb-6">Profile Information</h3>
                <div className="space-y-6 max-w-lg">
                  <div className="flex items-center gap-6">
                    {avatar ? (
                      <img src={avatar} alt={displayName} className="w-20 h-20 rounded-full object-cover shadow-sm border border-border" />
                    ) : (
                      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center text-primary-foreground text-2xl font-bold shadow-sm">
                        {initials}
                      </div>
                    )}
                    <div className="flex flex-col gap-2">
                      <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={onPickAvatar} />
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="px-4 py-2 bg-card border border-border rounded-lg text-sm font-semibold text-foreground hover:bg-muted shadow-sm transition-colors"
                      >
                        Change Avatar
                      </button>
                      {avatar && (
                        <button
                          onClick={() => setAvatar("")}
                          className="px-4 py-1.5 text-xs font-semibold text-muted-foreground hover:text-destructive transition-colors text-left"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-semibold text-foreground mb-1.5">Full Name</label>
                      <input type="text" value={name} onChange={(e) => setName(e.target.value)} className={inputCls} placeholder="Your name" />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-foreground mb-1.5">Email Address</label>
                      <input type="email" value={displayEmail} readOnly className={`${inputCls} bg-muted/40 text-muted-foreground cursor-not-allowed`} />
                    </div>
                  </div>

                  <div className="pt-4 flex items-center justify-between gap-3">
                    <StatusLine status={profileStatus} />
                    <button
                      onClick={onSaveProfile}
                      disabled={!profileDirty || profileStatus.kind === "saving"}
                      className="px-6 py-2.5 bg-primary hover:opacity-90 text-primary-foreground rounded-xl text-sm font-bold shadow-sm shadow-primary/20 transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Save Changes
                    </button>
                  </div>
                </div>
              </>
            )}

            {activeTab === "security" && (
              <>
                <h3 className="text-lg font-bold text-foreground border-b border-border pb-4 mb-6">Privacy &amp; Security</h3>
                <div className="space-y-4 max-w-lg">
                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1.5">Current Password</label>
                    <input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className={inputCls} placeholder="Leave blank if none set" autoComplete="current-password" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1.5">New Password</label>
                    <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className={inputCls} placeholder="At least 8 characters" autoComplete="new-password" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-foreground mb-1.5">Confirm New Password</label>
                    <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className={inputCls} autoComplete="new-password" />
                  </div>
                  <div className="pt-2 flex items-center justify-between gap-3">
                    <StatusLine status={pwStatus} />
                    <button
                      onClick={onChangePassword}
                      disabled={!newPassword || pwStatus.kind === "saving"}
                      className="px-6 py-2.5 bg-primary hover:opacity-90 text-primary-foreground rounded-xl text-sm font-bold shadow-sm shadow-primary/20 transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Change Password
                    </button>
                  </div>
                </div>
              </>
            )}

            {activeTab === "notifications" && (
              <div>
                <h3 className="text-lg font-bold text-foreground border-b border-border pb-4 mb-6">Notification Preferences</h3>
                <p className="text-muted-foreground text-sm">
                  In-app notifications are delivered to the bell in the top bar — you&apos;re alerted when a call finishes
                  evaluation and when an agent flags a result for review.
                </p>
              </div>
            )}

            {activeTab === "api" && (
              <div>
                <h3 className="text-lg font-bold text-foreground border-b border-border pb-4 mb-6">API Keys</h3>
                <p className="text-muted-foreground text-sm">Generate and revoke integration tokens. Coming soon.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
