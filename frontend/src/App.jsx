import { lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout, RoleGate } from "./components/layout";
import { useAuth } from "./context/AuthContext";
import { ROLES } from "./lib/roles";
import LoginPage from "./pages/LoginPage";

const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const ProjectsPage = lazy(() => import("./pages/ProjectsPage"));
const ProjectDetailPage = lazy(() => import("./pages/ProjectDetailPage"));
const ParcelsPage = lazy(() => import("./pages/ParcelsPage"));
const ParcelDetailPage = lazy(() => import("./pages/ParcelDetailPage"));
const GisMapPage = lazy(() => import("./pages/GisMapPage"));
const ProposalsPage = lazy(() => import("./pages/ProposalsPage"));
const ProposalFormPage = lazy(() => import("./pages/ProposalFormPage"));
const ProposalDetailPage = lazy(() => import("./pages/ProposalDetailPage"));
const AcquisitionsPage = lazy(() => import("./pages/AcquisitionsPage"));
const AcquisitionDetailPage = lazy(() => import("./pages/AcquisitionDetailPage"));
const WorkflowPage = lazy(() => import("./pages/WorkflowPage"));
const CompensationPage = lazy(() => import("./pages/CaseLinkedPage").then((m) => ({ default: m.CompensationPage })));
const PossessionPage = lazy(() => import("./pages/CaseLinkedPage").then((m) => ({ default: m.PossessionPage })));
const RehabilitationPage = lazy(() => import("./pages/CaseLinkedPage").then((m) => ({ default: m.RehabilitationPage })));
const ResettlementPage = lazy(() => import("./pages/CaseLinkedPage").then((m) => ({ default: m.ResettlementPage })));
const FamiliesPage = lazy(() => import("./pages/FamiliesPage"));
const FieldListPage = lazy(() => import("./pages/FieldPages").then((m) => ({ default: m.FieldListPage })));
const FieldDetailPage = lazy(() => import("./pages/FieldPages").then((m) => ({ default: m.FieldDetailPage })));
const DocumentsPage = lazy(() => import("./pages/DocumentsPage"));
const AlertsPage = lazy(() => import("./pages/AlertsNotificationsAudit").then((m) => ({ default: m.AlertsPage })));
const AnalyticsPage = lazy(() => import("./pages/AlertsNotificationsAudit").then((m) => ({ default: m.AnalyticsPage })));
const AuditPage = lazy(() => import("./pages/AlertsNotificationsAudit").then((m) => ({ default: m.AuditPage })));
const IntegrationsPage = lazy(() => import("./pages/AlertsNotificationsAudit").then((m) => ({ default: m.IntegrationsPage })));
const ModelPage = lazy(() => import("./pages/AlertsNotificationsAudit").then((m) => ({ default: m.ModelPage })));
const NotificationsPage = lazy(() => import("./pages/AlertsNotificationsAudit").then((m) => ({ default: m.NotificationsPage })));
const ReportsPage = lazy(() => import("./pages/AlertsNotificationsAudit").then((m) => ({ default: m.ReportsPage })));
const SettingsPage = lazy(() => import("./pages/AlertsNotificationsAudit").then((m) => ({ default: m.SettingsPage })));
const UsersPage = lazy(() => import("./pages/AlertsNotificationsAudit").then((m) => ({ default: m.UsersPage })));

function Protected({ children }) {
  const { user, ready } = useAuth();
  if (!ready) {
    return <div className="p-10 text-sm text-slate-500">Restoring session…</div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function Gate({ roles, children }) {
  return (
    <RoleGate roles={roles}>
      {children}
    </RoleGate>
  );
}

export default function App() {
  const officerPlus = [ROLES.ADMIN, ROLES.OFFICER, ROLES.APPROVER];
  const ops = [ROLES.ADMIN, ROLES.OFFICER];
  const field = [ROLES.ADMIN, ROLES.FIELD];
  const docs = [ROLES.ADMIN, ROLES.OFFICER, ROLES.FIELD];

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <Protected>
            <AppLayout />
          </Protected>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/projects" element={<Gate roles={officerPlus}><ProjectsPage /></Gate>} />
        <Route path="/projects/:id" element={<Gate roles={officerPlus}><ProjectDetailPage /></Gate>} />
        <Route path="/parcels" element={<ParcelsPage />} />
        <Route path="/parcels/:id" element={<ParcelDetailPage />} />
        <Route path="/map" element={<GisMapPage />} />
        <Route path="/proposals" element={<Gate roles={officerPlus}><ProposalsPage /></Gate>} />
        <Route path="/proposals/new" element={<Gate roles={ops}><ProposalFormPage /></Gate>} />
        <Route path="/proposals/:id" element={<Gate roles={officerPlus}><ProposalDetailPage /></Gate>} />
        <Route path="/acquisitions" element={<AcquisitionsPage />} />
        <Route path="/acquisitions/:id" element={<AcquisitionDetailPage />} />
        <Route path="/workflow" element={<WorkflowPage />} />
        <Route path="/compensation" element={<Gate roles={officerPlus}><CompensationPage /></Gate>} />
        <Route path="/possession" element={<Gate roles={officerPlus}><PossessionPage /></Gate>} />
        <Route path="/families" element={<Gate roles={officerPlus}><FamiliesPage /></Gate>} />
        <Route path="/rehabilitation" element={<Gate roles={officerPlus}><RehabilitationPage /></Gate>} />
        <Route path="/resettlement" element={<Gate roles={officerPlus}><ResettlementPage /></Gate>} />
        <Route path="/field" element={<Gate roles={field}><FieldListPage /></Gate>} />
        <Route path="/field/:id" element={<Gate roles={field}><FieldDetailPage /></Gate>} />
        <Route path="/documents" element={<Gate roles={docs}><DocumentsPage /></Gate>} />
        <Route path="/analytics" element={<Gate roles={officerPlus}><AnalyticsPage /></Gate>} />
        <Route path="/model" element={<Gate roles={officerPlus}><ModelPage /></Gate>} />
        <Route path="/reports" element={<Gate roles={officerPlus}><ReportsPage /></Gate>} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/integrations" element={<Gate roles={[ROLES.ADMIN]}><IntegrationsPage /></Gate>} />
        <Route path="/audit" element={<Gate roles={[ROLES.ADMIN]}><AuditPage /></Gate>} />
        <Route path="/users" element={<Gate roles={[ROLES.ADMIN]}><UsersPage /></Gate>} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

function NotFound() {
  return (
    <div className="py-16 text-center">
      <h1 className="font-serif text-2xl">Page not found</h1>
      <p className="mt-2 text-sm text-slate-600">This route is not part of the Phase 4A command center.</p>
    </div>
  );
}
