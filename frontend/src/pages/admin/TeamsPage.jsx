import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2, UserPlus } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { orgService } from "../../services/orgService";
import { getErrorMessage } from "../../services/api";
import { teamSchema } from "../../validations/schemas";
import { ROLES } from "../../utils/constants";
import { EmptyState, ErrorBanner, LoadingSpinner, Modal, PageHeader } from "../../components/common/UIPrimitives";

export function TeamsPage() {
  const { user } = useAuth();
  const [teams, setTeams] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [engineers, setEngineers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [teamModal, setTeamModal] = useState(false);
  const [memberModalTeam, setMemberModalTeam] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState("");

  const isAdmin = user?.role === ROLES.ADMIN;
  const canManageMembers = [ROLES.ADMIN, ROLES.MANAGER].includes(user?.role);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(teamSchema) });

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [tRes, dRes] = await Promise.all([
        orgService.listTeams({ page_size: 100 }),
        orgService.listDepartments({ page_size: 100 }),
      ]);
      setTeams(tRes.results || []);
      setDepartments(dRes.results || []);
      if (canManageMembers) {
        const eRes = await orgService.listUsers({ role: "ENGINEER", page_size: 100 });
        setEngineers(eRes.results || []);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load support teams."));
    } finally {
      setLoading(false);
    }
  }, [canManageMembers]);

  useEffect(() => {
    load();
  }, [load]);

  const onCreateTeam = async (values) => {
    setError("");
    try {
      await orgService.createTeam({
        ...values,
        lead: values.lead ? Number(values.lead) : null,
      });
      setTeamModal(false);
      reset();
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to create support team."));
    }
  };

  const onAddMember = async (e) => {
    e.preventDefault();
    if (!memberModalTeam || !selectedUserId) return;
    setError("");
    try {
      await orgService.addTeamMember(memberModalTeam.id, { user: Number(selectedUserId), is_primary: false });
      setMemberModalTeam(null);
      setSelectedUserId("");
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to add team member."));
    }
  };

  const onRemoveMember = async (teamId, userId) => {
    setError("");
    try {
      await orgService.removeTeamMember(teamId, userId);
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to remove team member."));
    }
  };

  return (
    <div>
      <PageHeader
        title="Support Teams"
        subtitle="Specialized IT queues and assigned support engineers."
        actions={
          isAdmin && (
            <button
              type="button"
              onClick={() => setTeamModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold"
            >
              <Plus className="w-4 h-4" /> New Team
            </button>
          )
        }
      />

      <ErrorBanner message={error} onDismiss={() => setError("")} />

      {loading ? (
        <LoadingSpinner />
      ) : teams.length === 0 ? (
        <EmptyState title="No support teams" description="Create a support team under a department." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {teams.map((team) => (
            <div key={team.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-base font-bold text-slate-900">{team.name}</h3>
                  <p className="text-xs text-slate-500">
                    {team.department_detail?.name} • Lead: {team.lead_detail?.full_name || "Unassigned"}
                  </p>
                </div>
                {canManageMembers && (
                  <button
                    type="button"
                    onClick={() => setMemberModalTeam(team)}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold hover:bg-slate-50"
                  >
                    <UserPlus className="w-3.5 h-3.5" /> Add Member
                  </button>
                )}
              </div>

              <div className="space-y-2 mt-4">
                <div className="text-xs font-semibold uppercase text-slate-400">
                  Team Engineers ({team.members?.length || 0})
                </div>
                {(team.members || []).map((m) => (
                  <div key={m.id} className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-50 text-sm">
                    <div>
                      <span className="font-medium text-slate-900">{m.user.full_name}</span>
                      <span className="text-xs text-slate-500 ml-2">{m.user.email}</span>
                    </div>
                    {canManageMembers && (
                      <button
                        type="button"
                        onClick={() => onRemoveMember(team.id, m.user.id)}
                        className="text-slate-400 hover:text-red-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
                {(!team.members || team.members.length === 0) && (
                  <p className="text-xs text-slate-500">No engineers assigned to this team yet.</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={teamModal} title="Create Support Team" onClose={() => setTeamModal(false)}>
        <form onSubmit={handleSubmit(onCreateTeam)} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Team Name</label>
            <input {...register("name")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            {errors.name && <p className="text-xs text-red-600 mt-1">{errors.name.message}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Department</label>
            <select {...register("department")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
              <option value="">Select department...</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
            {errors.department && <p className="text-xs text-red-600 mt-1">{errors.department.message}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Team Lead</label>
            <select {...register("lead")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
              <option value="">None</option>
              {engineers.map((eng) => (
                <option key={eng.id} value={eng.id}>{eng.full_name}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setTeamModal(false)} className="px-4 py-2 text-sm rounded-lg border border-slate-300">Cancel</button>
            <button type="submit" disabled={isSubmitting} className="px-4 py-2 text-sm rounded-lg bg-blue-700 text-white font-semibold">Create Team</button>
          </div>
        </form>
      </Modal>

      <Modal open={!!memberModalTeam} title={`Add Engineer to ${memberModalTeam?.name}`} onClose={() => setMemberModalTeam(null)}>
        <form onSubmit={onAddMember} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Select Engineer</label>
            <select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
            >
              <option value="">Choose engineer...</option>
              {engineers.map((eng) => (
                <option key={eng.id} value={eng.id}>{eng.full_name} ({eng.email})</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setMemberModalTeam(null)} className="px-4 py-2 text-sm rounded-lg border border-slate-300">Cancel</button>
            <button type="submit" className="px-4 py-2 text-sm rounded-lg bg-blue-700 text-white font-semibold">Add Member</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
