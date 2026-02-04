import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, CheckCircle, FileText, Download, ClipboardList } from 'lucide-react'
import StepIndicator from '../components/StepIndicator'
import GapDetailModal from '../components/GapDetailModal'
import RemediationPlanModal from '../components/RemediationPlanModal'
import './Results.css'

function Results() {
    const navigate = useNavigate()
    const [gapReport, setGapReport] = useState(null)
    const [queryResult, setQueryResult] = useState(null)
    const [loading, setLoading] = useState(true)
    const [selectedGap, setSelectedGap] = useState(null)
    const [selectedGapIndex, setSelectedGapIndex] = useState(0)
    const [activeTab, setActiveTab] = useState('rta')
    const [showRemediationPlan, setShowRemediationPlan] = useState(false)

    // Get data from session storage
    const analysisData = JSON.parse(sessionStorage.getItem('analysisData') || '{}')
    const { deviceName, standards } = analysisData

    useEffect(() => {
        // Load gap report from session storage
        const storedGapReport = sessionStorage.getItem('gapReport')
        const storedQueryResult = sessionStorage.getItem('queryResult')

        if (storedGapReport) {
            try {
                const parsed = JSON.parse(storedGapReport)
                setGapReport(parsed)
            } catch (e) {
                console.error('Failed to parse gap report:', e)
            }
        }

        if (storedQueryResult) {
            try {
                setQueryResult(JSON.parse(storedQueryResult))
            } catch (e) {
                console.error('Failed to parse query result:', e)
            }
        }

        setLoading(false)
    }, [])

    // Transform backend gap data to display format
    const transformGaps = (backendGaps) => {
        if (!backendGaps || !Array.isArray(backendGaps)) return []

        return backendGaps.map((gap, index) => ({
            id: index + 1,
            priority: gap.severity === 'critical' ? 'critical' :
                gap.severity === 'high' ? 'critical' :
                    gap.severity === 'medium' ? 'moderate' : 'passed',
            category: gap.category || 'General',
            requirement: gap.requirement || gap.fda_requirement || 'FDA Requirement',
            status: gap.evidence_found ? 'Incomplete' : 'Missing',
            fdaRequires: {
                title: gap.fda_requirement || gap.requirement,
                description: `Per FDA regulations and ${gap.category} standards:`,
                items: gap.remediation_steps?.slice(0, 2) || [],
                source: `FDA RTA Checklist, ${gap.category} Section`
            },
            youSubmitted: {
                includes: gap.evidence_found ? ['Partial documentation found'] : [],
                missing: gap.evidence_found ? ['Complete documentation'] : ['No evidence found in submission'],
                analysis: gap.evidence_found || 'No matching content was found in your uploaded documents.'
            },
            gapIdentified: {
                type: gap.evidence_found ? 'INCOMPLETE REQUIREMENT' : 'MISSING REQUIREMENT',
                description: gap.gap_description || `Your submission lacks required ${gap.category} documentation.`,
                remediation: gap.remediation_steps || ['Review FDA requirements', 'Add missing documentation'],
                timeline: gap.estimated_timeline || 'TBD',
                cost: gap.estimated_cost || 'TBD'
            }
        }))
    }

    if (loading) {
        return (
            <div className="results-page">
                <StepIndicator currentStep={3} />
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading results...</p>
                </div>
            </div>
        )
    }

    if (!gapReport) {
        return (
            <div className="results-page">
                <StepIndicator currentStep={3} />
                <div className="error-state">
                    <AlertTriangle size={48} />
                    <h2>No Results Found</h2>
                    <p>Please upload and analyze documents first.</p>
                    <button
                        className="btn btn-primary"
                        onClick={() => navigate('/upload')}
                    >
                        Start New Analysis
                    </button>
                </div>
            </div>
        )
    }

    const gaps = transformGaps(gapReport.gaps)
    const criticalGaps = gaps.filter(g => g.priority === 'critical').length
    const moderateGaps = gaps.filter(g => g.priority === 'moderate').length
    const passedGaps = gaps.filter(g => g.priority === 'passed').length
    const totalGapsCount = gapReport.total_gaps || gaps.length
    const completion = totalGapsCount > 0
        ? Math.round(((totalGapsCount - criticalGaps - moderateGaps) / totalGapsCount) * 100)
        : 100

    const getRiskLevel = () => {
        if (criticalGaps >= 2) return { level: 'HIGH', color: 'critical', confidence: 87 }
        if (criticalGaps >= 1) return { level: 'MEDIUM', color: 'moderate', confidence: 72 }
        return { level: 'LOW', color: 'passed', confidence: 95 }
    }

    const risk = getRiskLevel()

    const handleViewDetails = (gap, index) => {
        setSelectedGap(gap)
        setSelectedGapIndex(index)
    }

    const handlePreviousGap = () => {
        const actionableGaps = gaps.filter(g => g.priority !== 'passed')
        const currentIdx = actionableGaps.findIndex(g => g.id === selectedGap.id)
        if (currentIdx > 0) {
            setSelectedGap(actionableGaps[currentIdx - 1])
        }
    }

    const handleNextGap = () => {
        const actionableGaps = gaps.filter(g => g.priority !== 'passed')
        const currentIdx = actionableGaps.findIndex(g => g.id === selectedGap.id)
        if (currentIdx < actionableGaps.length - 1) {
            setSelectedGap(actionableGaps[currentIdx + 1])
        }
    }

    return (
        <div className="results-page">
            <StepIndicator currentStep={3} />

            {/* Risk Banner */}
            <div className={`risk-banner risk-${risk.color}`}>
                <AlertTriangle size={24} />
                <div>
                    <h2>RTA RISK: {risk.level}</h2>
                    <p>
                        {risk.level === 'HIGH'
                            ? 'Your submission is likely to receive a Refusal to Accept notification.'
                            : risk.level === 'MEDIUM'
                                ? 'Your submission may need additional documentation.'
                                : 'Your submission appears to meet basic FDA requirements.'
                        }
                        <br />
                        {risk.confidence}% confidence based on {criticalGaps} critical gap{criticalGaps !== 1 ? 's' : ''}
                    </p>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="stats-grid">
                <div className="stat-card">
                    <span className="stat-label">Device</span>
                    <span className="stat-value stat-device">{deviceName || 'Unknown'}</span>
                </div>
                <div className="stat-card">
                    <span className="stat-label">Gaps Detected</span>
                    <span className="stat-value stat-critical">{totalGapsCount}</span>
                </div>
                <div className="stat-card">
                    <span className="stat-label">Compliance Score</span>
                    <span className={`stat-value ${completion >= 70 ? 'stat-passed' : 'stat-critical'}`}>
                        {completion}%
                    </span>
                </div>
            </div>

            {/* Gap Table */}
            <div className="gap-table card">
                <table>
                    <thead>
                        <tr>
                            <th>Priority</th>
                            <th>Gap Category</th>
                            <th>FDA Requirement</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {gaps.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="no-gaps">
                                    <CheckCircle size={24} />
                                    No gaps detected. Your documentation appears complete.
                                </td>
                            </tr>
                        ) : (
                            gaps.map((gap, index) => (
                                <tr key={gap.id}>
                                    <td>
                                        <span className={`badge badge-${gap.priority}`}>
                                            {gap.priority.toUpperCase()}
                                        </span>
                                    </td>
                                    <td>{gap.category}</td>
                                    <td>{gap.requirement}</td>
                                    <td>
                                        <span className={`status-${gap.status.toLowerCase()}`}>
                                            {gap.status}
                                        </span>
                                    </td>
                                    <td>
                                        {gap.priority !== 'passed' ? (
                                            <button
                                                className="link-btn"
                                                onClick={() => handleViewDetails(gap, index)}
                                            >
                                                View Details →
                                            </button>
                                        ) : (
                                            '—'
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* RAG Query Result Section */}
            {queryResult && queryResult.answer && (
                <div className="tabs-section card">
                    <div className="tabs">
                        <button
                            className={`tab ${activeTab === 'rta' ? 'active' : ''}`}
                            onClick={() => setActiveTab('rta')}
                        >
                            AI Analysis
                        </button>
                        <button
                            className={`tab ${activeTab === 'citations' ? 'active' : ''}`}
                            onClick={() => setActiveTab('citations')}
                        >
                            Citations ({queryResult.citations?.length || 0})
                        </button>
                        {standards?.length > 0 && (
                            <button
                                className={`tab ${activeTab === 'standards' ? 'active' : ''}`}
                                onClick={() => setActiveTab('standards')}
                            >
                                Standards Detected
                            </button>
                        )}
                    </div>

                    <div className="tab-content">
                        {activeTab === 'rta' && (
                            <>
                                <h3>RAG Analysis Summary</h3>
                                <blockquote>
                                    {queryResult.answer}
                                    {queryResult.fallback_used && (
                                        <p className="fallback-note">
                                            ⚠️ This answer was generated with limited evidence from your documents.
                                        </p>
                                    )}
                                </blockquote>
                            </>
                        )}

                        {activeTab === 'citations' && (
                            <>
                                <h3>Source Citations</h3>
                                <div className="citations-list">
                                    {queryResult.citations?.map((citation, idx) => (
                                        <div key={idx} className="citation-item">
                                            <div className="citation-header">
                                                <FileText size={16} />
                                                <strong>Chunk {citation.chunk_id}</strong>
                                                {citation.page_number && <span>Page {citation.page_number}</span>}
                                                <span className="relevance-score">
                                                    {Math.round(citation.relevance_score * 100)}% relevant
                                                </span>
                                            </div>
                                            <p className="citation-snippet">{citation.snippet}</p>
                                        </div>
                                    )) || <p>No citations available.</p>}
                                </div>
                            </>
                        )}

                        {activeTab === 'standards' && (
                            <>
                                <h3>Regulatory Standards Detected</h3>
                                <div className="standards-list">
                                    {standards?.map((standard, idx) => (
                                        <span key={idx} className="standard-badge">{standard}</span>
                                    )) || <p>No standards detected.</p>}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* Action Buttons */}
            <div className="results-actions">
                <button
                    className="btn btn-outline"
                    onClick={() => {
                        // Create a simple text report
                        const reportText = `TraceBridge AI Gap Report
Device: ${deviceName}
Generated: ${new Date().toISOString()}
Total Gaps: ${totalGapsCount}
Risk Level: ${risk.level}

Gaps:
${gaps.map(g => `- [${g.priority.toUpperCase()}] ${g.category}: ${g.requirement} (${g.status})`).join('\n')}
            `
                        const blob = new Blob([reportText], { type: 'text/plain' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `gap-report-${deviceName?.replace(/\s+/g, '-')}.txt`
                        a.click()
                    }}
                >
                    <Download size={18} />
                    Export Report
                </button>
                <button
                    className="btn btn-secondary"
                    onClick={() => setShowRemediationPlan(true)}
                >
                    <ClipboardList size={18} />
                    View Remediation Plan
                </button>
                <button
                    className="btn btn-primary"
                    onClick={() => navigate('/upload')}
                >
                    Analyze New Document
                </button>
            </div>

            {/* Gap Detail Modal */}
            {selectedGap && (
                <GapDetailModal
                    gap={selectedGap}
                    allGaps={gaps}
                    onClose={() => setSelectedGap(null)}
                    onPrevious={handlePreviousGap}
                    onNext={handleNextGap}
                />
            )}

            {/* Remediation Plan Modal */}
            {showRemediationPlan && (
                <RemediationPlanModal onClose={() => setShowRemediationPlan(false)} />
            )}
        </div>
    )
}

export default Results
