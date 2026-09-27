import { Link, useNavigate } from 'react-router-dom'
import AccountRegisterForm from '../components/AccountRegisterForm'
import AuthLayout from '../layouts/AuthLayout'

function AccountRegister() {
  const navigate = useNavigate()

  return (
    <AuthLayout
      title="Create your account"
      subtitle="One account, connect any number of ServiceNow instances"
    >
      <AccountRegisterForm onRegistered={() => navigate('/')} />
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  )
}

export default AccountRegister
