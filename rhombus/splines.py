"""
Utility module for working with cubic Hermite splines.

The term "spline point" always refers to an object of type `tuple[float, float, float]`
that describes a point on a Hermite spline function. Here, the first value is the
x-position, the second is the y-value and the third is the slope at that points.

[Wikipedia](https://en.wikipedia.org/wiki/Cubic_Hermite_spline)
"""

from typing import Callable
from matplotlib.figure import Figure
import numpy as np
import matplotlib.pyplot as plt


def sample_spline_points(
    f: Callable[[float], float],
    interval: tuple[float, float],
    points: int = 5,
    *,
    step_size=1e-5,
) -> list[tuple[float, float, float]]:
    """Samples exactly `points` spline points optimally distributed for cubic interpolation.

    Uses a curvature-based density function (|f''(x)|^(1/4)) to place more points
    where the function changes rapidly, minimizing the interpolation error while keeping
    the point count fixed.

    Ideal for functions that satisfy:
    *   **Smoothness:** Function must be at least twice continuously differentiable in the interval.
    *   **Limited curvature:** Very steep or diverging derivatives → many segments required.
    *   **Monotonic or periodic:** Better approximation, fewer segments.

    Parameters:
        f (float -> float): The function to sample the spline points from.
        interval ((float, float)): The interval between to sample the function.
        points (int): The amount of points to sample between within the sample interval.
        step_size (float): The infinitesimal value that is used to calculate derivatives.

    """
    if points < 2:
        raise ValueError("At least 2 points are required.")

    def get_point(x):
        y = f(x)
        # 1st derivative for Hermite tangent
        m = (f(x + step_size) - f(x - step_size)) / (2 * step_size)
        return (float(x), float(y), float(m))

    if points == 2:
        return [get_point(interval[0]), get_point(interval[1])]

    def d2f(x):
        # 2nd derivative to estimate curvature
        return (f(x + step_size) - 2 * f(x) + f(x - step_size)) / (step_size**2)

    # 1. Erstelle ein dichtes Raster zum Integrieren der "Fehler-Dichte"
    resolution = max(1000, points * 10)
    dense_xs = np.linspace(interval[0], interval[1], resolution)

    # 2. Berechne die Dichte D(x) = |f''(x)|^(1/4)
    # (Der Exponent 1/4 ist theoretisch optimal für die Fehlerverteilung bei kubischen Splines)
    density = np.zeros_like(dense_xs)
    for i, x in enumerate(dense_xs):
        density[i] = abs(d2f(x)) ** 0.25

    # Füge eine minimale Basisdichte hinzu, damit rein lineare Bereiche (Dichte=0) nicht ignoriert werden
    # Eine zu niedrige Basisdichte sorgt bei sehr großen Intervallen (z.B. -10 bis 10 bei Sigmoid)
    # für Überschwinger in den flachen Bereichen (Runge-Phänomen).
    base_density = np.mean(density) * 0.5
    if base_density == 0:
        base_density = 1.0
    density += base_density

    # 3. Berechne die kumulative Verteilungsfunktion (CDF)
    cdf = np.zeros_like(dense_xs)
    for i in range(1, resolution):
        cdf[i] = cdf[i - 1] + (density[i] + density[i - 1]) / 2 * (
            dense_xs[i] - dense_xs[i - 1]
        )

    # Normalisiere auf den Bereich [0, 1]
    cdf /= cdf[-1]

    # 4. Verteile die Punkte gleichmäßig auf der Y-Achse der CDF und projiziere sie auf X zurück
    target_cdfs = np.linspace(0, 1, points)
    optimal_xs = np.interp(target_cdfs, cdf, dense_xs)

    # Punkte exakt berechnen (Tangenten etc.)
    return [get_point(x) for x in optimal_xs]


