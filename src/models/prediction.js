const mongoose = require('mongoose');

const predictionSchema = new mongoose.Schema({
  jobId: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'Job', 
    required: true 
  },
  aoi: {
    type: { 
      type: String, 
      enum: ['Polygon'], 
      default: 'Polygon' 
    },
    coordinates: { 
      type: [[[Number]]], 
      required: true 
    } // GeoJSON: [[outer ring]]
  },
  builtUpAreaHa: { 
    type: Number, 
    min: 0 
  },
  growthPercent: { 
    type: Number, 
    min: -100, 
    max: 1000 
  }, // Can be negative (loss) or >100% (rapid growth)
  iou: { 
    type: Number, 
    min: 0, 
    max: 1 
  },
  resultUrl: { 
    type: String 
  }, // GCS URL to prediction GeoTIFF
  confidence: { 
    type: Number, 
    min: 0, 
    max: 1 
  }, // Optional: model confidence
  createdAt: { 
    type: Date, 
    default: Date.now 
  },
  processedAt: { 
    type: Date 
  }
});

// Geospatial index for AOI queries (e.g., "find all predictions in Nairobi")
predictionSchema.index({ aoi: '2dsphere' });

// Index for fast lookup by job
predictionSchema.index({ jobId: 1 });

// Compound index for dashboard queries
predictionSchema.index({ 'jobId': 1, 'createdAt': -1 });

module.exports = mongoose.model('Prediction', predictionSchema);