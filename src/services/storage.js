const { Storage } = require('@google-cloud/storage');
require('dotenv').config();

const storage = new Storage({
  keyFilename: process.env.GCS_KEYFILE_PATH,
  projectId: process.env.GCS_PROJECT_ID,
});

const bucket = storage.bucket(process.env.GCS_BUCKET);

const uploadFile = async (localPath, destName) => {
  const dest = `raw-imagery/${destName}`;
  await bucket.upload(localPath, { destination: dest });
  const file = bucket.file(dest);
  await file.makePublic();
  return `https://storage.googleapis.com/${process.env.GCS_BUCKET}/${dest}`;
};

module.exports = { uploadFile };