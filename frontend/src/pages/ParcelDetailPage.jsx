import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { listAcquisitions } from "../api/acquisitions";
import { listDocuments } from "../api/documents";
import { getParcel } from "../api/parcels";
import ParcelMap from "../components/ParcelMap";
import { Card, DataTable, EmptyState, ErrorState, PageHeader, Skeleton, StatusBadge } from "../components/ui";
import { errorMessage, ha } from "../lib/format";

export default function ParcelDetailPage() {
  const { id } = useParams();
  const [parcel, setParcel] = useState(null);
  const [cases, setCases] = useState([]);
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let alive = true;
    Promise.all([
      getParcel(id),
      listAcquisitions({ parcel_id: id, page_size: 20 }),
      listDocuments({ parcel_id: id, page_size: 20 }),
    ])
      .then(([p, c, d]) => {
        if (!alive) return;
        setParcel(p.data);
        setCases(c.data || []);
        setDocs(d.data || []);
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
  }, [id, reloadKey]);

  function handleRetry() {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  }

  if (loading) return <Skeleton className="h-64" />;
  if (error && !parcel) return <ErrorState message={error} onRetry={handleRetry} />;
  if (!parcel) return <EmptyState title="Parcel not found" body="Could not locate parcel details." />;

  const feature = parcel.geometry
    ? {
        ...parcel.geometry,
        properties: {
          ...(parcel.geometry.properties || {}),
          id: parcel.id,
          ulpin: parcel.ulpin,
          khasra_number: parcel.khasra_number,
          village: parcel.village,
          district_code: parcel.district_code,
          state_code: parcel.state_code,
          area_ha: parcel.area_ha,
          acquisition_status: parcel.acquisition_status,
        },
      }
    : null;

  return (
    <div>
      <PageHeader crumbs="Land & Projects / Parcels" title={parcel.ulpin} subtitle={`${parcel.village}, ${parcel.tehsil}`} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="font-serif text-lg text-ink">Identity</h2>
          <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
            <dt className="text-slate-500">Khasra</dt><dd>{parcel.khasra_number}</dd>
            <dt className="text-slate-500">Village</dt><dd>{parcel.village}</dd>
            <dt className="text-slate-500">Tehsil</dt><dd>{parcel.tehsil}</dd>
            <dt className="text-slate-500">District</dt><dd>{parcel.district_code}</dd>
            <dt className="text-slate-500">State</dt><dd>{parcel.state_code}</dd>
            <dt className="text-slate-500">Area</dt><dd>{ha(parcel.area_ha)}</dd>
            <dt className="text-slate-500">Status</dt><dd><StatusBadge value={parcel.acquisition_status} /></dd>
            <dt className="text-slate-500">Stage</dt><dd><StatusBadge value={parcel.current_stage} /></dd>
            <dt className="text-slate-500">Project</dt>
            <dd>{parcel.project ? <Link className="text-navy" to={`/projects/${parcel.project.id}`}>{parcel.project.code}</Link> : "—"}</dd>
          </dl>
        </Card>
        <Card>
          <h2 className="font-serif text-lg text-ink">Ownership summary</h2>
          <p className="mt-1 text-xs text-slate-500">Name, type and share only. Identification numbers are not returned by the API.</p>
          <ul className="mt-3 space-y-2 text-sm">
            {(parcel.owners || []).map((o, i) => (
              <li key={i} className="flex justify-between border-b border-line pb-2">
                <span>{o.name}</span>
                <span className="text-slate-500">{o.ownership_type} · {o.share_pct}%</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
      <div className="mt-4">
        <ParcelMap features={feature ? [feature] : []} />
      </div>
      <Card className="mt-4">
        <h2 className="mb-3 font-serif text-lg text-ink">Acquisition cases</h2>
        <DataTable
          rows={cases}
          columns={[
            { key: "case_number", header: "Case", render: (r) => <Link className="font-semibold text-navy" to={`/acquisitions/${r.id}`}>{r.case_number}</Link> },
            { key: "current_stage", header: "Stage", render: (r) => <StatusBadge value={r.current_stage} /> },
            { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
          ]}
          empty={<EmptyState title="No acquisition cases" body="No acquisition cases linked to this parcel." />}
        />
      </Card>
      <Card className="mt-4">
        <h2 className="mb-3 font-serif text-lg text-ink">Documents</h2>
        <DataTable
          rows={docs}
          empty={<EmptyState title="No documents" body="No documents uploaded for this parcel." />}
          columns={[
            { key: "name", header: "Name" },
            { key: "doc_type", header: "Type" },
            { key: "verification_status", header: "Status", render: (r) => <StatusBadge value={r.verification_status} /> },
          ]}
        />
      </Card>
    </div>
  );
}
