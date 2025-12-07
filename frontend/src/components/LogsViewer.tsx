import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { ScrollArea } from './ui/scroll-area'
import { Badge } from './ui/badge'
import { AlertCircle, CheckCircle, Info, XCircle, RefreshCw } from 'lucide-react'
import { Select, MenuItem, FormControl, InputLabel } from '@mui/material'

interface LogsViewerProps {
  isAdmin: boolean
}

export function LogsViewer({ isAdmin }: LogsViewerProps) {
  const [activeService, setActiveService] = useState<'backend' | 'mock-alm' | 'frontend'>('backend')
  const [logs, setLogs] = useState<string[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const [logLevel, setLogLevel] = useState<string>('all')
  const scrollRef = useRef<HTMLDivElement>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs, autoScroll])

  const fetchLogs = async (service: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/logs/${service}?lines=100`)
      const data = await response.json()
      setLogs(data.logs || [])
    } catch (error) {
      console.error('Failed to fetch logs:', error)
      setLogs([`Error fetching logs: ${error}`])
    }
  }

  const startStreaming = (service: string) => {
    stopStreaming()
    
    const url = logLevel === 'all' 
      ? `http://localhost:8000/api/logs/${service}/stream`
      : `http://localhost:8000/api/logs/${service}/stream?level=${logLevel}`
    
    const eventSource = new EventSource(url)
    
    eventSource.onmessage = (event) => {
      setLogs(prev => [...prev, event.data])
    }
    
    eventSource.onerror = () => {
      console.error('EventSource failed')
      stopStreaming()
    }
    
    eventSourceRef.current = eventSource
    setIsStreaming(true)
  }

  const stopStreaming = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsStreaming(false)
  }

  const handleServiceChange = (service: 'backend' | 'mock-alm' | 'frontend') => {
    setActiveService(service)
    stopStreaming()
    fetchLogs(service)
  }

  const handleToggleStreaming = () => {
    if (isStreaming) {
      stopStreaming()
    } else {
      startStreaming(activeService)
    }
  }

  const handleRefresh = () => {
    fetchLogs(activeService)
  }

  const getLogLevel = (line: string): 'error' | 'warning' | 'info' | 'success' => {
    if (line.includes('ERROR') || line.includes('Failed') || line.includes('failed')) return 'error'
    if (line.includes('WARNING') || line.includes('WARN')) return 'warning'
    if (line.includes('SUCCESS') || line.includes('✓')) return 'success'
    return 'info'
  }

  const getLogIcon = (level: string) => {
    switch (level) {
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />
      case 'warning': return <AlertCircle className="h-4 w-4 text-yellow-500" />
      case 'success': return <CheckCircle className="h-4 w-4 text-green-500" />
      default: return <Info className="h-4 w-4 text-blue-500" />
    }
  }

  useEffect(() => {
    if (isAdmin) {
      fetchLogs(activeService)
    }

    return () => {
      stopStreaming()
    }
  }, [isAdmin, activeService])

  if (!isAdmin) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">Admin access required to view logs.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Service Logs</CardTitle>
          <div className="flex gap-2 items-center">
            <FormControl size="small" style={{ minWidth: 120 }}>
              <InputLabel>Log Level</InputLabel>
              <Select
                value={logLevel}
                label="Log Level"
                onChange={(e) => {
                  setLogLevel(e.target.value)
                  if (isStreaming) {
                    stopStreaming()
                    setTimeout(() => startStreaming(activeService), 100)
                  }
                }}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="ERROR">Error</MenuItem>
                <MenuItem value="WARNING">Warning</MenuItem>
                <MenuItem value="INFO">Info</MenuItem>
                <MenuItem value="DEBUG">Debug</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isStreaming}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button
              variant={isStreaming ? 'destructive' : 'default'}
              size="sm"
              onClick={handleToggleStreaming}
            >
              {isStreaming ? 'Stop Stream' : 'Start Stream'}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={activeService} onValueChange={(v) => handleServiceChange(v as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="backend">
              Backend
              <Badge variant="secondary" className="ml-2">
                {logs.filter(l => l.includes('backend')).length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="mock-alm">
              Mock ALM
              <Badge variant="secondary" className="ml-2">
                {logs.filter(l => l.includes('mock')).length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="frontend">
              Frontend
              <Badge variant="secondary" className="ml-2">
                {logs.filter(l => l.includes('frontend')).length}
              </Badge>
            </TabsTrigger>
          </TabsList>

          {['backend', 'mock-alm', 'frontend'].map(service => (
            <TabsContent key={service} value={service} className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    {logs.length} lines
                  </span>
                  {isStreaming && (
                    <Badge variant="outline" className="animate-pulse">
                      Live
                    </Badge>
                  )}
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={autoScroll}
                    onChange={(e) => setAutoScroll(e.target.checked)}
                    className="rounded"
                  />
                  Auto-scroll
                </label>
              </div>
              
              <ScrollArea className="h-[500px] w-full rounded-md border bg-slate-950 p-4">
                <div ref={scrollRef} className="font-mono text-xs space-y-1">
                  {logs.length === 0 ? (
                    <p className="text-muted-foreground">No logs available</p>
                  ) : (
                    logs.map((line, index) => {
                      const level = getLogLevel(line)
                      return (
                        <div
                          key={index}
                          className="flex items-start gap-2 hover:bg-slate-900 p-1 rounded"
                        >
                          {getLogIcon(level)}
                          <span className={`flex-1 ${
                            level === 'error' ? 'text-red-400' :
                            level === 'warning' ? 'text-yellow-400' :
                            level === 'success' ? 'text-green-400' :
                            'text-slate-300'
                          }`}>
                            {line}
                          </span>
                        </div>
                      )
                    })
                  )}
                </div>
              </ScrollArea>
            </TabsContent>
          ))}
        </Tabs>
      </CardContent>
    </Card>
  )
}
