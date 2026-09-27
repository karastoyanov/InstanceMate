import { Link, useNavigate } from 'react-router-dom'
import AccountLoginForm from '../components/AccountLoginForm'
import AuthLayout from '../layouts/AuthLayout'

function AccountLogin() {
  const navigate = useNavigate()

  return (
    <AuthLayout
      title="InstanceMate"
      subtitle="AI troubleshooting for your ServiceNow instance"
    >
      <AccountLoginForm onLoggedIn={() => navigate('/')} />
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Don't have an account?{' '}
        <Link
          to="/register"
          className="font-medium text-primary hover:underline"
        >
          Register
        </Link>
      </p>
    </AuthLayout>
  )
}

export default AccountLogin
