import { Check } from 'lucide-react'
import './StepIndicator.css'

function StepIndicator({ currentStep = 1 }) {
    const steps = [
        { number: 1, label: 'Upload' },
        { number: 2, label: 'Analysis' },
        { number: 3, label: 'Results' },
    ]

    return (
        <div className="step-indicator">
            {steps.map((step, index) => (
                <div key={step.number} className="step-item">
                    <div className={`step-circle ${currentStep > step.number ? 'completed' :
                            currentStep === step.number ? 'active' : ''
                        }`}>
                        {currentStep > step.number ? (
                            <Check size={16} />
                        ) : (
                            step.number
                        )}
                    </div>
                    <span className={`step-label ${currentStep >= step.number ? 'active' : ''}`}>
                        {step.label}
                    </span>
                    {index < steps.length - 1 && (
                        <div className={`step-connector ${currentStep > step.number ? 'completed' : ''}`} />
                    )}
                </div>
            ))}
        </div>
    )
}

export default StepIndicator
