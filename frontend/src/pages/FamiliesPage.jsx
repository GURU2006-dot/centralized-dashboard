import { useEffect, useState } from "react";
import { createFamily, listFamilies } from "../api/families";
import { listProjects } from "../api/projects";
import { Button, Card, DataTable, EmptyState, ErrorState, Input, Modal, PageHeader, Pagination, Select, StatusBadge } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { errorMessage } from "../lib/format";
import { canTransition } from "../lib/roles";

export default function FamiliesPage() {
  const { role } = useAuth();
  const toast = useToast();
  const [params, setParams] = useState({ page: 1, page_size: 15, project_id: "" });
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [projects, setProjects] = useState([]);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [form, setForm] = useState({ project_id: "", family_head_name: "", member_count: 1, is_displaced: false });

  function load() {
    setLoading(true);
    setError(null);
    const q = { ...params };
    if (!q.project_id) delete q.project_id;
    return listFamilies(q)
      .then((r) => {
        setRows(r.data || []);
        setTotal(r.meta?.total || 0);
        setError(null);
      })
      .catch((e) => {
        setError(e?.response?.data?.detail || e.message || "Failed to load families.");
        toast.error(errorMessage(e));
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    listProjects({ page_size: 50 }).then((r) => setProjects(r.data || [])).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [params, reloadKey]);

  const handleRetry = () => {
    setError(null);
    setReloadKey((k) => k + 1);
  };

  async function onCreate(e) {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    try {
      await createFamily({ ...form, member_count: Number(form.member_count) });
      toast.success("Family recorded");
      setOpen(false);
      load();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader
        crumbs="Compensation & R&R"
        title="Affected families"
        subtitle="Contact details are not returned by the API and are not displayed."
        actions={canTransition(role) ? <Button onClick={() => setOpen(true)}>Add family</Button> : null}
      />
      <Card className="mb-4">
        <Select label="Project" value={params.project_id} onChange={(e) => setParams({ ...params, page: 1, project_id: e.target.value })}>
          <option value="">All</option>
          {projects.map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
        </Select>
      </Card>
      {error ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : (
        <>
          <DataTable
            loading={loading}
            rows={rows}
            empty={<EmptyState title="No families found" body="No affected families match the selected project filter." />}
            columns={[
              { key: "family_head_name", header: "Head of family" },
              { key: "member_count", header: "Members" },
              { key: "is_displaced", header: "Displaced", render: (r) => (r.is_displaced ? "Yes" : "No") },
              { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
            ]}
          />
          <Pagination page={params.page} pageSize={params.page_size} total={total} onPage={(p) => setParams({ ...params, page: p })} />
        </>
      )}
      <Modal open={open} title="Add family" onClose={() => setOpen(false)} footer={<Button type="submit" form="fam" loading={saving}>Save</Button>}>
        <form id="fam" className="space-y-3" onSubmit={onCreate}>
          <Select label="Project" value={form.project_id} onChange={(e) => setForm({ ...form, project_id: e.target.value })} required>
            <option value="">Select</option>
            {projects.map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
          </Select>
          <Input label="Head of family" value={form.family_head_name} onChange={(e) => setForm({ ...form, family_head_name: e.target.value })} required />
          <Input label="Members" type="number" min="1" value={form.member_count} onChange={(e) => setForm({ ...form, member_count: e.target.value })} />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_displaced} onChange={(e) => setForm({ ...form, is_displaced: e.target.checked })} />
            Displaced
          </label>
        </form>
      </Modal>
    </div>
  );
}
