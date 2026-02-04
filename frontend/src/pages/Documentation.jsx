import { FileText, Code, Zap, Shield } from 'lucide-react'
import './Documentation.css'

function Documentation() {
    return (
        <div className="docs-page">
            <div className="docs-hero">
                <h1>Documentation</h1>
                <p>Learn how to integrate TraceBridge AI into your regulatory workflow</p>
            </div>

            <div className="docs-content">
                <section className="docs-section">
                    <h2><Zap size={24} /> Quick Start</h2>
                    <div className="code-block">
                        <pre>{`# Upload a document
curl -X POST http://localhost:8000/upload \\
  -F "file=@document.pdf" \\
  -F "device_name=My Device" \\
  -F "doc_type=vnv"

# Generate gap report
curl -X POST http://localhost:8000/gap-report \\
  -H "Content-Type: application/json" \\
  -d '{"device_name": "My Device", "focus_area": "V&V"}'`}</pre>
                    </div>
                </section>

                <section className="docs-section">
                    <h2><FileText size={24} /> API Endpoints</h2>
                    <div className="endpoint-grid">
                        <div className="endpoint-card">
                            <span className="method post">POST</span>
                            <code>/upload</code>
                            <p>Upload and index documents</p>
                        </div>
                        <div className="endpoint-card">
                            <span className="method get">GET</span>
                            <code>/documents</code>
                            <p>List all indexed documents</p>
                        </div>
                        <div className="endpoint-card">
                            <span className="method post">POST</span>
                            <code>/query</code>
                            <p>RAG query with citations</p>
                        </div>
                        <div className="endpoint-card">
                            <span className="method post">POST</span>
                            <code>/gap-report</code>
                            <p>Generate gap analysis</p>
                        </div>
                    </div>
                </section>

                <section className="docs-section">
                    <h2><Shield size={24} /> Supported Standards</h2>
                    <div className="standards-grid">
                        <div className="standard-badge">ISO 10993</div>
                        <div className="standard-badge">IEC 62304</div>
                        <div className="standard-badge">ISO 14971</div>
                        <div className="standard-badge">ISO 13485</div>
                        <div className="standard-badge">FDA 21 CFR</div>
                        <div className="standard-badge">IEC 60601</div>
                    </div>
                </section>
            </div>
        </div>
    )
}

export default Documentation
