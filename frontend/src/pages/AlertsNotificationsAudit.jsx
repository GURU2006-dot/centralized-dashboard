import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { evaluateAlerts, listAlerts, markAlertRead } from "../api/alerts";
import { listAudit } from "../api/audit";
import { listNotifications, markAllNotificationsRead, markNotificationRead } from "../api/notifications";
import { getCharts, getKpis } from "../api/dashboard";
import { getIntegrationStatus, lookupIntegration, syncIntegration } from "../api/integrations";
import { getMlAnalytics, getMlMetrics } from "../api/ml";
import { Button, Card, DataTable, EmptyState, ErrorState, PageHeader, Pagination, Skeleton, StatCard, StatusBadge } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { dt, errorMessage } from "../lib/format";
import { ROLES } from "../lib/roles";

export function AlertsPage() {
  const { role } = useAuth();
  const toast = useToast();
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [evaluating, setEvaluating] = useState(false);
  const [markingId, setMarkingId] = useState(null);

  useEffect(() => {
    let active = true;
    listAlerts({ page, page_size: 15 })
      .then((r) => {
        if (!active) return;
        setRows(r.data || []);
        setTotal(r.meta?.total || 0);
      })
      .catch((e) => {
        if (!active) return;
        const msg = errorMessage(e);
        setError(msg);
        toast.error(msg);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [page, reloadKey, toast]);

  function handleRetry() {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  }

  async function onEvaluate() {
    if (evaluating) return;
    setEvaluating(true);
    try {
      const r = await evaluateAlerts();
      toast.success(`Created ${r.data.created} new unread alerts`);
      setReloadKey((k) => k + 1);
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setEvaluating(false);
    }
  }

  async function onMarkRead(id) {
    if (markingId) return;
    setMarkingId(id);
    try {
      await markAlertRead(id);
      setReloadKey((k) => k + 1);
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setMarkingId(null);
    }
  }

  return (
    <div>
      <PageHeader
        crumbs="Intelligence"
        title="Alerts"
        actions={role === ROLES.ADMIN ? (
          <Button loading={evaluating} disabled={evaluating} onClick={onEvaluate}>
            {evaluating ? "Evaluating..." : "Evaluate rules"}
          </Button>
        ) : null}
      />
      {error && !rows.length ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : (
        <>
          <DataTable
            rows={rows}
            loading={loading}
            empty={<EmptyState title="No alerts" body="No active or unread alerts at this time." />}
            columns={[
              { key: "severity", header: "Severity", render: (r) => <StatusBadge value={r.severity} /> },
              { key: "alert_type", header: "Type" },
              { key: "message", header: "Message" },
              { key: "is_read", header: "State", render: (r) => (r.is_read ? "Read" : "Unread") },
              { key: "created_at", header: "Created", render: (r) => dt(r.created_at) },
              { key: "id", header: "Action", render: (r) => !r.is_read ? (
                <Button variant="ghost" disabled={markingId === r.id} onClick={() => onMarkRead(r.id)} aria-label={`Mark alert ${r.id.slice(0, 8)} as read`}>
                  Mark read
                </Button>
              ) : null },
            ]}
          />
          <Pagination page={page} pageSize={15} total={total} onPage={setPage} />
        </>
      )}
    </div>
  );
}

export function NotificationsPage() {
  const toast = useToast();
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [markingAll, setMarkingAll] = useState(false);
  const [markingId, setMarkingId] = useState(null);

  useEffect(() => {
    let active = true;
    listNotifications({ page, page_size: 15 })
      .then((r) => {
        if (!active) return;
        setRows(r.data || []);
        setTotal(r.meta?.total || 0);
      })
      .catch((e) => {
        if (!active) return;
        const msg = errorMessage(e);
        setError(msg);
        toast.error(msg);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [page, reloadKey, toast]);

  function handleRetry() {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  }

  async function onMarkAllRead() {
    if (markingAll) return;
    setMarkingAll(true);
    try {
      await markAllNotificationsRead();
      toast.success("All notifications marked as read");
      setReloadKey((k) => k + 1);
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setMarkingAll(false);
    }
  }

  async function onMarkRead(id) {
    if (markingId) return;
    setMarkingId(id);
    try {
      await markNotificationRead(id);
      setReloadKey((k) => k + 1);
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setMarkingId(null);
    }
  }

  return (
    <div>
      <PageHeader
        crumbs="System"
        title="Notifications"
        actions={
          <Button variant="ghost" loading={markingAll} disabled={markingAll} onClick={onMarkAllRead}>
            {markingAll ? "Marking..." : "Mark all read"}
          </Button>
        }
      />
      {error && !rows.length ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : (
        <>
          <DataTable
            rows={rows}
            loading={loading}
            empty={<EmptyState title="No notifications" body="You are all caught up." />}
            columns={[
              { key: "title", header: "Title" },
              { key: "body", header: "Message" },
              { key: "is_read", header: "State", render: (r) => (r.is_read ? "Read" : "Unread") },
              { key: "created_at", header: "Created", render: (r) => dt(r.created_at) },
              { key: "id", header: "Action", render: (r) => !r.is_read ? (
                <Button variant="ghost" disabled={markingId === r.id} onClick={() => onMarkRead(r.id)} aria-label={`Mark notification ${r.id.slice(0, 8)} as read`}>
                  Mark read
                </Button>
              ) : null },
            ]}
          />
          <Pagination page={page} pageSize={15} total={total} onPage={setPage} />
        </>
      )}
    </div>
  );
}

export function AuditPage() {
  const toast = useToast();
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    listAudit({ page, page_size: 20 })
      .then((r) => {
        if (!active) return;
        setRows(r.data || []);
        setTotal(r.meta?.total || 0);
      })
      .catch((e) => {
        if (!active) return;
        const msg = errorMessage(e);
        setError(msg);
        toast.error(msg);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [page, reloadKey, toast]);

  function handleRetry() {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  }

  return (
    <div>
      <PageHeader crumbs="System" title="Audit logs" subtitle="Append-only. ADMIN only." />
      {error && !rows.length ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : (
        <>
          <DataTable
            rows={rows}
            loading={loading}
            empty={<EmptyState title="No audit logs" body="No audit records found." />}
            columns={[
              { key: "occurred_at", header: "When", render: (r) => dt(r.occurred_at) },
              { key: "action", header: "Action" },
              { key: "entity_type", header: "Entity" },
              { key: "entity_id", header: "ID", render: (r) => <span className="font-mono text-xs">{String(r.entity_id).slice(0, 12)}</span> },
              { key: "user_id", header: "Actor", render: (r) => <span className="font-mono text-xs">{String(r.user_id || "").slice(0, 8)}</span> },
            ]}
          />
          <Pagination page={page} pageSize={20} total={total} onPage={setPage} />
        </>
      )}
    </div>
  );
}

export function AnalyticsPage() {
  const toast = useToast();
  const [_kpis, setKpis] = useState(null);
  const [charts, setCharts] = useState(null);
  const [ml, setMl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    Promise.all([getKpis(), getCharts(), getMlAnalytics()])
      .then(([k, c, m]) => {
        if (!active) return;
        setKpis(k.data);
        setCharts(c.data);
        setMl(m.data);
      })
      .catch((e) => {
        if (!active) return;
        const msg = errorMessage(e);
        setError(msg);
        toast.error(msg);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [reloadKey, toast]);

  function handleRetry() {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  }

  const summary = ml?.summary;
  return (
    <div>
      <PageHeader crumbs="Intelligence" title="Analytics" subtitle="Operational KPIs plus latest persisted delay-risk predictions. Synthetic model." />
      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-32" />
          <div className="grid gap-4 lg:grid-cols-2">
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
          </div>
          <Skeleton className="h-48" />
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="High risk" value={summary?.high_risk_cases ?? "—"} />
            <StatCard label="Medium risk" value={summary?.medium_risk_cases ?? "—"} />
            <StatCard label="Low risk" value={summary?.low_risk_cases ?? "—"} />
            <StatCard label="Average score" value={summary ? `${summary.average_risk_score}/100` : "—"} />
          </div>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="font-serif text-lg">Risk by stage</h2>
              {ml?.by_stage?.length ? (
                <ul className="mt-2 text-sm">
                  {ml.by_stage.map((s) => (
                    <li key={s.stage} className="flex justify-between border-b border-line py-1">
                      <span>{s.stage}</span>
                      <span>H {s.HIGH} · M {s.MEDIUM} · L {s.LOW}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState title="No stage risk breakdown" body="No stage distribution data available." />
              )}
            </Card>
            <Card>
              <h2 className="font-serif text-lg">Risk by state</h2>
              {ml?.by_state?.length ? (
                <ul className="mt-2 text-sm">
                  {ml.by_state.map((s) => (
                    <li key={s.state_code} className="flex justify-between border-b border-line py-1">
                      <span>{s.state_code}</span>
                      <span>H {s.HIGH} · M {s.MEDIUM} · L {s.LOW}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState title="No state risk breakdown" body="No state risk data available." />
              )}
            </Card>
          </div>
          <Card className="mt-4">
            <h2 className="font-serif text-lg">Acquisition stages (all cases)</h2>
            {charts?.stage_distribution?.length ? (
              <ul className="mt-2 grid gap-1 text-sm md:grid-cols-2">
                {charts.stage_distribution.map((s) => (
                  <li key={s.stage} className="flex justify-between border-b border-line py-1">
                    <span>{s.stage}</span><span>{s.count}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No stage distribution" body="No acquisition stage data recorded." />
            )}
          </Card>
        </>
      )}
    </div>
  );
}

export function ModelPage() {
  const toast = useToast();
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    getMlMetrics()
      .then((r) => {
        if (!active) return;
        setMetrics(r.data);
      })
      .catch((e) => {
        if (!active) return;
        const msg = errorMessage(e);
        setError(msg);
        toast.error(msg);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [reloadKey, toast]);

  function handleRetry() {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  }

  return (
    <div>
      <PageHeader crumbs="Intelligence" title="Model information" />
      {loading ? (
        <Skeleton className="h-64" />
      ) : error ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : (
        <Card>
          <dl className="grid gap-2 text-sm md:grid-cols-2">
            <dt className="text-slate-500">Model</dt><dd>Random Forest Classifier</dd>
            <dt className="text-slate-500">Purpose</dt><dd>Land acquisition delay risk screening</dd>
            <dt className="text-slate-500">Training data</dt><dd>Synthetic demonstration dataset ({metrics?.n_samples ?? "—"} rows)</dd>
            <dt className="text-slate-500">Version</dt><dd>{metrics?.model_version ?? "—"}</dd>
            <dt className="text-slate-500">Output</dt><dd>0–100 display score (stored 0–1 = class-midpoint index / 100; not P(delay))</dd>
            <dt className="text-slate-500">Categories</dt><dd>LOW 0–39 · MEDIUM 40–69 · HIGH 70–100 (prototype conventions)</dd>
            <dt className="text-slate-500">Accuracy</dt><dd>{metrics?.accuracy ?? "—"}</dd>
            <dt className="text-slate-500">F1 macro</dt><dd>{metrics?.f1_macro ?? "—"}</dd>
            <dt className="text-slate-500">ROC-AUC (OVR)</dt><dd>{metrics?.roc_auc_ovr ?? "—"}</dd>
          </dl>
          <p className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-950">
            This model is a prototype trained on synthetic demonstration data and is not a validated government decision-making model.
          </p>
        </Card>
      )}
    </div>
  );
}

export function ReportsPage() {
  return (
    <div>
      <PageHeader crumbs="Intelligence" title="Reports" subtitle="Downloadable report APIs are not implemented. This is a viewing surface over live dashboard numbers." />
      <Card>
        <p className="text-sm text-slate-600">PDF / Excel export is unavailable. Use the dashboard filters, then print from the browser if needed. No fake PDF is generated.</p>
      </Card>
    </div>
  );
}

export function IntegrationsPage() {
  const toast = useToast();
  const { role } = useAuth();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [ulpin, setUlpin] = useState("");
  const [lookup, setLookup] = useState(null);
  const [syncingName, setSyncingName] = useState(null);
  const [lookingUp, setLookingUp] = useState(false);

  useEffect(() => {
    let active = true;
    getIntegrationStatus()
      .then((r) => {
        if (!active) return;
        setStatus(r.data);
      })
      .catch((e) => {
        if (!active) return;
        const msg = errorMessage(e);
        setError(msg);
        toast.error(msg);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [reloadKey, toast]);

  function handleRetry() {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  }

  async function onSync(name) {
    if (syncingName) return;
    setSyncingName(name);
    try {
      const endpoint = name === "land_records" ? "land-records" : name === "cadastral_maps" ? "cadastral" : name;
      const r = await syncIntegration(endpoint);
      toast.success(r.data.message);
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSyncingName(null);
    }
  }

  async function onLookup(e) {
    e.preventDefault();
    if (!ulpin.trim() || lookingUp) return;
    setLookingUp(true);
    try {
      const r = await lookupIntegration("land-records", ulpin.trim());
      setLookup(r.data);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setLookingUp(false);
    }
  }

  return (
    <div>
      <PageHeader
        crumbs="System"
        title="Integrations"
        subtitle="Government land-record, cadastral, registration, and financial APIs require departmental authorization and are not connected."
      />
      {loading ? (
        <Skeleton className="h-40" />
      ) : error ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : !status?.systems?.length ? (
        <EmptyState title="No integrations configured" body="Integration system statuses will appear here." />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {status.systems.map((s) => (
            <Card key={s.name}>
              <h2 className="font-serif text-lg text-ink">{s.name}</h2>
              <p className="text-sm text-slate-600">{s.message}</p>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-amber-800">MOCK / DEMONSTRATION · {s.mode}</p>
              {role === ROLES.ADMIN ? (
                <Button
                  className="mt-3"
                  variant="ghost"
                  loading={syncingName === s.name}
                  disabled={syncingName === s.name}
                  onClick={() => onSync(s.name)}
                >
                  {syncingName === s.name ? "Syncing..." : "Mock sync"}
                </Button>
              ) : null}
            </Card>
          ))}
        </div>
      )}
      <Card className="mt-4">
        <h2 className="font-serif text-lg">Mock land-records lookup</h2>
        <form className="mt-3 flex flex-wrap gap-2" onSubmit={onLookup}>
          <input
            className="min-h-11 rounded-lg border border-line px-3 text-sm focus-visible:outline-2 focus-visible:outline-teal-700"
            value={ulpin}
            onChange={(e) => setUlpin(e.target.value)}
            placeholder="ULPIN"
            aria-label="ULPIN for land records lookup"
          />
          <Button type="submit" loading={lookingUp} disabled={!ulpin.trim() || lookingUp}>
            {lookingUp ? "Looking up..." : "Lookup"}
          </Button>
        </form>
        {lookup ? <pre className="mt-3 overflow-auto text-xs">{JSON.stringify(lookup, null, 2)}</pre> : null}
      </Card>
    </div>
  );
}

export function UsersPage() {
  return (
    <div>
      <PageHeader crumbs="System" title="Users & roles" subtitle="No user-management API exists in the current backend." />
      <Card>
        <p className="text-sm text-slate-600">No user-management API exists. Demo directory accounts are seeded in PostgreSQL. This page does not invent a frontend-only user store.</p>
      </Card>
    </div>
  );
}

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div>
      <PageHeader crumbs="System" title="Settings" />
      <Card>
        <p className="text-sm">Signed in as {user?.full_name} ({user?.email})</p>
        <p className="mt-1 text-sm text-slate-600">Role {user?.role} · scope {user?.state_code || "national"} {user?.district_code || ""}</p>
        <Button
          className="mt-4"
          variant="ghost"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          Log out
        </Button>
      </Card>
    </div>
  );
}
