from PIL import Image
import numpy as np

def preprocess_image(image: Image.Image) -> np.ndarray:
    return np.asarray(image) / 255.0
