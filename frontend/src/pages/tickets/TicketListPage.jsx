import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PlusCircle, Search } from "lucide-react";
import { ticketService } from "../../services/ticketService";
import { orgService } from "../../services/orgService";
import { getErrorMessage } from "../../services/api";
import {
  DataTable,
  ErrorBanner,
  LoadingSpinner,
  PageHeader,
  Pagination,
  PriorityBadge,
  StatusBadge,
} from "../../components/common/UIPrimitives";
import { formatDateTime, PRIORITIES, STATUSES } from "../../utils/constants";

export function TicketListPage({ mode = "all" }) {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [departments, setDepartments] = useState([]);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [deptFilter, setDeptFilter] = useState("");
  const [ordering, setOrdering] = useState("-created_at");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    orgService.listDepartments({ page_size: 100 }).then((d) => setDepartments(d.results || [])).catch(() => {});
  }, []);

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = {
        page,
        ordering,
        ...(search ? { search } : {}),
        ...(statusFilter ? { status: statusFilter } : {}),
        ...(priorityFilter ? { priority: priorityFilter } : {}),
        ...(deptFilter ? { department: deptFilter } : {}),
        ...(mode === "mine" ? { my_tickets: true } : {}),
        ...(mode === "assigned" ? { assigned_to_me: true } : {}),
      };
      const data = await ticketService.list(params);
      setTickets(data.results || []);
      setTotalCount(data.count || 0);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load tickets."));
    } finally {
      setLoading(false);
    }
  }, [page, ordering, search, statusFilter, priorityFilter, deptFilter, mode]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const titleMap = {
    all: "All Support Tickets",
    mine: "My Submitted Tickets",
    assigned: "Assigned to Me",
  };

  const columns = [
    { key: "ticket_number", label: "Ticket #", render: (r) => <span className="font-semibold text-blue-700">{r.ticket_number}</span> },
    { key: "title", label: "Title", render: (r) => <span className="font-medium text-slate-900">{r.title}</span> },
    { key: "priority", label: "Priority", render: (r) => <PriorityBadge priority={r.priority} /> },
    { key: "status", label: "Status", render: (r) => <StatusBadge status={r.status} /> },
    { key: "department", label: "Department", render: (r) => r.department_detail?.name || "—" },
    { key: "assigned_engineer", label: "Assignee", render: (r) => r.assigned_engineer_detail?.full_name || "Unassigned" },
    { key: "resolution_deadline", label: "SLA Due", render: (r) => formatDateTime(r.resolution_deadline) },
  ];

  return (
    <div>
      <PageHeader
        title={titleMap[mode] || "Tickets"}
        subtitle="Search, filter, sort, and inspect live support incidents."
        actions={
          <Link
            to="/tickets/new"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold"
          >
            <PlusCircle className="w-4 h-4" /> Create Ticket
          </Link>
        }
      />

      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search ticket # or title..."
            className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
        >
          <option value="">All Statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s.replaceAll("_", " ")}</option>
          ))}
        </select>

        <select
          value={priorityFilter}
          onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
        >
          <option value="">All Priorities</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>

        <select
          value={deptFilter}
          onChange={(e) => { setDeptFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
        >
          <option value="">All Departments</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>

        <select
          value={ordering}
          onChange={(e) => setOrdering(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
        >
          <option value="-created_at">Newest First</option>
          <option value="created_at">Oldest First</option>
          <option value="resolution_deadline">SLA Deadline (Soonest)</option>
          <option value="-priority">Priority</option>
        </select>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError("")} />

      {loading ? (
        <LoadingSpinner label="Loading tickets..." />
      ) : (
        <>
          <DataTable
            columns={columns}
            rows={tickets}
            onRowClick={(row) => navigate(`/tickets/${row.id}`)}
            emptyTitle="No matching tickets"
            emptyDescription="No tickets matched your current filters."
          />
          <Pagination page={page} totalCount={totalCount} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
