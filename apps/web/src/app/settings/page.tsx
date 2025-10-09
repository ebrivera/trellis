'use client'

import { useState } from 'react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Upload, CheckCircle2, Database, Plug, User as UserIcon, Mail } from 'lucide-react'

export default function SettingsPage() {
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success'>('idle')
  const [fileName, setFileName] = useState<string>('')

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setFileName(file.name)
      setUploadStatus('uploading')
      
      // Simulate upload
      setTimeout(() => {
        setUploadStatus('success')
      }, 1500)
    }
  }

  return (
    <main className="min-h-screen px-6 pt-32 pb-20">
      <div className="w-full max-w-5xl mx-auto">
        {/* Header */}
        <header className="mb-8">
          <h1 className="mb-2 text-4xl font-bold text-white">Settings</h1>
          <p className="text-lg text-white/70">
            Manage your church data, connectors, and account preferences.
          </p>
        </header>

        <div className="space-y-6">
          {/* Church Data Section */}
          <section>
            <h2 className="mb-4 text-2xl font-semibold text-white">Church Data</h2>
            <Card padding="lg">
              <div className="space-y-6">
                {/* Current Status */}
                <div className="flex items-start justify-between pb-4 border-b border-white/10">
                  <div className="flex items-start gap-3">
                    <Database className="w-6 h-6 mt-1 text-blue-400" />
                    <div>
                      <h3 className="mb-1 text-lg font-semibold text-white">Data Status</h3>
                      <p className="text-sm text-white/60">
                        Last upload: 2 days ago
                      </p>
                      <div className="flex gap-4 mt-2 text-sm">
                        <span className="text-white/80">
                          <span className="font-bold text-white">245</span> members
                        </span>
                        <span className="text-white/80">
                          <span className="font-bold text-white">8</span> groups
                        </span>
                        <span className="text-white/80">
                          <span className="font-bold text-white">2</span> initiatives
                        </span>
                      </div>
                    </div>
                  </div>
                  <Badge variant="success">Active</Badge>
                </div>

                {/* Upload Section */}
                {/* <div>
                  <h3 className="mb-3 text-lg font-semibold text-white">
                    Upload New Data
                  </h3>
                  <p className="mb-4 text-sm text-white/60">
                    Upload a CSV or Excel file with your member list, groups, or event data.
                    Trellis will automatically detect the format and merge it with your existing data.
                  </p>

                  <div className="p-6 border-2 border-dashed rounded-2xl border-white/20 bg-white/5">
                    <input
                      type="file"
                      id="file-upload"
                      className="hidden"
                      accept=".csv,.xlsx,.xls"
                      onChange={handleFileUpload}
                      disabled={uploadStatus === 'uploading'}
                    />
                    <label
                      htmlFor="file-upload"
                      className="flex flex-col items-center gap-3 cursor-pointer"
                    >
                      {uploadStatus === 'idle' && (
                        <>
                          <Upload className="w-12 h-12 text-white/40" />
                          <div className="text-center">
                            <p className="font-medium text-white">
                              Click to upload or drag and drop
                            </p>
                            <p className="text-sm text-white/50">
                              CSV, XLSX, or XLS (max 10MB)
                            </p>
                          </div>
                          <Button variant="outline" size="sm">
                            Choose File
                          </Button>
                        </>
                      )}

                      {uploadStatus === 'uploading' && (
                        <>
                          <div className="w-12 h-12 border-4 rounded-full border-white/20 border-t-white animate-spin" />
                          <p className="font-medium text-white">
                            Uploading {fileName}...
                          </p>
                        </>
                      )}

                      {uploadStatus === 'success' && (
                        <>
                          <CheckCircle2 className="w-12 h-12 text-green-400" />
                          <div className="text-center">
                            <p className="font-medium text-white">
                              Upload successful!
                            </p>
                            <p className="text-sm text-white/60">
                              {fileName} · 245 members processed
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.preventDefault()
                              setUploadStatus('idle')
                              setFileName('')
                            }}
                          >
                            Upload Another
                          </Button>
                        </>
                      )}
                    </label>
                  </div>
                </div> */}
              </div>
            </Card>
          </section>

          {/* Connectors Section */}
          <section>
            <h2 className="mb-4 text-2xl font-semibold text-white">Connectors</h2>
            <Card padding="lg">
              <div className="space-y-4">
                <p className="text-sm text-white/60">
                  Connect Foundry to your existing tools for seamless data sync.
                </p>

                <ConnectorItem
                  name="Google Sheets"
                  description="Sync member data from Google Sheets in real-time"
                  status="coming-soon"
                />
                <ConnectorItem
                  name="Twilio"
                  description="Send SMS messages to members and groups"
                  status="coming-soon"
                />
                <ConnectorItem
                  name="Mailgun"
                  description="Send email campaigns and automated messages"
                  status="coming-soon"
                />
                <ConnectorItem
                  name="Planning Center"
                  description="Import events, services, and volunteer schedules"
                  status="coming-soon"
                />
              </div>
            </Card>
          </section>

          {/* Account Info Section */}
          <section>
            <h2 className="mb-4 text-2xl font-semibold text-white">Account Information</h2>
            <Card padding="lg">
              <div className="space-y-4">
                <div className="flex items-start gap-3 pb-4 border-b border-white/10">
                  <UserIcon className="w-5 h-5 mt-1 text-white/60" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white/60">Full Name</p>
                    <p className="text-lg text-white">Pastor John Doe</p>
                  </div>
                </div>

                <div className="flex items-start gap-3 pb-4 border-b border-white/10">
                  <Mail className="w-5 h-5 mt-1 text-white/60" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white/60">Email</p>
                    <p className="text-lg text-white">john@church.org</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Badge variant="info">Lead Pastor</Badge>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white/60">Role</p>
                  </div>
                </div>
              </div>
            </Card>
          </section>
        </div>
      </div>
    </main>
  )
}

function ConnectorItem({
  name,
  description,
  status,
}: {
  name: string
  description: string
  status: 'connected' | 'disconnected' | 'coming-soon'
}) {
  return (
    <div className="flex items-center justify-between p-4 transition-colors rounded-lg bg-white/5 hover:bg-white/10">
      <div className="flex items-start gap-3">
        <Plug className="w-5 h-5 mt-1 text-white/60" />
        <div>
          <h4 className="font-semibold text-white">{name}</h4>
          <p className="text-sm text-white/60">{description}</p>
        </div>
      </div>
      {status === 'coming-soon' && <Badge variant="default">Coming Soon</Badge>}
      {status === 'connected' && <Badge variant="success">Connected</Badge>}
      {status === 'disconnected' && <Badge variant="default">Disconnected</Badge>}
    </div>
  )
}

