import React, { useState } from 'react'
import { AppBar, Box, Button, Container, Tab, Tabs, Typography, Toolbar } from '@mui/material'
import { logout } from '../api'
import TestTree from '../components/TestTree'
import DefectsTable from '../components/DefectsTable'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} style={{ width: '100%' }}>
    {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
  </div>
)

interface HomeProps {
  onLogout: () => void
}

const HomePage: React.FC<HomeProps> = ({ onLogout }) => {
  const [tabValue, setTabValue] = useState(0)
  const user = localStorage.getItem('user') || 'User'
  const domain = localStorage.getItem('domain') || 'Domain'
  const project = localStorage.getItem('project') || 'Project'

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleLogout = async () => {
    try {
      await logout(user)
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      onLogout()
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            <img src="/logo.svg" alt="ReleaseCraft Logo" style={{ height: '50px' }} />
          </Box>
          <Typography variant="body2" sx={{ mr: 2 }}>Welcome, {user}</Typography>
          <Button color="inherit" onClick={handleLogout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ flex: 1, py: 2 }}>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1">
            Domain: <strong>{domain}</strong> | Project: <strong>{project}</strong>
          </Typography>
        </Box>

        <Tabs value={tabValue} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="TestPlan" />
          <Tab label="TestLab" />
          <Tab label="Defects" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <TestTree type="TestPlan" username={user} domain={domain} project={project} />
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <TestTree type="TestLab" username={user} domain={domain} project={project} />
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          <DefectsTable />
        </TabPanel>
      </Container>
    </Box>
  )
}

export default HomePage
