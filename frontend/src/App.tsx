import { Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import Login from './pages/Login'
import NotFound from './pages/NotFound'

function App() {
  return (
    <Routes>
      <Route index element={<Login />} />
      <Route element={<AppLayout />}>
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}

export default App
