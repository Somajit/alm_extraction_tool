import React, { useEffect, useState } from 'react'
import {
  Box,
  Checkbox,
  FormControlLabel,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { getDefects, Defect } from '../api'

type ColumnKey = keyof Defect

interface DefectsState {
  allDefects: Defect[]
  filteredDefects: Defect[]
  filters: {
    id: string
    summary: string
    status: string
  }
  visibleColumns: {
    id: boolean
    summary: boolean
    status: boolean
    priority: boolean
    project: boolean
  }
  loading: boolean
}

const DefectsTable: React.FC = () => {
  const [state, setState] = useState<DefectsState>({
    allDefects: [],
    filteredDefects: [],
    filters: { id: '', summary: '', status: '' },
    visibleColumns: { id: true, summary: true, status: true, priority: true, project: true },
    loading: true,
  })

  useEffect(() => {
    loadDefects()
  }, [])

  const loadDefects = async () => {
    try {
      const project = localStorage.getItem('project') || ''
      const res = await getDefects(project)
      setState(prev => ({
        ...prev,
        allDefects: res.data,
        filteredDefects: res.data,
        loading: false,
      }))
    } catch (err) {
      console.error('Failed to load defects:', err)
      setState(prev => ({ ...prev, loading: false }))
    }
  }

  const applyFilters = (newFilters: any) => {
    const filtered = state.allDefects.filter(defect => {
      return (
        (!newFilters.id || defect.id.toLowerCase().includes(newFilters.id.toLowerCase())) &&
        (!newFilters.summary || defect.summary.toLowerCase().includes(newFilters.summary.toLowerCase())) &&
        (!newFilters.status || defect.status.toLowerCase().includes(newFilters.status.toLowerCase()))
      )
    })
    setState(prev => ({
      ...prev,
      filters: newFilters,
      filteredDefects: filtered,
    }))
  }

  const handleFilterChange = (field: 'id' | 'summary' | 'status', value: string) => {
    applyFilters({ ...state.filters, [field]: value })
  }

  const toggleColumn = (column: keyof typeof state.visibleColumns) => {
    setState(prev => ({
      ...prev,
      visibleColumns: { ...prev.visibleColumns, [column]: !prev.visibleColumns[column] },
    }))
  }

  if (state.loading) return <Typography>Loading defects...</Typography>

  const columns: ColumnKey[] = ['id', 'summary', 'status', 'priority', 'project']

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Filters
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
          <TextField
            label="Filter by ID"
            size="small"
            value={state.filters.id}
            onChange={e => handleFilterChange('id', e.target.value)}
          />
          <TextField
            label="Filter by Summary"
            size="small"
            value={state.filters.summary}
            onChange={e => handleFilterChange('summary', e.target.value)}
          />
          <TextField
            label="Filter by Status"
            size="small"
            value={state.filters.status}
            onChange={e => handleFilterChange('status', e.target.value)}
          />
        </Box>
      </Box>

      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Visible Columns
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {columns.map(col => (
            <FormControlLabel
              key={String(col)}
              control={
                <Checkbox
                  checked={state.visibleColumns[col]}
                  onChange={() => toggleColumn(col)}
                />
              }
              label={String(col).charAt(0).toUpperCase() + String(col).slice(1)}
            />
          ))}
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              {state.visibleColumns.id && <TableCell><strong>ID</strong></TableCell>}
              {state.visibleColumns.summary && <TableCell><strong>Summary</strong></TableCell>}
              {state.visibleColumns.status && <TableCell><strong>Status</strong></TableCell>}
              {state.visibleColumns.priority && <TableCell><strong>Priority</strong></TableCell>}
              {state.visibleColumns.project && <TableCell><strong>Project</strong></TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {state.filteredDefects.map(defect => (
              <TableRow key={defect.id} hover>
                {state.visibleColumns.id && <TableCell>{defect.id}</TableCell>}
                {state.visibleColumns.summary && <TableCell>{defect.summary}</TableCell>}
                {state.visibleColumns.status && (
                  <TableCell>
                    <Box
                      sx={{
                        display: 'inline-block',
                        px: 1,
                        py: 0.5,
                        borderRadius: 1,
                        backgroundColor: defect.status === 'Open' ? '#ffebee' : '#e8f5e9',
                        color: defect.status === 'Open' ? '#c62828' : '#2e7d32',
                        fontSize: '0.85rem',
                      }}
                    >
                      {defect.status}
                    </Box>
                  </TableCell>
                )}
                {state.visibleColumns.priority && <TableCell>{defect.priority}</TableCell>}
                {state.visibleColumns.project && <TableCell>{defect.project}</TableCell>}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {state.filteredDefects.length === 0 && (
        <Box sx={{ mt: 2, p: 2, textAlign: 'center', backgroundColor: '#f5f5f5', borderRadius: 1 }}>
          <Typography>No defects found matching the selected filters.</Typography>
        </Box>
      )}

      <Box sx={{ mt: 2 }}>
        <Typography variant="body2">
          Showing {state.filteredDefects.length} of {state.allDefects.length} defects
        </Typography>
      </Box>
    </Box>
  )
}

export default DefectsTable
