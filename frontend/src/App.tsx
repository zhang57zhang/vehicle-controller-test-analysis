import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ProjectManager from './pages/ProjectManager'
import DataImport from './pages/DataImport'
import DataAnalysis from './pages/DataAnalysis'
import ReportGeneration from './pages/ReportGeneration'

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<ProjectManager />} />
            <Route path="/import" element={<DataImport />} />
            <Route path="/analysis" element={<DataAnalysis />} />
            <Route path="/reports" element={<ReportGeneration />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
