import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { listAlerts } from "../api/alerts";
import { getCharts, getFilters, getKpis } from "../api/dashboard";
import { getMlSummary } from "../api/ml";
import { listProjects } from "../api/projects";
import { Card, ErrorState, PageHeader, Select, Skeleton, StatCard, StatusBadge } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { errorMessage, ha, inr, num } from "../lib/format";
import { canField, canWriteProposals } from "../lib/roles";

const PIE = ["#143a5c", "#0f766e", "#b45309", "#7c3aed", "#be123c", "#0369a1", "#365314", "#57534e"];

export default function DashboardPage() {
  const { role } = useAuth();
  const [filters, setFilters] = useState({ state: "", district: "", project_id: "", stage: "", status: "" });
  const [options, setOptions] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [charts, setCharts] = useState(null);
  const [projects, setProjects] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [ml, setMl] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);

  const params = useMemo(() => {
    const p = {};
    Object.entries(filters).forEach(([k, v]) => {
      if (v) p[k] = v;
    });
    return p;
  }, [filters]);

  useEffect(() => {
    getFilters()
      .then((r) => setOptions(r.data))
      .catch(() => {});
  }, [reloadKey]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    Promise.all([
      getKpis(params),
      getCharts(params),
      listProjects({ page_size: 5, ...params }),
      listAlerts({ page_size: 5 }),
      getMlSummary(),
    ])
      .then(([k, c, p, a, m]) => {
        if (!alive) return;
        setKpis(k.data);
        setCharts(c.data);
        setProjects(p.data || []);
        setAlerts(a.data || []);
        setMl(m.data);
      })
      .catch((e) => {
        if (!alive) return;
        setError(errorMessage(e));
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [params, reloadKey]);

  function handleRetry() {
    setReloadKey((k) => k + 1);
  }

  if (error) return <ErrorState message={error} onRetry={handleRetry} />;

  return (
    <div>
      <PageHeader
        crumbs="Overview"
        title="National command dashboard"
        subtitle="Figures are assembled from PostgreSQL via the dashboard API. They are synthetic demonstration values."
      />
      <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <Select label="State" value={filters.state} onChange={(e) => setFilters({ ...filters, state: e.target.value })}>
          <option value="">All states</option>
          {options?.states?.map((s) => (
            <option key={s.code} value={s.code}>
              {s.name}
            </option>
          ))}
        </Select>
        <Select label="District" value={filters.district} onChange={(e) => setFilters({ ...filters, district: e.target.value })}>
          <option value="">All districts</option>
          {options?.districts?.map((s) => (
            <option key={s.code} value={s.code}>
              {s.name}
            </option>
          ))}
        </Select>
        <Select label="Project" value={filters.project_id} onChange={(e) => setFilters({ ...filters, project_id: e.target.value })}>
          <option value="">All projects</option>
          {options?.projects?.map((s) => (
            <option key={s.code} value={s.code}>
              {s.name}
            </option>
          ))}
        </Select>
        <Select label="Stage" value={filters.stage} onChange={(e) => setFilters({ ...filters, stage: e.target.value })}>
          <option value="">All stages</option>
          {options?.stages?.map((s) => (
            <option key={s.code} value={s.code}>
              {s.name}
            </option>
          ))}
        </Select>
        <Select label="Status" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">All statuses</option>
          {options?.statuses?.map((s) => (
            <option key={s.code} value={s.code}>
              {s.name}
            </option>
          ))}
        </Select>
      </div>

      {/* ── National Acquisition Pulse ── */}
      <NationalAcquisitionPulse kpis={kpis} ml={ml} loading={loading} />

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
        <StatCard loading={loading} label="Total projects" value={num(kpis?.total_projects)} />
        <StatCard loading={loading} label="Area notified" value={ha(kpis?.area_notified_ha)} />
        <StatCard loading={loading} label="Area acquired" value={ha(kpis?.area_acquired_ha)} />
        <StatCard loading={loading} label="Compensation assessed" value={inr(kpis?.compensation_assessed_inr)} />
        <StatCard loading={loading} label="Compensation paid" value={inr(kpis?.compensation_paid_inr)} />
        <StatCard loading={loading} label="Affected families" value={num(kpis?.affected_families)} />
        <StatCard loading={loading} label="Displaced families" value={num(kpis?.displaced_families)} />
        <StatCard loading={loading} label="Delayed projects" value={num(kpis?.delayed_projects)} />
        <StatCard loading={loading} label="Projects at risk" value={num(kpis?.projects_at_risk)} hint="Delayed or HIGH model risk (synthetic)" />
        <StatCard loading={loading} label="R&R complete" value={`${kpis?.rr_progress?.pct_complete ?? "—"}%`} />
        <StatCard loading={loading} label="Cases scored" value={num(ml?.cases_scored)} hint="Latest prediction per case" />
        <StatCard loading={loading} label="High delay risk" value={num(ml?.high_risk_cases)} hint="Decision support only" />
        <StatCard loading={loading} label="Medium / Low" value={`${ml?.medium_risk_cases ?? "—"} / ${ml?.low_risk_cases ?? "—"}`} />
        <StatCard loading={loading} label="Average risk score" value={ml?.average_risk_score != null ? `${ml.average_risk_score}/100` : "—"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        <ChartCard title="Acquisition stage distribution">
          {loading ? <Skeleton className="h-64" /> : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={charts?.stage_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" tick={{ fontSize: 10 }} interval={0} angle={-25} textAnchor="end" height={70} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#143a5c" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <ChartCard title="State-wise projects">
          {loading ? <Skeleton className="h-64" /> : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={charts?.state_wise_progress || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="state_code" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="projects" fill="#0f766e" name="Projects" />
                <Bar dataKey="area_notified_ha" fill="#143a5c" name="Notified ha" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <ChartCard title="Compensation assessed vs paid">
          {loading ? <Skeleton className="h-64" /> : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={charts?.compensation || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="project_code" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip formatter={(v) => inr(v)} />
                <Legend />
                <Bar dataKey="assessed_inr" fill="#143a5c" name="Assessed" />
                <Bar dataKey="paid_inr" fill="#0f766e" name="Paid" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <ChartCard title="R&R status">
          {loading ? <Skeleton className="h-64" /> : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={charts?.rr_status || []} dataKey="count" nameKey="status" outerRadius={90} label>
                  {(charts?.rr_status || []).map((_, i) => (
                    <Cell key={i} fill={PIE[i % PIE.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <ChartCard title="Model risk distribution">
          {loading ? <Skeleton className="h-64" /> : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={charts?.risk || []} dataKey="count" nameKey="risk_level" outerRadius={90} label>
                  {(charts?.risk || []).map((_, i) => (
                    <Cell key={i} fill={PIE[i % PIE.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-serif text-lg text-ink">Projects</h2>
            <Link to="/projects" className="text-sm font-semibold text-teal-800">View all</Link>
          </div>
          <ul className="space-y-2 text-sm">
            {projects.map((p) => (
              <li key={p.id} className="flex items-center justify-between gap-2 border-b border-line pb-2">
                <Link to={`/projects/${p.id}`} className="font-semibold text-navy hover:underline">{p.code}</Link>
                <StatusBadge value={p.status} />
              </li>
            ))}
          </ul>
          <div className="mt-4 flex flex-wrap gap-2 text-sm">
            {canWriteProposals(role) ? (
              <Link className="rounded-lg bg-navy px-3 py-2 font-semibold text-white" to="/proposals/new">New proposal</Link>
            ) : null}
            {canField(role) ? (
              <Link className="rounded-lg border border-line px-3 py-2 font-semibold" to="/field">Field queue</Link>
            ) : null}
            <Link className="rounded-lg border border-line px-3 py-2 font-semibold" to="/alerts">Alerts</Link>
          </div>
        </Card>
      </div>

      <Card className="mt-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-serif text-lg text-ink">Important alerts</h2>
          <Link to="/alerts" className="text-sm font-semibold text-teal-800">Open alerts</Link>
        </div>
        {alerts.length === 0 ? <p className="text-sm text-slate-500">No alerts in this page.</p> : (
          <ul className="space-y-2">
            {alerts.map((a) => (
              <li key={a.id} className="flex flex-wrap items-start justify-between gap-2 border-b border-line pb-2 text-sm">
                <span>{a.message}</span>
                <StatusBadge value={a.severity} />
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <Card>
      <h2 className="mb-3 font-serif text-lg text-ink">{title}</h2>
      {children}
    </Card>
  );
}

/**
 * National Acquisition Pulse
 * A compact, operationally-focused band of headline KPIs placed near the top
 * of the Dashboard. Reuses existing kpis + ml API data — no new endpoints.
 */
function NationalAcquisitionPulse({ kpis, ml, loading }) {
  // Derived: compensation disbursement rate (paid / assessed)
  const disbRate =
    kpis?.compensation_assessed_inr && kpis.compensation_assessed_inr > 0
      ? Math.round((kpis.compensation_paid_inr / kpis.compensation_assessed_inr) * 100)
      : null;

  const metrics = [
    {
      id: "pulse-projects",
      label: "Active projects",
      value: num(kpis?.total_projects),
      accent: "teal",
    },
    {
      id: "pulse-acquired",
      label: "Land acquired",
      value: ha(kpis?.area_acquired_ha),
      accent: "teal",
    },
    {
      id: "pulse-disb",
      label: "Disbursement progress",
      value: disbRate != null ? `${disbRate}%` : "—",
      hint: "paid vs assessed",
      accent: disbRate != null && disbRate < 50 ? "amber" : "teal",
    },
    {
      id: "pulse-delayed",
      label: "Delayed projects",
      value: num(kpis?.delayed_projects),
      accent: kpis?.delayed_projects > 0 ? "red" : "teal",
    },
    {
      id: "pulse-highrisk",
      label: "High delay risk",
      value: num(ml?.high_risk_cases),
      hint: "Prototype Risk Index",
      accent: ml?.high_risk_cases > 0 ? "red" : "teal",
    },
    {
      id: "pulse-rr",
      label: "R\u0026R complete",
      value: kpis?.rr_progress?.pct_complete != null ? `${kpis.rr_progress.pct_complete}%` : "—",
      accent: "teal",
    },
  ];

  return (
    <section
      aria-label="National Acquisition Pulse"
      className="mb-5 rounded-2xl border border-teal-100 bg-gradient-to-r from-[#0f3552]/[0.04] to-teal-50/40 p-4"
    >
      <div className="mb-3 flex items-center gap-2">
        <span
          className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-teal-600"
          aria-hidden="true"
        />
        <h2 className="text-xs font-semibold uppercase tracking-widest text-teal-800">
          National Acquisition Pulse
        </h2>
        <span className="ml-auto text-xs text-slate-400">
          Synthetic demonstration data
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {metrics.map((m) =>
          loading ? (
            <div key={m.id} className="space-y-2">
              <div className="h-3 w-20 animate-pulse rounded bg-slate-200" aria-hidden="true" />
              <div className="h-7 w-16 animate-pulse rounded bg-slate-200" aria-hidden="true" />
            </div>
          ) : (
            <PulseMetric key={m.id} id={m.id} {...m} />
          )
        )}
      </div>
    </section>
  );
}

const PULSE_ACCENT = {
  teal: "text-teal-700",
  amber: "text-amber-600",
  red: "text-red-600",
};

function PulseMetric({ id, label, value, hint, accent = "teal" }) {
  return (
    <div>
      <p
        id={`${id}-label`}
        className="text-xs font-semibold uppercase tracking-wide text-slate-500"
      >
        {label}
      </p>
      <p
        aria-labelledby={`${id}-label`}
        className={`mt-1 font-serif text-2xl font-semibold leading-tight ${PULSE_ACCENT[accent] ?? PULSE_ACCENT.teal}`}
      >
        {value ?? "—"}
      </p>
      {hint ? (
        <p className="mt-0.5 text-xs text-slate-400">{hint}</p>
      ) : null}
    </div>
  );
}
