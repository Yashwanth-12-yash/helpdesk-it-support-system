
import { Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import { AppLayout } from "./layouts/AppLayout";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import { ROLES } from "./utils/constants";

import { LoginPage } from "./pages/auth/LoginPage";
import { DashboardPage } from "./pages/dashboards/DashboardPage";
import { TicketListPage } from "./pages/tickets/TicketListPage";
import { CreateTicketPage } from "./pages/tickets/CreateTicketPage";
import { TicketDetailPage } from "./pages/tickets/TicketDetailPage";
import { DepartmentsPage } from "./pages/admin/DepartmentsPage";
import { TeamsPage } from "./pages/admin/TeamsPage";
import { UsersPage } from "./pages/admin/UsersPage";
import { SettingsPage } from "./pages/admin/SettingsPage";
import { SLAPage } from "./pages/sla/SLAPage";
import { KnowledgeBasePage } from "./pages/knowledge/KnowledgeBasePage";
import { AnalyticsPage } from "./pages/analytics/AnalyticsPage";
import { NotificationsPage } from "./pages/notifications/NotificationsPage";
import { ProfilePage } from "./pages/profile/ProfilePage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />

            <Route
              path="/tickets/mine"
              element={<TicketListPage mode="mine" />}
            />

            <Route path="/tickets/new" element={<CreateTicketPage />} />
            <Route path="/tickets/:id" element={<TicketDetailPage />} />
            <Route path="/knowledge" element={<KnowledgeBasePage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/profile" element={<ProfilePage />} />

            <Route
              element={
                <ProtectedRoute
                  allowedRoles={[
                    ROLES.ADMIN,
                    ROLES.MANAGER,
                    ROLES.ENGINEER,
                  ]}
                />
              }
            >
              <Route
                path="/tickets"
                element={<TicketListPage mode="all" />}
              />

              <Route
                path="/tickets/assigned"
                element={<TicketListPage mode="assigned" />}
              />

              <Route path="/departments" element={<DepartmentsPage />} />
              <Route path="/teams" element={<TeamsPage />} />
            </Route>

            <Route
              element={
                <ProtectedRoute
                  allowedRoles={[ROLES.ADMIN, ROLES.MANAGER]}
                />
              }
            >
              <Route path="/sla" element={<SLAPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/users" element={<UsersPage />} />
            </Route>

            <Route
              element={
                <ProtectedRoute allowedRoles={[ROLES.ADMIN]} />
              }
            >
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
}
