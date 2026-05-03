import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

export default function Repositories() {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/repos')
      .then(r => r.json())
      .then(setRepos)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading repositories...</div>

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>Repositories</h1>
      
      <table className="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Language</th>
            <th>Stars</th>
            <th>Issues</th>
            <th>Health</th>
            <th>Last Analyzed</th>
          </tr>
        </thead>
        <tbody>
          {repos.map(repo => (
            <tr key={repo.id}>
              <td>
                <a href={repo.html_url} target="_blank" rel="noopener noreferrer">
                  {repo.full_name}
                </a>
              </td>
              <td>{repo.language || 'Unknown'}</td>
              <td>{repo.stars}</td>
              <td>{repo.open_issues}</td>
              <td>
                {repo.health_score !== null ? (
                  <div>
                    <div className="health-bar">
                      <div 
                        className={`health-fill ${
                          repo.health_score >= 70 ? 'health-good' :
                          repo.health_score >= 40 ? 'health-medium' : 'health-poor'
                        }`}
                        style={{ width: `${repo.health_score}%` }}
                      />
                    </div>
                    <span style={{ fontSize: '0.8rem' }}>{Math.round(repo.health_score)}%</span>
                  </div>
                ) : 'Not analyzed'}
              </td>
              <td>
                {repo.last_analyzed ? new Date(repo.last_analyzed).toLocaleDateString() : 'Never'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}