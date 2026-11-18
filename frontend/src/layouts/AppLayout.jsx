
import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  BarChart3,
  Bell,
  BookOpen,
  Building2,
  ClipboardCheck,
  LayoutDashboard,
  LifeBuoy,
  LogOut,
  Menu,
  PlusCircle,
  Settings,
  ShieldAlert,
  Ticket,
  UserCheck,
  Users,
  UsersRound,
  X,
} from "lucide-react";

import { useAuth } from "../hooks/useAuth";
import { notificationService } from "../services/domainServices";
import { ROLES } from "../utils/constants";

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    let active = true;

    const fetchUnread = async () => {
      try {
        const count = await notificationService.getUnreadCount();

        if (active) {
          setUnreadCount(count);
        }
      } catch {
        // Ignore transient notification badge errors.
      }
    };

    fetchUnread();

    const timer = setInterval(fetchUnread, 30000);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  const navItems = [
    {
      to: "/dashboard",
      label: "Dashboard",
      icon: LayoutDashboard,
      roles: [ROLES.ADMIN, ROLES.MANAGER, ROLES.ENGINEER, ROLES.EMPLOYEE],
    },
    {
      to: "/tickets/mine",
      label: "My Tickets",
      icon: Ticket,
      roles: [ROLES.ADMIN, ROLES.MANAGER, ROLES.ENGINEER, ROLES.EMPLOYEE],
    },
    {
      to: "/tickets",
      label: "All Tickets",
      icon: ClipboardCheck,
      roles: [ROLES.ADMIN, ROLES.MANAGER, ROLES.ENGINEER],
    },
    {
      to: "/tickets/new",
      label: "Create Ticket",
      icon: PlusCircle,
      roles: [ROLES.ADMIN, ROLES.MANAGER, ROLES.ENGINEER, ROLES.EMPLOYEE],
    },
    {
      to: "/tickets/assigned",
      label: "Assigned to Me",
      icon: UserCheck,
      roles: [ROLES.ADMIN, ROLES.MANAGER, ROLES.ENGINEER],
    },
    {
      to: "/departments",
      label: "Departments",
      icon: Building2,
      roles: [ROLES.ADMIN, ROLES.MANAGER, ROLES.ENGINEER],
    },
    {
      to: "/teams",
      label: "Support Teams",
      icon: UsersRound,
      roles: [ROLES.ADMIN, ROLES.MANAGER, ROLES.ENGINEER],
    },
    {
      to: "/sla",
      label: "SLA Management",
      icon: ShieldAlert,
      roles: [ROLES.ADMIN, ROLES.MANAGER],
    },
    {
      to: "/knowledge",
      label: "Knowledge Base",
      icon: BookOpen,
      roles: [ROLES.ADMIN, ROLES.MANAGER, ROLES.ENGINEER, ROLES.EMPLOYEE],
    },
    {
      to: "/analytics",
      label: "Analytics",
      icon: BarChart3,
      roles: [ROLES.ADMIN, ROLES.MANAGER],
    },
    {
      to: "/notifications",
      label: "Notifications",
      icon: Bell,
      roles: [ROLES.ADMIN, ROLES.MANAGER, ROLES.ENGINEER, ROLES.EMPLOYEE],
      badge: unreadCount,
    },
    {
      to: "/users",
      label: "User Management",
      icon: Users,
      roles: [ROLES.ADMIN, ROLES.MANAGER],
    },
    {
      to: "/settings",
      label: "Settings",
      icon: Settings,
      roles: [ROLES.ADMIN],
    },
  ].filter((item) => item.roles.includes(user?.role));

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex bg-slate-50">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-navy-900 text-slate-200 flex flex-col transition-transform duration-200 ${
          sidebarOpen
            ? "translate-x-0"
            : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="h-16 px-5 flex items-center justify-between border-b border-navy-700">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white">
              <LifeBuoy className="w-5 h-5" />
            </div>

            <div>
              <div className="text-sm font-bold text-white leading-tight">
                HelpDesk
              </div>
              <div className="text-[11px] text-slate-400">
                IT Service Portal
              </div>
            </div>
          </div>

          <button
            type="button"
            className="lg:hidden text-slate-400"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/tickets" || item.to === "/dashboard"}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-blue-700 text-white"
                      : "text-slate-300 hover:bg-navy-800 hover:text-white"
                  }`
                }
              >
                <span className="flex items-center gap-3">
                  <Icon className="w-4 h-4 shrink-0" />
                  {item.label}
                </span>

                {item.badge > 0 && (
                  <span className="px-2 py-0.5 text-[11px] font-bold rounded-full bg-blue-500 text-white">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        <div className="p-3 border-t border-navy-700">
          <button
            type="button"
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-navy-800 hover:text-white"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-20">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="hidden lg:block text-sm text-slate-500">
            Enterprise IT Support & Ticket Management
          </div>

          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => navigate("/notifications")}
              className="relative p-2 rounded-lg text-slate-600 hover:bg-slate-100"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />

              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-600" />
              )}
            </button>

            <button
              type="button"
              onClick={() => navigate("/profile")}
              className="flex items-center gap-3 pl-3 border-l border-slate-200 text-left hover:opacity-85"
            >
              <div className="w-8 h-8 rounded-full bg-navy-800 text-white flex items-center justify-center text-xs font-bold">
                {user?.first_name?.[0]}
                {user?.last_name?.[0]}
              </div>

              <div className="hidden sm:block">
                <div className="text-sm font-semibold text-slate-900 leading-tight">
                  {user?.full_name}
                </div>
                <div className="text-[11px] font-medium text-blue-700">
                  {user?.role}
                </div>
              </div>
            </button>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
