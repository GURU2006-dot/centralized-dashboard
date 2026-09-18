import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getFilters } from "../api/dashboard";
import { createProject, listProjects } from "../api/projects";
import {
  Button,
  Card,
  DataTable,
  EmptyState,
  ErrorState,
  Input,
  Modal,
  PageHeader,
  Pagination,
  Select,
  StatusBadge,
} from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { errorMessage, ha } from "../lib/format";
import { canWriteProjects } from "../lib/roles";

export default function ProjectsPage() {
  const { role } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [params, setParams] = useState({ page: 1, page_size: 10, search: "", state: "", status: "" });
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [options, setOptions] = useState(null);
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [form, setForm] = useState({ code: "", name: "", purpose: "", state_code: "TG", district_code: "TG-RR" });

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
    listProjects(q)
      .then((r) => {
        if (!alive) return;
        setRows(r.data);
        setTotal(r.meta?.total || 0);
        setError(null);
      })
      .catch((e) => {
        if (!alive) return;
        setError(e?.response?.data?.detail || e.message || "Failed to load projects.");
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

  async function onCreate(e) {
    e.preventDefault();
    if (creating) return;
    setCreating(true);
    try {
      const res = await createProject(form);
      toast.success("Project created");
      setOpen(false);
      navigate(`/projects/${res.data.id}`);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div>
      <PageHeader
        crumbs="Land & Projects"
        title="Projects"
        actions={
          canWriteProjects(role) ? (
            <Button onClick={() => setOpen(true)}>New project</Button>
          ) : null
        }
      />
      <Card className="mb-4">
        <div className="grid gap-3 md:grid-cols-4">
          <Input label="Search" value={params.search} onChange={(e) => setParams({ ...params, page: 1, search: e.target.value })} />
          <Select label="State" value={params.state} onChange={(e) => setParams({ ...params, page: 1, state: e.target.value })}>
            <option value="">All</option>
            {options?.states?.map((s) => (
              <option key={s.code} value={s.code}>{s.name}</option>
            ))}
          </Select>
          <Select label="Status" value={params.status} onChange={(e) => setParams({ ...params, page: 1, status: e.target.value })}>
            <option value="">All</option>
            {options?.statuses?.map((s) => (
              <option key={s.code} value={s.code}>{s.name}</option>
            ))}
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
                title="No projects found"
                body="No projects match your search or filter criteria. Try adjusting filters or create a new project."
              />
            }
            columns={[
              { key: "code", header: "Code", render: (r) => <Link className="font-semibold text-navy hover:underline" to={`/projects/${r.id}`}>{r.code}</Link> },
              { key: "name", header: "Name" },
              { key: "state_code", header: "State" },
              { key: "district_code", header: "District" },
              { key: "area_ha", header: "Area", render: (r) => ha(r.area_ha) },
              { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
              { key: "current_stage", header: "Stage", render: (r) => <StatusBadge value={r.current_stage} /> },
            ]}
          />
          <Pagination page={params.page} pageSize={params.page_size} total={total} onPage={(p) => setParams({ ...params, page: p })} />
        </>
      )}
      <Modal open={open} title="Create project" onClose={() => setOpen(false)} footer={<Button type="submit" form="create-project" loading={creating}>Save</Button>}>
        <form id="create-project" className="space-y-3" onSubmit={onCreate}>
          <Input label="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} required />
          <Input label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <Input label="Purpose" value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })} required />
          <Input label="State code" value={form.state_code} onChange={(e) => setForm({ ...form, state_code: e.target.value })} required />
          <Input label="District code" value={form.district_code} onChange={(e) => setForm({ ...form, district_code: e.target.value })} />
        </form>
      </Modal>
    </div>
  );
}
