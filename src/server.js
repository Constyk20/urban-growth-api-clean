require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors());
app.use(express.json({ limit: '500mb' }));   // large satellite zips

// MongoDB connection
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('MongoDB connected'))
  .catch(err => console.error('MongoDB error:', err));

// Routes
const authRoutes = require('./routes/auth');
const uploadRoutes = require('./routes/upload');
const predictRoutes = require('./routes/predict');
app.use('/api/auth', authRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/predict', predictRoutes);

app.get('/', (req, res) => res.send('Urban Growth Backend Running'));

app.listen(PORT, () => console.log(`Server on http://localhost:${PORT}`));