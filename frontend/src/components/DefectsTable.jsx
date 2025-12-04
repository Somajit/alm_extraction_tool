import React, { useEffect, useMemo, useState } from 'react'
import { Box, Paper, Table, TableHead, TableRow, TableCell, TableBody, TextField, Button, Checkbox, FormGroup, FormControlLabel } from '@mui/material'
import { getDefects } from '../api'

export default function DefectsTable({project}){
  const [defects, setDefects] = useState([])
  const [filters, setFilters] = useState({id:'', summary:'', status:''})
  const [columns, setColumns] = useState({id:true, summary:true, status:true, priority:true})

  useEffect(()=>{
    if(project) load()
  },[project])

  async function load(){
    const res = await getDefects(project)
    setDefects(res.data)
  }

  const filtered = useMemo(()=> defects.filter(d=>{
    return (!filters.id || (d.id||'').includes(filters.id)) &&
      (!filters.summary || (d.summary||'').toLowerCase().includes(filters.summary.toLowerCase())) &&
      (!filters.status || (d.status||'').toLowerCase().includes(filters.status.toLowerCase()))
  }), [defects, filters])

  return (
    <Box>
      <Paper sx={{p:2, mb:2}}>
        <TextField label="ID" value={filters.id} onChange={e=>setFilters({...filters, id: e.target.value})} sx={{mr:1}} />
        <TextField label="Summary" value={filters.summary} onChange={e=>setFilters({...filters, summary: e.target.value})} sx={{mr:1}} />
        <TextField label="Status" value={filters.status} onChange={e=>setFilters({...filters, status: e.target.value})} sx={{mr:1}} />
        <Button onClick={()=>load()}>Refresh</Button>
      </Paper>

      <Paper sx={{p:2, mb:2}}>
        <FormGroup row>
          {Object.keys(columns).map(k=> (
            <FormControlLabel key={k} control={<Checkbox checked={columns[k]} onChange={e=>setColumns({...columns, [k]: e.target.checked})} />} label={k} />
          ))}
        </FormGroup>
      </Paper>

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              {columns.id && <TableCell>ID</TableCell>}
              {columns.summary && <TableCell>Summary</TableCell>}
              {columns.status && <TableCell>Status</TableCell>}
              {columns.priority && <TableCell>Priority</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map(r=> (
              <TableRow key={r.id || Math.random()}>
                {columns.id && <TableCell>{r.id}</TableCell>}
                {columns.summary && <TableCell>{r.summary}</TableCell>}
                {columns.status && <TableCell>{r.status}</TableCell>}
                {columns.priority && <TableCell>{r.priority}</TableCell>}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  )
}
