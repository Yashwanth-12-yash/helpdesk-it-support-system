import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, CheckCheck } from "lucide-react";
import { notificationService } from "../../services/domainServices";
import { getErrorMessage } from "../../services/api";
import { formatDateTime } from "../../utils/constants";
import { EmptyState, ErrorBanner, LoadingSpinner, PageHeader } from "../../components/common/UIPrimitives";

export function NotificationsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await notificationService.list({ page_size: 50 });
      setItems(res.results || []);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load notifications."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleMarkRead = async (item) => {
    try {
      if (!item.is_read) {
        await notificationService.markRead(item.id);
      }
      if (item.ticket) {
        navigate(`/tickets/${item.ticket}`);
      } else {
        await load();
      }
    } catch (err) {
      setError(getErrorMessage(err, "Failed to update notification."));
    }
  };

  const handleMarkAll = async () => {
    try {
      await notificationService.markAllRead();
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to mark all notifications as read."));
    }
  };

  return (
    <div className="max-w-4xl">
      <PageHeader
        title="Notifications"
        subtitle="Real-time alerts for ticket assignments, comments, and SLA deadlines."
        actions={
          <button
            type="button"
            onClick={handleMarkAll}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 bg-white text-sm font-semibold hover:bg-slate-50"
          >
            <CheckCheck className="w-4 h-4" /> Mark All Read
          </button>
        }
      />

      <ErrorBanner message={error} onDismiss={() => setError("")} />

      {loading ? (
        <LoadingSpinner />
      ) : items.length === 0 ? (
        <EmptyState title="You're all caught up" description="No notifications at this time." />
      ) : (
        <div className="space-y-3">
          {items.map((n) => (
            <div
              key={n.id}
              onClick={() => handleMarkRead(n)}
              className={`p-4 rounded-xl border cursor-pointer transition-colors flex items-start justify-between gap-4 ${
                n.is_read ? "bg-white border-slate-200" : "bg-blue-50/70 border-blue-200"
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${n.is_read ? "bg-slate-100 text-slate-500" : "bg-blue-700 text-white"}`}>
                  <Bell className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-900">{n.title}</div>
                  <p className="text-xs text-slate-600 mt-1">{n.message}</p>
                  <div className="text-[11px] text-slate-400 mt-1.5">{formatDateTime(n.created_at)}</div>
                </div>
              </div>
              {!n.is_read && <span className="w-2.5 h-2.5 rounded-full bg-blue-700 shrink-0 mt-1.5" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
