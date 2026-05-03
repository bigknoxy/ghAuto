import React, { useEffect, useState } from 'react'

export default function Admin() {
  const [config, setConfig] = useState({
    github_username: '',
    schedule_interval: 24,
    dashboard_port: 3000,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/admin/config')
      .then(r => r.json())
      .then(setConfig)
      .finally(() => setLoading(false))
  }, [])

  const handleChange = (key, value) => {
    setConfig({ ...config, [key]: value })
  }

  const saveConfig = async () => {
    await fetch('/api/admin/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    alert('Configuration saved!')
  }

  if (loading) return <div className="loading">Loading...</div>

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>Admin Settings</h1>
      
      <div className="card" style={{ maxWidth: '600px' }}>
        <h2>GitHub Configuration</h2>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>
            GitHub Username
          </label>
          <input
            type="text"
            value={config.github_username}
            onChange={e => handleChange('github_username', e.target.value)}
            style={{ width: '100%', padding: '0.5rem' }}
          />
        </div>
        
        <h2 style={{ marginTop: '1.5rem' }}>Schedule</h2>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>
            Analysis Interval (hours)
          </label>
          <input
            type="number"
            value={config.schedule_interval}
            onChange={e => handleChange('schedule_interval', parseInt(e.target.value))}
            style={{ width: '100%', padding: '0.5rem' }}
          />
        </div>
        
        <h2 style={{ marginTop: '1.5rem' }}>Dashboard</h2>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>
            Port
          </label>
          <input
            type="number"
            value={config.dashboard_port}
            onChange={e => handleChange('dashboard_port', parseInt(e.target.value))}
            style={{ width: '100%', padding: '0.5rem' }}
          />
        </div>
        
        <button className="btn btn-primary" onClick={saveConfig}>
          Save Configuration
        </button>
      </div>
    </div>
  )
}