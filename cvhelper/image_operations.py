import enum
from typing import Dict, Union

import numpy as np
import cv2 as cv

from .model import Rect, Point


class MorphShape(enum.Enum):
    RECT: int = cv.MORPH_RECT
    CROSS: int = cv.MORPH_CROSS


class AngleUnit(enum.Enum):
    RADIANS = enum.auto()
    DEGREES = enum.auto()


class Contour:
    def __init__(self, points, moment: Dict = None):
        """
        :param points: points from cv.findContour()
        :param moment: moments from cv.moments().
        """
        self.points = points
        if moment is None:
            moment = cv.moments(points)
        self.moment = moment
        self.area = moment["m00"]

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.points[key, 0]
        if len(key) > 2:
            raise ValueError(f"Too many indices: {len(key)}")
        return self.points[key[0], 0, key[1]]

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self.points[key, 0] = value
        if len(key) > 2:
            raise ValueError(f"Too many indices: {len(key)}")
        self.points[key[0], 0, key[1]] = value


def dilate(image: np.ndarray, kernel_size, shape: MorphShape = MorphShape.RECT):
    _error_if_image_empty(image)
    return cv.dilate(
        image, cv.getStructuringElement(shape.value, (kernel_size, kernel_size))
    )


def morph_open(image: np.ndarray, size: int, iterations=1) -> np.ndarray:
    _error_if_image_empty(image)
    return cv.morphologyEx(
        image,
        cv.MORPH_OPEN,
        cv.getStructuringElement(cv.MORPH_RECT, (size, size)),
        iterations=iterations,
    )


def morph_close(image: np.ndarray, size: int, iterations=1) -> np.ndarray:
    _error_if_image_empty(image)
    return cv.morphologyEx(
        image,
        cv.MORPH_CLOSE,
        cv.getStructuringElement(cv.MORPH_RECT, (size, size)),
        iterations=iterations,
    )


def normalize(image: np.ndarray, min: int = 0, max: int = 255) -> np.ndarray:
    _error_if_image_empty(image)
    normalized = np.zeros_like(image)
    cv.normalize(image, normalized, max, min, cv.NORM_MINMAX)
    return normalized


def resize(image: np.ndarray, factor: int) -> np.ndarray:
    """
    Resize an image with the given factor. A factor of 2 gives an image of half the size.
    :param image: Image to resize
    :param factor: Shrink factor. A factor of 2 halves the image size.
    :return: A resized image.
    """
    _error_if_image_empty(image)
    return cv.resize(
        image, None, fx=1 / factor, fy=1 / factor, interpolation=cv.INTER_CUBIC
    )


def bgr2gray(image: np.ndarray) -> np.ndarray:
    _error_if_image_empty(image)
    return cv.cvtColor(image, cv.COLOR_BGR2GRAY)


def bgr2hsv(image: np.ndarray) -> np.ndarray:
    _error_if_image_empty(image)
    return cv.cvtColor(image, cv.COLOR_BGR2HSV)


def bgr2xyz(image: np.ndarray) -> np.ndarray:
    _error_if_image_empty(image)
    return cv.cvtColor(image, cv.COLOR_BGR2XYZ)


def bgr2hls(image: np.ndarray) -> np.ndarray:
    _error_if_image_empty(image)
    return cv.cvtColor(image, cv.COLOR_BGR2HLS)


def bgr2luv(image: np.ndarray) -> np.ndarray:
    _error_if_image_empty(image)
    return cv.cvtColor(image, cv.COLOR_BGR2LUV)


def blur_gaussian(
    image: np.ndarray, kernel_size: int = 3, sigma_x=None, sigma_y=None
) -> np.ndarray:
    _error_if_image_empty(image)
    if sigma_x is None:
        sigma_x = 0
    if sigma_y is None:
        sigma_y = 0

    return cv.GaussianBlur(
        image, ksize=(kernel_size, kernel_size), sigmaX=sigma_x, sigmaY=sigma_y
    )


def blur_median(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    _error_if_image_empty(image)
    return cv.medianBlur(image, kernel_size)


def threshold_otsu(image: np.ndarray, max_value: int = 255) -> np.ndarray:
    _error_if_image_empty(image)
    _, img = cv.threshold(image, 0, max_value, cv.THRESH_BINARY + cv.THRESH_OTSU)
    return img


def threshold_binary(image: np.ndarray, value: int, max_value: int = 255) -> np.ndarray:
    _error_if_image_empty(image)
    _, img = cv.threshold(image, value, max_value, cv.THRESH_BINARY)
    return img


def threshold_tozero(image: np.ndarray, value: int, max_value: int = 255) -> np.ndarray:
    _error_if_image_empty(image)
    _, img = cv.threshold(image, value, max_value, cv.THRESH_TOZERO)
    return img


def threshold_otsu_tozero(image: np.ndarray, max_value: int = 255) -> np.ndarray:
    _error_if_image_empty(image)
    _, img = cv.threshold(image, 0, max_value, cv.THRESH_OTSU | cv.THRESH_TOZERO)
    return img


def canny(image: np.ndarray, low_threshold: float, high_threshold: float) -> np.ndarray:
    _error_if_image_empty(image)
    return cv.Canny(
        image, threshold1=low_threshold, threshold2=high_threshold, L2gradient=True
    )


def scale_contour_to_rect(contour: Contour, rect: Rect) -> Contour:
    contour = Contour(contour.points, contour.moment)
    for i in range(len(contour)):
        contour[i, 0] = contour[i, 0] - rect.x
        contour[i, 1] = contour[i, 1] - rect.y

    return contour


def rotate_image(
    image: np.ndarray,
    center: Point,
    angle: float,
    scale: int = 1,
    unit: AngleUnit = AngleUnit.RADIANS,
) -> np.ndarray:
    if unit is AngleUnit.RADIANS:
        angle = 180 / np.pi * angle
    rotation_matrix = cv.getRotationMatrix2D((*center,), angle, scale=scale)

    if image.ndim == 2:
        return cv.warpAffine(image, rotation_matrix, image.shape[::-1])
    elif image.ndim == 3:
        copy = np.zeros_like(image)
        shape = image.shape[-2::-1]  # The two first, reversed
        for i in range(copy.shape[-1]):
            copy[..., i] = cv.warpAffine(image[..., i], rotation_matrix, shape)
        return copy
    else:
        raise ValueError("Image must have 2 or 3 dimensions.")


def _error_if_image_empty(image: np.ndarray) -> None:
    if image is None or image.size == 0:
        raise ValueError("Image is empty")
