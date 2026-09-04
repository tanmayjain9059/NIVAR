import { useState } from "react";
import { ScanLine, Menu, X, LayoutDashboard, Search, History } from "lucide-react";

interface NavigationProps {
  currentView?: string;
  onNavigate?: (view: string) => void;
}

export function Navigation({ currentView, onNavigate }: NavigationProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-zinc-200/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
        {/* Wordmark */}
        <div className="flex items-center gap-2">
          <ScanLine className="w-4 h-4 text-civic-primary" />
          <span className="text-base font-bold tracking-tight text-civic-text">
            NIVAR
          </span>
          <span className="hidden sm:inline text-[11px] text-civic-muted font-normal ml-1 leading-none border-l border-zinc-200 pl-2">
            label intelligence
          </span>
        </div>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {[
            { label: "Overview", icon: LayoutDashboard },
            { label: "Scan Product", icon: Search },
            { label: "History", icon: History },
          ].map(({ label, icon: Icon }) => (
            <button
              key={label}
              onClick={() => onNavigate?.(label)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                currentView === label
                  ? "bg-civic-accent text-civic-primary"
                  : "text-civic-secondary hover:text-civic-text hover:bg-zinc-100"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>

        {/* Mobile menu toggle */}
        <button
          className="md:hidden p-2 rounded-md text-civic-secondary hover:text-civic-text"
          onClick={() => setMobileOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
        </button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="md:hidden border-t border-zinc-200 bg-white px-4 py-3 flex flex-col gap-1">
          {[
            { label: "Overview", icon: LayoutDashboard },
            { label: "Scan Product", icon: Search },
            { label: "History", icon: History },
          ].map(({ label, icon: Icon }) => (
            <button
              key={label}
              onClick={() => {
                onNavigate?.(label);
                setMobileOpen(false);
              }}
              className="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-civic-secondary hover:text-civic-text hover:bg-zinc-100 text-left"
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      )}
    </nav>
  );
}
