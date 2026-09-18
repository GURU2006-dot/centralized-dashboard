import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { listAcquisitions } from "../api/acquisitions";
import { listFamilies } from "../api/families";
import { getMlSummary } from "../api/ml";
import { listParcels } from "../api/parcels";
import { getProject } from "../api/projects";
import ParcelMap from "../components/ParcelMap";
import { getParcel } from "../api/parcels";
import { Card, DataTable, EmptyState, ErrorState, PageHeader, Skeleton, StatCard, StatusBadge, Tabs } from "../components/ui";
import { ha, inr, num } from "../lib/format";

export default function ProjectDetailPage() {
  const { id } = useParams();
  const [tab, setTab] = useState("overview");
  const [project, setProject] = useState(null);
  const [parcels, setParcels] = useState([]);
  const [cases, setCases] = useState([]);
  const [families, setFamilies] = useState([]);
  const [features, setFeatures] = useState([]);
  const [risk, setRisk] = useState(null);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let alive = true;
    setError(null);
    Promise.all([
      getProject(id),
      listParcels({ project_id: id, page_size: 50 }),
      listAcquisitions({ project_id: id, page_size: 50 }),
      listFamilies({ project_id: id, page_size: 50 }),
      getMlSummary({ project_id: id }).catch(() => ({ data: null })),
    ])
      .then(async ([p, parcelsRes, casesRes, famRes, mlRes]) => {
        if (!alive) return;
        setProject(p.data);
        setParcels(parcelsRes.data || []);
        setCases(casesRes.data || []);
        setFamilies(famRes.data || []);
        setRisk(mlRes.data);
        const details = await Promise.all((parcelsRes.data || []).slice(0, 30).map((row) => getParcel(row.id).then((r) => r.data).catch(() => null)));
        if (!alive) return;
        setFeatures(
          details.filter(Boolean).map((d) => ({
            ...d.geometry,
            properties: {
              ...(d.geometry?.properties || {}),
              id: d.id,
              ulpin: d.ulpin,
              khasra_number: d.khasra_number,
              village: d.village,
              district_code: d.district_code,
              state_code: d.state_code,
              area_ha: d.area_ha,
              acquisition_status: d.acquisition_status,
            },
          })),
        );
      })
      .catch((e) => {
        if (!alive) return;
        if (e?.response?.status === 404) {
          setError("Project not found. The specified project does not exist.");
        } else {
          setError(e?.response?.data?.detail || e.message || "Failed to load project details.");
        }
      });
    return () => {
      alive = false;
    };
  }, [id, reloadKey]);

  const handleRetry = () => {
    setError(null);
    setProject(null);
    setReloadKey((k) => k + 1);
  };

  if (error) return <ErrorState message={error} onRetry={handleRetry} />;
  if (!project) return <Skeleton className="h-64" />;

  return (
    <div>
      <PageHeader crumbs="Land & Projects / Projects" title={`${project.code} — ${project.name}`} subtitle={project.purpose} />
      <div className="mb-4 flex flex-wrap gap-2">
        <StatusBadge value={project.status} />
        <StatusBadge value={project.current_stage} />
        <span className="text-sm text-slate-500">{project.state_code} · {project.district_code}</span>
      </div>
      <Tabs
        value={tab}
        onChange={setTab}
        tabs={[
          { id: "overview", label: "Overview" },
          { id: "parcels", label: "Land parcels" },
          { id: "acquisition", label: "Acquisition" },
          { id: "families", label: "Families" },
          { id: "gis", label: "GIS" },
        ]}
      />
      {tab === "overview" && (
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Estimated area" value={ha(project.estimated_area_ha)} />
          <StatCard label="Notified" value={ha(project.area_notified_ha)} />
          <StatCard label="Acquired" value={ha(project.area_acquired_ha)} />
          <StatCard label="Compensation assessed" value={inr(project.compensation_assessed_inr)} />
          <StatCard label="Compensation paid" value={inr(project.compensation_paid_inr)} />
          <StatCard label="Parcels" value={num(project.parcel_count)} />
          <StatCard label="Cases" value={num(project.case_count)} />
          <StatCard label="Families" value={num(project.affected_families)} />
          <StatCard label="Project risk index" value={risk ? `${risk.average_risk_score}/100` : "—"} hint="Mean of latest case scores (display 0–100)" />
          <StatCard label="High / med / low cases" value={risk ? `${risk.high_risk_cases} / ${risk.medium_risk_cases} / ${risk.low_risk_cases}` : "—"} />
        </div>
      )}
      {tab === "parcels" && (
        <div className="mt-4">
          <DataTable
            rows={parcels}
            empty={<EmptyState title="No land parcels linked" body="No land parcels have been associated with this project." />}
            columns={[
              { key: "ulpin", header: "ULPIN", render: (r) => <Link className="font-semibold text-navy hover:underline" to={`/parcels/${r.id}`}>{r.ulpin}</Link> },
              { key: "khasra_number", header: "Khasra" },
              { key: "village", header: "Village" },
              { key: "area_ha", header: "Area", render: (r) => ha(r.area_ha) },
              { key: "acquisition_status", header: "Status", render: (r) => <StatusBadge value={r.acquisition_status} /> },
            ]}
          />
        </div>
      )}
      {tab === "acquisition" && (
        <div className="mt-4">
          <DataTable
            rows={cases}
            empty={<EmptyState title="No acquisition cases" body="No acquisition cases have been registered for this project." />}
            columns={[
              { key: "case_number", header: "Case", render: (r) => <Link className="font-semibold text-navy hover:underline" to={`/acquisitions/${r.id}`}>{r.case_number}</Link> },
              { key: "ulpin", header: "ULPIN" },
              { key: "current_stage", header: "Stage", render: (r) => <StatusBadge value={r.current_stage} /> },
              { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
            ]}
          />
        </div>
      )}
      {tab === "families" && (
        <div className="mt-4">
          <DataTable
            rows={families}
            empty={<EmptyState title="No affected families" body="No affected families have been surveyed or recorded for this project." />}
            columns={[
              { key: "family_head_name", header: "Head" },
              { key: "member_count", header: "Members" },
              { key: "is_displaced", header: "Displaced", render: (r) => (r.is_displaced ? "Yes" : "No") },
              { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
            ]}
          />
        </div>
      )}
      {tab === "gis" && (
        <div className="mt-4">
          {features.length ? (
            <ParcelMap features={features} />
          ) : (
            <EmptyState
              title="No spatial boundaries available"
              body="Parcel geometries have not yet been mapped or loaded for this project."
            />
          )}
        </div>
      )}
      <Card className="mt-4 text-sm text-slate-600">
        Requiring body: {project.requiring_body || "—"} · Data source {project.data_source}
      </Card>
    </div>
  );
}
