import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  AlertTriangle,
  BookOpen,
  Download,
  History,
  MessageSquare,
  Paperclip,
  Send,
  Sparkles,
  UserPlus,
} from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { ticketService } from "../../services/ticketService";
import { orgService } from "../../services/orgService";
import { aiService, knowledgeService } from "../../services/domainServices";
import { getErrorMessage } from "../../services/api";
import {
  ErrorBanner,
  LoadingSpinner,
  Modal,
  PageHeader,
  PriorityBadge,
  StatusBadge,
} from "../../components/common/UIPrimitives";
import { formatDateTime, ROLES, STATUSES } from "../../utils/constants";

export function TicketDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [ticket, setTicket] = useState(null);
  const [comments, setComments] = useState([]);
  const [attachments, setAttachments] = useState([]);
  const [history, setHistory] = useState([]);
  const [kbArticles, setKbArticles] = useState([]);
  const [engineers, setEngineers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Comment & attachment state
  const [commentBody, setCommentBody] = useState("");
  const [isInternal, setIsInternal] = useState(false);
  const [submittingComment, setSubmittingComment] = useState(false);

  // Action modals
  const [assignModal, setAssignModal] = useState(false);
  const [selectedEngineerId, setSelectedEngineerId] = useState("");
  const [resolveModal, setResolveModal] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [reopenModal, setReopenModal] = useState(false);
  const [reopenReason, setReopenReason] = useState("");

  // AI state
  const [aiResult, setAiResult] = useState(null);
  const [aiType, setAiType] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  const isStaff = [ROLES.ADMIN, ROLES.MANAGER, ROLES.ENGINEER].includes(user?.role);
  const canAssign = [ROLES.ADMIN, ROLES.MANAGER].includes(user?.role);

  const loadTicketData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [tData, cData, aData, hData, kbData] = await Promise.all([
        ticketService.get(id),
        ticketService.getComments(id),
        ticketService.getAttachments(id),
        ticketService.getHistory(id),
        knowledgeService.recommend(id).catch(() => []),
      ]);
      setTicket(tData);
      setComments(cData);
      setAttachments(aData);
      setHistory(hData);
      setKbArticles(kbData);
      if (canAssign) {
        const uData = await orgService.listUsers({ role: "ENGINEER", page_size: 100 });
        setEngineers(uData.results || []);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Unable to load ticket details."));
    } finally {
      setLoading(false);
    }
  }, [id, canAssign]);

  useEffect(() => {
    loadTicketData();
  }, [loadTicketData]);

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!commentBody.trim()) return;
    setSubmittingComment(true);
    setError("");
    try {
      await ticketService.addComment(id, { body: commentBody, is_internal: isInternal });
      setCommentBody("");
      setIsInternal(false);
      await loadTicketData();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to post comment."));
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    try {
      await ticketService.uploadAttachment(id, file);
      await loadTicketData();
    } catch (err) {
      setError(getErrorMessage(err, "Attachment upload failed."));
    }
  };

  const handleStatusChange = async (newStatus) => {
    if (newStatus === "RESOLVED") {
      setResolveModal(true);
      return;
    }
    setError("");
    try {
      await ticketService.changeStatus(id, { status: newStatus });
      await loadTicketData();
    } catch (err) {
      setError(getErrorMessage(err, "Status transition not allowed."));
    }
  };

  const handleAssignSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await ticketService.assign(id, {
        assigned_engineer: selectedEngineerId ? Number(selectedEngineerId) : null,
      });
      setAssignModal(false);
      await loadTicketData();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to assign ticket."));
    }
  };

  const handleSelfAccept = async () => {
    setError("");
    try {
      await ticketService.assign(id, { assigned_engineer: user.id });
      await loadTicketData();
    } catch (err) {
      setError(getErrorMessage(err, "Could not accept ticket."));
    }
  };

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await ticketService.resolve(id, resolutionNotes);
      setResolveModal(false);
      setResolutionNotes("");
      await loadTicketData();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to resolve ticket."));
    }
  };

  const handleReopenSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await ticketService.reopen(id, reopenReason);
      setReopenModal(false);
      setReopenReason("");
      await loadTicketData();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to reopen ticket."));
    }
  };

  const runAIAction = async (type) => {
    setAiLoading(true);
    setAiType(type);
    setError("");
    try {
      let res;
      if (type === "summary") res = await aiService.summarizeTicket(id);
      if (type === "solutions") res = await aiService.suggestSolutions(id);
      if (type === "similar") res = await aiService.similarTickets(id);
      setAiResult(res);
    } catch (err) {
      setError(getErrorMessage(err, "Gemini AI assistant unavailable."));
    } finally {
      setAiLoading(false);
    }
  };

  if (loading) return <LoadingSpinner label="Loading ticket workspace..." />;
  if (!ticket) return <ErrorBanner message={error || "Ticket not found."} />;

  return (
    <div>
      <PageHeader
        title={`${ticket.ticket_number} — ${ticket.title}`}
        subtitle={`Reported by ${ticket.created_by_detail?.full_name} • ${ticket.department_detail?.name}`}
        actions={
          <div className="flex items-center gap-2 flex-wrap">
            {canAssign && !["RESOLVED", "CLOSED"].includes(ticket.status) && (
              <button
                type="button"
                onClick={() => setAssignModal(true)}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 bg-white text-sm font-medium hover:bg-slate-50"
              >
                <UserPlus className="w-4 h-4" /> Assign
              </button>
            )}
            {user?.role === ROLES.ENGINEER && ticket.assigned_engineer !== user.id && !["RESOLVED", "CLOSED"].includes(ticket.status) && (
              <button
                type="button"
                onClick={handleSelfAccept}
                className="px-3 py-2 rounded-lg bg-blue-700 text-white text-sm font-semibold hover:bg-blue-800"
              >
                Accept Ticket
              </button>
            )}
            {["RESOLVED", "CLOSED"].includes(ticket.status) && (
              <button
                type="button"
                onClick={() => setReopenModal(true)}
                className="px-3 py-2 rounded-lg border border-rose-300 bg-rose-50 text-rose-700 text-sm font-semibold hover:bg-rose-100"
              >
                Reopen Ticket
              </button>
            )}
          </div>
        }
      />

      <ErrorBanner message={error} onDismiss={() => setError("")} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <StatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
              <span className="text-xs font-medium text-slate-500">{ticket.category}</span>
            </div>
            <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">{ticket.description}</p>
            {ticket.resolution_notes && (
              <div className="mt-4 p-4 rounded-lg bg-emerald-50 border border-emerald-200">
                <div className="text-xs font-semibold uppercase text-emerald-800 mb-1">Resolution Notes</div>
                <p className="text-sm text-emerald-900">{ticket.resolution_notes}</p>
              </div>
            )}
          </div>

          {isStaff && (
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Sparkles className="w-4 h-4 text-blue-700" />
                  AI Troubleshooting Assistant (Advisory)
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    type="button"
                    disabled={aiLoading}
                    onClick={() => runAIAction("summary")}
                    className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-800"
                  >
                    Summarize
                  </button>
                  <button
                    type="button"
                    disabled={aiLoading}
                    onClick={() => runAIAction("solutions")}
                    className="px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-900 text-xs font-semibold text-white"
                  >
                    Suggest Solutions
                  </button>
                  <button
                    type="button"
                    disabled={aiLoading}
                    onClick={() => runAIAction("similar")}
                    className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-800"
                  >
                    Similar Resolved
                  </button>
                </div>
              </div>

              {aiLoading && <LoadingSpinner label="Consulting Gemini AI..." />}
              {!aiLoading && aiResult && (
                <div className="p-4 rounded-lg bg-blue-50 border border-blue-200 text-sm text-slate-800 space-y-2">
                  {aiType === "summary" && (
                    <>
                      <p className="font-medium">{aiResult.summary}</p>
                      <div className="text-xs text-slate-700">Next Action: {aiResult.recommended_next_action}</div>
                    </>
                  )}
                  {aiType === "solutions" && (
                    <>
                      <div className="font-semibold">Probable Cause: {aiResult.probable_root_cause}</div>
                      <ul className="list-disc pl-5 space-y-1 text-xs">
                        {(aiResult.troubleshooting_steps || []).map((s, idx) => (
                          <li key={idx}>{s}</li>
                        ))}
                      </ul>
                    </>
                  )}
                  {aiType === "similar" && (
                    <>
                      <p className="text-xs">{aiResult.reasoning}</p>
                      {(aiResult.similar_tickets || []).map((st) => (
                        <div key={st.id} className="p-2 bg-white rounded border border-blue-100 text-xs">
                          <strong>{st.ticket_number}</strong>: {st.title} — <em>{st.resolution_notes}</em>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-4">
              <MessageSquare className="w-4 h-4" /> Discussion ({comments.length})
            </h3>

            <div className="space-y-4 mb-6">
              {comments.map((c) => (
                <div
                  key={c.id}
                  className={`p-4 rounded-lg border ${
                    c.is_internal ? "bg-amber-50 border-amber-200" : "bg-slate-50 border-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
                    <span className="font-semibold text-slate-800">
                      {c.author_detail?.full_name} ({c.author_detail?.role})
                      {c.is_internal && (
                        <span className="ml-2 px-2 py-0.5 rounded bg-amber-200 text-amber-900 font-bold">INTERNAL NOTE</span>
                      )}
                    </span>
                    <span>{formatDateTime(c.created_at)}</span>
                  </div>
                  <p className="text-sm text-slate-800 whitespace-pre-wrap">{c.body}</p>
                </div>
              ))}
              {comments.length === 0 && <p className="text-xs text-slate-500">No comments posted yet.</p>}
            </div>

            <form onSubmit={handleAddComment} className="space-y-3">
              <textarea
                rows={3}
                value={commentBody}
                onChange={(e) => setCommentBody(e.target.value)}
                placeholder="Write a reply or troubleshooting update..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
              />
              <div className="flex items-center justify-between">
                {isStaff ? (
                  <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-700">
                    <input
                      type="checkbox"
                      checked={isInternal}
                      onChange={(e) => setIsInternal(e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    Internal Staff Note (hidden from employee)
                  </label>
                ) : (
                  <span />
                )}
                <button
                  type="submit"
                  disabled={submittingComment}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold disabled:opacity-60"
                >
                  <Send className="w-4 h-4" /> Post Comment
                </button>
              </div>
            </form>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                <Paperclip className="w-4 h-4" /> Attachments ({attachments.length})
              </h3>
              <label className="cursor-pointer px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold hover:bg-slate-50">
                Upload File
                <input type="file" onChange={handleFileUpload} className="hidden" />
              </label>
            </div>
            <div className="space-y-2">
              {attachments.map((att) => (
                <div key={att.id} className="flex items-center justify-between p-3 rounded-lg border border-slate-200 text-sm">
                  <div>
                    <div className="font-medium text-slate-900">{att.original_filename}</div>
                    <div className="text-xs text-slate-500">
                      {(att.file_size / 1024).toFixed(1)} KB • Uploaded by {att.uploaded_by_detail?.full_name}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => ticketService.downloadAttachment(att.id, att.original_filename)}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded border border-slate-300 text-xs font-medium hover:bg-slate-50"
                  >
                    <Download className="w-3.5 h-3.5" /> Download
                  </button>
                </div>
              ))}
              {attachments.length === 0 && <p className="text-xs text-slate-500">No files attached.</p>}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-900">Ticket Details & SLA</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Assigned To</dt>
                <dd className="font-medium text-slate-900">{ticket.assigned_engineer_detail?.full_name || "Unassigned"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Support Team</dt>
                <dd className="font-medium text-slate-900">{ticket.support_team_detail?.name || "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Response Due</dt>
                <dd className="font-medium text-slate-900">{formatDateTime(ticket.response_deadline)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Resolution Due</dt>
                <dd className="font-medium text-slate-900">{formatDateTime(ticket.resolution_deadline)}</dd>
              </div>
              {ticket.sla && (
                <div className="pt-2 border-t border-slate-100 flex items-center gap-2 text-xs">
                  {ticket.sla.resolution_breached ? (
                    <span className="inline-flex items-center gap-1 text-red-700 font-semibold">
                      <AlertTriangle className="w-3.5 h-3.5" /> Resolution SLA Breached
                    </span>
                  ) : (
                    <span className="text-emerald-700 font-semibold">Within SLA Policy ({ticket.sla.policy_name})</span>
                  )}
                </div>
              )}
            </dl>

            {isStaff && (
              <div className="pt-3 border-t border-slate-100">
                <label className="block text-xs font-semibold uppercase text-slate-500 mb-1.5">Update Status</label>
                <select
                  value={ticket.status}
                  onChange={(e) => handleStatusChange(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>{s.replaceAll("_", " ")}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {kbArticles.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
                <BookOpen className="w-4 h-4 text-blue-700" /> Recommended KB Articles
              </h3>
              <div className="space-y-2.5">
                {kbArticles.map((art) => (
                  <div key={art.id} className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="text-xs font-semibold text-slate-900">{art.title}</div>
                    <p className="text-xs text-slate-600 mt-1 line-clamp-2">{art.summary}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
              <History className="w-4 h-4" /> Activity History
            </h3>
            <div className="space-y-3 max-h-72 overflow-y-auto">
              {history.map((h) => (
                <div key={h.id} className="text-xs border-l-2 border-blue-600 pl-3 py-0.5">
                  <div className="font-semibold text-slate-800">{h.action_type.replaceAll("_", " ")}</div>
                  <div className="text-slate-500">
                    {h.changed_by_detail?.full_name || "System"} • {formatDateTime(h.created_at)}
                  </div>
                  {h.note && <div className="text-slate-700 mt-0.5">{h.note}</div>}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <Modal open={assignModal} title="Assign Ticket" onClose={() => setAssignModal(false)}>
        <form onSubmit={handleAssignSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Support Engineer</label>
            <select
              value={selectedEngineerId}
              onChange={(e) => setSelectedEngineerId(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
            >
              <option value="">Select engineer...</option>
              {engineers.map((eng) => (
                <option key={eng.id} value={eng.id}>{eng.full_name} ({eng.email})</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setAssignModal(false)} className="px-4 py-2 text-sm rounded-lg border border-slate-300">Cancel</button>
            <button type="submit" className="px-4 py-2 text-sm rounded-lg bg-blue-700 text-white font-semibold">Assign</button>
          </div>
        </form>
      </Modal>

      <Modal open={resolveModal} title="Resolve Ticket" onClose={() => setResolveModal(false)}>
        <form onSubmit={handleResolveSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Resolution Notes</label>
            <textarea
              required
              rows={4}
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Document the root cause and fix verified..."
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setResolveModal(false)} className="px-4 py-2 text-sm rounded-lg border border-slate-300">Cancel</button>
            <button type="submit" className="px-4 py-2 text-sm rounded-lg bg-emerald-700 text-white font-semibold">Confirm Resolution</button>
          </div>
        </form>
      </Modal>

      <Modal open={reopenModal} title="Reopen Ticket" onClose={() => setReopenModal(false)}>
        <form onSubmit={handleReopenSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Reason for Reopening</label>
            <textarea
              required
              rows={3}
              value={reopenReason}
              onChange={(e) => setReopenReason(e.target.value)}
              placeholder="Explain why the issue persists..."
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setReopenModal(false)} className="px-4 py-2 text-sm rounded-lg border border-slate-300">Cancel</button>
            <button type="submit" className="px-4 py-2 text-sm rounded-lg bg-rose-700 text-white font-semibold">Reopen</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
