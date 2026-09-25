import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ROLE_HOME } from '../config/roleAccess'

export default function ProtectedRoute({ allowedRoles, children }) {
  const { user } = useAuth()

  if (!user) return <Navigate to="/login" replace />
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to={ROLE_HOME[user.role] || '/app'} replace />

  return children || <Outlet />
}
