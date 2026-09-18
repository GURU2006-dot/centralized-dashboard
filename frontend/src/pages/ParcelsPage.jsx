import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getFilters } from "../api/dashboard";
import { listParcels } from "../api/parcels";
import { Card, DataTable, EmptyState, ErrorState, Input, PageHeader, Pagination, Select, StatusBadge } from "../components/ui";
import { ha } from "../lib/format";

export default function ParcelsPage() {
  const [params, setParams] = useState({
    page: 1,
    page_size: 15,
    ulpin: "",
    khasra: "",
    state: "",
    district: "",
    project_id: "",
    status: "",
  });
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
    Object.keys(q).forEach((k) => {
      if (q[k] === "") delete q[k];
    });
    listParcels(q)
      .then((r) => {
        if (!alive) return;
        setRows(r.data);
        setTotal(r.meta?.total || 0);
        setError(null);
      })
      .catch((e) => {
        if (!alive) return;
        setError(e?.response?.data?.detail || e.message || "Failed to load land parcels.");
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
      <PageHeader crumbs="Land & Projects" title="Land parcels" subtitle="Owner identity numbers, phones and addresses are not shown." />
      <Card className="mb-4">
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
          <Input label="ULPIN" value={params.ulpin} onChange={(e) => setParams({ ...params, page: 1, ulpin: e.target.value })} />
          <Input label="Khasra" value={params.khasra} onChange={(e) => setParams({ ...params, page: 1, khasra: e.target.value })} />
          <Select label="State" value={params.state} onChange={(e) => setParams({ ...params, page: 1, state: e.target.value })}>
            <option value="">All</option>
            {options?.states?.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
          </Select>
          <Select label="District" value={params.district} onChange={(e) => setParams({ ...params, page: 1, district: e.target.value })}>
            <option value="">All</option>
            {options?.districts?.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
          </Select>
          <Select label="Project" value={params.project_id} onChange={(e) => setParams({ ...params, page: 1, project_id: e.target.value })}>
            <option value="">All</option>
            {options?.projects?.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
          </Select>
          <Select label="Status" value={params.status} onChange={(e) => setParams({ ...params, page: 1, status: e.target.value })}>
            <option value="">All</option>
            <option value="NOT_STARTED">NOT_STARTED</option>
            <option value="IN_PROCESS">IN_PROCESS</option>
            <option value="ACQUIRED">ACQUIRED</option>
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
                title="No land parcels found"
                body="No land parcels match the current filter criteria. Try adjusting your search or filters."
              />
            }
            columns={[
              { key: "ulpin", header: "ULPIN", render: (r) => <Link className="font-semibold text-navy hover:underline" to={`/parcels/${r.id}`}>{r.ulpin}</Link> },
              { key: "khasra_number", header: "Khasra" },
              { key: "village", header: "Village" },
              { key: "tehsil", header: "Tehsil" },
              { key: "district_code", header: "District" },
              { key: "area_ha", header: "Area", render: (r) => ha(r.area_ha) },
              { key: "project_code", header: "Project" },
              { key: "acquisition_status", header: "Status", render: (r) => <StatusBadge value={r.acquisition_status} /> },
            ]}
          />
          <Pagination page={params.page} pageSize={params.page_size} total={total} onPage={(p) => setParams({ ...params, page: p })} />
        </>
      )}
    </div>
  );
}
