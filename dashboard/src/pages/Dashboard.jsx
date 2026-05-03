import React, { useEffect, useState } from 'react'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/stats')
      .then(r => r.json())
      .then(setStats)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading...</div>
  if (!stats) return <div className="loading">No data available</div>

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>Dashboard</h1>
      
      <div className="grid" style={{ marginBottom: '2rem' }}>
        <div className="card stat-card">
          <div className="stat-value">{stats.total_repositories}</div>
          <div className="stat-label">Repositories</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value">{stats.total_findings}</div>
          <div className="stat-label">Total Findings</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value" style={{ color: stats.critical_findings > 5 ? '#f56565' : '#4299e1' }}>
            {stats.critical_findings}
          </div>
          <div className="stat-label">Critical Issues</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value" style={{ color: '#48bb78' }}>{stats.opportunities}</div>
          <div className="stat-label">Opportunities</div>
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>Average Health Score</h2>
        <div className="health-bar">
          <div 
            className={`health-fill ${
              stats.average_health_score >= 70 ? 'health-good' :
              stats.average_health_score >= 40 ? 'health-medium' : 'health-poor'
            }`}
            style={{ width: `${stats.average_health_score}%` }}
          />
        </div>
        <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#718096' }}>
          {stats.average_health_score}/100
        </p>
      </div>
    </div>
  )
}