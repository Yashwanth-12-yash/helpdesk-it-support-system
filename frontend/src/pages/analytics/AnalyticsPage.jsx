import { useCallback, useEffect, useState } from "react";
import { Download } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { analyticsService } from "../../services/domainServices";
import { orgService } from "../../services/orgService";
import { getErrorMessage } from "../../services/api";
import { DataTable, ErrorBanner, LoadingSpinner, PageHeader } from "../../components/common/UIPrimitives";

export function AnalyticsPage() {
  const [dashboard, setDashboard] = useState(null);
  const [performance, setPerformance] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [deptId, setDeptId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    orgService.listDepartments({ page_size: 100 }).then((r) => setDepartments(r.results || [])).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = {
        ...(startDate ? { start_date: startDate } : {}),
        ...(endDate ? { end_date: endDate } : {}),
        ...(deptId ? { department: deptId } : {}),
      };
      const [dRes, pRes] = await Promise.all([
        analyticsService.getDashboard(params),
        analyticsService.getPerformance(params),
      ]);
      setDashboard(dRes);
      setPerformance(pRes);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load analytics."));
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, deptId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleExport = async () => {
    try {
      await analyticsService.downloadCSV({
        ...(startDate ? { start_date: startDate } : {}),
        ...(endDate ? { end_date: endDate } : {}),
        ...(deptId ? { department: deptId } : {}),
      });
    } catch (err) {
      setError(getErrorMessage(err, "CSV export failed."));
    }
  };

  const perfCols = [
    { key: "name", label: "Engineer", render: (r) => <span className="font-semibold text-slate-900">{r.name}</span> },
    { key: "email", label: "Email" },
    { key: "total_assigned", label: "Assigned" },
    { key: "resolved_count", label: "Resolved" },
    { key: "open_count", label: "Active" },
    { key: "sla_breached_count", label: "Breaches" },
    { key: "sla_compliance_percentage", label: "SLA %", render: (r) => `${r.sla_compliance_percentage}%` },
    { key: "avg_resolution_hours", label: "Avg Resolution (hrs)" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Operations Analytics & Reports"
        subtitle="Real-time support metrics, departmental volume, and engineer performance."
        actions={
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-navy-800 hover:bg-navy-900 text-white text-sm font-semibold"
          >
            <Download className="w-4 h-4" /> Export CSV Report
          </button>
        }
      />

      <div className="bg-white border border-slate-200 rounded-xl p-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Start Date</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">End Date</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Department</label>
          <select value={deptId} onChange={(e) => setDeptId(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError("")} />

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-900 mb-4">Tickets by Department</h2>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dashboard?.by_department || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="code" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#1d4ed8" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-900 mb-4">Tickets by Status</h2>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dashboard?.by_status || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="status" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#0f172a" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div>
            <h2 className="text-base font-semibold text-slate-900 mb-3">Support Engineer Performance</h2>
            <DataTable
              columns={perfCols}
              rows={performance.map((p) => ({ ...p, id: p.engineer_id }))}
              emptyTitle="No engineer assignment data yet"
              emptyDescription="Assign tickets to engineers to track resolution performance."
            />
          </div>
        </>
      )}
    </div>
  );
}
