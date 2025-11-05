const { spawn } = require('child_process');

new Worker('urban-predict', async (job) => {
  const { jobId, aoi, rawUrl } = job.data;

  return new Promise((resolve, reject) => {
    const python = spawn('python', [
      'ml/predict.py',
      rawUrl,
      JSON.stringify(aoi)
    ]);

    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code !== 0) {
        console.error('Python error:', error);
        return reject(new Error(`Python exited with code ${code}`));
      }

      try {
        const result = JSON.parse(output);
        resolve(result);
      } catch (e) {
        reject(new Error('Invalid JSON from Python: ' + output));
      }
    });
  });
}, { connection });