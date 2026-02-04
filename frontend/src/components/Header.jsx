import { Link, useLocation } from 'react-router-dom'
import './Header.css'

function Header() {
    const location = useLocation()

    return (
        <header className="header">
            <div className="header-container">
                <Link to="/" className="header-logo">
                    <span className="logo-icon">⚡</span>
                    TraceBridge AI
                </Link>

                <nav className="header-nav">
                    <Link
                        to="/"
                        className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
                    >
                        Home
                    </Link>
                    <Link
                        to="/documentation"
                        className={`nav-link ${location.pathname === '/documentation' ? 'active' : ''}`}
                    >
                        Documentation
                    </Link>
                </nav>
            </div>
        </header>
    )
}

export default Header
