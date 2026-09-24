import { Navigate, Route, Routes } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import DashboardPage from './pages/DashboardPage'
import CatalogPage from './pages/CatalogPage'
import QuotesPage from './pages/QuotesPage'
import LeadsPage from './pages/LeadsPage'
import CustomersPage from './pages/CustomersPage'
import ClientQuotesPage from './pages/ClientQuotesPage'
import OrdersPage from './pages/OrdersPage'
import InventoryPage from './pages/InventoryPage'
import InvoicesPage from './pages/InvoicesPage'
import ProcurementPage from './pages/ProcurementPage'
import ReportsPage from './pages/ReportsPage'
import AuditPage from './pages/AuditPage'
import SchedulesPage from './pages/SchedulesPage'
import WarehousesPage from './pages/WarehousesPage'
import ReturnsPage from './pages/ReturnsPage'
import QuoteConfiguratorPage from './pages/QuoteConfiguratorPage'
import ProductionPage from './pages/ProductionPage'
import PaymentReconciliationPage from './pages/PaymentReconciliationPage'
import ContractsPage from './pages/ContractsPage'
import ProjectPortalPage from './pages/ProjectPortalPage'
import OpsPage from './pages/OpsPageEnhanced'
import SecurityPage from './pages/SecurityEnhancedPage'
import GstPage from './pages/GstPage'
import DataAdminPage from './pages/DataAdminEnhancedPage'
import AccessControlPage from './pages/AccessControlPage'
import ServicePage from './pages/ServicePage'
import AnalyticsPage from './pages/AnalyticsPage'
import IntegrationsPage from './pages/IntegrationsPage'
import FieldOperationsPage from './pages/FieldOperationsPage'
import BusinessControlPage from './pages/BusinessControlPage'
import ProductionSchedulingPage from './pages/ProductionSchedulingPage'
import MobilePortalPage from './pages/MobilePortalPage'
import RecommendationsPage from './pages/RecommendationsPage'
import InventoryForecastPage from './pages/InventoryForecastPage'
import QualityControlPage from './pages/QualityControlPage'
import AccountingCenterPage from './pages/AccountingCenterPage'
import BranchSecurityPage from './pages/BranchSecurityPage'
import NotificationAutomationPage from './pages/NotificationAutomationPage'
import RoutePlanningPage from './pages/RoutePlanningPage'
import AIDesignAssistantPage from './pages/AIDesignAssistantPage'
import ProductionGanttPage from './pages/ProductionGanttPage'
import LiveCollaborationPage from './pages/LiveCollaborationPage'
import PredictiveAnalyticsPage from './pages/PredictiveAnalyticsPage'
import TenantWorkspacePage from './pages/TenantWorkspacePage'
import ProtectedRoute from './components/ProtectedRoute'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/app" element={<DashboardPage />} />
        <Route path="/app/catalog" element={<CatalogPage />} />
        <Route path="/app/quotes" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><QuotesPage /></ProtectedRoute>} />
        <Route path="/app/configurator" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><QuoteConfiguratorPage /></ProtectedRoute>} />
        <Route path="/app/production" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><ProductionPage /></ProtectedRoute>} />
        <Route path="/app/production-scheduling" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><ProductionSchedulingPage /></ProtectedRoute>} />
        <Route path="/app/ai-design-assistant" element={<AIDesignAssistantPage />} />
        <Route path="/app/production-gantt" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><ProductionGanttPage /></ProtectedRoute>} />
        <Route path="/app/live-collaboration" element={<LiveCollaborationPage />} />
        <Route path="/app/predictive-analytics" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><PredictiveAnalyticsPage /></ProtectedRoute>} />
        <Route path="/app/tenant-workspaces" element={<ProtectedRoute allowedRoles={['admin']}><TenantWorkspacePage /></ProtectedRoute>} />
        <Route path="/app/quality-control" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><QualityControlPage /></ProtectedRoute>} />
        <Route path="/app/payment-reconciliation" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'client']}><PaymentReconciliationPage /></ProtectedRoute>} />
        <Route path="/app/contracts" element={<ContractsPage />} />
        <Route path="/app/project-portal" element={<ProtectedRoute allowedRoles={['client']}><ProjectPortalPage /></ProtectedRoute>} />
        <Route path="/app/mobile-portal" element={<ProtectedRoute allowedRoles={['client']}><MobilePortalPage /></ProtectedRoute>} />
        <Route path="/app/operations" element={<ProtectedRoute allowedRoles={['admin']}><OpsPage /></ProtectedRoute>} />
        <Route path="/app/security" element={<SecurityPage />} />
        <Route path="/app/gst" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'client']}><GstPage /></ProtectedRoute>} />
        <Route path="/app/data-admin" element={<ProtectedRoute allowedRoles={['admin']}><DataAdminPage /></ProtectedRoute>} />
        <Route path="/app/access-control" element={<ProtectedRoute allowedRoles={['admin']}><AccessControlPage /></ProtectedRoute>} />
        <Route path="/app/service" element={<ServicePage />} />
        <Route path="/app/analytics" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><AnalyticsPage /></ProtectedRoute>} />
        <Route path="/app/business-control" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><BusinessControlPage /></ProtectedRoute>} />
        <Route path="/app/accounting-center" element={<ProtectedRoute allowedRoles={['admin', 'sales']}><AccountingCenterPage /></ProtectedRoute>} />
        <Route path="/app/branch-security" element={<ProtectedRoute allowedRoles={['admin']}><BranchSecurityPage /></ProtectedRoute>} />
        <Route path="/app/notification-automation" element={<ProtectedRoute allowedRoles={['admin', 'sales']}><NotificationAutomationPage /></ProtectedRoute>} />
        <Route path="/app/route-planning" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><RoutePlanningPage /></ProtectedRoute>} />
        <Route path="/app/integrations" element={<ProtectedRoute allowedRoles={['admin']}><IntegrationsPage /></ProtectedRoute>} />
        <Route path="/app/field-operations" element={<FieldOperationsPage />} />
        <Route path="/app/customers" element={<ProtectedRoute allowedRoles={['admin', 'sales']}><CustomersPage /></ProtectedRoute>} />
        <Route
          path="/app/leads"
          element={
            <ProtectedRoute allowedRoles={['admin', 'sales']}>
              <LeadsPage />
            </ProtectedRoute>
          }
        />
        <Route path="/app/client-quotes" element={<ProtectedRoute allowedRoles={['client']}><ClientQuotesPage /></ProtectedRoute>} />
        <Route path="/app/orders" element={<OrdersPage />} />
        <Route path="/app/inventory" element={<InventoryPage />} />
        <Route path="/app/inventory-forecast" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><InventoryForecastPage /></ProtectedRoute>} />
        <Route path="/app/recommendations" element={<RecommendationsPage />} />
        <Route path="/app/invoices" element={<InvoicesPage />} />
        <Route path="/app/procurement" element={<ProcurementPage />} />
        <Route path="/app/reports" element={<ProtectedRoute allowedRoles={['admin', 'sales']}><ReportsPage /></ProtectedRoute>} />
        <Route path="/app/audit" element={<ProtectedRoute allowedRoles={['admin']}><AuditPage /></ProtectedRoute>} />
        <Route path="/app/schedules" element={<SchedulesPage />} />
        <Route path="/app/warehouses" element={<WarehousesPage />} />
        <Route path="/app/returns" element={<ReturnsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
