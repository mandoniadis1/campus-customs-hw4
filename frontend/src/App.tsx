import { Route, Routes, useLocation } from 'react-router-dom'
import ChatWidget from './components/ChatWidget'
import Footer from './components/Footer'
import NavBar from './components/NavBar'
import About from './pages/About'
import CreateAccount from './pages/CreateAccount'
import GoingFast from './pages/GoingFast'
import Home from './pages/Home'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import ProductDetail from './pages/ProductDetail'
import Products from './pages/Products'

export default function App() {
  const { pathname } = useLocation()
  return (
    <div className="app">
      <NavBar />
      {/* keyed by path so each page fades in on navigation (filters/search on the same page don't re-animate) */}
      <main className="page page-enter" key={pathname}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/going-fast" element={<GoingFast />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
      <ChatWidget />
    </div>
  )
}
