const mongoose = require('mongoose');

const jobSchema = new mongoose.Schema({
  userId: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'User', 
    required: true 
  },
  sceneId: { 
    type: String, 
    required: true 
  },
  status: { 
    type: String, 
    enum: ['uploaded', 'queued', 'processing', 'completed', 'failed'], 
    default: 'uploaded' 
  },
  rawUrl: { 
    type: String 
  },
  resultUrl: { 
    type: String 
  },
  queueJobId: { 
    type: String 
  }, // BullMQ job ID
  createdAt: { 
    type: Date, 
    default: Date.now 
  },
  processedAt: { 
    type: Date 
  } // Optional: when prediction finishes
});

// Index for fast lookup by user + status
jobSchema.index({ userId: 1, status: 1 });
jobSchema.index({ queueJobId: 1 });

module.exports = mongoose.model('Job', jobSchema);