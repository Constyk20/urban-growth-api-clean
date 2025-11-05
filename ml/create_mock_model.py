# ml/create_mock_model.py - FAKE BUILDINGS
import tensorflow as tf
import numpy as np
import os

# Input: 64x64x5
inputs = tf.keras.Input(shape=(64, 64, 5))

# Fake U-Net
x = tf.keras.layers.Conv2D(16, 3, activation='relu', padding='same')(inputs)
x = tf.keras.layers.MaxPooling2D(2)(x)
x = tf.keras.layers.Conv2D(32, 3, activation='relu', padding='same')(x)
x = tf.keras.layers.UpSampling2D(2)(x)
outputs = tf.keras.layers.Conv2D(1, 1, activation='sigmoid')(x)

model = tf.keras.Model(inputs, outputs)

# Create fake training data (1 sample)
X = np.random.rand(1, 64, 64, 5).astype('float32')
Y = np.zeros((1, 64, 64, 1), dtype='float32')
Y[0, 10:50, 10:50, 0] = 1  # Fake building block

# Train 1 epoch
model.compile(optimizer='adam', loss='binary_crossentropy')
model.fit(X, Y, epochs=1, verbose=1)

# Save
os.makedirs("ml/model", exist_ok=True)
model.save("ml/model/unet_model.h5")
print("Trained mock model with fake building saved!")