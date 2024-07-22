import React from 'react';
import { Link } from 'react-router-dom';
import './landingpage.css';

const LandingPage = () => {
  return (
    <div className="landing-page">
      <header className="header">
        <nav className="navbar">
          <ul>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/admin">Admin Page</Link></li>
          </ul>
        </nav>
        <h1>Welcome to ParkEasy</h1>
      </header>
      <div className="welcome-message">
        <p>
          Discover a smarter way to park with ParkEasy. Our innovative app utilizes advanced sensor technology to guide you to available parking spaces effortlessly. No more circling the lot in search of a spot – ParkEasy helps you find the best parking spaces quickly and efficiently, saving you valuable time and reducing stress. Enjoy the convenience and ease of finding parking with ParkEasy, your ultimate parking companion.
        </p>
      </div>
      <div className="image-container">
        <img src="/parkingLot1.jpg" alt="Parking Lot" className="parking-image"/>
      </div>
      <div className="image-container">
        <img src="/parkingLot2.jpg" alt="Parking Lot" className="parking-image"/>
      </div>
    </div>
  );
};

export default LandingPage;
