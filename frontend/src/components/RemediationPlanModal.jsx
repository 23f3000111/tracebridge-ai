import { useState } from 'react'
import { X, CheckCircle, Calendar, DollarSign, AlertCircle } from 'lucide-react'
import './RemediationPlanModal.css'

function RemediationPlanModal({ onClose }) {
    const [plan, setPlan] = useState(() => {
        return JSON.parse(sessionStorage.getItem('remediationPlan') || '[]')
    })
    
    const handleClearPlan = () => {
        if (window.confirm('Are you sure you want to clear the entire remediation plan?')) {
            sessionStorage.removeItem('remediationPlan')
            setPlan([])
        }
    }
    
    const handleRemoveItem = (id) => {
        const updated = plan.filter(item => item.id !== id)
        sessionStorage.setItem('remediationPlan', JSON.stringify(updated))
        setPlan(updated)
    }
    
    const handleExportPlan = () => {
        const text = `REMEDIATION PLAN
Generated: ${new Date().toISOString()}

${plan.map((item, idx) => `
${idx + 1}. ${item.category} - ${item.requirement}
   Priority: ${item.priority.toUpperCase()}
   
   Remediation Steps:
   ${item.remediation.map((step, i) => `   ${i + 1}. ${step}`).join('\n')}
   
   Timeline: ${item.timeline || 'TBD'}
   Cost: ${item.cost || 'TBD'}
`).join('\n---\n')}

Total Items: ${plan.length}
Critical: ${plan.filter(i => i.priority === 'critical').length}
Moderate: ${plan.filter(i => i.priority === 'moderate').length}
        `.trim()
        
        const blob = new Blob([text], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `remediation-plan-${new Date().toISOString().split('T')[0]}.txt`
        a.click()
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="remediation-modal" onClick={(e) => e.stopPropagation()}>
                <div className="remediation-header">
                    <h2>Remediation Plan ({plan.length} items)</h2>
                    <button className="close-btn" onClick={onClose}>
                        <X size={24} />
                    </button>
                </div>
                
                <div className="remediation-body">
                    {plan.length === 0 ? (
                        <div className="empty-plan">
                            <AlertCircle size={48} />
                            <h3>No Items in Plan</h3>
                            <p>Click "Add to Remediation Plan" in gap details to build your action plan.</p>
                        </div>
                    ) : (
                        <div className="plan-items">
                            {plan.map((item, idx) => (
                                <div key={item.id} className="plan-item">
                                    <div className="plan-item-header">
                                        <div className="plan-item-title">
                                            <span className="plan-number">{idx + 1}</span>
                                            <div>
                                                <h4>{item.category} - {item.requirement}</h4>
                                                <span className={`badge badge-${item.priority}`}>
                                                    {item.priority.toUpperCase()}
                                                </span>
                                            </div>
                                        </div>
                                        <button 
                                            className="remove-item-btn"
                                            onClick={() => handleRemoveItem(item.id)}
                                            title="Remove from plan"
                                        >
                                            <X size={18} />
                                        </button>
                                    </div>
                                    
                                    <div className="plan-item-content">
                                        <div className="plan-section">
                                            <strong>Remediation Steps:</strong>
                                            <ol>
                                                {item.remediation.map((step, i) => (
                                                    <li key={i}>{step}</li>
                                                ))}
                                            </ol>
                                        </div>
                                        
                                        <div className="plan-meta">
                                            <span className="meta-item">
                                                <Calendar size={16} />
                                                {item.timeline || 'TBD'}
                                            </span>
                                            <span className="meta-item">
                                                <DollarSign size={16} />
                                                {item.cost || 'TBD'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                
                {plan.length > 0 && (
                    <div className="remediation-footer">
                        <button 
                            className="btn btn-outline"
                            onClick={handleClearPlan}
                        >
                            Clear All
                        </button>
                        <button 
                            className="btn btn-primary"
                            onClick={handleExportPlan}
                        >
                            Export Plan
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}

export default RemediationPlanModal
