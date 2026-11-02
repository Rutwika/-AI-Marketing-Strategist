import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import './index.css'
import { Analyze } from './pages/Analyze'
import { Landing } from './pages/Landing'
import { Main } from './pages/Main'
import { Segments } from './pages/Segments'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/app" element={<Main />} />
          <Route path="/app/analyze" element={<Analyze />} />
          <Route path="/app/segments" element={<Segments />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
