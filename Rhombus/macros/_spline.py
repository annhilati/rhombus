from typing import Callable
from matplotlib.figure import Figure
import numpy as np, matplotlib.pyplot as plt


# https://en.wikipedia.org/wiki/Cubic_Hermite_spline

def poly_spline_points(
    a: float, b: float, c: float, d: float, sample_interval: tuple[float, float]) -> list[tuple[float, float, float]]:
    """Calculates spline points for an arbitrary polynomial `ax³ + bx² + cx + d` within the `sample_interval`."""
    x0, x1 = sample_interval

    def f(x):
        return a*x**3 + b*x**2 + c*x + d

    def df(x):
        return 3*a*x**2 + 2*b*x + c

    return [
        (x0, f(x0), df(x0)),
        (x1, f(x1), df(x1))
    ]

def function_spline_points(f: Callable[[float], float], sample_interval: tuple[float, float], points=5, step_size=1e-8) -> list[tuple[float, float, float]]:
    """Samples spline points based of an arbitrary function.

    Ideal for functions that satisfy:
    *   **Smoothness:** Function must be at least twice continuously differentiable in the interval.
    *   **Limited curvature:** Very steep or diverging derivatives → many segments required.
    *   **Monotonic or periodic:** Better approximation, fewer segments.

    Parameters:
        f (float -> float): The function to sample the spline points from.
        sample_interval ((float, float)): The interval between to sample the function.
        points (int): The amount of points to sample between within the sample interval.
        step_size (float): The infinitesimal value that is used to calculate derivatives.

    Returns:
        out (list[tuple[float, float, float]]): A list of the spline points. The tuples yield `(x, y, m)`
    """

    xs = np.linspace(sample_interval[0], sample_interval[1], points)
    points = []

    for x in xs:
        y = f(x)

        m = (f(x + step_size) - f(x - step_size)) / (2 * step_size)

        points.append((float(x), y, m))

    return points


def show_spline(points: list[tuple[float, float, float]], *, show: bool = True) -> Figure:

    points = sorted(points, key=lambda p: p[0])

    def hermite_segment(x0, y0, m0, x1, y1, m1, x):
        h = x1 - x0
        t = (x - x0) / h

        h00 = 2*t**3 - 3*t**2 + 1
        h10 = t**3 - 2*t**2 + t
        h01 = -2*t**3 + 3*t**2
        h11 = t**3 - t**2

        return h00*y0 + h10*h*m0 + h01*y1 + h11*h*m1

    def evaluate_spline(points, resolution=200, padding=0.5):
        xs = []
        ys = []

        # linker konstanter Bereich
        x0, y0, _ = points[0]
        x_left = np.linspace(x0 - padding, x0, resolution)
        y_left = np.full_like(x_left, y0)

        xs.append(x_left)
        ys.append(y_left)

        # spline Segmente
        for i in range(len(points) - 1):
            x0, y0, m0 = points[i]
            x1, y1, m1 = points[i + 1]

            x_segment = np.linspace(x0, x1, resolution)
            y_segment = hermite_segment(x0, y0, m0, x1, y1, m1, x_segment)

            xs.append(x_segment)
            ys.append(y_segment)

        # rechter konstanter Bereich
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
    if show: plt.show()
    return plt.gcf()