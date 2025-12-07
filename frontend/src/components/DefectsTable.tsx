import React, { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Paper,
  Typography,
  Grid,
  Divider,
  CircularProgress,
} from '@mui/material'
import { DataGrid, GridColDef, GridPaginationModel } from '@mui/x-data-grid'
import CloseIcon from '@mui/icons-material/Close'
import DownloadIcon from '@mui/icons-material/Download'
import AttachFileIcon from '@mui/icons-material/AttachFile'
import FileDownloadIcon from '@mui/icons-material/FileDownload'
import { getDefects, getDefectDetails, downloadAttachment, Defect, DefectDetails } from '../api'
import * as XLSX from 'xlsx'

interface DefectDialogState {
  open: boolean
  defect: DefectDetails | null
  loading: boolean
}

const DefectsTable: React.FC = () => {
  const [defects, setDefects] = useState<Defect[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [exporting, setExporting] = useState(false)
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 10, // Start with 10 defects initially
  })
  const [dialogState, setDialogState] = useState<DefectDialogState>({
    open: false,
    defect: null,
    loading: false,
  })

  const username = localStorage.getItem('user') || ''
  const domain = localStorage.getItem('domain') || ''
  const project = localStorage.getItem('project') || ''

  useEffect(() => {
    if (username && domain && project) {
      loadDefects()
    }
  }, [paginationModel.page, paginationModel.pageSize, username, domain, project])

  const loadDefects = async () => {
    try {
      setLoading(true)
      const startIndex = paginationModel.page * paginationModel.pageSize + 1
      
      // On first load, switch to 100 per page after loading initial 10
      if (isInitialLoad && paginationModel.pageSize === 10) {
        const response = await getDefects(
          username,
          domain,
          project,
          startIndex,
          10 // Load initial 10
        )
        setDefects(response.data.defects)
        setTotal(response.data.total)
        setIsInitialLoad(false)
        // Switch to 100 per page for subsequent loads
        setPaginationModel(prev => ({ ...prev, pageSize: 100 }))
      } else {
        const response = await getDefects(
          username,
          domain,
          project,
          startIndex,
          paginationModel.pageSize
        )
        setDefects(response.data.defects)
        setTotal(response.data.total)
      }
    } catch (error) {
      console.error('Failed to load defects:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRowDoubleClick = async (params: any) => {
    const defectId = params.row.id
    setDialogState({ open: true, defect: null, loading: true })

    try {
      const response = await getDefectDetails(username, domain, project, defectId)
      setDialogState({ open: true, defect: response.data, loading: false })
    } catch (error) {
      console.error('Failed to load defect details:', error)
      setDialogState({ open: false, defect: null, loading: false })
    }
  }

  const handleCloseDialog = () => {
    setDialogState({ open: false, defect: null, loading: false })
  }

  const handleDownloadAttachment = (attachmentId: string, filename: string) => {
    const url = downloadAttachment(username, domain, project, attachmentId, filename)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleExportToExcel = async () => {
    try {
      setExporting(true)
      
      // Fetch all defects using export_all flag (backend will fetch all matching defects)
      const response = await getDefects(
        username, 
        domain, 
        project, 
        1, 
        10000, // Large page size
        undefined, // No filter for now (can be added later)
        false, // Don't force refresh
        true // Export all flag
      )
      
      const allDefects = response.data.defects || []
      
      // Prepare data for Excel
      const excelData = allDefects.map(defect => ({
        'ID': defect.id,
        'Name': defect.name,
        'Status': defect.status,
        'Severity': defect.severity,
        'Priority': defect.priority,
        'Detected By': defect['detected-by'],
        'Assigned To': defect['assigned-to'],
        'Owner': defect.owner,
        'Created': defect['creation-time'],
        'Modified': defect['last-modified'],
        'Detected In Release': defect['detected-in-rel'],
        'Detected In Cycle': defect['detected-in-rcyc'],
        'Target Release': defect['target-rel'],
        'Target Cycle': defect['target-rcyc'],
        'Reproducible': defect.reproducible,
        'Description': defect.description,
        'Steps to Reproduce': defect['steps-to-reproduce'],
        'Expected Result': defect['expected-result'],
        'Actual Result': defect['actual-result'],
        'Resolution': defect.resolution,
        'Has Attachments': defect['has-attachments']
      }))
      
      // Create workbook and worksheet
      const wb = XLSX.utils.book_new()
      const ws = XLSX.utils.json_to_sheet(excelData)
      
      // Set column widths
      const colWidths = [
        { wch: 8 },  // ID
        { wch: 30 }, // Name
        { wch: 12 }, // Status
        { wch: 12 }, // Severity
        { wch: 12 }, // Priority
        { wch: 15 }, // Detected By
        { wch: 15 }, // Assigned To
        { wch: 15 }, // Owner
        { wch: 20 }, // Created
        { wch: 20 }, // Modified
        { wch: 20 }, // Detected In Release
        { wch: 20 }, // Detected In Cycle
        { wch: 20 }, // Target Release
        { wch: 15 }, // Target Cycle
        { wch: 12 }, // Reproducible
        { wch: 40 }, // Description
        { wch: 50 }, // Steps to Reproduce
        { wch: 50 }, // Expected Result
        { wch: 50 }, // Actual Result
        { wch: 40 }, // Resolution
        { wch: 12 }  // Has Attachments
      ]
      ws['!cols'] = colWidths
      
      XLSX.utils.book_append_sheet(wb, ws, 'Defects')
      
      // Generate file name with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
      const fileName = `Defects_${project}_${timestamp}.xlsx`
      
      // Download file
      XLSX.writeFile(wb, fileName)
      
    } catch (error) {
      console.error('Failed to export defects:', error)
      alert('Failed to export defects to Excel')
    } finally {
      setExporting(false)
    }
  }

  const columns: GridColDef[] = [
    {
      field: 'id',
      headerName: 'ID',
      width: 80,
      filterable: true,
    },
    {
      field: 'name',
      headerName: 'Name',
      width: 250,
      filterable: true,
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 100,
      filterable: true,
    },
    {
      field: 'severity',
      headerName: 'Severity',
      width: 110,
      filterable: true,
    },
    {
      field: 'priority',
      headerName: 'Priority',
      width: 100,
      filterable: true,
    },
    {
      field: 'detected-by',
      headerName: 'Detected By',
      width: 120,
      filterable: true,
    },
    {
      field: 'assigned-to',
      headerName: 'Assigned To',
      width: 120,
      filterable: true,
    },
    {
      field: 'owner',
      headerName: 'Owner',
      width: 120,
      filterable: true,
    },
    {
      field: 'creation-time',
      headerName: 'Created',
      width: 160,
      filterable: true,
    },
    {
      field: 'last-modified',
      headerName: 'Modified',
      width: 160,
      filterable: true,
    },
    {
      field: 'detected-in-rel',
      headerName: 'Detected In Release',
      width: 140,
      filterable: true,
    },
    {
      field: 'detected-in-rcyc',
      headerName: 'Detected In Cycle',
      width: 140,
      filterable: true,
    },
    {
      field: 'target-rel',
      headerName: 'Target Release',
      width: 130,
      filterable: true,
    },
    {
      field: 'target-rcyc',
      headerName: 'Target Cycle',
      width: 120,
      filterable: true,
    },
    {
      field: 'reproducible',
      headerName: 'Reproducible',
      width: 110,
      filterable: true,
    },
    {
      field: 'description',
      headerName: 'Description',
      width: 250,
      filterable: true,
      renderCell: (params: any) => (
        <Box
          sx={{
            whiteSpace: 'normal',
            wordWrap: 'break-word',
            lineHeight: 1.4,
            overflow: 'auto',
            maxHeight: '100%',
            cursor: 'text',
          }}
          title={params.value || ''}
        >
          {params.value || ''}
        </Box>
      ),
    },
    {
      field: 'steps-to-reproduce',
      headerName: 'Steps to Reproduce',
      width: 300,
      filterable: true,
      renderCell: (params: any) => (
        <Box
          sx={{
            whiteSpace: 'normal',
            wordWrap: 'break-word',
            lineHeight: 1.4,
            overflow: 'auto',
            maxHeight: '100%',
            cursor: 'text',
          }}
          title={params.value || ''}
        >
          {params.value || ''}
        </Box>
      ),
    },
    {
      field: 'expected-result',
      headerName: 'Expected Result',
      width: 300,
      filterable: true,
      renderCell: (params: any) => (
        <Box
          sx={{
            whiteSpace: 'normal',
            wordWrap: 'break-word',
            lineHeight: 1.4,
            overflow: 'auto',
            maxHeight: '100%',
            cursor: 'text',
          }}
          title={params.value || ''}
        >
          {params.value || ''}
        </Box>
      ),
    },
    {
      field: 'actual-result',
      headerName: 'Actual Result',
      width: 300,
      filterable: true,
      renderCell: (params: any) => (
        <Box
          sx={{
            whiteSpace: 'normal',
            wordWrap: 'break-word',
            lineHeight: 1.4,
            overflow: 'auto',
            maxHeight: '100%',
            cursor: 'text',
          }}
          title={params.value || ''}
        >
          {params.value || ''}
        </Box>
      ),
    },
    {
      field: 'resolution',
      headerName: 'Resolution',
      width: 250,
      filterable: true,
      renderCell: (params: any) => (
        <Box
          sx={{
            whiteSpace: 'normal',
            wordWrap: 'break-word',
            lineHeight: 1.4,
            overflow: 'auto',
            maxHeight: '100%',
            cursor: 'text',
          }}
          title={params.value || ''}
        >
          {params.value || ''}
        </Box>
      ),
    },
    {
      field: 'has-attachments',
      headerName: 'Attachments',
      width: 100,
      filterable: true,
      renderCell: (params: any) => (
        params.value === 'Y' ? <AttachFileIcon fontSize="small" color="action" /> : null
      ),
    },
  ]

  return (
    <Box sx={{ height: 'calc(100vh - 250px)', width: '100%' }}>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          startIcon={<FileDownloadIcon />}
          onClick={handleExportToExcel}
          disabled={exporting || loading || total === 0}
        >
          {exporting ? 'Exporting...' : `Export All Defects to Excel (${total})`}
        </Button>
      </Box>
      <Paper sx={{ height: 'calc(100% - 50px)', width: '100%' }}>
        <DataGrid
          rows={defects}
          columns={columns}
          pagination
          paginationMode="server"
          rowCount={total}
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          pageSizeOptions={[25, 50, 100, 200]}
          loading={loading}
          onRowDoubleClick={handleRowDoubleClick}
          disableRowSelectionOnClick
          filterMode="client"
          getRowHeight={() => 'auto'}
          sx={{
            '& .MuiDataGrid-row': {
              cursor: 'pointer',
              minHeight: '52px !important',
            },
            '& .MuiDataGrid-cell': {
              padding: '8px',
              alignItems: 'flex-start',
              paddingTop: '12px',
              whiteSpace: 'normal !important',
              wordWrap: 'break-word',
              lineHeight: '1.4',
            },
            '& .MuiDataGrid-cell:focus': {
              outline: '2px solid #1976d2',
            },
            '& .MuiDataGrid-cell:focus-within': {
              outline: '2px solid #1976d2',
            },
          }}
        />
      </Paper>

      {/* Defect Details Dialog */}
      <Dialog
        open={dialogState.open}
        onClose={handleCloseDialog}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              Defect Details: {dialogState.defect?.id || ''}
            </Typography>
            <IconButton onClick={handleCloseDialog}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {dialogState.loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
              <CircularProgress />
            </Box>
          ) : dialogState.defect ? (
            <Grid container spacing={2}>
              {/* Left Pane: JSON Viewer */}
              <Grid item xs={8}>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                  Defect Information
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    bgcolor: '#1e1e1e',
                    color: '#d4d4d4',
                    padding: 2,
                    borderRadius: 1,
                    overflow: 'auto',
                    maxHeight: '60vh',
                    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                    fontSize: '0.875rem',
                    lineHeight: 1.5,
                  }}
                >
                  {JSON.stringify(dialogState.defect, null, 2)}
                </Box>
              </Grid>

              {/* Right Pane: Attachments */}
              <Grid item xs={4}>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                  Attachments ({dialogState.defect.attachments?.length || 0})
                </Typography>
                <Divider sx={{ mb: 2 }} />
                {dialogState.defect.attachments && dialogState.defect.attachments.length > 0 ? (
                  <List>
                    {dialogState.defect.attachments.map((attachment) => (
                      <ListItem
                        key={attachment.id}
                        disablePadding
                        sx={{
                          mb: 1,
                          border: '1px solid #e0e0e0',
                          borderRadius: 1,
                        }}
                      >
                        <ListItemButton
                          onClick={() => handleDownloadAttachment(attachment.id, attachment.name)}
                        >
                          <AttachFileIcon sx={{ mr: 1 }} color="action" />
                          <ListItemText
                            primary={attachment.name}
                            secondary={
                              attachment['file-size']
                                ? `${(attachment['file-size'] / 1024).toFixed(2)} KB`
                                : 'Size unknown'
                            }
                          />
                          <DownloadIcon color="primary" />
                        </ListItemButton>
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography color="text.secondary">No attachments</Typography>
                )}
              </Grid>
            </Grid>
          ) : (
            <Typography>No data available</Typography>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  )
}

export default DefectsTable
