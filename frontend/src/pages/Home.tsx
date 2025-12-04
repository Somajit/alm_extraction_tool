import React, { useState } from 'react'
import { AppBar, Box, Container, Tab, Tabs, Typography, Toolbar } from '@mui/material'
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

const HomePage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0)
  const user = localStorage.getItem('user') || 'User'
  const project = localStorage.getItem('project') || 'Project'

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            ALM Extraction Tool
          </Typography>
          <Typography variant="body2">Welcome, {user}</Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ flex: 1, py: 2 }}>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1">Project: {project}</Typography>
        </Box>

        <Tabs value={tabValue} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="TestPlan" />
          <Tab label="TestLab" />
          <Tab label="Defects" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <TestTree type="TestPlan" />
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <TestTree type="TestLab" />
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          <DefectsTable />
        </TabPanel>
      </Container>
    </Box>
  )
}

export default HomePage
