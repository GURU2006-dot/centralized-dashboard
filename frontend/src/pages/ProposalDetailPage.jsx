import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  approveProposal,
  getProposal,
  rejectProposal,
  submitProposal,
  updateProposal,
  verifyProposal,
} from "../api/proposals";
import { Button, Card, ErrorState, Modal, PageHeader, Skeleton, StatusBadge, Textarea } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { errorMessage, inr } from "../lib/format";
import { canApprove, canWriteProposals } from "../lib/roles";
import { validateRejectRemarks } from "../lib/validation";

export default function ProposalDetailPage() {
  const { id } = useParams();
  const { role } = useAuth();
  const toast = useToast();
  const [row, setRow] = useState(null);
  const [remarks, setRemarks] = useState("");
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectError, setRejectError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let alive = true;
    getProposal(id)
      .then((r) => {
        if (!alive) return;
        setRow(r.data);
        setError(null);
      })
      .catch((e) => {
        if (!alive) return;
        const msg =
          e?.response?.status === 404
            ? "Proposal not found. The specified proposal does not exist."
            : e?.response?.data?.detail || e.message || "Failed to load proposal details.";
        setError(msg);
        toast.error(errorMessage(e));
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [id, reloadKey, toast]);

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  };

  async function run(fn, ok) {
    setBusy(true);
    try {
      const res = await fn();
      setRow(res.data);
      toast.success(ok);
      return true;
    } catch (e) {
      toast.error(errorMessage(e));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirmReject() {
    const err = validateRejectRemarks(remarks);
    if (err) {
      setRejectError(err);
      return;
    }
    const ok = await run(() => rejectProposal(id, remarks.trim()), "Rejected");
    if (ok) {
      setRejectOpen(false);
      setRejectError("");
    }
  }

  if (error && !row) return <ErrorState message={error} onRetry={handleRetry} />;
  if (loading && !row) return <Skeleton className="h-64" />;
  if (!row) return <ErrorState message="Proposal not found" onRetry={handleRetry} />;

  return (
    <div>
      <PageHeader
        crumbs="Acquisition / Proposals"
        title={row.proposal_number}
        subtitle={`Project ${row.project_code}`}
        actions={<StatusBadge value={row.status} />}
      />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <dt className="text-slate-500">Purpose</dt><dd className="col-span-1 lg:col-span-1">{row.purpose}</dd>
            <dt className="text-slate-500">Required area</dt><dd>{row.required_area_ha} ha</dd>
            <dt className="text-slate-500">Estimated compensation</dt><dd>{inr(row.estimated_compensation_inr)}</dd>
            <dt className="text-slate-500">Affected families</dt><dd>{row.affected_families_count ?? "—"}</dd>
            <dt className="text-slate-500">Parcels</dt>
            <dd>{(row.parcel_ids || []).length} linked</dd>
          </dl>
          {row.status === "DRAFT" && canWriteProposals(role) ? (
            <div className="mt-4">
              <Textarea label="Edit purpose" value={row.purpose} onChange={(e) => setRow({ ...row, purpose: e.target.value })} />
              <Button className="mt-2" variant="ghost" loading={busy} onClick={() => run(() => updateProposal(id, { purpose: row.purpose }), "Draft updated")}>
                Save draft
              </Button>
            </div>
          ) : null}
        </Card>
        <Card>
          <h2 className="font-serif text-lg text-ink">Actions</h2>
          <p className="mt-1 text-xs text-slate-500">Approval creates acquisition cases for parcels that do not already have one. There is no second case-level approve.</p>
          <Textarea className="mt-3" label="Remarks" value={remarks} onChange={(e) => setRemarks(e.target.value)} />
          <div className="mt-3 flex flex-col gap-2">
            {row.status === "DRAFT" && canWriteProposals(role) ? (
              <Button loading={busy} disabled={busy} onClick={() => run(() => submitProposal(id, remarks), "Submitted")}>Submit</Button>
            ) : null}
            {row.status === "SUBMITTED" && canWriteProposals(role) ? (
              <Button loading={busy} disabled={busy} onClick={() => run(() => verifyProposal(id, remarks), "Moved to verification")}>Verify</Button>
            ) : null}
            {row.status === "UNDER_VERIFICATION" && canApprove(role) ? (
              <>
                <Button loading={busy} disabled={busy} onClick={() => run(() => approveProposal(id, remarks), "Approved — cases created where needed")}>Approve</Button>
                <Button variant="danger" disabled={busy} onClick={() => { setRejectError(""); setRejectOpen(true); }}>Reject</Button>
              </>
            ) : null}
          </div>
          {row.cases_created != null ? (
            <p className="mt-3 text-sm text-teal-800">Cases created: {row.cases_created}. Already present: {row.cases_already_present}.</p>
          ) : null}
          <Link to="/acquisitions" className="mt-4 inline-block text-sm font-semibold text-navy">View acquisition cases</Link>
        </Card>
      </div>
      <Modal
        open={rejectOpen}
        title="Reject proposal"
        onClose={() => {
          setRejectOpen(false);
          setRejectError("");
        }}
        footer={
          <Button
            variant="danger"
            loading={busy}
            disabled={busy}
            onClick={handleConfirmReject}
          >
            Confirm reject
          </Button>
        }
      >
        <p className="text-sm text-slate-600">Rejection remarks are required by the API.</p>
        <Textarea
          className="mt-3"
          label="Remarks *"
          value={remarks}
          error={rejectError}
          onChange={(e) => {
            setRemarks(e.target.value);
            if (rejectError && e.target.value.trim()) {
              setRejectError("");
            }
          }}
        />
      </Modal>
    </div>
  );
}
