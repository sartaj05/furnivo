import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import { ModalProvider } from './context/ModalContext'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <HashRouter>
      <ModalProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ModalProvider>
    </HashRouter>
  </React.StrictMode>,
)
