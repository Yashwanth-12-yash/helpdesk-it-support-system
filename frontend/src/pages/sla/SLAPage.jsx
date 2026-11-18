
import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2, Plus } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { slaService } from "../../services/domainServices";
import { orgService } from "../../services/orgService";
import { getErrorMessage } from "../../services/api";
import { slaPolicySchema } from "../../validations/schemas";
import { formatDateTime, PRIORITIES, ROLES } from "../../utils/constants";
import {
  DataTable,
  ErrorBanner,
  LoadingSpinner,
  Modal,
  PageHeader,
  PriorityBadge,
} from "../../components/common/UIPrimitives";

export function SLAPage() {
  const { user } = useAuth();

  const [overview, setOverview] = useState(null);
  const [policies, setPolicies] = useState([]);
  const [escalations, setEscalations] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [policyModal, setPolicyModal] = useState(false);

  const isAdmin = user?.role === ROLES.ADMIN;
  const isAdminOrManager = [ROLES.ADMIN, ROLES.MANAGER].includes(user?.role);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(slaPolicySchema),
    defaultValues: {
      name: "",
      priority: "HIGH",
      department: "",
      first_response_minutes: 30,
      resolution_minutes: 240,
      escalation_threshold_pct: 80,
      business_hours_only: false,
    },
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [ov, pol, dept] = await Promise.all([
        slaService.getOverview(),
        slaService.listPolicies({ page_size: 100 }),
        orgService.listDepartments({ page_size: 100 }),
      ]);

      setOverview(ov);
      setPolicies(pol.results || []);
      setDepartments(dept.results || dept || []);

      if (isAdminOrManager) {
        const esc = await slaService.listEscalations({ page_size: 50 });
        setEscalations(esc.results || []);
      } else {
        setEscalations([]);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load SLA data."));
    } finally {
      setLoading(false);
    }
  }, [isAdminOrManager]);

  useEffect(() => {
    load();
  }, [load]);

  const onCreatePolicy = async (values) => {
    setError("");

    try {
      await slaService.createPolicy(values);
      setPolicyModal(false);
      reset();
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to save SLA policy."));
    }
  };

  const handleAck = async (escId) => {
    setError("");

    try {
      await slaService.acknowledgeEscalation(escId);
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to acknowledge escalation."));
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading SLA governance..." />;
  }

  const policyCols = [
    {
      key: "name",
      label: "Policy Name",
      render: (r) => (
        <span className="font-semibold text-slate-900">{r.name}</span>
      ),
    },
    {
      key: "priority",
      label: "Priority",
      render: (r) => <PriorityBadge priority={r.priority} />,
    },
    {
      key: "department_name",
      label: "Department",
      render: (r) => r.department_name || "Department",
    },
    {
      key: "first_response_minutes",
      label: "First Response",
      render: (r) => `${r.first_response_minutes} min`,
    },
    {
      key: "resolution_minutes",
      label: "Resolution Target",
      render: (r) => `${r.resolution_minutes} min`,
    },
    {
      key: "business_hours_only",
      label: "Schedule",
      render: (r) =>
        r.business_hours_only ? "Business Hours" : "24 x 7",
    },
  ];

  const escalationCols = [
    {
      key: "ticket_number",
      label: "Ticket #",
      render: (r) => (
        <span className="font-semibold text-blue-700">
          {r.ticket_number}
        </span>
      ),
    },
    { key: "escalation_type", label: "Type" },
    { key: "reason", label: "Reason" },
    {
      key: "created_at",
      label: "Triggered",
      render: (r) => formatDateTime(r.created_at),
    },
    {
      key: "is_acknowledged",
      label: "Status",
      render: (r) =>
        r.is_acknowledged ? (
          <span className="inline-flex items-center gap-1 text-emerald-700 text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Acknowledged
          </span>
        ) : (
          <button
            type="button"
            onClick={() => handleAck(r.id)}
            className="px-2.5 py-1 rounded bg-amber-600 text-white text-xs font-semibold hover:bg-amber-700"
          >
            Acknowledge
          </button>
        ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="SLA Management & Escalations"
        subtitle="Configure priority response/resolution deadlines and monitor breaches."
        actions={
          isAdmin && (
            <button
              type="button"
              onClick={() => setPolicyModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold"
            >
              <Plus className="w-4 h-4" />
              New SLA Policy
            </button>
          )
        }
      />

      <ErrorBanner
        message={error}
        onDismiss={() => setError("")}
      />

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-500 uppercase">
            SLA Compliance
          </div>
          <div className="text-2xl font-bold text-emerald-700 mt-1">
            {overview?.sla_compliance_percentage == null
              ? "N/A"
              : `${overview.sla_compliance_percentage}%`}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-500 uppercase">
            Active Overdue
          </div>
          <div className="text-2xl font-bold text-red-700 mt-1">
            {overview?.active_overdue ?? 0}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-500 uppercase">
            Response Breaches
          </div>
          <div className="text-2xl font-bold text-amber-700 mt-1">
            {overview?.response_breached ?? 0}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-500 uppercase">
            Open Escalations
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {overview?.unacknowledged_escalations ?? 0}
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-base font-semibold text-slate-900 mb-3">
          Configured SLA Policies
        </h2>

        <DataTable
          columns={policyCols}
          rows={policies}
          emptyTitle="No custom SLA policies"
          emptyDescription="Default SLA deadlines apply automatically until custom policies are added."
        />
      </div>

      {isAdminOrManager && (
        <div>
          <h2 className="text-base font-semibold text-slate-900 mb-3">
            Escalations Log
          </h2>

          <DataTable
            columns={escalationCols}
            rows={escalations}
            emptyTitle="No escalations recorded"
            emptyDescription="All tickets are currently within SLA thresholds."
          />
        </div>
      )}

      <Modal
        open={policyModal}
        title="Create SLA Policy"
        onClose={() => setPolicyModal(false)}
      >
        <form
          onSubmit={handleSubmit(onCreatePolicy)}
          className="space-y-4"
        >
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Policy Name
            </label>

            <input
              {...register("name")}
              placeholder="Example: IT High Priority SLA"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            />

            {errors.name && (
              <p className="text-xs text-red-600 mt-1">
                {errors.name.message}
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Department
            </label>

            <select
              {...register("department")}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
              defaultValue=""
            >
              <option value="">Select Department</option>

              {departments.map((department) => (
                <option key={department.id} value={department.id}>
                  {department.name}
                </option>
              ))}
            </select>

            {errors.department && (
              <p className="text-xs text-red-600 mt-1">
                {errors.department.message}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Priority
              </label>

              <select
                {...register("priority")}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
              >
                {PRIORITIES.map((priority) => (
                  <option key={priority} value={priority}>
                    {priority}
                  </option>
                ))}
              </select>

              {errors.priority && (
                <p className="text-xs text-red-600 mt-1">
                  {errors.priority.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Warning Threshold (%)
              </label>

              <input
                type="number"
                {...register("escalation_threshold_pct")}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />

              {errors.escalation_threshold_pct && (
                <p className="text-xs text-red-600 mt-1">
                  {errors.escalation_threshold_pct.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                First Response (min)
              </label>

              <input
                type="number"
                {...register("first_response_minutes")}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />

              {errors.first_response_minutes && (
                <p className="text-xs text-red-600 mt-1">
                  {errors.first_response_minutes.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Resolution Target (min)
              </label>

              <input
                type="number"
                {...register("resolution_minutes")}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />

              {errors.resolution_minutes && (
                <p className="text-xs text-red-600 mt-1">
                  {errors.resolution_minutes.message}
                </p>
              )}
            </div>
          </div>

          <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-700">
            <input
              type="checkbox"
              {...register("business_hours_only")}
              className="rounded border-slate-300"
            />
            Calculate deadlines using Business Hours only
          </label>

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => {
                setPolicyModal(false);
                reset();
              }}
              className="px-4 py-2 text-sm rounded-lg border border-slate-300"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={isSubmitting || departments.length === 0}
              className="px-4 py-2 text-sm rounded-lg bg-blue-700 text-white font-semibold disabled:opacity-50"
            >
              {isSubmitting ? "Saving..." : "Save Policy"}
            </button>
          </div>

          {departments.length === 0 && (
            <p className="text-xs text-amber-700">
              No departments are available. Create a department before configuring an SLA policy.
            </p>
          )}
        </form>
      </Modal>
    </div>
  );
}
