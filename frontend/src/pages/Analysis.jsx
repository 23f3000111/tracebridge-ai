import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, AlertCircle } from 'lucide-react'
import StepIndicator from '../components/StepIndicator'
import { generateGapReport, queryDocuments } from '../api/client'
import './Analysis.css'

function Analysis() {
    const navigate = useNavigate()
    const [progress, setProgress] = useState(0)
    const [currentStep, setCurrentStep] = useState(0)
    const [error, setError] = useState(null)
    const [analysisComplete, setAnalysisComplete] = useState(false)

    // Get data from upload page
    const analysisData = JSON.parse(sessionStorage.getItem('analysisData') || '{}')
    const { deviceName, docIds, standards, totalChunks } = analysisData

    const steps = [
        {
            label: 'Documents indexed:',
            value: `${totalChunks || 0} chunks processed`,
            status: 'pending'
        },
        {
            label: 'Standards detected:',
            value: standards?.length ? standards.slice(0, 3).join(', ') : 'Scanning...',
            status: 'pending'
        },
        {
            label: 'Querying FDA requirements database',
            status: 'pending'
        },
        {
            label: 'Cross-referencing regulatory standards',
            status: 'pending'
        },
        {
            label: 'Generating gap analysis report',
            status: 'pending'
        },
    ]

    useEffect(() => {
        // Check if we have valid data
        if (!deviceName || !docIds?.length) {
            setError('No documents found. Please upload documents first.')
            return
        }

        // Simulate initial progress while actually calling API
        const progressInterval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 85) {
                    clearInterval(progressInterval)
                    return 85
                }
                return prev + 5
            })
        }, 300)

        // Update current step based on progress
        const stepInterval = setInterval(() => {
            setCurrentStep(prev => {
                if (prev >= steps.length - 1) {
                    clearInterval(stepInterval)
                    return steps.length - 1
                }
                return prev + 1
            })
        }, 1000)

        // Actually run the analysis
        runAnalysis()

        return () => {
            clearInterval(progressInterval)
            clearInterval(stepInterval)
        }
    }, [])

    const runAnalysis = async () => {
        try {
            // First, query the documents to test RAG
            const queryResult = await queryDocuments(
                'What are the main verification and validation activities documented?',
                { deviceName, topK: 5 }
            )

            // Store query result
            sessionStorage.setItem('queryResult', JSON.stringify(queryResult))

            // Generate gap report for V&V focus area
            const gapReport = await generateGapReport(deviceName, 'V&V', docIds)

            // Store the actual gap report
            sessionStorage.setItem('gapReport', JSON.stringify(gapReport))

            // Complete the progress
            setProgress(100)
            setCurrentStep(steps.length)
            setAnalysisComplete(true)

            // Navigate to results after a short delay
            setTimeout(() => {
                navigate('/results')
            }, 800)

        } catch (err) {
            console.error('Analysis error:', err)
            setError(`Analysis failed: ${err.message}. Please try again.`)
            setProgress(0)
        }
    }

    const timeRemaining = Math.max(1, Math.ceil((100 - progress) / 15))

    if (error) {
        return (
            <div className="analysis-page">
                <StepIndicator currentStep={2} />
                <div className="analysis-content">
                    <div className="error-state">
                        <AlertCircle size={48} className="error-icon" />
                        <h2>Analysis Error</h2>
                        <p>{error}</p>
                        <button
                            className="btn btn-primary"
                            onClick={() => navigate('/upload')}
                        >
                            Back to Upload
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="analysis-page">
            <StepIndicator currentStep={2} />

            <div className="analysis-content">
                <div className="spinner"></div>

                <h1>Analyzing Your Submission...</h1>
                <p className="analysis-subtitle">
                    Processing <strong>{deviceName}</strong> documentation
                </p>

                <div className="analysis-steps">
                    {steps.map((step, index) => (
                        <div
                            key={index}
                            className={`analysis-step ${index <= currentStep ? 'active' : ''} ${index < currentStep ? 'completed' : ''}`}
                        >
                            <span className="step-icon">
                                {index < currentStep ? (
                                    <Check size={16} />
                                ) : null}
                            </span>
                            <span className="step-text">
                                {step.label}
                                {step.value && <strong> {step.value}</strong>}
                            </span>
                        </div>
                    ))}
                </div>

                <div className="progress-section">
                    <div className="progress-bar">
                        <div
                            className="progress-fill progress-fill-primary"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <p className="progress-text">
                        {analysisComplete
                            ? '✓ Analysis complete! Redirecting...'
                            : `${progress}% complete · ${timeRemaining} seconds remaining`
                        }
                    </p>
                </div>
            </div>
        </div>
    )
}

export default Analysis
