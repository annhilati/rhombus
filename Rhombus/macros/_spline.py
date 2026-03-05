from typing import Callable
import numpy as np, matplotlib.pyplot as plt


def poly_spline_points(a: float, b: float, c: float, d: float, ab: tuple[float, float]) -> list[tuple[float, float, float]]:
    "Calculates points of a cubic hermite spline from a cubic function in the range between two points"
    def f(x):
        return a*x**3 + b*x**2 + c*x + d

    def df(x):
        return 3*a*x**2 + 2*b*x + c

    return [
        (ab[0], f(ab[0]), df(ab[0])),
        (ab[1], f(ab[1]), df(ab[1]))
    ]


def function_spline_points(f: Callable[[float], float], ab: tuple[float, float], n=5, h=1e-6) -> list[tuple[float, float, float]]:

    xs = np.linspace(ab[0], ab[1], n)
    points = []

    for x in xs:
        y = f(x)

        m = (f(x + h) - f(x - h)) / (2 * h)

        points.append((float(x), y, m))

    return points



from matplotlib.figure import Figure
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
    plt.xlabel("x")
    plt.ylabel("y")
    plt.axis("equal")
    plt.title("Cubic Hermite spline")
    if show: plt.show()
    return plt.gcf()