import cv2
from sklearn.cluster import MiniBatchKMeans
import numpy as np


class AssertStyles:
    def __init__(self):
        pass

######################################################################################
# PIXEL ART
######################################################################################
    def apply_pixel_art(self, bgra_image, slider_value):
        # Return original if no effect
        if slider_value == 0:
            return bgra_image

        # Work on BGR channels only
        bgr = bgra_image[:, :, :3]

        # Determine pixelation block size from slider (2–16)
        pixel_size = max(2, int(1 + (slider_value / 100) * 15))

        h, w = bgr.shape[:2]
        small_h = max(1, h // pixel_size)
        small_w = max(1, w // pixel_size)

        # Downscale image to create pixel blocks
        small = cv2.resize(bgr, (small_w, small_h), interpolation=cv2.INTER_AREA)

        # Reduce color palette if slider > 50
        if slider_value > 50:
            colors = max(4, 256 - slider_value * 2)
            factor = 256 // colors
            if factor > 1:
                small = (small // factor) * factor

        # Upscale back to original size using nearest neighbor
        pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

        # Merge with original alpha
        result = bgra_image.copy()
        result[:, :, :3] = pixelated

        return result

######################################################################################
# DITHERING ART
######################################################################################
    def apply_dithering_art(self, bgra_image, slider_value):
        # Return original if slider is zero
        if slider_value == 0:
            return bgra_image

        bgr = bgra_image[:, :, :3].copy()
        dither_strength = slider_value / 100.0

        # Prepare output array
        result_bgr = np.zeros_like(bgr)

        for channel in range(3):  # Apply to B, G, R channels separately
            channel_img = bgr[:, :, channel]

            # Simple 2x2 Bayer matrix for ordered dithering
            dither = np.array([[0, 2], [3, 1]], dtype=np.float32) / 4.0
            h, w = channel_img.shape

            # Tile the small Bayer matrix to cover the full image
            tiled = np.tile(dither, (h // 2 + 1, w // 2 + 1))[:h, :w]

            # Normalize channel to [0, 1]
            channel_norm = channel_img.astype(np.float32) / 255.0

            # Create low/high thresholds for softer dithering
            low = tiled * dither_strength * 0.85
            high = tiled * dither_strength * 1.15

            # Initialize output channel
            dithered = np.zeros_like(channel_norm)

            # Assign pixel levels based on thresholds
            dithered[channel_norm > low] = 128
            dithered[channel_norm > high] = 255

            # Store results
            result_bgr[:, :, channel] = dithered.astype(np.uint8)

        # Merge with original alpha
        result = bgra_image.copy()
        result[:, :, :3] = result_bgr

        return result

######################################################################################
# GAMEBOY ART
######################################################################################
    def apply_gameboy_art(self, bgra_image: np.ndarray, slider_value: int):
        if slider_value == 0:
            return bgra_image.copy()

        image = bgra_image.copy()
        bgr = image[:, :, :3]

        # Extract dominant color from the image
        dominant_color = self._get_dominant_color(bgr)

        # Convert to grayscale and posterize
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        levels = 4
        posterized = (gray // (256 // levels)) * (256 // levels)

        # Apply dominant color tint based on brightness
        colored = np.zeros_like(bgr)
        intensity_map = posterized.astype(np.float32) / 255.0
        for i in range(3):
            colored[:, :, i] = (intensity_map * dominant_color[i] +
                                (1 - intensity_map) * posterized)

        colored = np.clip(colored, 0, 255).astype(np.uint8)

        # Blend with original image according to slider
        intensity = slider_value / 100.0
        if intensity < 1.0:
            colored = cv2.addWeighted(bgr, 1 - intensity, colored, intensity, 0)

        image[:, :, :3] = colored
        return image

    def _get_dominant_color(self, bgr_image):
        # Resize to 32x32 for faster computation
        small = cv2.resize(bgr_image, (32, 32), interpolation=cv2.INTER_AREA)
        avg = small.mean(axis=(0, 1))
        return avg.astype(np.uint8)

######################################################################################
# ANIME ART
######################################################################################
    def apply_anime_art(self, bgra_image: np.ndarray, slider_value: int) -> np.ndarray:
        original = bgra_image.copy()
        bgr_image = original[:, :, :3]

        if slider_value == 0:
            return original

        t = slider_value / 100
        # Determine number of colors based on slider
        if t < 0.25:
            colors = int(256 - (t / 0.25) * 192)
        elif t < 0.5:
            colors = int(64 - ((t - 0.25) / 0.25) * 32)
        elif t < 0.75:
            colors = int(32 - ((t - 0.5) / 0.25) * 16)
        else:
            colors = int(16 - ((t - 0.75) / 0.25) * 12)

        colors = max(4, colors)

        quantized = self._quantize_colors(bgr_image, colors)

        # Preserve alpha
        original[:, :, :3] = quantized[:, :, :3]

        return original

    def _quantize_colors(self, image: np.ndarray, n_colors: int) -> np.ndarray:
        if n_colors >= 256:
            return image

        pixels = image.reshape(-1, 3).astype(np.float32)
        mbk = MiniBatchKMeans(n_clusters=n_colors, batch_size=5000, max_iter=50, random_state=42)
        mbk.fit(pixels)

        labels = mbk.predict(pixels)
        centers = np.uint8(mbk.cluster_centers_)
        quantized = centers[labels].reshape(image.shape)
        return quantized

######################################################################################
# CEL SHADING ART
######################################################################################
    def apply_cel_shaded_art(self, bgra_image: np.ndarray, slider_value: int) -> np.ndarray:
        if slider_value == 0:
            return bgra_image.copy()

        t = slider_value / 100.0
        image = bgra_image.copy()
        bgr = image[:, :, :3]

        # Smooth image while preserving edges
        smooth = cv2.bilateralFilter(bgr, d=5, sigmaColor=50 * t + 25, sigmaSpace=15)

        # Posterize luminance (V channel) only
        hsv = cv2.cvtColor(smooth, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        levels = max(2, int(4 + 4 * (1 - t)))
        step = 256 // levels
        v = (v // step) * step
        hsv_poster = cv2.merge([h, s, v])
        posterized = cv2.cvtColor(hsv_poster, cv2.COLOR_HSV2BGR)

        # Extract edges for outlines
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
        edges = cv2.GaussianBlur(edges, (3, 3), 0)
        edges_mask = (edges > 50).astype(np.uint8)

        edges_3c = np.stack([edges_mask] * 3, axis=-1) * 255
        cel_with_edges = np.where(edges_3c == 255, 0, posterized)

        # Blend with original image
        result = cv2.addWeighted(bgr, 1 - t, cel_with_edges, t, 0)
        image[:, :, :3] = result

        return image

######################################################################################
# SIMPLE ANIMATION ART
######################################################################################
    def apply_simple_animation_art(self, bgra_image: np.ndarray, slider_value: int) -> np.ndarray:
        if slider_value == 0:
            return bgra_image.copy()

        image = bgra_image.copy()
        bgr = image[:, :, :3]
        t = slider_value / 100.0

        # Extract edges
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        # Remove small noise
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel)

        # Blur edges slightly to reduce aliasing
        edges = cv2.GaussianBlur(edges, (3, 3), 0)

        # Invert edges for cartoon effect
        edges_inv = 255 - edges
        edges_3c = cv2.cvtColor(edges_inv, cv2.COLOR_GRAY2BGR)

        # Posterize colors for cartoon shading
        levels = int(4 + (12 * (1 - t)))  # 16→4 levels based on slider
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        step = 256 // levels
        v = (v // step) * step
        hsv_poster = cv2.merge([h, s, v])
        posterized = cv2.cvtColor(hsv_poster, cv2.COLOR_HSV2BGR)

        # Combine posterized colors with edges
        cartoon = cv2.multiply(posterized, edges_3c, scale=1 / 255.0)

        # Blend with original image
        result = cv2.addWeighted(bgr, 1 - t, cartoon, t, 0)
        image[:, :, :3] = result

        return image