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
import CustomReportsPage from './pages/CustomReportsPage'
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
import AnalyticsPage from './pages/AnalyticsEnhancedPage'
import IntegrationsPage from './pages/IntegrationsPage'
import FieldOperationsPage from './pages/FieldOperationsPage'
import MobileWorkshopPage from './pages/MobileWorkshopPage'
import BusinessControlPage from './pages/BusinessControlPage'
import ProductionSchedulingPage from './pages/ProductionSchedulingPage'
import MobilePortalPage from './pages/MobilePortalPage'
import RecommendationsPage from './pages/RecommendationsPage'
import InventoryForecastPage from './pages/InventoryForecastPage'
import QualityControlPage from './pages/QualityControlPage'
import AccountingCenterPage from './pages/AccountingCenterPage'
import BranchSecurityPage from './pages/BranchSecurityPage'
import NotificationAutomationPage from './pages/NotificationAutomationEnhancedPage'
import AutomationBuilderPage from './pages/AutomationBuilderPage'
import SupplierPortalPage from './pages/SupplierPortalPage'
import RoutePlanningPage from './pages/RoutePlanningPage'
import AIDesignAssistantPage from './pages/AIDesignAssistantPage'
import ProductionGanttPage from './pages/ProductionGanttPage'
import LiveCollaborationPage from './pages/LiveCollaborationPage'
import PredictiveAnalyticsPage from './pages/PredictiveAnalyticsPage'
import TenantWorkspacePage from './pages/TenantWorkspaceEnhancedPage'
import ProtectedRoute from './components/ProtectedRoute'
import { rolesFor } from './config/roleAccess'

function workspaceRoute(path, element) {
  return <Route path={path} element={<ProtectedRoute allowedRoles={rolesFor(path)}>{element}</ProtectedRoute>} />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/supplier-portal" element={<SupplierPortalPage />} />

      <Route element={<ProtectedRoute />}>
        {workspaceRoute('/app', <DashboardPage />)}
        {workspaceRoute('/app/catalog', <CatalogPage />)}
        {workspaceRoute('/app/quotes', <QuotesPage />)}
        {workspaceRoute('/app/configurator', <QuoteConfiguratorPage />)}
        {workspaceRoute('/app/production', <ProductionPage />)}
        {workspaceRoute('/app/production-scheduling', <ProductionSchedulingPage />)}
        {workspaceRoute('/app/ai-design-assistant', <AIDesignAssistantPage />)}
        {workspaceRoute('/app/production-gantt', <ProductionGanttPage />)}
        {workspaceRoute('/app/live-collaboration', <LiveCollaborationPage />)}
        {workspaceRoute('/app/predictive-analytics', <PredictiveAnalyticsPage />)}
        {workspaceRoute('/app/tenant-workspaces', <TenantWorkspacePage />)}
        {workspaceRoute('/app/quality-control', <QualityControlPage />)}
        {workspaceRoute('/app/payment-reconciliation', <PaymentReconciliationPage />)}
        {workspaceRoute('/app/contracts', <ContractsPage />)}
        {workspaceRoute('/app/project-portal', <ProjectPortalPage />)}
        {workspaceRoute('/app/mobile-portal', <MobilePortalPage />)}
        {workspaceRoute('/app/operations', <OpsPage />)}
        {workspaceRoute('/app/security', <SecurityPage />)}
        {workspaceRoute('/app/gst', <GstPage />)}
        {workspaceRoute('/app/data-admin', <DataAdminPage />)}
        {workspaceRoute('/app/access-control', <AccessControlPage />)}
        {workspaceRoute('/app/service', <ServicePage />)}
        {workspaceRoute('/app/analytics', <AnalyticsPage />)}
        {workspaceRoute('/app/business-control', <BusinessControlPage />)}
        {workspaceRoute('/app/accounting-center', <AccountingCenterPage />)}
        {workspaceRoute('/app/branch-security', <BranchSecurityPage />)}
        {workspaceRoute('/app/notification-automation', <NotificationAutomationPage />)}
        {workspaceRoute('/app/automation-builder', <AutomationBuilderPage />)}
        {workspaceRoute('/app/route-planning', <RoutePlanningPage />)}
        {workspaceRoute('/app/integrations', <IntegrationsPage />)}
        {workspaceRoute('/app/field-operations', <FieldOperationsPage />)}
        {workspaceRoute('/app/mobile-workshop', <MobileWorkshopPage />)}
        {workspaceRoute('/app/customers', <CustomersPage />)}
        {workspaceRoute('/app/leads', <LeadsPage />)}
        {workspaceRoute('/app/client-quotes', <ClientQuotesPage />)}
        {workspaceRoute('/app/orders', <OrdersPage />)}
        {workspaceRoute('/app/inventory', <InventoryPage />)}
        {workspaceRoute('/app/inventory-forecast', <InventoryForecastPage />)}
        {workspaceRoute('/app/recommendations', <RecommendationsPage />)}
        {workspaceRoute('/app/invoices', <InvoicesPage />)}
        {workspaceRoute('/app/procurement', <ProcurementPage />)}
        {workspaceRoute('/app/reports', <CustomReportsPage />)}
        {workspaceRoute('/app/audit', <AuditPage />)}
        {workspaceRoute('/app/schedules', <SchedulesPage />)}
        {workspaceRoute('/app/warehouses', <WarehousesPage />)}
        {workspaceRoute('/app/returns', <ReturnsPage />)}
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
