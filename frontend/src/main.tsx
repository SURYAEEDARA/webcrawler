import ReactDOM from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { BrowserRouter } from 'react-router'
import { AuthProvider } from './contexts/AuthContext'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <AuthProvider>
  <BrowserRouter>
    <App />
  </BrowserRouter>,
  </AuthProvider>
)
