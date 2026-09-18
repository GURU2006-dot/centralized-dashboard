import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getField, listField, submitField, updateField, uploadFieldPhoto } from "../api/fieldVerification";
import { getParcel } from "../api/parcels";
import { Button, Card, EmptyState, ErrorState, Input, PageHeader, Skeleton, StatusBadge, Textarea } from "../components/ui";
import { useToast } from "../context/ToastContext";
import { errorMessage } from "../lib/format";

export function FieldListPage() {
  const [rows, setRows] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    listField({ page_size: 50 })
      .then((r) => {
        if (!active) return;
        setRows(r.data || []);
      })
      .catch((e) => {
        if (!active) return;
        setError(errorMessage(e));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [reloadKey]);

  function handleRetry() {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  }

  return (
    <div>
      <PageHeader crumbs="Field Operations" title="Field verification" subtitle="Assigned records only for field officers. Designed for phone use." />
      {loading ? (
        <Skeleton className="h-40" />
      ) : error ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : rows && rows.length === 0 ? (
        <EmptyState title="No field verifications assigned" body="Assigned field verification tasks will appear here." />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {(rows || []).map((r) => (
            <Link key={r.id} to={`/field/${r.id}`} className="glass-card block rounded-2xl p-4">
              <div className="flex items-start justify-between gap-2">
                <p className="font-semibold text-ink">Verification</p>
                <StatusBadge value={r.status} />
              </div>
              <p className="mt-2 text-sm text-slate-600">Parcel {r.parcel_id?.slice(0, 8)}…</p>
              <p className="text-xs text-slate-500">GPS {r.gps_lat ?? "—"}, {r.gps_lng ?? "—"}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export function FieldDetailPage() {
  const { id } = useParams();
  const toast = useToast();
  const navigate = useNavigate();
  const [row, setRow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [parcel, setParcel] = useState(null);
  const [busy, setBusy] = useState(false);
  const [remarks, setRemarks] = useState("");

  useEffect(() => {
    let active = true;
    getField(id)
      .then(async (r) => {
        if (!active) return;
        setRow(r.data);
        setRemarks(r.data.remarks || "");
        if (r.data.parcel_id) {
          try {
            const pRes = await getParcel(r.data.parcel_id);
            if (active) setParcel(pRes.data);
          } catch {
            if (active) setParcel(null);
          }
        }
      })
      .catch((e) => {
        if (!active) return;
        const msg = errorMessage(e);
        setError(msg);
        toast.error(msg);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id, reloadKey, toast]);

  function handleRetry() {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  }

  async function save(patch) {
    if (busy) return;
    setBusy(true);
    try {
      const res = await updateField(id, patch);
      setRow(res.data);
      toast.success("Saved");
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  function captureGps() {
    if (!navigator.geolocation) {
      toast.error("Geolocation is not available in this browser");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        save({ gps_lat: pos.coords.latitude, gps_lng: pos.coords.longitude });
      },
      () => toast.error("Could not read GPS. Location was not invented."),
    );
  }

  async function onPhoto(e) {
    const file = e.target.files?.[0];
    if (!file || busy) return;
    setBusy(true);
    try {
      await uploadFieldPhoto(id, file);
      toast.success("Photo uploaded to local document store");
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function onSubmit() {
    if (busy) return;
    setBusy(true);
    try {
      const res = await submitField(id, remarks);
      setRow(res.data);
      toast.success("Verification submitted");
      navigate("/field");
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Skeleton className="h-64" />;
  if (error && !row) return <ErrorState message={error} onRetry={handleRetry} />;
  if (!row) return <EmptyState title="Verification record not found" body="Could not load details for this field verification task." />;
  const locked = row.status === "SUBMITTED";

  return (
    <div className="mx-auto max-w-xl">
      <PageHeader crumbs="Field Operations" title="Submit verification" />
      <Card className="space-y-4">
        {parcel ? (
          <p className="text-sm text-slate-600">{parcel.ulpin} · {parcel.village} · {parcel.khasra_number}</p>
        ) : null}
        <StatusBadge value={row.status} />
        <Button className="w-full min-h-12" disabled={locked || busy} onClick={captureGps}>Capture GPS</Button>
        <div className="grid grid-cols-2 gap-3">
          <Input label="Latitude" value={row.gps_lat ?? ""} readOnly />
          <Input label="Longitude" value={row.gps_lng ?? ""} readOnly />
        </div>
        <label className="flex min-h-11 items-center gap-3 text-sm">
          <input type="checkbox" disabled={locked} checked={!!row.owner_verified} onChange={(e) => save({ owner_verified: e.target.checked })} />
          Owner verified
        </label>
        <label className="flex min-h-11 items-center gap-3 text-sm">
          <input type="checkbox" disabled={locked} checked={!!row.land_info_verified} onChange={(e) => save({ land_info_verified: e.target.checked })} />
          Land information verified
        </label>
        <label className="flex min-h-11 items-center gap-3 text-sm">
          <input type="checkbox" disabled={locked} checked={!!row.documents_verified} onChange={(e) => save({ documents_verified: e.target.checked })} />
          Documents verified
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Photograph</span>
          <input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" capture="environment" disabled={locked} onChange={onPhoto} />
        </label>
        <Textarea label="Notes" value={remarks} onChange={(e) => setRemarks(e.target.value)} disabled={locked} />
        <Button className="w-full min-h-12" loading={busy} disabled={locked} onClick={onSubmit}>Submit verification</Button>
      </Card>
    </div>
  );
}
