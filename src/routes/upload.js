const express = require('express');
const router = express.Router();
const { uploadScene } = require('../controllers/uploadController');  // ← EXACT NAME

const upload = require('../middleware/upload');
const auth = require('../middleware/auth');

router.post('/', auth, upload, uploadScene);

module.exports = router;