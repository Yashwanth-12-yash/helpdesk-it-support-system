import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { UserPlus } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { orgService } from "../../services/orgService";
import { getErrorMessage } from "../../services/api";
import { userCreateSchema } from "../../validations/schemas";
import { ROLES } from "../../utils/constants";
import {
  DataTable,
  ErrorBanner,
  LoadingSpinner,
  Modal,
  PageHeader,
  Pagination,
} from "../../components/common/UIPrimitives";

export function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);

  const isAdmin = currentUser?.role === ROLES.ADMIN;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(userCreateSchema),
    defaultValues: { role: "EMPLOYEE" },
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [uRes, dRes] = await Promise.all([
        orgService.listUsers({ page }),
        orgService.listDepartments({ page_size: 100 }),
      ]);
      setUsers(uRes.results || []);
      setTotalCount(uRes.count || 0);
      setDepartments(dRes.results || []);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load users."));
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onCreateUser = async (values) => {
    setError("");
    try {
      await orgService.createUser({
        ...values,
        department: values.department ? Number(values.department) : null,
      });
      setModalOpen(false);
      reset();
      await loadData();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to create user."));
    }
  };

  const handleToggleActive = async (e, targetId) => {
    e.stopPropagation();
    setError("");
    try {
      await orgService.toggleUserActive(targetId);
      await loadData();
    } catch (err) {
      setError(getErrorMessage(err, "Unable to toggle user status."));
    }
  };

  const columns = [
    { key: "full_name", label: "Name", render: (r) => <span className="font-semibold text-slate-900">{r.full_name}</span> },
    { key: "email", label: "Email" },
    { key: "role", label: "Role", render: (r) => <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-xs font-semibold">{r.role}</span> },
    { key: "department_name", label: "Department", render: (r) => r.department_name || "—" },
    {
      key: "is_active",
      label: "Status",
      render: (r) => (
        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${r.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
          {r.is_active ? "Active" : "Inactive"}
        </span>
      ),
    },
    ...(isAdmin
      ? [
          {
            key: "actions",
            label: "Actions",
            render: (r) =>
              r.id !== currentUser?.id ? (
                <button
                  type="button"
                  onClick={(e) => handleToggleActive(e, r.id)}
                  className="text-xs font-semibold text-blue-700 hover:underline"
                >
                  {r.is_active ? "Deactivate" : "Activate"}
                </button>
              ) : (
                <span className="text-xs text-slate-400">Current User</span>
              ),
          },
        ]
      : []),
  ];

  return (
    <div>
      <PageHeader
        title="User Management"
        subtitle="Manage employee, engineer, manager, and administrator accounts."
        actions={
          isAdmin && (
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold"
            >
              <UserPlus className="w-4 h-4" /> Create User
            </button>
          )
        }
      />

      <ErrorBanner message={error} onDismiss={() => setError("")} />

      {loading ? (
        <LoadingSpinner label="Loading users..." />
      ) : (
        <>
          <DataTable columns={columns} rows={users} />
          <Pagination page={page} totalCount={totalCount} onPageChange={setPage} />
        </>
      )}

      <Modal open={modalOpen} title="Create User Account" onClose={() => setModalOpen(false)}>
        <form onSubmit={handleSubmit(onCreateUser)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">First Name</label>
              <input {...register("first_name")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
              {errors.first_name && <p className="text-xs text-red-600 mt-1">{errors.first_name.message}</p>}
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Last Name</label>
              <input {...register("last_name")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
              {errors.last_name && <p className="text-xs text-red-600 mt-1">{errors.last_name.message}</p>}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Email</label>
            <input type="email" {...register("email")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            {errors.email && <p className="text-xs text-red-600 mt-1">{errors.email.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Role</label>
              <select {...register("role")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
                {Object.values(ROLES).map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Department</label>
              <select {...register("department")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
                <option value="">None</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Initial Password</label>
            <input type="password" {...register("password")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            {errors.password && <p className="text-xs text-red-600 mt-1">{errors.password.message}</p>}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => setModalOpen(false)} className="px-4 py-2 text-sm rounded-lg border border-slate-300">Cancel</button>
            <button type="submit" disabled={isSubmitting} className="px-4 py-2 text-sm rounded-lg bg-blue-700 text-white font-semibold">
              {isSubmitting ? "Creating..." : "Create User"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
