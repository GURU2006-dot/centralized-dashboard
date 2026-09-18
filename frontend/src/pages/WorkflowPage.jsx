import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listAcquisitions } from "../api/acquisitions";
import { Card, EmptyState, ErrorState, PageHeader, Skeleton, StatusBadge } from "../components/ui";
import { STAGES } from "../lib/roles";

export default function WorkflowPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let alive = true;
    listAcquisitions({ page_size: 40 })
      .then((r) => {
        if (!alive) return;
        setRows(r.data || []);
        setError(null);
      })
      .catch((e) => {
        if (!alive) return;
        setError(e?.response?.data?.detail || e.message || "Failed to load workflow cases.");
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [reloadKey]);

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  };

  return (
    <div>
      <PageHeader crumbs="Acquisition" title="Workflow tracker" subtitle="Catalogue stages only. Progress is derived from current_stage on each case." />
      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : rows.length === 0 ? (
        <EmptyState title="No workflow cases found" body="No active acquisition cases to track at this time." />
      ) : (
        <div className="space-y-3">
          {rows.map((r) => {
            const idx = STAGES.indexOf(r.current_stage);
            return (
              <Card key={r.id}>
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <Link className="font-semibold text-navy hover:underline" to={`/acquisitions/${r.id}`}>{r.case_number}</Link>
                  <div className="flex gap-2"><StatusBadge value={r.current_stage} /><StatusBadge value={r.status} /></div>
                </div>
                <div className="grid grid-cols-8 gap-1">
                  {STAGES.map((s, i) => (
                    <div key={s} className={`h-2 rounded ${i <= idx ? "bg-teal-700" : "bg-slate-200"}`} title={s} />
                  ))}
                </div>
                <p className="mt-2 text-xs text-slate-500">{r.project_code} · {r.ulpin}</p>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
