import { useEffect, useId } from "react";

export function Button({
  children,
  variant = "primary",
  type = "button",
  className = "",
  disabled,
  loading,
  ...props
}) {
  const styles = {
    primary: "bg-teal-700 text-white hover:bg-teal-800",
    secondary: "bg-navy text-white hover:bg-navy-800",
    ghost: "bg-white text-navy border border-line hover:bg-sand",
    danger: "bg-red-700 text-white hover:bg-red-800",
  };
  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading ? "true" : undefined}
      className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 ${styles[variant] || styles.primary} ${className}`}
      {...props}
    >
      {loading ? "Working…" : children}
    </button>
  );
}

export function Input({ label, id, error, className = "", ref, ...props }) {
  const autoId = useId();
  const inputId = id || autoId;
  const errorId = `${inputId}-error`;
  return (
    <label className={`block ${className}`} htmlFor={inputId}>
      {label ? <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span> : null}
      <input
        ref={ref}
        id={inputId}
        aria-required={props.required ? "true" : undefined}
        aria-describedby={error ? errorId : undefined}
        className={`min-h-11 w-full rounded-lg border bg-white px-3 text-sm focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-teal-700 ${error ? "border-red-400" : "border-line"}`}
        aria-invalid={error ? "true" : undefined}
        {...props}
      />
      {error ? <span id={errorId} role="alert" className="mt-1 block text-xs text-red-700">{error}</span> : null}
    </label>
  );
}

export function Select({ label, id, error, children, className = "", ref, ...props }) {
  const autoId = useId();
  const inputId = id || autoId;
  const errorId = `${inputId}-error`;
  return (
    <label className={`block ${className}`} htmlFor={inputId}>
      {label ? <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span> : null}
      <select
        ref={ref}
        id={inputId}
        aria-required={props.required ? "true" : undefined}
        aria-describedby={error ? errorId : undefined}
        className={`min-h-11 w-full rounded-lg border bg-white px-3 text-sm focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-teal-700 ${error ? "border-red-400" : "border-line"}`}
        aria-invalid={error ? "true" : undefined}
        {...props}
      >
        {children}
      </select>
      {error ? <span id={errorId} role="alert" className="mt-1 block text-xs text-red-700">{error}</span> : null}
    </label>
  );
}

export function Textarea({ label, id, error, className = "", ref, ...props }) {
  const autoId = useId();
  const inputId = id || autoId;
  const errorId = `${inputId}-error`;
  return (
    <label className={`block ${className}`} htmlFor={inputId}>
      {label ? <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span> : null}
      <textarea
        ref={ref}
        id={inputId}
        aria-required={props.required ? "true" : undefined}
        aria-describedby={error ? errorId : undefined}
        className={`min-h-24 w-full rounded-lg border bg-white px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-teal-700 ${error ? "border-red-400" : "border-line"}`}
        aria-invalid={error ? "true" : undefined}
        {...props}
      />
      {error ? <span id={errorId} role="alert" className="mt-1 block text-xs text-red-700">{error}</span> : null}
    </label>
  );
}

export function Card({ children, className = "" }) {
  return <section className={`glass-card rounded-2xl p-5 ${className}`}>{children}</section>;
}

export function PageHeader({ title, crumbs, actions, subtitle }) {
  return (
    <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        {crumbs ? <p className="mb-1 text-xs uppercase tracking-wider text-slate-500">{crumbs}</p> : null}
        <h1 className="font-serif text-2xl font-semibold text-ink md:text-3xl">{title}</h1>
        {subtitle ? <p className="mt-1 max-w-3xl text-sm text-slate-600">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function Badge({ children, tone = "slate" }) {
  const map = {
    slate: "bg-slate-100 text-slate-700",
    teal: "bg-teal-50 text-teal-800",
    navy: "bg-sky-50 text-sky-900",
    green: "bg-emerald-50 text-emerald-800",
    amber: "bg-amber-50 text-amber-900",
    red: "bg-red-50 text-red-800",
    violet: "bg-violet-50 text-violet-800",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${map[tone] || map.slate}`}>
      {children}
    </span>
  );
}

const STATUS_TONE = {
  DRAFT: "slate",
  SUBMITTED: "navy",
  UNDER_VERIFICATION: "amber",
  APPROVED: "green",
  REJECTED: "red",
  OPEN: "navy",
  CLOSED: "green",
  PLANNED: "slate",
  ACTIVE: "teal",
  DELAYED: "red",
  ON_HOLD: "amber",
  COMPLETED: "green",
  SIA: "navy",
  NOTIFICATION: "navy",
  AWARD: "violet",
  COMPENSATION_ASSESSMENT: "amber",
  COMPENSATION_PAID: "green",
  POSSESSION: "teal",
  REHABILITATION_RESETTLEMENT: "violet",
  HIGH: "red",
  MEDIUM: "amber",
  LOW: "slate",
  CRITICAL: "red",
  PAID: "green",
  PARTIAL: "amber",
  ASSESSED: "navy",
  TAKEN: "green",
  NOT_TAKEN: "slate",
  SUBMITTED: "green",
  ASSIGNED: "navy",
  IN_PROGRESS: "amber",
  VERIFIED: "green",
  PENDING: "amber",
  SYNTHETIC: "slate",
};

export function StatusBadge({ value }) {
  if (!value) return <Badge>—</Badge>;
  return <Badge tone={STATUS_TONE[value] || "slate"}>{String(value).replaceAll("_", " ")}</Badge>;
}

