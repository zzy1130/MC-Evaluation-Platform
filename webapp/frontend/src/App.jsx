import { useState, useEffect } from 'react'
import { Network, Target, Play, Trash2, GitBranch, AlertTriangle, CheckCircle, Zap } from 'lucide-react'

const API_BASE = '/api'

function App() {
  const [graphInput, setGraphInput] = useState('')
  const [targetNode, setTargetNode] = useState('0')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [originalGraphHtml, setOriginalGraphHtml] = useState('')
  const [analyzedGraphHtml, setAnalyzedGraphHtml] = useState('')

  // Load default graph on mount
  useEffect(() => {
    fetch(`${API_BASE}/default-graph`)
      .then(res => res.json())
      .then(data => {
        setGraphInput(JSON.stringify(data.graph, null, 2))
        setTargetNode(String(data.target))
      })
      .catch(err => console.error('Failed to load default graph:', err))
  }, [])

  const generateNetwork = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/graph/original`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ graph: graphInput, target: parseInt(targetNode) })
      })
      const html = await response.text()
      setOriginalGraphHtml(html)
    } catch (err) {
      setError('Failed to generate network: ' + err.message)
    }
    setLoading(false)
  }

  const analyzeNetwork = async () => {
    setLoading(true)
    setError(null)
    try {
      // Get analysis results
      const analysisRes = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ graph: graphInput, target: parseInt(targetNode) })
      })
      const analysisData = await analysisRes.json()
      
      if (!analysisData.success) {
        throw new Error(analysisData.error)
      }
      setResults(analysisData)

      // Get original graph
      const originalRes = await fetch(`${API_BASE}/graph/original`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ graph: graphInput, target: parseInt(targetNode) })
      })
      setOriginalGraphHtml(await originalRes.text())

      // Get analyzed graph
      const analyzedRes = await fetch(`${API_BASE}/graph/analyzed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ graph: graphInput, target: parseInt(targetNode) })
      })
      setAnalyzedGraphHtml(await analyzedRes.text())

    } catch (err) {
      setError('Analysis failed: ' + err.message)
    }
    setLoading(false)
  }

  const clearAll = () => {
    setGraphInput('')
    setTargetNode('0')
    setResults(null)
    setOriginalGraphHtml('')
    setAnalyzedGraphHtml('')
    setError(null)
  }

  const criticalEdges = results?.results?.filter(r => r.size >= 4) || []
  const warningEdges = results?.results?.filter(r => r.size > 0 && r.size < 4) || []
  const safeEdges = results?.results?.filter(r => r.size === 0) || []

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/25">
            <GitBranch className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold gradient-text">Invariant Subset Analyzer</h1>
            <p className="text-midnight-400">Analyze network robustness and identify critical transitions</p>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-2 gap-6 h-[calc(100vh-180px)]">
        
        {/* Top Left: Input Panel */}
        <div className="glass rounded-2xl p-6 glow flex flex-col">
          <div className="flex items-center gap-2 mb-4">
            <Network className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-semibold">Graph Input</h2>
          </div>
          
          <div className="flex-1 flex flex-col gap-4">
            <div className="flex-1">
              <label className="block text-sm text-midnight-400 mb-2">
                Adjacency List (JSON format)
              </label>
              <textarea
                value={graphInput}
                onChange={(e) => setGraphInput(e.target.value)}
                className="code-editor w-full h-full bg-midnight-900/80 border border-midnight-700 rounded-xl p-4 text-midnight-100 resize-none focus:border-indigo-500 transition-colors"
                placeholder='{"0": [], "1": [0], "2": [0], ...}'
                spellCheck={false}
              />
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-red-400" />
                <label className="text-sm text-midnight-400">Target Node</label>
              </div>
              <input
                type="number"
                value={targetNode}
                onChange={(e) => setTargetNode(e.target.value)}
                className="w-24 bg-midnight-900/80 border border-midnight-700 rounded-lg px-3 py-2 text-midnight-100 focus:border-indigo-500 transition-colors"
              />
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={generateNetwork}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-midnight-700 hover:bg-midnight-600 rounded-xl font-medium transition-colors disabled:opacity-50"
              >
                <Network className="w-4 h-4" />
                Generate
              </button>
              <button
                onClick={analyzeNetwork}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-xl font-medium transition-all shadow-lg shadow-indigo-500/25 disabled:opacity-50"
              >
                <Zap className="w-4 h-4" />
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
              <button
                onClick={clearAll}
                className="px-4 py-3 bg-midnight-800 hover:bg-red-500/20 hover:text-red-400 rounded-xl transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          {error && (
            <div className="mt-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300 text-sm">
              {error}
            </div>
          )}
        </div>

        {/* Top Right: Analyzed Network */}
        <div className="glass rounded-2xl p-6 glow flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <h2 className="text-lg font-semibold">Analyzed Network</h2>
            </div>
            {results && (
              <div className="flex gap-4 text-sm">
                <span className="text-midnight-400">
                  <span className="text-red-400 font-semibold">{criticalEdges.length}</span> critical
                </span>
                <span className="text-midnight-400">
                  <span className="text-amber-400 font-semibold">{warningEdges.length}</span> warning
                </span>
                <span className="text-midnight-400">
                  <span className="text-green-400 font-semibold">{safeEdges.length}</span> safe
                </span>
              </div>
            )}
          </div>
          <div className="flex-1 bg-midnight-900/50 rounded-xl overflow-hidden relative">
            {analyzedGraphHtml ? (
              <iframe
                srcDoc={analyzedGraphHtml}
                className="pyvis-frame"
                title="Analyzed Network"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center text-midnight-500">
                <div className="text-center">
                  <Network className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>Click "Analyze" to visualize the network</p>
                  <p className="text-sm mt-2 text-midnight-600">Red edges indicate critical transitions</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Left: Original Network */}
        <div className="glass rounded-2xl p-6 glow flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-cyan-400" />
              <h2 className="text-lg font-semibold">Original Network</h2>
            </div>
            {results && (
              <div className="text-sm text-midnight-400">
                {results.node_count} nodes · {results.edge_count} edges
              </div>
            )}
          </div>
          <div className="flex-1 bg-midnight-900/50 rounded-xl overflow-hidden relative">
            {originalGraphHtml ? (
              <iframe
                srcDoc={originalGraphHtml}
                className="pyvis-frame"
                title="Original Network"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center text-midnight-500">
                <div className="text-center">
                  <GitBranch className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>Click "Generate" or "Analyze" to see the network</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Right: Results Table */}
        <div className="glass rounded-2xl p-6 glow flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <h2 className="text-lg font-semibold">Invariant Subset Analysis</h2>
            </div>
            {results && (
              <div className="text-xs text-midnight-400 font-mono">
                Robustness = 1 - |invariant| / (n-1)
              </div>
            )}
          </div>
          <div className="flex-1 bg-midnight-900/50 rounded-xl overflow-hidden">
            {results?.results ? (
              <div className="h-full overflow-auto">
                <table className="results-table">
                  <thead className="sticky top-0">
                    <tr>
                      <th>Transition</th>
                      <th>Invariant Subset</th>
                      <th>Robustness</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.results.map((row, idx) => (
                      <tr
                        key={idx}
                        className={
                          row.size >= 4 ? 'row-critical' :
                          row.size > 0 ? 'row-warning' : 'row-normal'
                        }
                      >
                        <td className="font-mono text-midnight-200">
                          ({row.edge[0]} → {row.edge[1]})
                        </td>
                        <td className="font-mono">
                          {row.size > 0 ? (
                            <span className="text-red-400">
                              {'{' + row.invariant_subset.join(', ') + '}'}
                            </span>
                          ) : (
                            <span className="text-midnight-500">∅</span>
                          )}
                        </td>
                        <td>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-2 bg-midnight-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${
                                  row.robustness >= 0.9 ? 'bg-green-500' :
                                  row.robustness >= 0.7 ? 'bg-amber-500' : 'bg-red-500'
                                }`}
                                style={{ width: `${row.robustness * 100}%` }}
                              />
                            </div>
                            <span className={`font-mono text-sm ${
                              row.robustness >= 0.9 ? 'text-green-400' :
                              row.robustness >= 0.7 ? 'text-amber-400' : 'text-red-400'
                            }`}>
                              {row.robustness.toFixed(3)}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-midnight-500">
                <div className="text-center">
                  <CheckCircle className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>Analysis results will appear here</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

