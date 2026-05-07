import { useEffect, useState } from "react";
import { User, Bell, Shield, Key } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";

export function ManagerSettings() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<string>(() => {
    const hash = typeof window !== "undefined" ? window.location.hash.replace("#", "") : "";
    return ["profile", "notifications", "security", "api"].includes(hash) ? hash : "profile";
  });

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

  const displayName = user?.name || "Manager User";
  const displayEmail = user?.email || "manager@vocalmind.io";
  const initials = displayName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || "MU";

  return (
    <div className="p-4 md:p-8 bg-background min-h-screen transition-colors duration-300">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground">Settings & Preferences</h2>
          <p className="text-muted-foreground text-sm mt-1">Manage your account settings and application preferences.</p>
        </div>

        <div className="bg-card rounded-2xl border border-border shadow-sm overflow-hidden flex flex-col md:flex-row transition-all duration-300">
          {/* Sidebar Tabs */}
          <div className="w-full md:w-64 border-r border-border bg-muted/20 p-4 space-y-1">
            <button 
              onClick={() => { setActiveTab("profile"); window.location.hash = "profile"; }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 font-semibold rounded-xl text-sm transition-colors ${
                activeTab === "profile" ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted"
              }`}
            >
              <User className="w-4 h-4" /> Profile
            </button>
            <button 
              onClick={() => { setActiveTab("notifications"); window.location.hash = "notifications"; }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 font-semibold rounded-xl text-sm transition-colors ${
                activeTab === "notifications" ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted"
              }`}
            >
              <Bell className="w-4 h-4" /> Notifications
            </button>
            <button 
              onClick={() => { setActiveTab("security"); window.location.hash = "security"; }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 font-semibold rounded-xl text-sm transition-colors ${
                activeTab === "security" ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted"
              }`}
            >
              <Shield className="w-4 h-4" /> Privacy & Security
            </button>
            <button 
              onClick={() => { setActiveTab("api"); window.location.hash = "api"; }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 font-semibold rounded-xl text-sm transition-colors ${
                activeTab === "api" ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted"
              }`}
            >
              <Key className="w-4 h-4" /> API Keys
            </button>
          </div>

          {/* Content Area */}
          <div className="flex-1 p-6 md:p-8">
            {activeTab === "profile" && (
              <>
                <h3 className="text-lg font-bold text-foreground border-b border-border pb-4 mb-6">Profile Information</h3>
                <div className="space-y-6 max-w-lg">
                  <div className="flex items-center gap-6">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center text-primary-foreground text-2xl font-bold shadow-sm">
                      {initials}
                    </div>
                    <div>
                      <button className="px-4 py-2 bg-card border border-border rounded-lg text-sm font-semibold text-foreground hover:bg-muted shadow-sm transition-colors">
                        Change Avatar
                      </button>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-semibold text-foreground mb-1.5">Full Name</label>
                      <input 
                        type="text" 
                        value={displayName} 
                        readOnly 
                        className="w-full h-11 px-3 bg-muted/40 border border-border rounded-xl text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors" 
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-semibold text-foreground mb-1.5">Email Address</label>
                      <input 
                        type="email" 
                        value={displayEmail} 
                        readOnly 
                        className="w-full h-11 px-3 bg-muted/40 border border-border rounded-xl text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors" 
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-foreground mb-1.5">Organization</label>
                      <input 
                        type="text" 
                        defaultValue="VocalMind Corp" 
                        disabled 
                        className="w-full h-11 px-3 bg-muted/10 border border-border rounded-xl text-sm text-muted-foreground/50 cursor-not-allowed" 
                      />
                    </div>
                  </div>

                  <div className="pt-4 flex justify-end">
                    <button className="px-6 py-2.5 bg-primary hover:opacity-90 text-primary-foreground rounded-xl text-sm font-bold shadow-sm shadow-primary/20 transition-all active:scale-95">
                      Save Changes
                    </button>
                  </div>
                </div>
              </>
            )}
            {activeTab === "notifications" && (
              <div>
                <h3 className="text-lg font-bold text-foreground border-b border-border pb-4 mb-6">Notification Preferences</h3>
                <p className="text-muted-foreground text-sm">Configure how you receive alerts and updates.</p>
              </div>
            )}
            {activeTab === "security" && (
              <div>
                <h3 className="text-lg font-bold text-foreground border-b border-border pb-4 mb-6">Privacy & Security</h3>
                <p className="text-muted-foreground text-sm">Manage passwords and active sessions.</p>
              </div>
            )}
            {activeTab === "api" && (
              <div>
                <h3 className="text-lg font-bold text-foreground border-b border-border pb-4 mb-6">API Keys</h3>
                <p className="text-muted-foreground text-sm">Generate and revoke integration tokens.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
