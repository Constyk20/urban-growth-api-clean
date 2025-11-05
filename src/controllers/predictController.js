const Job = require('../models/job');        // ← Capital J
const Prediction = require('../models/prediction'); // ← Capital P
const { predictQueue } = require('../services/queue');

exports.submitPrediction = async (req, res) => {
  const { jobId, aoi } = req.body;
  const userId = req.user.id;

  try {
    // Validate job exists and belongs to user
    const job = await Job.findOne({ _id: jobId, userId });
    if (!job) return res.status(404).json({ message: 'Job not found' });

    if (job.status !== 'uploaded') {
      return res.status(400).json({ message: 'Job already processed or invalid' });
    }

    // Validate AOI (basic GeoJSON check)
    if (!aoi || !aoi.type || aoi.type !== 'Polygon' || !Array.isArray(aoi.coordinates)) {
      return res.status(400).json({ message: 'Invalid AOI: Must be GeoJSON Polygon' });
    }

    // Update job status + save queueJobId
    job.status = 'queued';
    await job.save();

    // Add to BullMQ queue
    const queueJob = await predictQueue.add('predict', {
      jobId: job._id.toString(),
      aoi,
      userId,
      rawUrl: job.rawUrl
    }, {
      jobId: `predict-${job._id}`, // Prevent duplicates
      removeOnComplete: true,
      removeOnFail: false
    });

    // Save queueJobId to Job model
    job.queueJobId = queueJob.id;
    await job.save();

    res.json({
      message: 'Prediction queued successfully',
      queueJobId: queueJob.id,
      jobId: job._id,
      status: 'queued'
    });

  } catch (err) {
    console.error('Submit prediction error:', err);
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// Poll job status + result
exports.getPredictionStatus = async (req, res) => {
  const { queueJobId } = req.params;

  try {
    const queueJob = await predictQueue.getJob(queueJobId);
    if (!queueJob) return res.status(404).json({ message: 'Queue job not found' });

    const state = await queueJob.getState();
    const result = queueJob.returnvalue;

    // If completed, enrich with Prediction doc
    let enrichedResult = result;
    if (state === 'completed' && result && result.predictionId) {
      const prediction = await Prediction.findById(result.predictionId);
      if (prediction) {
        enrichedResult = {
          ...result,
          prediction: {
            builtUpAreaHa: prediction.builtUpAreaHa,
            growthPercent: prediction.growthPercent,
            iou: prediction.iou,
            confidence: prediction.confidence,
            resultUrl: prediction.resultUrl,
            processedAt: prediction.processedAt
          }
        };
      }
    }

    res.json({
      queueJobId,
      state,
      result: enrichedResult || null,
      progress: queueJob.progress || 0
    });

  } catch (err) {
    console.error('Get status error:', err);
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};