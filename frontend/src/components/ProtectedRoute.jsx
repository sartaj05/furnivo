import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ allowedRoles, children }) {
  const { user } = useAuth()

  if (!user) return <Navigate to="/login" replace />
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/app" replace />

  return children || <Outlet />
}
