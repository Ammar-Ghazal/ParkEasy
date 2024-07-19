import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import AdminPage from './components/AdminPage';

export default function App() {
  console.log("App component is rendering");
  return (
    // <Router>
    //   <Routes>
    //     <Route path="/" element={<LandingPage />} />
    //     <Route path="/admin" element={<AdminPage />} />
    //   </Routes>
    // </Router>
    <LandingPage />
  );
}
