import {Routes, Route} from 'react-router'
// import Home from './pages/Home'
import About from './pages/About'
import Login from './components/Login'
import Signup from './components/Signup'

function App() {

  return (
    <Routes>
      <Route path="/" element={<About />} />
      {/* <Route path="/about" element={<About />} /> */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
    </Routes>
  )
}

export default App
