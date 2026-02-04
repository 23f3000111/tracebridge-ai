import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Landing from './pages/Landing'
import Upload from './pages/Upload'
import Analysis from './pages/Analysis'
import Results from './pages/Results'
import Documentation from './pages/Documentation'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/results" element={<Results />} />
            <Route path="/documentation" element={<Documentation />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
