import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listAcquisitions } from "../api/acquisitions";
import { getFilters } from "../api/dashboard";
import { Card, DataTable, EmptyState, ErrorState, PageHeader, Pagination, Select, StatusBadge } from "../components/ui";
import { num } from "../lib/format";

export default function AcquisitionsPage() {
  const [params, setParams] = useState({ page: 1, page_size: 15, stage: "", status: "", project_id: "", risk_level: "" });
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [options, setOptions] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    getFilters().then((r) => setOptions(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    const q = { ...params };
    Object.keys(q).forEach((k) => { if (q[k] === "") delete q[k]; });
    listAcquisitions(q)
      .then((r) => {
        if (!alive) return;
        setRows(r.data);
        setTotal(r.meta?.total || 0);
        setError(null);
      })
      .catch((e) => {
        if (!alive) return;
        setError(e?.response?.data?.detail || e.message || "Failed to load acquisition cases.");
      })
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [params, reloadKey]);

  const handleRetry = () => {
    setError(null);
    setReloadKey((k) => k + 1);
  };

  return (
    <div>
      <PageHeader crumbs="Acquisition" title="Acquisition cases" />
      <Card className="mb-4">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <Select label="Project" value={params.project_id} onChange={(e) => setParams({ ...params, page: 1, project_id: e.target.value })}>
            <option value="">All</option>
            {options?.projects?.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
          </Select>
          <Select label="Stage" value={params.stage} onChange={(e) => setParams({ ...params, page: 1, stage: e.target.value })}>
            <option value="">All</option>
            {options?.stages?.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
          </Select>
          <Select label="Status" value={params.status} onChange={(e) => setParams({ ...params, page: 1, status: e.target.value })}>
            <option value="">All</option>
            <option value="OPEN">OPEN</option>
            <option value="CLOSED">CLOSED</option>
          </Select>
          <Select label="Risk" value={params.risk_level} onChange={(e) => setParams({ ...params, page: 1, risk_level: e.target.value })}>
            <option value="">All</option>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
          </Select>
        </div>
      </Card>
      {error ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : (
        <>
          <DataTable
            loading={loading}
            rows={rows}
            empty={
              <EmptyState
                title="No acquisition cases found"
                body="No acquisition cases match the current filter criteria."
              />
            }
            columns={[
              { key: "case_number", header: "Case", render: (r) => <Link className="font-semibold text-navy hover:underline" to={`/acquisitions/${r.id}`}>{r.case_number}</Link> },
              { key: "project_code", header: "Project" },
              { key: "ulpin", header: "ULPIN" },
              { key: "current_stage", header: "Stage", render: (r) => <StatusBadge value={r.current_stage} /> },
              { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
              { key: "risk_level", header: "Risk", render: (r) => <StatusBadge value={r.risk_level} /> },
              { key: "risk_score", header: "Score", render: (r) => (r.risk_score != null ? num(r.risk_score, 2) : "—") },
            ]}
          />
          <Pagination page={params.page} pageSize={params.page_size} total={total} onPage={(p) => setParams({ ...params, page: p })} />
        </>
      )}
    </div>
  );
}
