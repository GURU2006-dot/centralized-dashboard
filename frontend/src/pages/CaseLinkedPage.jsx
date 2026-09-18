import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listAcquisitions } from "../api/acquisitions";
import { createCompensation, getCompensation, updateCompensation } from "../api/compensation";
import { createPossession, getPossession, updatePossession } from "../api/possession";
import { createRehab, createResettlement, getRehab, getResettlement, updateRehab, updateResettlement } from "../api/rr";
import { Button, Card, DataTable, EmptyState, Input, PageHeader, Select, Skeleton, StatusBadge, Textarea } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { errorMessage, inr } from "../lib/format";
import { canTransition } from "../lib/roles";

export function CompensationPage() {
  return (
    <CaseWorkbench
      title="Compensation"
      crumbs="Compensation & R&R"
      subtitle="Paid amount cannot exceed assessed amount. Workflow gates stay on the server."
      load={getCompensation}
      create={(id, form) => createCompensation({ acquisition_case_id: id, assessed_amount_inr: Number(form.assessed_amount_inr || 0), paid_amount_inr: Number(form.paid_amount_inr || 0) })}
      update={(id, form) => updateCompensation(id, { assessed_amount_inr: Number(form.assessed_amount_inr), paid_amount_inr: Number(form.paid_amount_inr) })}
      render={(rec) => rec ? `${inr(rec.assessed_amount_inr)} assessed · ${inr(rec.paid_amount_inr)} paid · ${inr(rec.remaining_amount_inr)} remaining` : "No compensation record"}
      fields={(form, setForm) => (
        <>
          <Input label="Assessed (₹)" type="number" min="0" value={form.assessed_amount_inr || ""} onChange={(e) => setForm({ ...form, assessed_amount_inr: e.target.value })} />
          <Input label="Paid (₹)" type="number" min="0" value={form.paid_amount_inr || ""} onChange={(e) => setForm({ ...form, paid_amount_inr: e.target.value })} />
        </>
      )}
    />
  );
}

export function PossessionPage() {
  return (
    <CaseWorkbench
      title="Possession"
      crumbs="Compensation & R&R"
      load={getPossession}
      create={(id, form) => createPossession({ acquisition_case_id: id, status: form.status || "NOT_TAKEN", area_ha: form.area_ha ? Number(form.area_ha) : null, remarks: form.remarks })}
      update={(id, form) => updatePossession(id, { status: form.status, area_ha: form.area_ha ? Number(form.area_ha) : undefined, remarks: form.remarks })}
      render={(rec) => rec ? `${rec.status}${rec.area_ha != null ? ` · ${rec.area_ha} ha` : ""}` : "No possession record"}
      fields={(form, setForm) => (
        <>
          <Select label="Status" value={form.status || "NOT_TAKEN"} onChange={(e) => setForm({ ...form, status: e.target.value })}>
            <option>NOT_TAKEN</option>
            <option>PARTIAL</option>
            <option>TAKEN</option>
          </Select>
          <Input label="Area (ha)" type="number" min="0" step="0.01" value={form.area_ha || ""} onChange={(e) => setForm({ ...form, area_ha: e.target.value })} />
          <Textarea label="Remarks" value={form.remarks || ""} onChange={(e) => setForm({ ...form, remarks: e.target.value })} />
        </>
      )}
    />
  );
}

export function RehabilitationPage() {
  return <RRList title="Rehabilitation" kind="rehab" />;
}

export function ResettlementPage() {
  return <RRList title="Resettlement" kind="reset" />;
}

