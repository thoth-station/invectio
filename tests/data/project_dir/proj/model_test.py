import numpy as np
import tensorflow as tf
from tensorflow.keras import layers


def get_model():
    model = tf.keras.Sequential()
    # Adds a densely-connected layer with 64 units to the model:
    model.add(layers.Dense(64, activation="relu"))
    # Add another:
    model.add(layers.Dense(64, activation="relu"))
    # Add a softmax layer with 10 output units:
    model.add(layers.Dense(10, activation="softmax"))

    data = np.random.random((1000, 32))
    labels = np.random.random((1000, 10))

    val_data = np.random.random((100, 32))
    val_labels = np.random.random((100, 10))

    model.fit(
        data,
        labels,
        epochs=10,
        batch_size=32,
        validation_data=(val_data, val_labels),
    )
    return model
