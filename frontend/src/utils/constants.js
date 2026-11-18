export const ROLES = {
  ADMIN: "ADMIN",
  MANAGER: "MANAGER",
  ENGINEER: "ENGINEER",
  EMPLOYEE: "EMPLOYEE",
};

export const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

export const STATUSES = [
  "OPEN",
  "ASSIGNED",
  "IN_PROGRESS",
  "ON_HOLD",
  "RESOLVED",
  "CLOSED",
  "REOPENED",
];

export const CATEGORIES = [
  { value: "HARDWARE", label: "Hardware" },
  { value: "SOFTWARE", label: "Software" },
  { value: "NETWORK", label: "Network & VPN" },
  { value: "ACCESS", label: "Access & Identity" },
  { value: "EMAIL", label: "Email & Collaboration" },
  { value: "SECURITY", label: "Security Incident" },
  { value: "OTHER", label: "Other" },
];

export const PRIORITY_BADGE_STYLES = {
  LOW: "bg-slate-100 text-slate-700 border-slate-200",
  MEDIUM: "bg-sky-50 text-sky-700 border-sky-200",
  HIGH: "bg-amber-50 text-amber-700 border-amber-200",
  CRITICAL: "bg-red-50 text-red-700 border-red-200",
};

export const STATUS_BADGE_STYLES = {
  OPEN: "bg-blue-50 text-blue-700 border-blue-200",
  ASSIGNED: "bg-indigo-50 text-indigo-700 border-indigo-200",
  IN_PROGRESS: "bg-violet-50 text-violet-700 border-violet-200",
  ON_HOLD: "bg-amber-50 text-amber-700 border-amber-200",
  RESOLVED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  CLOSED: "bg-slate-100 text-slate-600 border-slate-200",
  REOPENED: "bg-rose-50 text-rose-700 border-rose-200",
};

export function formatDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
