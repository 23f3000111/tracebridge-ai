import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Upload as UploadIcon, X, AlertCircle, CheckCircle } from 'lucide-react'
import StepIndicator from '../components/StepIndicator'
import { uploadDocument } from '../api/client'
import './Upload.css'

function Upload() {
    const navigate = useNavigate()
    const [deviceName, setDeviceName] = useState('')
    const [deviceClass, setDeviceClass] = useState('Class II')
    const [deviceDescription, setDeviceDescription] = useState('')
    const [files, setFiles] = useState({ vnv: null, biocomp: null })
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState(null)
    const [uploadStatus, setUploadStatus] = useState({ vnv: null, biocomp: null })

    const handleFileChange = (type, file) => {
        setFiles(prev => ({ ...prev, [type]: file }))
        setUploadStatus(prev => ({ ...prev, [type]: null }))
    }

    const handleRemoveFile = (type) => {
        setFiles(prev => ({ ...prev, [type]: null }))
        setUploadStatus(prev => ({ ...prev, [type]: null }))
    }

    const handleDrop = (type) => (e) => {
        e.preventDefault()
        const file = e.dataTransfer.files[0]
        if (file && (file.type === 'application/pdf' || file.name.endsWith('.docx'))) {
            handleFileChange(type, file)
        }
    }

    const handleSubmit = async () => {
        if (!deviceName.trim()) {
            setError('Please provide a device name')
            return
        }

        if (!files.vnv && !files.biocomp) {
            setError('Please upload at least one document')
            return
        }

        setUploading(true)
        setError(null)

        const uploadResults = []
        const detectedStandards = []

        try {
            // Upload V&V document if provided
            if (files.vnv) {
                setUploadStatus(prev => ({ ...prev, vnv: 'uploading' }))
                try {
                    const result = await uploadDocument(files.vnv, deviceName, 'vnv')
                    uploadResults.push(result)
                    if (result.standards_detected) {
                        detectedStandards.push(...result.standards_detected)
                    }
                    setUploadStatus(prev => ({ ...prev, vnv: 'success' }))
                } catch (err) {
                    setUploadStatus(prev => ({ ...prev, vnv: 'error' }))
                    throw new Error(`V&V upload failed: ${err.message}`)
                }
            }

            // Upload Biocompatibility document if provided
            if (files.biocomp) {
                setUploadStatus(prev => ({ ...prev, biocomp: 'uploading' }))
                try {
                    const result = await uploadDocument(files.biocomp, deviceName, 'biocompatibility')
                    uploadResults.push(result)
                    if (result.standards_detected) {
                        detectedStandards.push(...result.standards_detected)
                    }
                    setUploadStatus(prev => ({ ...prev, biocomp: 'success' }))
                } catch (err) {
                    setUploadStatus(prev => ({ ...prev, biocomp: 'error' }))
                    throw new Error(`Biocompatibility upload failed: ${err.message}`)
                }
            }

            // Store data for analysis page
            const analysisData = {
                deviceName,
                deviceClass,
                deviceDescription,
                docIds: uploadResults.map(r => r.doc_id),
                totalChunks: uploadResults.reduce((sum, r) => sum + r.chunks_indexed, 0),
                standards: [...new Set(detectedStandards)],
                uploadedAt: new Date().toISOString()
            }

            sessionStorage.setItem('analysisData', JSON.stringify(analysisData))

            // Navigate to analysis page
            navigate('/analysis')

        } catch (err) {
            setError(err.message || 'Upload failed. Please try again.')
        } finally {
            setUploading(false)
        }
    }

    const getStatusIcon = (status) => {
        if (status === 'uploading') return <div className="mini-spinner" />
        if (status === 'success') return <CheckCircle size={18} className="status-success" />
        if (status === 'error') return <AlertCircle size={18} className="status-error" />
        return null
    }

    return (
        <div className="upload-page">
            <StepIndicator currentStep={1} />

            <div className="upload-container">
                {/* Step 1: Device Description */}
                <div className="upload-section card">
                    <h2>Step 1: Device Description</h2>

                    <div className="form-group">
                        <label className="form-label">Device Name *</label>
                        <input
                            type="text"
                            className="form-input"
                            placeholder="e.g., CardioSense Pro Wearable ECG Monitor"
                            value={deviceName}
                            onChange={(e) => setDeviceName(e.target.value)}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Device Class</label>
                        <select
                            className="form-select"
                            value={deviceClass}
                            onChange={(e) => setDeviceClass(e.target.value)}
                        >
                            <option value="Class I">Class I</option>
                            <option value="Class II">Class II</option>
                            <option value="Class III">Class III</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Device Description</label>
                        <textarea
                            className="form-textarea"
                            placeholder="Describe your device's intended use, technology, and patient contact..."
                            value={deviceDescription}
                            onChange={(e) => setDeviceDescription(e.target.value)}
                            rows={4}
                        />
                    </div>

                    <p className="hint-text">
                        We'll extract your Product Code from this description
                    </p>
                </div>

                {/* Step 2: Upload Documents */}
                <div className="upload-section card">
                    <h2>Step 2: Upload Submission Documents</h2>

                    {/* V&V Documentation Upload */}
                    <div
                        className={`file-upload-card ${files.vnv ? 'has-file' : ''} ${uploadStatus.vnv === 'error' ? 'has-error' : ''}`}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={handleDrop('vnv')}
                    >
                        {files.vnv ? (
                            <div className="file-info">
                                <FileText size={32} className="file-icon" />
                                <div className="file-details">
                                    <strong>V&V Documentation</strong>
                                    <span>{files.vnv.name} ({(files.vnv.size / 1024 / 1024).toFixed(2)} MB)</span>
                                </div>
                                {getStatusIcon(uploadStatus.vnv)}
                                {!uploading && (
                                    <button className="remove-btn" onClick={() => handleRemoveFile('vnv')}>
                                        <X size={18} />
                                    </button>
                                )}
                            </div>
                        ) : (
                            <label className="upload-label">
                                <UploadIcon size={32} className="upload-icon" />
                                <strong>V&V Documentation</strong>
                                <span>PDF or DOCX • Drag & drop or click to upload</span>
                                <input
                                    type="file"
                                    accept=".pdf,.docx"
                                    onChange={(e) => handleFileChange('vnv', e.target.files[0])}
                                    hidden
                                />
                            </label>
                        )}
                    </div>

                    {/* Biocompatibility Report Upload */}
                    <div
                        className={`file-upload-card ${files.biocomp ? 'has-file biocomp' : ''} ${uploadStatus.biocomp === 'error' ? 'has-error' : ''}`}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={handleDrop('biocomp')}
                    >
                        {files.biocomp ? (
                            <div className="file-info">
                                <FileText size={32} className="file-icon" />
                                <div className="file-details">
                                    <strong>Biocompatibility Report</strong>
                                    <span>{files.biocomp.name} ({(files.biocomp.size / 1024 / 1024).toFixed(2)} MB)</span>
                                </div>
                                {getStatusIcon(uploadStatus.biocomp)}
                                {!uploading && (
                                    <button className="remove-btn" onClick={() => handleRemoveFile('biocomp')}>
                                        <X size={18} />
                                    </button>
                                )}
                            </div>
                        ) : (
                            <label className="upload-label">
                                <UploadIcon size={32} className="upload-icon" />
                                <strong>Biocompatibility Report</strong>
                                <span>PDF or DOCX • Drag & drop or click to upload</span>
                                <input
                                    type="file"
                                    accept=".pdf,.docx"
                                    onChange={(e) => handleFileChange('biocomp', e.target.files[0])}
                                    hidden
                                />
                            </label>
                        )}
                    </div>

                    <p className="upload-note">
                        Supported formats: PDF, DOCX. Maximum file size: 10MB
                    </p>
                </div>
            </div>

            {error && (
                <div className="error-message">
                    <AlertCircle size={18} />
                    {error}
                </div>
            )}

            {/* Action Buttons */}
            <div className="upload-actions">
                <button
                    className="btn btn-primary"
                    onClick={handleSubmit}
                    disabled={uploading || (!files.vnv && !files.biocomp)}
                >
                    {uploading ? 'Uploading & Indexing...' : 'Analyze Submission'}
                </button>
            </div>
        </div>
    )
}

export default Upload
