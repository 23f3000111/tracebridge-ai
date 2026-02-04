import { useNavigate } from 'react-router-dom'
import { FileText, Search, Shield, ArrowRight, Sparkles } from 'lucide-react'
import './Landing.css'

function Landing() {
    const navigate = useNavigate()

    const features = [
        {
            icon: FileText,
            title: 'RTA Prediction',
            description: 'Know if your submission will pass the Refusal to Accept threshold',
            color: '#1a4b8c'
        },
        {
            icon: Search,
            title: 'Gap Detection',
            description: 'Automated audit against FDA RTA Checklists and eSTAR Templates',
            color: '#00b894'
        },
        {
            icon: Shield,
            title: 'Regulatory Guardrails',
            description: 'Built to IEC 62304, ISO 14971, and ISO 13485 standards',
            color: '#6c5ce7'
        }
    ]

    return (
        <div className="landing">
            {/* Hero Section */}
            <section className="hero hero-gradient">
                <div className="hero-bg-shapes">
                    <div className="shape shape-1"></div>
                    <div className="shape shape-2"></div>
                    <div className="shape shape-3"></div>
                </div>

                <div className="hero-content">
                    <div className="hero-badge animate-scale-in">
                        <Sparkles size={16} />
                        AI-Powered Regulatory Analysis
                    </div>

                    <h1 className="animate-slide-up">
                        Predict Your 510(k) Outcome
                        <span className="hero-highlight">Before You Submit</span>
                    </h1>

                    <p className="hero-subtitle animate-slide-up" style={{ animationDelay: '0.1s' }}>
                        Our RAG-powered engine analyzes your technical documentation against FDA
                        requirements and identifies missing gaps with 95% accuracy.
                    </p>

                    <div className="hero-actions animate-slide-up" style={{ animationDelay: '0.2s' }}>
                        <button
                            className="btn btn-hero"
                            onClick={() => navigate('/upload')}
                        >
                            Start Analysis
                            <ArrowRight size={18} />
                        </button>
                        <button
                            className="btn btn-hero-outline"
                            onClick={() => navigate('/documentation')}
                        >
                            View Documentation
                        </button>
                    </div>

                    <div className="hero-stats animate-slide-up" style={{ animationDelay: '0.3s' }}>
                        <div className="stat">
                            <span className="stat-number">95%</span>
                            <span className="stat-text">Accuracy</span>
                        </div>
                        <div className="stat-divider"></div>
                        <div className="stat">
                            <span className="stat-number">500+</span>
                            <span className="stat-text">Documents Analyzed</span>
                        </div>
                        <div className="stat-divider"></div>
                        <div className="stat">
                            <span className="stat-number">24hr</span>
                            <span className="stat-text">Turnaround</span>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="features">
                <div className="features-header">
                    <h2>How It Works</h2>
                    <p>Three powerful capabilities to streamline your regulatory submission</p>
                </div>

                <div className="features-grid stagger-children">
                    {features.map((feature, index) => (
                        <div key={index} className="feature-card glass-card">
                            <div className="feature-icon-wrapper" style={{ '--accent-color': feature.color }}>
                                <feature.icon size={28} strokeWidth={1.5} />
                            </div>
                            <h3>{feature.title}</h3>
                            <p>{feature.description}</p>
                            <div className="feature-hover-effect"></div>
                        </div>
                    ))}
                </div>
            </section>

            {/* CTA Section */}
            <section className="cta-section">
                <div className="cta-content glass-card">
                    <h2>Ready to Analyze Your Submission?</h2>
                    <p>Upload your documents and get instant gap analysis</p>
                    <button
                        className="btn btn-primary"
                        onClick={() => navigate('/upload')}
                    >
                        Get Started Free
                        <ArrowRight size={18} />
                    </button>
                </div>
            </section>

            {/* Disclaimer */}
            <footer className="landing-footer">
                <p className="disclaimer">
                    For demonstration purposes only. Not for regulatory submission.
                </p>
            </footer>
        </div>
    )
}

export default Landing
