import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Flame,
  PlusCircle,
  ShieldCheck,
  Ticket as TicketIcon,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useAuth } from "../../hooks/useAuth";
import { analyticsService } from "../../services/domainServices";
import { ticketService } from "../../services/ticketService";
import { getErrorMessage } from "../../services/api";
import {
  DataTable,
  ErrorBanner,
  LoadingSpinner,
  PageHeader,
  PriorityBadge,
  StatusBadge,
} from "../../components/common/UIPrimitives";
import { formatDateTime, ROLES } from "../../utils/constants";

const PIE_COLORS = ["#1d4ed8", "#0ea5e9", "#f59e0b", "#dc2626", "#10b981", "#64748b"];

function KpiCard({ label, value, icon: Icon, tone = "blue" }) {
  const toneClasses = {
    blue: "bg-blue-50 text-blue-700",
    amber: "bg-amber-50 text-amber-700",
    red: "bg-red-50 text-red-700",
    emerald: "bg-emerald-50 text-emerald-700",
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 flex items-center justify-between shadow-xs">
      <div>
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</div>
        <div className="text-2xl font-bold text-slate-900 mt-1">{value}</div>
      </div>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${toneClasses[tone]}`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [recentTickets, setRecentTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const [dashData, ticketsData] = await Promise.all([
          analyticsService.getDashboard(),
          ticketService.list({ page_size: 8 }),
        ]);
        if (mounted) {
          setAnalytics(dashData);
          setRecentTickets(ticketsData.results || []);
        }
      } catch (err) {
        if (mounted) setError(getErrorMessage(err, "Unable to load dashboard metrics."));
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) return <LoadingSpinner label="Loading live dashboard statistics..." />;

  const kpis = analytics?.kpis || {};
  const roleSubtitle = {
    [ROLES.ADMIN]: "Organization-wide ticket queue, SLA compliance, and operational health.",
    [ROLES.MANAGER]: "Departmental support queue, overdue monitoring, and SLA adherence.",
    [ROLES.ENGINEER]: "Assigned incidents, team queue workload, and resolution velocity.",
    [ROLES.EMPLOYEE]: "Track your submitted IT requests and live resolution progress.",
  }[user?.role];

  const columns = [
    { key: "ticket_number", label: "Ticket #", render: (r) => <span className="font-semibold text-blue-700">{r.ticket_number}</span> },
    { key: "title", label: "Subject", render: (r) => <span className="font-medium text-slate-900">{r.title}</span> },
    { key: "priority", label: "Priority", render: (r) => <PriorityBadge priority={r.priority} /> },
    { key: "status", label: "Status", render: (r) => <StatusBadge status={r.status} /> },
    { key: "department", label: "Department", render: (r) => r.department_detail?.name || "—" },
    { key: "created_at", label: "Created", render: (r) => formatDateTime(r.created_at) },
  ];

  return (
    <div>
      <PageHeader
        title={`Welcome back, ${user?.first_name}`}
        subtitle={roleSubtitle}
        actions={
          <Link
            to="/tickets/new"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold"
          >
            <PlusCircle className="w-4 h-4" /> New Ticket
          </Link>
        }
      />

      <ErrorBanner message={error} onDismiss={() => setError("")} />

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <KpiCard label="Total Tickets" value={kpis.total_tickets ?? 0} icon={TicketIcon} tone="blue" />
        <KpiCard label="Open / In Progress" value={(kpis.open_tickets ?? 0) + (kpis.in_progress_tickets ?? 0)} icon={Clock} tone="amber" />
        <KpiCard label="Overdue Tickets" value={kpis.overdue_tickets ?? 0} icon={AlertTriangle} tone="red" />
        <KpiCard
                  label="SLA Compliance"
                  value={
                    kpis.sla_compliance_percentage == null
                      ? "N/A"
                      : `${kpis.sla_compliance_percentage}%`
                  }
                  icon={ShieldCheck}
                  tone="emerald"
                />
      </div>

      {user?.role !== ROLES.EMPLOYEE && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <KpiCard label="Critical Active" value={kpis.critical_tickets ?? 0} icon={Flame} tone="red" />
          <KpiCard label="Avg First Response" value={`${kpis.avg_response_minutes ?? 0} min`} icon={Clock} tone="blue" />
          <KpiCard label="Resolved Tickets" value={kpis.resolved_tickets ?? 0} icon={CheckCircle2} tone="emerald" />
        </div>
      )}

      {user?.role !== ROLES.EMPLOYEE && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-slate-900 mb-4">Tickets by Priority</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics?.by_priority || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="priority" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#1d4ed8" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-slate-900 mb-4">Tickets by Category</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={analytics?.by_category || []}
                    dataKey="count"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    outerRadius={88}
                    label
                  >
                    {(analytics?.by_category || []).map((entry, idx) => (
                      <Cell key={entry.category} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-slate-900">Recent Tickets</h2>
          <Link to={user?.role === ROLES.EMPLOYEE ? "/tickets/mine" : "/tickets"} className="text-sm font-medium text-blue-700 hover:underline">
            View all
          </Link>
        </div>
        <DataTable
          columns={columns}
          rows={recentTickets}
          onRowClick={(row) => navigate(`/tickets/${row.id}`)}
          emptyTitle="No tickets yet"
          emptyDescription="Create your first support ticket to get started."
        />
      </div>
    </div>
  );
}
