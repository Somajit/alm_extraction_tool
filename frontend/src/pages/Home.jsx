import React, { useEffect, useState } from 'react'
import { Box, AppBar, Toolbar, Typography, Tabs, Tab, Container } from '@mui/material'
import TestTree from '../components/TestTree'
import DefectsTable from '../components/DefectsTable'

function TabPanel({value, index, children}){
  return value===index ? <Box sx={{p:2}}>{children}</Box> : null
}

export default function Home(){
  const [value, setValue] = useState(0)
  const [username, setUsername] = useState('')
  const [project, setProject] = useState('')

  useEffect(()=>{
    setUsername(localStorage.getItem('alm_user') || 'User')
    setProject(localStorage.getItem('alm_project') || '')
  },[])

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{flexGrow:1}}>ALM - Extraction</Typography>
          <Typography>Welcome {username}</Typography>
        </Toolbar>
      </AppBar>
      <Container sx={{mt:3}}>
        <Tabs value={value} onChange={(e,v)=>setValue(v)}>
          <Tab label="TestPlan" />
          <Tab label="TestLab" />
          <Tab label="Defects" />
        </Tabs>

        <TabPanel value={value} index={0}>
          <TestTree type="testplan" project={project} />
        </TabPanel>
        <TabPanel value={value} index={1}>
          <TestTree type="testlab" project={project} />
        </TabPanel>
        <TabPanel value={value} index={2}>
          <DefectsTable project={project} />
        </TabPanel>
      </Container>
    </Box>
  )
}
