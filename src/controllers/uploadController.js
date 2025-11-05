const Job = require('../models/job');
const { uploadFile } = require('../services/storage');
const path = require('path');
const fs = require('fs').promises;

exports.uploadScene = async (req, res) => {
  if (!req.file) return res.status(400).json({ message: 'No file uploaded' });

  try {
    const sceneId = path.parse(req.file.originalname).name;
    const rawUrl = await uploadFile(req.file.path, req.file.filename);

    const job = await Job.create({
      userId: req.user.id,
      sceneId,
      status: 'uploaded',
      rawUrl,
    });

    // Delete local file after upload
    await fs.unlink(req.file.path);

    res.json({ jobId: job._id, sceneId, rawUrl });
  } catch (err) {
    console.error('Upload error:', err);
    res.status(500).json({ message: err.message });
  }
};