import { Route, Routes } from 'react-router-dom'
import RequireAccount from './components/RequireAccount'
import AppLayout from './layouts/AppLayout'
import AccountLogin from './pages/AccountLogin'
import AccountRegister from './pages/AccountRegister'
import Home from './pages/Home'
import NotFound from './pages/NotFound'
import Settings from './pages/Settings'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<AccountLogin />} />
      <Route path="/register" element={<AccountRegister />} />
      <Route element={<RequireAccount />}>
        <Route element={<AppLayout />}>
          <Route index element={<Home />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Route>
    </Routes>
  )
}

export default App
