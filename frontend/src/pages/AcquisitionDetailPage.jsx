import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getAcquisition, getTimeline, transitionCase } from "../api/acquisitions";
import { getCompensation } from "../api/compensation";
import { getPredictionHistory, predictCase } from "../api/ml";
import { getPossession } from "../api/possession";
import { getRehab, getResettlement } from "../api/rr";
import { Button, Card, ErrorState, PageHeader, Skeleton, StatusBadge, Textarea, Timeline } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { dt, errorMessage, ha, inr, num } from "../lib/format";
import { STAGES, canPredict, canTransition, nextStage } from "../lib/roles";

export default function AcquisitionDetailPage() {
  const { id } = useParams();
  const { role } = useAuth();
  const toast = useToast();
  const [row, setRow] = useState(null);
  const [timeline, setTimeline] = useState({ stages: STAGES, events: [] });
  const [comp, setComp] = useState(null);
  const [poss, setPoss] = useState(null);
  const [rehab, setRehab] = useState([]);
  const [reset, setReset] = useState([]);
  const [remarks, setRemarks] = useState("");
  const [busy, setBusy] = useState(false);
  const [pred, setPred] = useState(null);
  const [history, setHistory] = useState([]);
  const [predicting, setPredicting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  function load() {
    setLoading(true);
    setError(null);
    return Promise.all([
      getAcquisition(id),
      getTimeline(id),
      getCompensation(id).catch(() => null),
      getPossession(id).catch(() => null),
      getRehab(id).catch(() => ({ data: [] })),
      getResettlement(id).catch(() => ({ data: [] })),
    ])
      .then(([a, t, c, p, rh, rs]) => {
        setRow(a.data);
        setTimeline(t.data);
        setComp(c?.data || a.data.compensation);
        setPoss(p?.data || a.data.possession);
        setRehab(rh.data || []);
        setReset(rs.data || []);
        setError(null);
      })
      .catch((e) => {
        const msg =
          e?.response?.status === 404
            ? "Acquisition case not found. The specified case does not exist."
            : e?.response?.data?.detail || e.message || "Failed to load acquisition case details.";
        setError(msg);
        toast.error(errorMessage(e));
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, [id, reloadKey]);

  const handleRetry = () => {
    setError(null);
    setReloadKey((k) => k + 1);
  };

  async function onTransition() {
    if (busy) return;
    const target = nextStage(row.current_stage);
    if (!target) return;
    setBusy(true);
    try {
      const res = await transitionCase(id, target, remarks);
      setRow(res.data);
      toast.success(`Moved to ${target}`);
      const t = await getTimeline(id);
      setTimeline(t.data);
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  if (error && !row) return <ErrorState message={error} onRetry={handleRetry} />;
  if (loading && !row) return <Skeleton className="h-64" />;
  if (!row) return <ErrorState message="Acquisition case not found" onRetry={handleRetry} />;
  const nxt = nextStage(row.current_stage);

  return (
    <div>
      <PageHeader
        crumbs="Acquisition / Cases"
        title={row.case_number}
        subtitle={`${row.project_code} · ${row.ulpin}`}
      />
      <div className="mb-4 flex flex-wrap gap-2">
        <StatusBadge value={row.current_stage} />
        <StatusBadge value={row.status} />
        <StatusBadge value={pred?.risk_category || row.risk_level} />
      </div>
      <Card className="mb-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-serif text-lg text-ink">Delay risk</h2>
            <p className="mt-1 max-w-2xl text-xs text-slate-500">
              Risk predictions are decision-support indicators and must not automatically determine land acquisition
              approvals, compensation, possession, or other statutory decisions. Prototype trained on synthetic data.
            </p>
          </div>
          {canPredict(role) ? (
            <Button
              loading={predicting}
              disabled={predicting}
              onClick={async () => {
                if (predicting) return;
                setPredicting(true);
                try {
                  const res = await predictCase(id);
                  setPred(res.data);
                  setHistory((h) => [res.data, ...h]);
                  toast.success(`Delay risk score ${res.data.risk_score}/100 — ${res.data.risk_category}`);
                } catch (e) {
                  toast.error(errorMessage(e));
                } finally {
                  setPredicting(false);
                }
              }}
            >
              Run prediction
            </Button>
          ) : null}
        </div>
        <div className="mt-4 flex flex-wrap items-end gap-8">
          <p className="font-serif text-5xl text-ink">{pred ? pred.risk_score : row.risk_score != null ? num(Number(row.risk_score) * 100, 1) : "—"} <span className="text-lg text-slate-500">/ 100</span></p>
          <div>
            <StatusBadge value={pred?.risk_category || row.risk_level} />
            <p className="mt-1 text-xs text-slate-500">{pred?.model_version || "seed score"} · {dt(pred?.predicted_at)}</p>
          </div>
        </div>
        <div className="mt-4">
          <h3 className="text-sm font-semibold">Risk indicators</h3>
          <p className="text-xs text-slate-500">Feature observations, not proven causes.</p>
          <ul className="mt-2 list-disc pl-5 text-sm">
            {(pred?.indicators || []).length ? pred.indicators.map((n) => <li key={n}>{n}</li>) : <li>Run a prediction to list indicators.</li>}
          </ul>
        </div>
        {history.length > 1 ? (
          <div className="mt-4 text-xs text-slate-600">
            <p className="font-semibold">Prediction history</p>
            {history.slice(0, 6).map((h) => (
              <p key={h.id}>{dt(h.predicted_at)} · {h.risk_score}/100 · {h.risk_category} · {h.model_version}</p>
            ))}
          </div>
        ) : null}
      </Card>
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="mb-3 font-serif text-lg text-ink">Workflow</h2>
          <Timeline stages={timeline.stages?.length ? timeline.stages : STAGES} current={row.current_stage} events={timeline.events || []} />
        </Card>
        <div className="space-y-4">
          <Card>
            <h2 className="font-serif text-lg text-ink">Transition</h2>
            <p className="mt-1 text-sm text-slate-600">Next permitted stage: <strong>{nxt || "none"}</strong>. The API rejects skipped stages.</p>
            {canTransition(role) && nxt ? (
              <>
                <Textarea className="mt-3" label="Remarks" value={remarks} onChange={(e) => setRemarks(e.target.value)} />
                <Button className="mt-3 w-full" loading={busy} onClick={onTransition}>Advance to {nxt}</Button>
              </>
            ) : (
              <p className="mt-3 text-sm text-slate-500">Your role cannot transition cases, or the case is complete.</p>
            )}
          </Card>
          <Card>
            <h2 className="font-serif text-lg text-ink">Linked</h2>
            <ul className="mt-2 space-y-1 text-sm">
              <li>Project <Link className="text-navy" to={`/projects/${row.project_id}`}>{row.project_code}</Link></li>
              <li>Parcel <Link className="text-navy" to={`/parcels/${row.parcel_id}`}>{row.ulpin}</Link></li>
              <li>Notified {ha(row.notified_area_ha)} · Acquired {ha(row.acquired_area_ha)}</li>
            </ul>
          </Card>
        </div>
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <Card>
          <h3 className="font-semibold">Compensation</h3>
          {comp ? (
            <p className="mt-2 text-sm">{inr(comp.assessed_amount_inr)} assessed · {inr(comp.paid_amount_inr)} paid · <StatusBadge value={comp.status} /></p>
          ) : <p className="mt-2 text-sm text-slate-500">No record</p>}
          <Link className="mt-2 inline-block text-sm text-navy" to="/compensation">Open compensation</Link>
        </Card>
        <Card>
          <h3 className="font-semibold">Possession</h3>
          {poss ? <p className="mt-2 text-sm"><StatusBadge value={poss.status} /> · {ha(poss.area_ha)}</p> : <p className="mt-2 text-sm text-slate-500">No record</p>}
        </Card>
        <Card>
          <h3 className="font-semibold">R&amp;R</h3>
          <p className="mt-2 text-sm">Rehab {rehab.length} · Resettlement {reset.length}</p>
        </Card>
      </div>
    </div>
  );
}
