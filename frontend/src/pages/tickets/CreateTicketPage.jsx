import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { ticketService } from "../../services/ticketService";
import { orgService } from "../../services/orgService";
import { aiService } from "../../services/domainServices";
import { getErrorMessage } from "../../services/api";
import { createTicketSchema } from "../../validations/schemas";
import { CATEGORIES, PRIORITIES } from "../../utils/constants";
import { ErrorBanner, PageHeader } from "../../components/common/UIPrimitives";

export function CreateTicketPage() {
  const navigate = useNavigate();
  const [departments, setDepartments] = useState([]);
  const [teams, setTeams] = useState([]);
  const [serverError, setServerError] = useState("");
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(createTicketSchema),
    defaultValues: {
      category: "OTHER",
      priority: "MEDIUM",
    },
  });

  const title = watch("title");
  const description = watch("description");
  const selectedDept = watch("department");

  useEffect(() => {
    Promise.all([
      orgService.listDepartments({ page_size: 100 }),
      orgService.listTeams({ page_size: 100 }),
    ])
      .then(([d, t]) => {
        setDepartments(d.results || []);
        setTeams(t.results || []);
      })
      .catch(() => {});
  }, []);

  const handleAIClassify = async () => {
    if (!title || !description) {
      setServerError("Enter a title and description first to request AI recommendations.");
      return;
    }
    setServerError("");
    setAiLoading(true);
    try {
      const res = await aiService.classifyTicket({ title, description });
      setAiSuggestion(res);
    } catch (err) {
      setServerError(getErrorMessage(err, "AI recommendations are currently unavailable."));
    } finally {
      setAiLoading(false);
    }
  };

  const applyAISuggestion = () => {
    if (!aiSuggestion) return;
    if (aiSuggestion.suggested_category) setValue("category", aiSuggestion.suggested_category);
    if (aiSuggestion.suggested_priority) setValue("priority", aiSuggestion.suggested_priority);
    if (aiSuggestion.suggested_department?.id) setValue("department", aiSuggestion.suggested_department.id);
  };

  const onSubmit = async (values) => {
    setServerError("");
    try {
      const payload = {
        ...values,
        support_team: values.support_team ? Number(values.support_team) : null,
      };
      const created = await ticketService.create(payload);
      navigate(`/tickets/${created.id}`);
    } catch (err) {
      setServerError(getErrorMessage(err, "Failed to create ticket."));
    }
  };

  const filteredTeams = selectedDept
    ? teams.filter((t) => Number(t.department) === Number(selectedDept))
    : teams;

  return (
    <div className="max-w-3xl">
      <PageHeader
        title="Create Support Ticket"
        subtitle="Describe your technical issue. Priority determines response and resolution SLAs."
      />

      <ErrorBanner message={serverError} onDismiss={() => setServerError("")} />

      <form onSubmit={handleSubmit(onSubmit)} className="bg-white border border-slate-200 rounded-xl p-6 space-y-5 shadow-xs">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Issue Title</label>
          <input
            type="text"
            {...register("title")}
            placeholder="e.g., Unable to connect to corporate VPN from Windows 11"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
          />
          {errors.title && <p className="text-xs text-red-600 mt-1">{errors.title.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Detailed Description</label>
          <textarea
            rows={5}
            {...register("description")}
            placeholder="Include error messages, affected system, and steps already tried..."
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
          />
          {errors.description && <p className="text-xs text-red-600 mt-1">{errors.description.message}</p>}
        </div>

        <div className="flex items-center justify-between p-3.5 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-xs text-slate-600">
            Need help choosing category or priority? Request advisory Gemini AI triage.
          </div>
          <button
            type="button"
            onClick={handleAIClassify}
            disabled={aiLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-900 text-white text-xs font-semibold disabled:opacity-60"
          >
            <Sparkles className="w-3.5 h-3.5" />
            {aiLoading ? "Analyzing..." : "AI Recommend"}
          </button>
        </div>

        {aiSuggestion && (
          <div className="p-4 rounded-lg border border-blue-200 bg-blue-50 text-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-blue-900">AI Classification Recommendation (Advisory)</span>
              <button
                type="button"
                onClick={applyAISuggestion}
                className="px-2.5 py-1 rounded bg-blue-700 text-white text-xs font-semibold hover:bg-blue-800"
              >
                Apply Suggestions
              </button>
            </div>
            <div className="text-xs text-blue-900">
              Category: <strong>{aiSuggestion.suggested_category}</strong> • Priority:{" "}
              <strong>{aiSuggestion.suggested_priority}</strong>
              {aiSuggestion.suggested_department ? ` • Dept: ${aiSuggestion.suggested_department.name}` : ""}
            </div>
            <p className="text-xs text-blue-800">{aiSuggestion.rationale}</p>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
            <select {...register("category")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
            <select {...register("priority")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Department</label>
            <select {...register("department")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
              <option value="">Select department...</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
              ))}
            </select>
            {errors.department && <p className="text-xs text-red-600 mt-1">{errors.department.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Support Team (Optional)</label>
            <select {...register("support_team")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
              <option value="">Auto / Unassigned</option>
              {filteredTeams.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="px-4 py-2 rounded-lg border border-slate-300 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-5 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold disabled:opacity-60"
          >
            {isSubmitting ? "Submitting..." : "Submit Ticket"}
          </button>
        </div>
      </form>
    </div>
  );
}