export function StatCard({ label, value, hint, loading }) {
  return (
    <Card className="min-h-[7.5rem]">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      {loading ? (
        <div className="mt-3 h-8 w-28 animate-pulse rounded bg-slate-200" />
      ) : (
        <p className="mt-2 font-serif text-2xl font-semibold text-ink">{value}</p>
      )}
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </Card>
  );
}

export function EmptyState({ title, body, action }) {
  return (
    <div className="rounded-2xl border border-dashed border-line bg-white/70 px-6 py-12 text-center" role="status">
      <p className="font-semibold text-ink">{title}</p>
      {body ? <p className="mx-auto mt-1 max-w-md text-sm text-slate-600">{body}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 px-6 py-8 text-center" role="alert">
      <p className="font-semibold text-red-900">Could not load this view</p>
      <p className="mt-1 text-sm text-red-800">{message || "An unexpected error occurred."}</p>
      {onRetry ? (
        <Button className="mt-4" variant="ghost" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}

export function Skeleton({ className = "h-24" }) {
  return <div className={`animate-pulse rounded-2xl bg-slate-200/80 ${className}`} aria-hidden="true" />;
}

export function Pagination({ page, pageSize, total, onPage }) {
  const pages = Math.max(1, Math.ceil((total || 0) / (pageSize || 20)));
  return (
    <nav aria-label="Pagination" className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-600">
      <span aria-live="polite">
        {total ?? 0} records · page {page} of {pages}
      </span>
      <div className="flex gap-2">
        <Button variant="ghost" disabled={page <= 1} onClick={() => onPage(page - 1)} aria-label="Previous page">
          Previous
        </Button>
        <Button variant="ghost" disabled={page >= pages} onClick={() => onPage(page + 1)} aria-label="Next page">
          Next
        </Button>
      </div>
    </nav>
  );
}

export function DataTable({ columns, rows, keyField = "id", loading, empty }) {
  if (loading) {
    return (
      <div className="space-y-2" aria-busy="true" aria-label="Loading table data">
        <Skeleton className="h-10" />
        <Skeleton className="h-16" />
        <Skeleton className="h-16" />
      </div>
    );
  }
  if (!rows?.length) {
    return empty || <EmptyState title="No records found" body="Try adjusting filters or search." />;
  }
  return (
    <div className="overflow-x-auto rounded-xl border border-line" tabIndex={0} role="region" aria-label="Data table">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-sand/80 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            {columns.map((c) => (
              <th key={c.key} scope="col" className="whitespace-nowrap px-3 py-3 font-semibold">
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[keyField]} className="border-t border-line bg-white hover:bg-sand/40">
              {columns.map((c) => (
                <td key={c.key} className="px-3 py-3 align-middle">
                  {c.render ? c.render(row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Modal({ open, title, children, onClose, footer }) {
  const dialogId = useId();
  const titleId = `${dialogId}-title`;

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") onClose?.();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-end justify-center bg-ink/40 p-3 sm:items-center" role="dialog" aria-modal="true" aria-labelledby={titleId}>
      <button type="button" tabIndex={-1} className="absolute inset-0 cursor-default" aria-label="Close dialog" onClick={onClose} />
      <div className="relative z-10 w-full max-w-lg rounded-2xl bg-white p-5 shadow-2xl">
        <div className="mb-4 flex items-start justify-between gap-3">
          <h2 id={titleId} className="font-serif text-xl text-ink">{title}</h2>
          <button className="rounded-md px-2 py-1 text-slate-500 hover:bg-sand focus-visible:outline-2 focus-visible:outline-teal-700" onClick={onClose} aria-label="Close dialog">
            ✕
          </button>
        </div>
        <div>{children}</div>
        {footer ? <div className="mt-5 flex justify-end gap-2">{footer}</div> : null}
      </div>
    </div>
  );
}

export function Tabs({ tabs, value, onChange }) {
  return (
    <div className="flex gap-1 overflow-x-auto border-b border-line" role="tablist">
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={value === t.id}
          className={`min-h-11 whitespace-nowrap px-4 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-teal-700 ${
            value === t.id ? "border-b-2 border-teal-700 text-teal-800" : "text-slate-500 hover:text-ink"
          }`}
          onClick={() => onChange(t.id)}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function Timeline({ stages, current, events = [] }) {
  const idx = stages.indexOf(current);
  return (
    <ol className="space-y-3">
      {stages.map((stage, i) => {
        const done = idx > i || current === "COMPLETED";
        const active = stage === current;
        const ev = events.filter((e) => e.to_stage === stage);
        return (
          <li key={stage} className="flex gap-3">
            <div className="flex flex-col items-center">
              <span
                className={`h-3.5 w-3.5 rounded-full ${
                  active ? "bg-teal-700 ring-4 ring-teal-100" : done ? "bg-emerald-600" : "bg-slate-300"
                }`}
              />
              {i < stages.length - 1 ? <span className="mt-1 w-px flex-1 bg-line" /> : null}
            </div>
            <div className="pb-4">
              <p className={`text-sm font-semibold ${active ? "text-teal-800" : "text-ink"}`}>
                {stage.replaceAll("_", " ")}
              </p>
              {ev.map((e) => (
                <p key={e.id} className="mt-1 text-xs text-slate-500">
                  {e.occurred_at ? new Date(e.occurred_at).toLocaleString("en-IN") : ""} {e.actor_name ? `· ${e.actor_name}` : ""}
                  {e.remarks ? ` · ${e.remarks}` : ""}
                </p>
              ))}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
