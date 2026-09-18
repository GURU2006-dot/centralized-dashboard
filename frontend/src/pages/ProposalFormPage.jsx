import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listParcels } from "../api/parcels";
import { listProjects } from "../api/projects";
import { createProposal } from "../api/proposals";
import { Button, Card, ErrorState, Input, PageHeader, Select, Skeleton, Textarea } from "../components/ui";
import { useToast } from "../context/ToastContext";
import { errorMessage } from "../lib/format";
import { validateProposalForm } from "../lib/validation";

export default function ProposalFormPage() {
  const toast = useToast();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [parcels, setParcels] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [projectsError, setProjectsError] = useState(null);
  const [loadingParcels, setLoadingParcels] = useState(false);
  const [parcelsError, setParcelsError] = useState(null);
  const [reloadProjectsKey, setReloadProjectsKey] = useState(0);
  const [errors, setErrors] = useState({});
  const [form, setForm] = useState({
    project_id: "",
    parcel_ids: [],
    required_area_ha: "",
    purpose: "",
    estimated_compensation_inr: "",
    affected_families_count: "",
  });
  const [saving, setSaving] = useState(false);

  const projectRef = useRef(null);
  const purposeRef = useRef(null);
  const areaRef = useRef(null);
  const parcelsContainerRef = useRef(null);

  function handleRetryProjects() {
    setLoadingProjects(true);
    setProjectsError(null);
    setReloadProjectsKey((k) => k + 1);
  }

  useEffect(() => {
    let active = true;
    listProjects({ page_size: 50 })
      .then((r) => {
        if (!active) return;
        setProjects(r.data || []);
      })
      .catch((e) => {
        if (!active) return;
        const msg = errorMessage(e);
        setProjectsError(msg);
        toast.error(msg);
      })
      .finally(() => {
        if (active) setLoadingProjects(false);
      });
    return () => {
      active = false;
    };
  }, [reloadProjectsKey, toast]);

  useEffect(() => {
    if (!form.project_id) {
      setParcels([]);
      setParcelsError(null);
      setLoadingParcels(false);
      return;
    }
    let active = true;
    setLoadingParcels(true);
    setParcelsError(null);
    listParcels({ project_id: form.project_id, page_size: 50 })
      .then((r) => {
        if (!active) return;
        setParcels(r.data || []);
      })
      .catch((e) => {
        if (!active) return;
        setParcels([]);
        setParcelsError(errorMessage(e));
      })
      .finally(() => {
        if (active) setLoadingParcels(false);
      });
    return () => {
      active = false;
    };
  }, [form.project_id]);

  function toggleParcel(id) {
    setForm((f) => {
      const nextIds = f.parcel_ids.includes(id)
        ? f.parcel_ids.filter((x) => x !== id)
        : [...f.parcel_ids, id];
      return { ...f, parcel_ids: nextIds };
    });
    if (errors.parcel_ids) {
      setErrors((prev) => ({ ...prev, parcel_ids: undefined }));
    }
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (saving) return;

    const validationErrors = validateProposalForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      if (validationErrors.project_id) {
        projectRef.current?.focus();
      } else if (validationErrors.purpose) {
        purposeRef.current?.focus();
      } else if (validationErrors.required_area_ha) {
        areaRef.current?.focus();
      } else if (validationErrors.parcel_ids) {
        parcelsContainerRef.current?.focus();
        parcelsContainerRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
      return;
    }

    setSaving(true);
    try {
      const body = {
        project_id: form.project_id,
        parcel_ids: form.parcel_ids,
        required_area_ha: Number(form.required_area_ha),
        purpose: form.purpose.trim(),
        estimated_compensation_inr: form.estimated_compensation_inr ? Number(form.estimated_compensation_inr) : null,
        affected_families_count: form.affected_families_count ? Number(form.affected_families_count) : null,
      };
      const res = await createProposal(body);
      toast.success("Draft proposal saved");
      navigate(`/proposals/${res.data.id}`);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader crumbs="Acquisition / Proposals" title="New proposal" />
      <Card>
        {projectsError ? (
          <div className="mb-4">
            <ErrorState message={projectsError} onRetry={handleRetryProjects} />
          </div>
        ) : null}
        <form className="space-y-4" onSubmit={onSubmit} noValidate>
          <Select
            ref={projectRef}
            label={loadingProjects ? "Project * (loading...)" : "Project *"}
            value={form.project_id}
            error={errors.project_id}
            onChange={(e) => {
              setForm({ ...form, project_id: e.target.value, parcel_ids: [] });
              if (errors.project_id) setErrors((prev) => ({ ...prev, project_id: undefined }));
              if (errors.parcel_ids) setErrors((prev) => ({ ...prev, parcel_ids: undefined }));
            }}
            disabled={loadingProjects}
          >
            <option value="">Select project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.code} — {p.name}</option>
            ))}
          </Select>

          <Textarea
            ref={purposeRef}
            label="Purpose *"
            value={form.purpose}
            error={errors.purpose}
            onChange={(e) => {
              setForm({ ...form, purpose: e.target.value });
              if (errors.purpose) setErrors((prev) => ({ ...prev, purpose: undefined }));
            }}
          />

          <div className="grid gap-3 md:grid-cols-3">
            <Input
              ref={areaRef}
              label="Required area (ha) *"
              type="number"
              step="0.01"
              min="0"
              value={form.required_area_ha}
              error={errors.required_area_ha}
              onChange={(e) => {
                setForm({ ...form, required_area_ha: e.target.value });
                if (errors.required_area_ha) setErrors((prev) => ({ ...prev, required_area_ha: undefined }));
              }}
            />
            <Input
              label="Estimated compensation (₹)"
              type="number"
              min="0"
              value={form.estimated_compensation_inr}
              error={errors.estimated_compensation_inr}
              onChange={(e) => {
                setForm({ ...form, estimated_compensation_inr: e.target.value });
                if (errors.estimated_compensation_inr) setErrors((prev) => ({ ...prev, estimated_compensation_inr: undefined }));
              }}
            />
            <Input
              label="Affected families"
              type="number"
              min="0"
              value={form.affected_families_count}
              error={errors.affected_families_count}
              onChange={(e) => {
                setForm({ ...form, affected_families_count: e.target.value });
                if (errors.affected_families_count) setErrors((prev) => ({ ...prev, affected_families_count: undefined }));
              }}
            />
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Parcels *</p>
              {form.parcel_ids.length > 0 ? (
                <span className="text-xs font-medium text-teal-800">{form.parcel_ids.length} selected</span>
              ) : null}
            </div>
            <div
              ref={parcelsContainerRef}
              tabIndex={0}
              role="group"
              aria-label="Parcel selection"
              aria-invalid={errors.parcel_ids ? "true" : undefined}
              aria-describedby={errors.parcel_ids ? "parcel-selection-error" : undefined}
              className={`max-h-64 overflow-auto rounded-xl border p-1 outline-none focus-visible:ring-2 focus-visible:ring-teal-700 ${
                errors.parcel_ids ? "border-red-400 bg-red-50/20 ring-1 ring-red-400" : "border-line"
              }`}
            >
              {loadingParcels ? (
                <div className="p-3"><Skeleton className="h-12" /></div>
              ) : parcelsError ? (
                <p className="p-3 text-sm text-red-600">{parcelsError}</p>
              ) : !form.project_id ? (
                <p className="p-3 text-sm text-slate-500">Select a project first.</p>
              ) : parcels.length === 0 ? (
                <p className="p-3 text-sm text-slate-500">No parcels found for this project.</p>
              ) : (
                parcels.map((p) => (
                  <label key={p.id} className="flex min-h-11 items-center gap-3 border-b border-line px-3 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.parcel_ids.includes(p.id)}
                      onChange={() => toggleParcel(p.id)}
                      aria-label={`Parcel ${p.ulpin}, Khasra ${p.khasra_number || "—"}, Village ${p.village || "—"}`}
                      className="focus-visible:outline-2 focus-visible:outline-teal-700"
                    />
                    <span className="font-medium">{p.ulpin}</span>
                    <span className="text-slate-500">{p.khasra_number} · {p.village}</span>
                  </label>
                ))
              )}
            </div>
            {errors.parcel_ids ? (
              <span id="parcel-selection-error" role="alert" className="mt-1 block text-xs text-red-700">{errors.parcel_ids}</span>
            ) : null}
          </div>

          <Button type="submit" loading={saving} disabled={saving}>
            {saving ? "Saving draft…" : "Save draft"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
