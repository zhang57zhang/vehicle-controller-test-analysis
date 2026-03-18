import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ProjectManager from './pages/ProjectManager'
import ProjectDetail from './pages/ProjectDetail'
import DataImport from './pages/DataImport'
import DataAnalysis from './pages/DataAnalysis'
import ReportGeneration from './pages/ReportGeneration'

/**
 * 应用主组件
 * 功能：配置路由和全局设置
 */
function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<ProjectManager />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
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
