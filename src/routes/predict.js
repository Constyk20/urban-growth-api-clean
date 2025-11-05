const express = require('express');
const router = express.Router();
const { submitPrediction, getPredictionStatus } = require('../controllers/predictController');
const auth = require('../middleware/auth');

// Submit AOI for prediction
router.post('/', auth, submitPrediction);

// Poll status
router.get('/status/:queueJobId', auth, getPredictionStatus);

module.exports = router;