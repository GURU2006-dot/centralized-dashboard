import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getFilters } from "../api/dashboard";
import { getParcelGeojson } from "../api/gis";
import ParcelMap from "../components/ParcelMap";
import {
  Badge,
  Button,
  Card,
  DataTable,
  EmptyState,
  ErrorState,
  PageHeader,
  Select,
  Skeleton,
  StatusBadge,
} from "../components/ui";
import { ha } from "../lib/format";

export default function GisMapPage() {
  const navigate = useNavigate();
  const [options, setOptions] = useState(null);
  const [filters, setFilters] = useState({
    state: "",
    district: "",
    project_id: "",
    status: "",
    risk_level: "",
    stage: "",
  });
  const [features, setFeatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [colorMode, setColorMode] = useState("risk");
  const [viewMode, setViewMode] = useState("both"); // "both" | "map" | "table"
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    getFilters()
      .then((r) => setOptions(r.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    const q = { limit: 80 };
    Object.entries(filters).forEach(([k, v]) => {
      if (v) q[k] = v;
    });
    getParcelGeojson(q)
      .then((r) => {
        if (!alive) return;
        setFeatures(r.data?.features || []);
        setError(null);
      })
      .catch((e) => {
        if (!alive) return;
        const msg =
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to load GIS parcel spatial data. Please check connection and try again.";
        setError(msg);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [filters, reloadKey]);

  const handleRetry = () => {
    setError(null);
    setReloadKey((k) => k + 1);
  };

  const handleResetFilters = () => {
    setFilters({ state: "", district: "", project_id: "", status: "", risk_level: "", stage: "" });
  };

  const tableRows = useMemo(() => {
    return (features || []).map((f) => f.properties || {});
  }, [features]);

  const columns = useMemo(
    () => [
      {
        key: "ulpin",
        header: "ULPIN",
        render: (r) => (
          <Link
            className="font-semibold text-navy hover:underline"
            to={r.case_id ? `/acquisitions/${r.case_id}` : `/parcels/${r.id}`}
          >
            {r.ulpin || "—"}
          </Link>
        ),
      },
      { key: "khasra_number", header: "Khasra", render: (r) => r.khasra_number || "—" },
      { key: "village", header: "Village", render: (r) => r.village || "—" },
      { key: "tehsil", header: "Tehsil", render: (r) => r.tehsil || "—" },
      { key: "district_code", header: "District", render: (r) => r.district_code || "—" },
      { key: "state_code", header: "State", render: (r) => r.state_code || "—" },
      { key: "area_ha", header: "Area", render: (r) => ha(r.area_ha) },
      {
        key: "acquisition_status",
        header: "Status",
        render: (r) => <StatusBadge value={r.acquisition_status} />,
      },
      {
        key: "current_stage",
        header: "Stage",
        render: (r) => <StatusBadge value={r.current_stage} />,
      },
      {
        key: "risk_level",
        header: "Risk",
        render: (r) => {
          const tone =
            r.risk_level === "HIGH"
              ? "red"
              : r.risk_level === "MEDIUM"
                ? "amber"
                : r.risk_level === "LOW"
                  ? "green"
                  : "slate";
          return (
            <Badge tone={tone}>
              {r.risk_level || "UNSCORED"}
              {r.risk_score != null ? ` (${r.risk_score})` : ""}
            </Badge>
          );
        },
      },
    ],
    [],
  );

  return (
    <div>
      <PageHeader
        crumbs="Land & Projects"
        title="GIS map"
        subtitle="One bulk GeoJSON response from /api/gis/parcels. Coordinates are not invented."
      />
      <Card className="mb-4">
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
          <Select label="State" value={filters.state} onChange={(e) => setFilters({ ...filters, state: e.target.value })}>
            <option value="">All</option>
            {options?.states?.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
          </Select>
          <Select label="District" value={filters.district} onChange={(e) => setFilters({ ...filters, district: e.target.value })}>
            <option value="">All</option>
            {options?.districts?.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
          </Select>
          <Select label="Project" value={filters.project_id} onChange={(e) => setFilters({ ...filters, project_id: e.target.value })}>
            <option value="">All</option>
            {options?.projects?.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
          </Select>
          <Select label="Status" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <option value="">All</option>
            <option value="NOT_STARTED">NOT_STARTED</option>
            <option value="IN_PROCESS">IN_PROCESS</option>
            <option value="ACQUIRED">ACQUIRED</option>
          </Select>
          <Select label="Stage" value={filters.stage} onChange={(e) => setFilters({ ...filters, stage: e.target.value })}>
            <option value="">All</option>
            {options?.stages?.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
          </Select>
          <Select label="Risk" value={filters.risk_level} onChange={(e) => setFilters({ ...filters, risk_level: e.target.value })}>
            <option value="">All</option>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
          </Select>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
          <Select label="Colour" value={colorMode} onChange={(e) => setColorMode(e.target.value)}>
            <option value="risk">Risk</option>
            <option value="status">Acquisition status</option>
            <option value="stage">Workflow stage</option>
          </Select>
          <Badge tone="green">LOW</Badge>
          <Badge tone="amber">MEDIUM</Badge>
          <Badge tone="red">HIGH</Badge>
          <span className="text-slate-500 font-medium">{features.length} geometries</span>

          <div className="flex items-center gap-1 rounded-lg border border-line bg-sand/50 p-0.5 ml-auto" role="group" aria-label="GIS view mode">
            <button
              type="button"
              onClick={() => setViewMode("both")}
              aria-pressed={viewMode === "both"}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition cursor-pointer focus-visible:outline-2 focus-visible:outline-teal-700 ${
                viewMode === "both" ? "bg-white text-navy shadow-xs" : "text-slate-600 hover:text-navy"
              }`}
            >
              Map & Table
            </button>
            <button
              type="button"
              onClick={() => setViewMode("map")}
              aria-pressed={viewMode === "map"}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition cursor-pointer focus-visible:outline-2 focus-visible:outline-teal-700 ${
                viewMode === "map" ? "bg-white text-navy shadow-xs" : "text-slate-600 hover:text-navy"
              }`}
            >
              Map only
            </button>
            <button
              type="button"
              onClick={() => setViewMode("table")}
              aria-pressed={viewMode === "table"}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition cursor-pointer focus-visible:outline-2 focus-visible:outline-teal-700 ${
                viewMode === "table" ? "bg-white text-navy shadow-xs" : "text-slate-600 hover:text-navy"
              }`}
            >
              Table only
            </button>
          </div>

          <Button variant="ghost" onClick={handleRetry} disabled={loading} title="Reload parcel spatial data" aria-label="Reload parcel spatial data">
            Refresh
          </Button>
        </div>
      </Card>

      {loading ? (
        <Skeleton className="h-[32rem]" />
      ) : error ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : features.length === 0 ? (
        <EmptyState
          title="No parcel geometries found"
          body="No parcels match the current filter criteria, or geometries have not yet been assigned to these parcels. Try resetting or adjusting filters."
          action={
            <div className="flex justify-center gap-2">
              <Button variant="ghost" onClick={handleResetFilters}>
                Reset filters
              </Button>
              <Button variant="ghost" onClick={handleRetry}>
                Retry query
              </Button>
            </div>
          }
        />
      ) : (
        <div className="space-y-4">
          {viewMode !== "table" ? (
            <ParcelMap
              features={features}
              colorMode={colorMode}
              height="32rem"
              onSwitchToTable={() => setViewMode("table")}
              onSelect={(p) => {
                if (p.case_id) navigate(`/acquisitions/${p.case_id}`);
                else if (p.id) navigate(`/parcels/${p.id}`);
              }}
            />
          ) : null}

          {viewMode !== "map" ? (
            <Card>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 className="text-base font-semibold text-ink">Parcel spatial registry</h2>
                  <p className="text-xs text-slate-600">
                    Tabular fallback view of {tableRows.length} spatial parcels loaded from GIS. Click any ULPIN to open case/parcel details.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone="navy">{tableRows.length} parcels</Badge>
                </div>
              </div>
              <DataTable columns={columns} rows={tableRows} keyField="id" />
            </Card>
          ) : null}
        </div>
      )}
    </div>
  );
}
