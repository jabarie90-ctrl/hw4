import { NavLink, Route, Routes } from 'react-router-dom'
import ChatWidget from './components/ChatStub'
import { AuthProvider, useAuth } from './auth'
import { ShopProvider, useShop } from './shop'
import AboutPage from './pages/AboutPage'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import ProductDetailPage from './pages/ProductDetailPage'
import ProductsPage from './pages/ProductsPage'
import SignupPage from './pages/SignupPage'

function NavBar() {
  const { user, logout } = useAuth()
  const { spotlight, setSpotlight, recentIds } = useShop()

  return (
    <header className="topnav">
      <NavLink to="/" className="logo">
        Campus Customs
      </NavLink>
      <nav>
        <NavLink to="/">Home</NavLink>
        <NavLink to="/about">About</NavLink>
        <NavLink
          to="/products"
          onClick={() => {
            if (spotlight.length) setSpotlight([])
          }}
        >
          Products
        </NavLink>
        {recentIds.length ? (
          <NavLink to={`/products/${recentIds[0]}`} className="nav-recent">
            Recently viewed
          </NavLink>
        ) : null}
        {user ? (
          <>
            <span className="nav-user">Hi, {user.first_name}</span>
            <button type="button" className="linkish" onClick={logout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login">Log in</NavLink>
            <NavLink to="/signup" className="nav-cta">
              Create account
            </NavLink>
          </>
        )}
      </nav>
    </header>
  )
}

function AppShell() {
  return (
    <div className="app-shell">
      <NavBar />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/products/:productId" element={<ProductDetailPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
        </Routes>
      </main>
      <ChatWidget />
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <ShopProvider>
        <AppShell />
      </ShopProvider>
    </AuthProvider>
  )
}
