import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listProposals } from "../api/proposals";
import { Button, Card, DataTable, EmptyState, ErrorState, PageHeader, Pagination, Select, StatusBadge } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { day } from "../lib/format";
import { canWriteProposals } from "../lib/roles";

export default function ProposalsPage() {
  const { role } = useAuth();
  const [params, setParams] = useState({ page: 1, page_size: 15, status: "" });
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    const q = { ...params };
    if (!q.status) delete q.status;
    listProposals(q)
      .then((r) => {
        if (!alive) return;
        setRows(r.data);
        setTotal(r.meta?.total || 0);
        setError(null);
      })
      .catch((e) => {
        if (!alive) return;
        setError(e?.response?.data?.detail || e.message || "Failed to load proposals.");
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [params, reloadKey]);

  const handleRetry = () => {
    setError(null);
    setReloadKey((k) => k + 1);
  };

  return (
    <div>
      <PageHeader
        crumbs="Acquisition"
        title="Proposals"
        subtitle="Proposal status is the only approval action. Approving a proposal opens acquisition cases."
        actions={canWriteProposals(role) ? <Link to="/proposals/new"><Button>New proposal</Button></Link> : null}
      />
      <Card className="mb-4">
        <Select label="Status" value={params.status} onChange={(e) => setParams({ ...params, page: 1, status: e.target.value })}>
          <option value="">All</option>
          {["DRAFT", "SUBMITTED", "UNDER_VERIFICATION", "APPROVED", "REJECTED"].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </Select>
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
                title="No proposals found"
                body="No proposals match the current filter. Create a new proposal to begin the workflow."
              />
            }
            columns={[
              { key: "proposal_number", header: "Number", render: (r) => <Link className="font-semibold text-navy hover:underline" to={`/proposals/${r.id}`}>{r.proposal_number}</Link> },
              { key: "project_code", header: "Project" },
              { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
              { key: "required_area_ha", header: "Area (ha)" },
              { key: "submitted_at", header: "Submitted", render: (r) => day(r.submitted_at) },
              { key: "reviewed_at", header: "Reviewed", render: (r) => day(r.reviewed_at) },
            ]}
          />
          <Pagination page={params.page} pageSize={params.page_size} total={total} onPage={(p) => setParams({ ...params, page: p })} />
        </>
      )}
    </div>
  );
}
