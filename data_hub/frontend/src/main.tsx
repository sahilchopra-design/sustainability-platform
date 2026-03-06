import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import App from './App.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    <Toaster
      position="bottom-right"
      toastOptions={{
        style: {
          background: '#16162a',
          color: '#e2e8f0',
          border: '1px solid #232340',
          borderRadius: '8px',
          fontSize: '14px',
        },
        success: {
          iconTheme: { primary: '#10b981', secondary: '#16162a' },
        },
        error: {
          iconTheme: { primary: '#ef4444', secondary: '#16162a' },
        },
      }}
    />
  </StrictMode>,
)