function RRList({ title, kind }) {
  const toast = useToast();
  const { role } = useAuth();
  const [cases, setCases] = useState([]);
  const [selected, setSelected] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);
  const writer = canTransition(role);

  useEffect(() => {
    listAcquisitions({ page_size: 40 }).then((r) => setCases(r.data || [])).catch((e) => toast.error(errorMessage(e)));
  }, [toast]);

  useEffect(() => {
    if (!selected) {
      setRows([]);
      return;
    }
    setLoading(true);
    const fn = kind === "rehab" ? getRehab : getResettlement;
    fn(selected)
      .then((r) => setRows(r.data || []))
      .catch((e) => toast.error(errorMessage(e)))
      .finally(() => setLoading(false));
  }, [selected, kind, toast]);

  async function add() {
    if (adding) return;
    setAdding(true);
    try {
      if (kind === "rehab") {
        const family_id = window.prompt("Family UUID for rehabilitation record");
        if (!family_id) return;
        await createRehab({ family_id, status: "NOT_STARTED" });
      } else {
        const family_id = window.prompt("Family UUID for resettlement record");
        if (!family_id) return;
        await createResettlement({ family_id, status: "NOT_ALLOTTED" });
      }
      const fn = kind === "rehab" ? getRehab : getResettlement;
      setRows((await fn(selected)).data || []);
      toast.success("Record saved");
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setAdding(false);
    }
  }

  async function patchStatus(row, status) {
    try {
      if (kind === "rehab") await updateRehab(row.id, { status });
      else await updateResettlement(row.id, { status });
      const fn = kind === "rehab" ? getRehab : getResettlement;
      setRows((await fn(selected)).data || []);
    } catch (e) {
      toast.error(errorMessage(e));
    }
  }

  return (
    <div>
      <PageHeader crumbs="Compensation & R&R" title={title} subtitle="Records are loaded by acquisition case from the R&R APIs." />
      <Card className="mb-4">
        <Select label="Acquisition case" value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">Select a case</option>
          {cases.map((c) => <option key={c.id} value={c.id}>{c.case_number} · {c.ulpin}</option>)}
        </Select>
        {writer && selected ? <Button className="mt-3" variant="ghost" loading={adding} onClick={add}>Add record</Button> : null}
      </Card>
      <DataTable
        loading={loading}
        rows={rows}
        empty={<EmptyState title="No records found" body={selected ? "No records have been filed for this acquisition case." : "Select an acquisition case above to view records."} />}
        columns={[
          { key: "id", header: "ID", render: (r) => <span className="font-mono text-xs">{r.id.slice(0, 8)}</span> },
          { key: "family_id", header: "Family" },
          { key: "status", header: "Status", render: (r) => (
            writer ? (
              <select
                aria-label={`Update ${kind} status for record ${r.id.slice(0, 8)}`}
                className="rounded border border-line px-2 py-1 focus-visible:outline-2 focus-visible:outline-teal-700"
                value={r.status}
                onChange={(e) => patchStatus(r, e.target.value)}
              >
                {kind === "rehab" ? ["NOT_STARTED", "IN_PROGRESS", "COMPLETED"].map((s) => <option key={s}>{s}</option>) : ["NOT_ALLOTTED", "ALLOTTED", "POSSESSED"].map((s) => <option key={s}>{s}</option>)}
              </select>
            ) : <StatusBadge value={r.status} />
          ) },
          kind === "rehab"
            ? { key: "package_type", header: "Package" }
            : { key: "site_name", header: "Site" },
        ]}
      />
    </div>
  );
}

function CaseWorkbench({ title, crumbs, subtitle, load, create, update, render, fields }) {
  const toast = useToast();
  const { role } = useAuth();
  const writer = canTransition(role);
  const [cases, setCases] = useState([]);
  const [selected, setSelected] = useState("");
  const [rec, setRec] = useState(null);
  const [missing, setMissing] = useState(false);
  const [form, setForm] = useState({});
  const [loadingRecord, setLoadingRecord] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listAcquisitions({ page_size: 40 }).then((r) => setCases(r.data || [])).catch((e) => toast.error(errorMessage(e)));
  }, [toast]);

  useEffect(() => {
    if (!selected) {
      setRec(null);
      setForm({});
      return;
    }
    setLoadingRecord(true);
    setMissing(false);
    load(selected)
      .then((r) => {
        setRec(r.data);
        setForm(r.data || {});
      })
      .catch((e) => {
        if (e?.response?.status === 404 || e.status === 404) {
          setRec(null);
          setMissing(true);
          setForm({});
        } else {
          toast.error(errorMessage(e));
        }
      })
      .finally(() => setLoadingRecord(false));
  }, [selected, load, toast]);

  async function save() {
    if (saving) return;
    setSaving(true);
    try {
      const res = missing ? await create(selected, form) : await update(selected, form);
      setRec(res.data);
      setMissing(false);
      toast.success("Saved");
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader crumbs={crumbs || "Compensation & R&R"} title={title} subtitle={subtitle} />
      <Card className="mb-4">
        <Select label="Acquisition case" value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">Select a case</option>
          {cases.map((c) => (
            <option key={c.id} value={c.id}>{c.case_number} · {c.project_code} · {c.ulpin}</option>
          ))}
        </Select>
        {selected ? <Link className="mt-2 inline-block text-sm text-navy" to={`/acquisitions/${selected}`}>Open case</Link> : null}
      </Card>
      {selected ? (
        <Card>
          {loadingRecord ? (
            <Skeleton className="h-24" />
          ) : (
            <>
              <p className="text-sm text-slate-600">{render(rec)}</p>
              {writer ? (
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  {fields(form, setForm)}
                  <div className="md:col-span-2">
                    <Button onClick={save} loading={saving}>{missing ? "Create record" : "Update"}</Button>
                  </div>
                </div>
              ) : null}
            </>
          )}
        </Card>
      ) : null}
    </div>
  );
}
