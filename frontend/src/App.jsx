import { Navigate, Route, Routes } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import CatalogPage from './pages/CatalogPage'
import QuotesPage from './pages/QuotesPage'
import LeadsPage from './pages/LeadsPage'
import CustomersPage from './pages/CustomersPage'
import ClientQuotesPage from './pages/ClientQuotesPage'
import OrdersPage from './pages/OrdersPage'
import ProtectedRoute from './components/ProtectedRoute'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/app" element={<DashboardPage />} />
        <Route path="/app/catalog" element={<CatalogPage />} />
        <Route path="/app/quotes" element={<ProtectedRoute allowedRoles={['admin', 'sales', 'designer']}><QuotesPage /></ProtectedRoute>} />
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
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
