// src/utils/uploadFile.js - GITHUB + LOCAL STORAGE
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const uploadFile = async (localPath, originalName) => {
  const ext = path.extname(originalName);
  const filename = `${uuidv4()}${ext}`;
  const destDir = path.join(__dirname, '..', 'uploads', 'raw-imagery');
  const destPath = path.join(destDir, filename);

  // Ensure directory exists
  if (!fs.existsSync(destDir)) {
    fs.mkdirSync(destDir, { recursive: true });
  }

  // Copy file
  fs.copyFileSync(localPath, destPath);

  // Return file:// URL for local testing
  const fileUrl = `file://${path.resolve(destPath).replace(/\\/g, '/')}`;

  // FOR RENDER: Return GitHub raw URL (uncomment when deployed)
  // const githubUrl = `https://github.com/Constyk20/urban-growth-api-clean/raw/main/uploads/raw-imagery/${filename}`;
  // return githubUrl;

  return fileUrl; // ← Use this for local testing
};

module.exports = { uploadFile };