import React, { useEffect, useState } from 'react'

export default function Opportunities() {
  const [opportunities, setOpportunities] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/opportunities')
      .then(r => r.json())
      .then(setOpportunities)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading opportunities...</div>

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>Opportunities</h1>
      
      {opportunities.length === 0 ? (
        <div className="card">
          <p>No opportunities identified yet. Run an analysis to discover new app ideas and feature improvements.</p>
        </div>
      ) : (
        <div className="grid">
          {opportunities.map(opp => (
            <div className="card" key={opp.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                <h3>{opp.title}</h3>
                <span className="badge badge-opportunity">{opp.type}</span>
              </div>
              <p style={{ marginBottom: '1rem', color: '#4a5568' }}>{opp.description}</p>
              {opp.related_repositories.length > 0 && (
                <div style={{ fontSize: '0.85rem', color: '#718096' }}>
                  <strong>Related repos:</strong>
                  <ul style={{ marginTop: '0.25rem' }}>
                    {opp.related_repositories.map(repo => (
                      <li key={repo}>{repo}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', fontSize: '0.85rem' }}>
                {opp.estimated_effort && (
                  <span><strong>Effort:</strong> {opp.estimated_effort}</span>
                )}
                {opp.potential_impact && (
                  <span><strong>Impact:</strong> {opp.potential_impact}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}