def poly_spline_points(
    a: float, b: float, c: float, d: float, sample_interval: tuple[float, float]
) -> list[tuple[float, float, float]]:
    """Calculates spline points for an arbitrary polynomial `ax³ + bx² + cx + d` within the `sample_interval`."""
    x0, x1 = sample_interval

    def f(x):
        return a * x**3 + b * x**2 + c * x + d

    def df(x):
        return 3 * a * x**2 + 2 * b * x + c

    return [(x0, f(x0), df(x0)), (x1, f(x1), df(x1))]


def spline_points_to_cubics(
    points: list[tuple[float, float, float]], shifted: bool = False
) -> list[tuple[float, float, float, float]]:
    """
    Returns the coefficients of the segments of a hermite spline based of spline points.

    Parameters:
        shifted (bool): Whether to shift the segment functions with its coordinates shifted to its begin.<br>
            If False returns the coefficients for the function as if it was globally plotted, but domain restricted.<br>
            If True, returns (a, b, c, d) for `s(x) = a + b*(x-x_i) + c*(x-x_i)^2 + d*(x-x_i)^3`.<br>

    Returns:
        out (list[(float, float, float, float)]): A list of coefficients of cubic polynomials.<br>
            The i-th polynomial corresponds to the segment between the i-th and the i+1-th point (after being sorted).
    """

    points = sorted(points, key=lambda p: p[0])

    if len(points) < 2:
        return []

    segments: list[tuple[float, float, float, float]] = []

    for i in range(len(points) - 1):
        x0, y0, m0 = points[i]
        x1, y1, m1 = points[i + 1]

        h = x1 - x0
        if h == 0:
            raise ValueError(f"Two x values ('{x0}' and '{x1}') cannot be equal")

        dy = y1 - y0

        a = y0
        b = m0
        c = (3 * dy - h * (2 * m0 + m1)) / (h * h)
        d = (h * (m0 + m1) - 2 * dy) / (h**3)

        if shifted:
            segments.append((a, b, c, d))
        else:
            A = d
            B = c - 3 * d * x0
            C = b - 2 * c * x0 + 3 * d * x0**2
            D = a - b * x0 + c * x0**2 - d * x0**3

            segments.append((A, B, C, D))

    return segments


def show_spline(
    points: list[tuple[float, float, float]], *, show: bool = True
) -> Figure:
    """Plots a hermite spline from spline points in a pyplot.

    Parameters:
        show (bool): Whether to open a pyplot window.
    """

    points = sorted(points, key=lambda p: p[0])

    def hermite_segment(x0, y0, m0, x1, y1, m1, x):
        h = x1 - x0
        t = (x - x0) / h

        h00 = 2 * t**3 - 3 * t**2 + 1
        h10 = t**3 - 2 * t**2 + t
        h01 = -2 * t**3 + 3 * t**2
        h11 = t**3 - t**2

        return h00 * y0 + h10 * h * m0 + h01 * y1 + h11 * h * m1

    def evaluate_spline(points, resolution=200, padding=0.5):
        xs = []
        ys = []

        x0, y0, _ = points[0]
        x_left = np.linspace(x0 - padding, x0, resolution)
        y_left = np.full_like(x_left, y0)

        xs.append(x_left)
        ys.append(y_left)

        for i in range(len(points) - 1):
            x0, y0, m0 = points[i]
            x1, y1, m1 = points[i + 1]

            x_segment = np.linspace(x0, x1, resolution)
            y_segment = hermite_segment(x0, y0, m0, x1, y1, m1, x_segment)

            xs.append(x_segment)
            ys.append(y_segment)

        xn, yn, _ = points[-1]
        x_right = np.linspace(xn, xn + padding, resolution)
        y_right = np.full_like(x_right, yn)

        xs.append(x_right)
        ys.append(y_right)

        return np.concatenate(xs), np.concatenate(ys)

    x_vals, y_vals = evaluate_spline(points)

    plt.figure()
    plt.plot(x_vals, y_vals)
    plt.scatter([p[0] for p in points], [p[1] for p in points], s=20)
    plt.xlabel("input")
    plt.ylabel("output")
    plt.axis("equal")
    plt.title("Cubic Hermite spline")
    if show:
        plt.show()
    return plt.gcf()
