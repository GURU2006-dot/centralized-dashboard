import { useEffect, useState } from "react";
import { listDocuments, uploadDocument, verifyDocument } from "../api/documents";
import { Button, Card, DataTable, EmptyState, ErrorState, Input, PageHeader, Pagination, Select, StatusBadge } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { dt, errorMessage } from "../lib/format";
import { canTransition } from "../lib/roles";

export default function DocumentsPage() {
  const { role } = useAuth();
  const toast = useToast();
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [file, setFile] = useState(null);
  const [docType, setDocType] = useState("OTHER");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [verifyingId, setVerifyingId] = useState(null);

  useEffect(() => {
    let active = true;
    listDocuments({ page, page_size: 15 })
      .then((r) => {
        if (!active) return;
        setRows(r.data || []);
        setTotal(r.meta?.total || 0);
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
  }, [page, reloadKey, toast]);

  function handleRetry() {
    setLoading(true);
    setError(null);
    setReloadKey((k) => k + 1);
  }

  async function onUpload(e) {
    e.preventDefault();
    if (!file || uploading) return;
    setUploading(true);
    try {
      await uploadDocument({ file, doc_type: docType, name: file.name });
      toast.success("Stored on local disk (not production object storage)");
      setFile(null);
      setReloadKey((k) => k + 1);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setUploading(false);
    }
  }

  async function verify(id, status) {
    if (verifyingId) return;
    setVerifyingId(id);
    try {
      await verifyDocument(id, status);
      toast.success(`Document marked as ${status.toLowerCase()}`);
      setReloadKey((k) => k + 1);
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setVerifyingId(null);
    }
  }

  return (
    <div>
      <PageHeader crumbs="Field Operations" title="Documents" subtitle="Files are saved to the API host local upload directory. This is not production object storage." />
      {canTransition(role) ? (
        <Card className="mb-4">
          <form className="flex flex-wrap items-end gap-3" onSubmit={onUpload}>
            <Input label="File" type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <Select label="Type" value={docType} onChange={(e) => setDocType(e.target.value)}>
              <option>OTHER</option>
              <option>PHOTO</option>
              <option>AWARD</option>
              <option>SIA</option>
            </Select>
            <Button type="submit" loading={uploading} disabled={!file || uploading}>
              {uploading ? "Uploading..." : "Upload"}
            </Button>
          </form>
        </Card>
      ) : null}

      {error && !rows.length ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : (
        <>
          <DataTable
            rows={rows}
            loading={loading}
            empty={<EmptyState title="No documents found" body="Uploaded documents and field evidence will appear here." />}
            columns={[
              { key: "name", header: "Name" },
              { key: "doc_type", header: "Type" },
              { key: "mime_type", header: "MIME" },
              { key: "uploaded_at", header: "Uploaded", render: (r) => dt(r.uploaded_at) },
              { key: "verification_status", header: "Status", render: (r) => <StatusBadge value={r.verification_status} /> },
              { key: "id", header: "Action", render: (r) => canTransition(role) && r.verification_status === "PENDING" ? (
                <div className="flex gap-2">
                  <Button variant="ghost" disabled={verifyingId === r.id} onClick={() => verify(r.id, "VERIFIED")} aria-label={`Verify document ${r.name}`}>Verify</Button>
                  <Button variant="ghost" disabled={verifyingId === r.id} onClick={() => verify(r.id, "REJECTED")} aria-label={`Reject document ${r.name}`}>Reject</Button>
                </div>
              ) : "—" },
            ]}
          />
          <Pagination page={page} pageSize={15} total={total} onPage={setPage} />
        </>
      )}
    </div>
  );
}
