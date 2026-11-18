import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { orgService } from "../../services/orgService";
import { getErrorMessage } from "../../services/api";
import { departmentSchema } from "../../validations/schemas";
import { ROLES } from "../../utils/constants";
import { DataTable, ErrorBanner, LoadingSpinner, Modal, PageHeader } from "../../components/common/UIPrimitives";

export function DepartmentsPage() {
  const { user } = useAuth();
  const [departments, setDepartments] = useState([]);
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);

  const isAdmin = user?.role === ROLES.ADMIN;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(departmentSchema) });

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const dRes = await orgService.listDepartments({ page_size: 100 });
      setDepartments(dRes.results || []);
      if (isAdmin) {
        const mRes = await orgService.listUsers({ role: "MANAGER", page_size: 100 });
        setManagers(mRes.results || []);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load departments."));
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => {
    load();
  }, [load]);

  const onSubmit = async (values) => {
    setError("");
    try {
      await orgService.createDepartment({
        ...values,
        manager: values.manager ? Number(values.manager) : null,
      });
      setModalOpen(false);
      reset();
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to create department."));
    }
  };

  const columns = [
    { key: "code", label: "Code", render: (r) => <span className="font-bold text-navy-800">{r.code}</span> },
    { key: "name", label: "Department Name", render: (r) => <span className="font-semibold text-slate-900">{r.name}</span> },
    { key: "manager", label: "Manager", render: (r) => r.manager_detail?.full_name || "Unassigned" },
    { key: "team_count", label: "Support Teams" },
    {
      key: "is_active",
      label: "Status",
      render: (r) => (
        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${r.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
          {r.is_active ? "Active" : "Inactive"}
        </span>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Departments"
        subtitle="Organizational departments and assigned department managers."
        actions={
          isAdmin && (
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold"
            >
              <Plus className="w-4 h-4" /> New Department
            </button>
          )
        }
      />

      <ErrorBanner message={error} onDismiss={() => setError("")} />
      {loading ? <LoadingSpinner /> : <DataTable columns={columns} rows={departments} />}

      <Modal open={modalOpen} title="Create Department" onClose={() => setModalOpen(false)}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <label className="block text-xs font-medium text-slate-700 mb-1">Name</label>
              <input {...register("name")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
              {errors.name && <p className="text-xs text-red-600 mt-1">{errors.name.message}</p>}
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Code</label>
              <input {...register("code")} placeholder="INFRA" className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm uppercase" />
              {errors.code && <p className="text-xs text-red-600 mt-1">{errors.code.message}</p>}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Department Manager</label>
            <select {...register("manager")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
              <option value="">Unassigned</option>
              {managers.map((m) => (
                <option key={m.id} value={m.id}>{m.full_name} ({m.email})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Description</label>
            <textarea rows={3} {...register("description")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>

          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setModalOpen(false)} className="px-4 py-2 text-sm rounded-lg border border-slate-300">Cancel</button>
            <button type="submit" disabled={isSubmitting} className="px-4 py-2 text-sm rounded-lg bg-blue-700 text-white font-semibold">Create</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
