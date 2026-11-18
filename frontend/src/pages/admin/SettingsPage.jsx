import { useEffect, useState } from "react";
import { analyticsService } from "../../services/domainServices";
import { getErrorMessage } from "../../services/api";
import { formatDateTime } from "../../utils/constants";
import { DataTable, ErrorBanner, LoadingSpinner, PageHeader, Pagination } from "../../components/common/UIPrimitives";

export function SettingsPage() {
  const [logs, setLogs] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    analyticsService
      .listAuditLogs({ page })
      .then((res) => {
        setLogs(res.results || []);
        setTotalCount(res.count || 0);
      })
      .catch((err) => setError(getErrorMessage(err, "Unable to load audit logs.")))
      .finally(() => setLoading(false));
  }, [page]);

  const columns = [
    { key: "created_at", label: "Timestamp", render: (r) => formatDateTime(r.created_at) },
    { key: "actor_email", label: "Actor" },
    { key: "action", label: "Action", render: (r) => <span className="font-semibold text-navy-800">{r.action}</span> },
    { key: "resource_type", label: "Resource" },
    { key: "resource_id", label: "Resource ID" },
    { key: "ip_address", label: "IP Address", render: (r) => r.ip_address || "—" },
  ];

  return (
    <div>
      <PageHeader
        title="System Settings & Audit Logs"
        subtitle="Immutable administrative audit trail across authentication, SLA policies, and tickets."
      />
      <ErrorBanner message={error} onDismiss={() => setError("")} />
      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          <DataTable columns={columns} rows={logs} emptyTitle="No audit events yet" />
          <Pagination page={page} totalCount={totalCount} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
