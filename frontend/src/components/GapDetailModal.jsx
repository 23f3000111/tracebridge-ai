import { useState } from 'react'
import { X, ChevronLeft, ChevronRight, Check, ExternalLink, Copy } from 'lucide-react'
import './GapDetailModal.css'

function GapDetailModal({ gap, onClose, onPrevious, onNext, allGaps = [] }) {
    const [acknowledged, setAcknowledged] = useState(false)
    const [addedToPlan, setAddedToPlan] = useState(false)
    const [copied, setCopied] = useState(false)

    if (!gap) return null

    const { fdaRequires, youSubmitted, gapIdentified } = gap

    // Find current gap index
    const actionableGaps = allGaps.filter(g => g.priority !== 'passed')
    const currentIndex = actionableGaps.findIndex(g => g.id === gap.id)
    const hasPrevious = currentIndex > 0
    const hasNext = currentIndex < actionableGaps.length - 1

    const handleAcknowledge = () => {
        setAcknowledged(!acknowledged)
        // Store acknowledged gaps in session storage
        const acknowledgedGaps = JSON.parse(sessionStorage.getItem('acknowledgedGaps') || '[]')
        if (!acknowledged) {
            acknowledgedGaps.push(gap.id)
        } else {
            const idx = acknowledgedGaps.indexOf(gap.id)
            if (idx > -1) acknowledgedGaps.splice(idx, 1)
        }
        sessionStorage.setItem('acknowledgedGaps', JSON.stringify(acknowledgedGaps))
    }

    const handleAddToPlan = () => {
        setAddedToPlan(true)
        // Store remediation plan in session storage
        const remediationPlan = JSON.parse(sessionStorage.getItem('remediationPlan') || '[]')
        if (!remediationPlan.find(g => g.id === gap.id)) {
            remediationPlan.push({
                id: gap.id,
                category: gap.category,
                requirement: gap.requirement,
                priority: gap.priority,
                remediation: gapIdentified?.remediation || [],
                timeline: gapIdentified?.timeline,
                cost: gapIdentified?.cost,
                addedAt: new Date().toISOString()
            })
            sessionStorage.setItem('remediationPlan', JSON.stringify(remediationPlan))
        }

        // Show confirmation briefly
        setTimeout(() => setAddedToPlan(false), 2000)
    }

    const handleCopyRemediation = () => {
        const text = `
Gap: ${gap.category} - ${gap.requirement}
Priority: ${gap.priority.toUpperCase()}
Status: ${gap.status}

FDA Requirement:
${fdaRequires?.title}
${fdaRequires?.description}

Gap Identified:
${gapIdentified?.type}: ${gapIdentified?.description}

Remediation Steps:
${gapIdentified?.remediation?.map((step, i) => `${i + 1}. ${step}`).join('\n')}

Estimated Timeline: ${gapIdentified?.timeline || 'TBD'}
Estimated Cost: ${gapIdentified?.cost || 'TBD'}
        `.trim()

        navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const handleViewDocument = () => {
        // Get the analysis data to find document info
        const analysisData = JSON.parse(sessionStorage.getItem('analysisData') || '{}')
        if (analysisData.docIds?.length > 0) {
            alert(`Document IDs: ${analysisData.docIds.join(', ')}\n\nIn a full implementation, this would open the document viewer with the relevant section highlighted.`)
        } else {
            alert('No documents found in current session.')
        }
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className="modal-header">
                    <div className="modal-title">
                        <h2>Gap Analysis: {gap.category} - {gap.requirement.split(' ').slice(0, 3).join(' ')}</h2>
                        <span className={`badge badge-${gap.priority}`}>
                            {gap.priority.toUpperCase()}
                        </span>
                    </div>
                    <button className="close-btn" onClick={onClose} title="Close">
                        <X size={24} />
                    </button>
                </div>

                {/* Three Column Layout */}
                <div className="modal-body">
                    {/* Column 1: What FDA Requires */}
                    <div className="modal-column fda-column">
                        <h3>What FDA Requires</h3>
                        <div className="column-content">
                            <h4>{fdaRequires?.title}</h4>
                            <p>{fdaRequires?.description}</p>

                            {fdaRequires?.items && fdaRequires.items.length > 0 && (
                                <ul>
                                    {fdaRequires.items.map((item, i) => (
                                        <li key={i}>{item}</li>
                                    ))}
                                </ul>
                            )}

                            {fdaRequires?.testReports && fdaRequires.testReports.length > 0 && (
                                <>
                                    <p className="section-label">Test reports must include:</p>
                                    <ul>
                                        {fdaRequires.testReports.map((item, i) => (
                                            <li key={i}>{item}</li>
                                        ))}
                                    </ul>
                                </>
                            )}

                            <p className="source-text">
                                Source: {fdaRequires?.source}
                            </p>
                        </div>
                    </div>

                    {/* Column 2: What You Submitted */}
                    <div className="modal-column submitted-column">
                        <h3>What You Submitted</h3>
                        <div className="column-content">
                            <p>Your {gap.category} Report includes:</p>

                            {youSubmitted?.includes && youSubmitted.includes.length > 0 && (
                                <ul className="check-list">
                                    {youSubmitted.includes.map((item, i) => (
                                        <li key={i} className="check-item">✓ {item}</li>
                                    ))}
                                </ul>
                            )}

                            {youSubmitted?.missing && youSubmitted.missing.length > 0 && (
                                <ul className="missing-list">
                                    {youSubmitted.missing.map((item, i) => (
                                        <li key={i} className="missing-item">✗ {item}</li>
                                    ))}
                                </ul>
                            )}

                            {youSubmitted?.analysis && (
                                <>
                                    <p className="section-label">AI Analysis:</p>
                                    <p className="analysis-text">{youSubmitted.analysis}</p>
                                </>
                            )}

                            <button
                                className="btn btn-outline view-doc-btn"
                                onClick={handleViewDocument}
                            >
                                <ExternalLink size={16} />
                                View Submitted Document
                            </button>
                        </div>
                    </div>

                    {/* Column 3: Gap Identified */}
                    <div className="modal-column gap-column">
                        <h3>Gap Identified</h3>
                        <div className="column-content">
                            <p className={`gap-type ${gapIdentified?.type?.includes('MISSING') ? 'missing' : 'incomplete'}`}>
                                {gapIdentified?.type}:
                            </p>
                            <p>{gapIdentified?.description}</p>

                            <p className="section-label">REMEDIATION:</p>
                            <ol className="remediation-list">
                                {gapIdentified?.remediation?.map((item, i) => (
                                    <li key={i}>{item}</li>
                                ))}
                            </ol>

                            <div className="estimates">
                                <p><strong>Estimated Timeline:</strong> {gapIdentified?.timeline || 'TBD'}</p>
                                <p><strong>Estimated Cost:</strong> {gapIdentified?.cost || 'TBD'}</p>
                            </div>

                            <button
                                className="btn btn-outline copy-btn"
                                onClick={handleCopyRemediation}
                            >
                                {copied ? <Check size={16} /> : <Copy size={16} />}
                                {copied ? 'Copied!' : 'Copy Details'}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="modal-footer">
                    <label className="acknowledge-label">
                        <input
                            type="checkbox"
                            checked={acknowledged}
                            onChange={handleAcknowledge}
                        />
                        <span className={acknowledged ? 'acknowledged' : ''}>
                            {acknowledged ? '✓ Acknowledged' : 'Mark as Acknowledged'}
                        </span>
                    </label>

                    <div className="footer-actions">
                        <button
                            className="btn btn-outline"
                            onClick={onPrevious}
                            disabled={!hasPrevious}
                            title={hasPrevious ? 'Previous gap' : 'No previous gap'}
                        >
                            <ChevronLeft size={18} /> Previous
                        </button>
                        <button
                            className="btn btn-outline"
                            onClick={onNext}
                            disabled={!hasNext}
                            title={hasNext ? 'Next gap' : 'No more gaps'}
                        >
                            Next <ChevronRight size={18} />
                        </button>
                        <button
                            className="btn btn-secondary"
                            onClick={handleAddToPlan}
                            disabled={addedToPlan}
                        >
                            {addedToPlan ? (
                                <><Check size={16} /> Added!</>
                            ) : (
                                'Add to Remediation Plan'
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default GapDetailModal
