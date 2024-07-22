import React, { useState } from 'react';
import './adminpage.css';

const AdminPage = () => {
  const [protocol, setProtocol] = useState('');
  const [imageLink, setImageLink] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');

  const handleProtocolChange = (event) => {
    setProtocol(event.target.value);
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://your-server-endpoint/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      setImageLink(result.fileLink);  // Assuming the server returns a JSON with a 'fileLink' field
      setUploadStatus('Upload successful!');
    } catch (error) {
      setUploadStatus('Upload failed. Please try again.');
    }
  };

  const handleFormSubmit = (event) => {
    event.preventDefault();
    // Add code here to handle form submission, if necessary
  };

  return (
    <div className="admin-page">
      <header className="header">
        <h1>Admin Page</h1>
      </header>
      <div className="content">
        <form onSubmit={handleFormSubmit}>
          <div className="form-group">
            <label htmlFor="protocol">Server Protocol:</label>
            <input
              type="text"
              id="protocol"
              value={protocol}
              onChange={handleProtocolChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="imageUpload">Upload Mapping Image:</label>
            <input
              type="file"
              id="imageUpload"
              onChange={handleImageUpload}
            />
            {uploadStatus && <p className="upload-status">{uploadStatus}</p>}
          </div>
          {imageLink && (
            <div className="image-preview">
              <p>Uploaded Image:</p>
              <img src={imageLink} alt="Mapping" className="mapping-image" />
            </div>
          )}
          <button type="submit">Submit</button>
        </form>
      </div>
    </div>
  );
};

export default AdminPage;
