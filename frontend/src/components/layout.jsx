import { Component, Suspense, useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Bell,
  BrainCircuit,
  Building2,
  Cable,
  ChartColumn,
  ClipboardCheck,
  FileBarChart,
  FileStack,
  Files,
  FolderKanban,
  GitBranch,
  HeartHandshake,
  Home,
  Inbox,
  IndianRupee,
  KeyRound,
  LayoutDashboard,
  LogOut,
  Map,
  MapPinned,
  Menu,
  ScrollText,
  Settings,
  Shield,
  Users,
  X,
} from "lucide-react";
import { listNotifications } from "../api/notifications";
import { useAuth } from "../context/AuthContext";
import { visibleNav } from "../lib/roles";
import { Badge, ErrorState, Skeleton } from "./ui";

export function RouteFallback() {
  return (
    <div className="space-y-4 p-2 md:p-4" role="status" aria-label="Loading page content" aria-busy="true">
      <div className="h-8 w-48 animate-pulse rounded-lg bg-slate-200" />
      <Skeleton className="h-28" />
      <Skeleton className="h-64" />
    </div>
  );
}

export class RouteErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("Route chunk failed to load:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4" role="alert">
          <ErrorState
            message={this.state.error?.message || "Failed to load page content. Please check connection and try again."}
            onRetry={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
          />
        </div>
      );
    }
    return this.props.children;
  }
}

const ICONS = {
  LayoutDashboard,
  Building2,
  MapPinned,
  Map,
  FileStack,
  FolderKanban,
  GitBranch,
  IndianRupee,
  Users,
  HeartHandshake,
  Home,
  KeyRound,
  ClipboardCheck,
  Files,
  ChartColumn,
  FileBarChart,
  BrainCircuit,
  Bell,
  Inbox,
  Cable,
  ScrollText,
  Shield,
  Settings,
};

export function DisclaimerBanner() {
  return (
    <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-center text-xs text-amber-950">
      All projects, parcels, owners, geometries, compensation figures, and ML scores in this prototype are
      synthetic demonstration data. They are not live land records, cadastral maps, or government statistics.
    </div>
  );
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    let alive = true;
    listNotifications({ unread: true, page_size: 1 })
      .then((res) => {
        if (alive) setUnread(res.meta?.total || 0);
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [location.pathname]);

  const groups = visibleNav(user?.role);

  const sidebar = (
    <div className="flex h-full flex-col bg-navy text-slate-100">
      <div className="flex items-center justify-between px-4 py-5">
        <Link to="/" className="block">
          <p className="font-serif text-lg leading-tight">NLAMP</p>
          <p className="text-[10px] uppercase tracking-[0.18em] text-teal-200">Command Center</p>
        </Link>
        <button className="rounded p-2 lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu">
          <X size={18} />
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto px-3 pb-6" aria-label="Main navigation">
        {groups.map((g) => (
          <div key={g.group} className="mb-4">
            <p className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">{g.group}</p>
            {g.items.map((item) => {
              const Icon = ICONS[item.icon] || LayoutDashboard;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    `mb-0.5 flex min-h-10 items-center gap-2 rounded-lg px-2 text-sm focus-visible:outline-2 focus-visible:outline-teal-200 ${
                      isActive ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white"
                    }`
                  }
                >
                  <Icon size={16} />
                  {item.label}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>
    </div>
  );

  return (
    <div className="min-h-screen bg-paper">
      <DisclaimerBanner />
      <div className="flex min-h-[calc(100vh-2.25rem)]">
        <aside className="hidden w-64 shrink-0 lg:block">{sidebar}</aside>
        {open ? (
          <div className="fixed inset-0 z-50 lg:hidden">
            <button tabIndex={-1} aria-hidden="true" className="absolute inset-0 bg-ink/50 cursor-default" aria-label="Close menu" onClick={() => setOpen(false)} />
            <div className="relative h-full w-72 max-w-[85vw]">{sidebar}</div>
          </div>
        ) : null}
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-line bg-white/90 px-4 py-3 backdrop-blur">
            <button className="rounded-lg p-2 hover:bg-sand focus-visible:outline-2 focus-visible:outline-teal-700 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
              <Menu size={20} />
            </button>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-ink">National Land Acquisition Management Platform</p>
              <p className="hidden text-xs text-slate-500 sm:block">Ministry prototype · SYNTHETIC data</p>
            </div>
            <Link
              to="/notifications"
              className="relative rounded-lg p-2 hover:bg-sand focus-visible:outline-2 focus-visible:outline-teal-700"
              aria-label={unread > 0 ? `Notifications (${unread} unread)` : "Notifications"}
            >
              <Bell size={18} />
              {unread > 0 ? (
                <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-600" aria-hidden="true" />
              ) : null}
            </Link>
            <div className="hidden items-center gap-2 sm:flex">
              <div className="text-right">
                <p className="text-sm font-semibold text-ink">{user?.full_name}</p>
                <p className="text-xs text-slate-500">{user?.email}</p>
              </div>
              <Badge tone="teal">{user?.role?.replaceAll("_", " ")}</Badge>
            </div>
            <button
              className="rounded-lg p-2 hover:bg-sand focus-visible:outline-2 focus-visible:outline-teal-700"
              onClick={() => {
                logout();
                navigate("/login");
              }}
              aria-label="Log out"
            >
              <LogOut size={18} />
            </button>
          </header>
          <main className="flex-1 px-4 py-5 md:px-6">
            <RouteErrorBoundary>
              <Suspense fallback={<RouteFallback />}>
                <Outlet />
              </Suspense>
            </RouteErrorBoundary>
          </main>
        </div>
      </div>
    </div>
  );
}

export function RoleGate({ roles, children }) {
  const { role } = useAuth();
  if (roles && !roles.includes(role)) {
    return (
      <div className="mx-auto max-w-lg py-16 text-center">
        <h1 className="font-serif text-2xl text-ink">Access not permitted</h1>
        <p className="mt-2 text-sm text-slate-600">
          Your role ({role?.replaceAll("_", " ")}) cannot open this page. Backend authorization remains in force.
        </p>
        <Link to="/" className="mt-4 inline-block text-sm font-semibold text-teal-800">
          Return to dashboard
        </Link>
      </div>
    );
  }
  return children;
}
