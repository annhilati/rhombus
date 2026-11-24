"""Classes and functions for working with vectors and matrices.

Since density functions are definitions for scalar fields there are no direct applications for vectors.
Nevertheless they can come in handy for certain calculations.

The `DensityVector` and `DensityMatrix` types manage groups of density functions
and handle calculations with them under the hood.
"""

__all__ = [
    "DensityVector",
    "DensityMatrix",
    "crossP",
    "dotP",
    "transpose",
    "transform",
]


from collections.abc import Iterable
from typing import overload

from rhombus.std.builtin import Density, AnyDensity


# ======// Vectors //============================================================================//


class DensityVector:
    values: tuple[Density, ...]

    @overload
    def __init__(self, i: Iterable[AnyDensity]): ...
    @overload
    def __init__(self, *v: AnyDensity): ...
    def __init__(self, *args): # don't take kwargs
        if len(args) == 1 and isinstance(args[0], Iterable) and not isinstance(args[0], (str, bytes)):
            raw_elements = args[0]
        else:
            raw_elements = args

        self.values = tuple(
            d if isinstance(d, Density) else Density(d) for d in raw_elements
        )

    @property
    def dims(self) -> int:
        return len(self)
    
    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, index: int) -> Density:
        return self.values[index]
    
    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join(repr(d) for d in self.values)})"


    # ======// Operations //=====================================================================//

    def __add__(self, other):
        if not isinstance(other, DensityVector):
            raise TypeError("Can only add another vector to a vector.")
        if len(other) != len(self):
            raise ValueError(f"Other vector must have same amount of dimensions ({len(self)})")
        return DensityVector(self[i] + other[i] for i in range(len(self)))

    def __sub__(self, other):
        if not isinstance(other, DensityVector):
            raise TypeError("Can only subtract another vector from a vector.")
        if len(other) != len(self):
            raise ValueError(f"Other vector must have same amount of dimensions ({len(self)})")
        return DensityVector(self[i] - other[i] for i in range(len(self)))

    def __mul__(self, other):
        return DensityVector(self[i] * Density(other) for i in range(len(self)))

    def __truediv__(self, other):
        return DensityVector(self[i] / Density(other) for i in range(len(self)))

    def __neg__(self):
        return DensityVector(-self[i] for i in range(len(self)))

    def __matmul__(self, other: "DensityVector") -> Density:
        return dotP(self, other)
            

def dotP(vec1: DensityVector, vec2: DensityVector) -> Density:
    if vec1.dims != vec2.dims:
        raise ValueError(f"Both vectors must have same amount of dimensions (not {vec1.dims} and {vec2.dims})")
    from rhombus.std.math import sum
    return sum(vec1[i] * vec2[i] for i in range(vec1.dims))


def crossP(vec1: DensityVector, vec2: DensityVector) -> DensityVector:
    if vec1.dims != vec2.dims != 3:
        raise ValueError(f"Cross product is only defined for 3 dimensions (not {vec1.dims} and {vec2.dims})")
    return DensityVector(
        vec1[1] * vec2[2] - vec1[2] * vec2[1],
        vec1[2] * vec2[0] - vec1[0] * vec2[2],
        vec1[0] * vec2[1] - vec1[1] * vec2[0],
    )


def norm(vec: DensityVector) -> Density:
    from rhombus.std.math import sqrt, sum
    return sqrt(sum(*[v ** 2 for v in vec.values]))


# ======// Matrices //===========================================================================//


class DensityMatrix:
    rows: tuple[DensityVector, ...]

    @overload
    def __init__(self, rows: Iterable[DensityVector | Iterable[AnyDensity]]): ...
    @overload
    def __init__(self, *rows: DensityVector | Iterable[AnyDensity]): ...
    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], Iterable) and not isinstance(args[0], (str, bytes, DensityVector)):
            raw_rows = args[0]
        else:
            raw_rows = args

        rows = tuple(r if isinstance(r, DensityVector) else DensityVector(r) for r in raw_rows)

        if rows:
            cols = len(rows[0])
            if any(len(r) != cols for r in rows):
                raise ValueError("All rows in a matrix must have the same length")

        self.rows = rows

    @property
    def shape(self) -> tuple[int, int]:
        """rows x columns"""
        if not self.rows:
            return (0, 0)
        return (len(self.rows), len(self.rows[0]))
    
    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)
    
    def __getitem__(self, index: int | tuple[int, int]):
        if isinstance(index, tuple):
            i, j = index
            return self.rows[i][j]
        return self.rows[index]
    
    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join(repr(r) for r in self.rows)})"


    # ======// Operations //=====================================================================//

    def __add__(self, other):
        if not isinstance(other, DensityMatrix):
            raise TypeError("Can only add another matrix to a matrix.")
        if other.shape != self.shape:
            raise ValueError(f"Other matrix must have same dimensions ({self.shape})")
        return DensityMatrix(
            DensityVector(self[i][j] + other[i][j] for j in range(self.shape[1]))
            for i in range(self.shape[0])
        )

    def __sub__(self, other):
        if not isinstance(other, DensityMatrix):
            raise TypeError("Can only subtract another matrix from a matrix.")
        if other.shape != self.shape:
            raise ValueError(f"Other matrix must have same dimensions ({self.shape})")
        return DensityMatrix(
            DensityVector(self[i][j] - other[i][j] for j in range(self.shape[1]))
            for i in range(self.shape[0])
        )

    def __mul__(self, other):
        # Scalar multiplication
        if Density.is_any_density(other):
            return DensityMatrix(
                DensityVector(self[i][j] * Density(other) for j in range(self.shape[1]))
                for i in range(self.shape[0])
            )
        # Matrix multiplication
        elif isinstance(other, DensityMatrix):
            return self.__matmul__(other)

    def __truediv__(self, other):
        # Scalar division
        if Density.is_any_density(other):
            return DensityMatrix(
                DensityVector(self[i][j] / Density(other) for j in range(self.shape[1]))
                for i in range(self.shape[0])
            )

    def __neg__(self):
        return DensityMatrix(
            DensityVector(-self[i][j] for j in range(self.shape[1]))
            for i in range(self.shape[0])
        )

    @overload
    def __matmul__(self, other: DensityVector) -> DensityVector: ...
    @overload
    def __matmul__(self, other: DensityMatrix) -> DensityMatrix: ...
    def __matmul__(self, other: DensityMatrix | DensityVector) -> DensityMatrix | DensityVector:
        if isinstance(other, DensityVector):
            return transform(vec=other, mat=self)
        elif isinstance(other, DensityMatrix):
            if self.shape[1] != other.shape[0]:
                raise ValueError(
                    f"Cannot multiply matrix with shape {self.shape} and matrix with shape {other.shape}"
                )
            m, k = self.shape
            _, n = other.shape
            return DensityMatrix(
                DensityVector(
                    sum(self[i][p] * other[p][j] for p in range(k))
                    for j in range(n)
                )
                for i in range(m)
            )
        else:
            raise TypeError(f"Cannot multiply matrix with {type(other).__name__}")


def transform(vec: DensityVector, mat: DensityMatrix) -> DensityVector:
    """Transforms a vector with a matrix."""
    if mat.shape[1] != vec.dims:
        raise ValueError(
            f"Matrix columns ({mat.shape[1]}) must match vector dimensions ({vec.dims})"
        )
    return DensityVector(
        sum(mat[i][j] * vec[j] for j in range(mat.shape[1]))
        for i in range(mat.shape[0])
    )


def transpose(mat: DensityMatrix) -> DensityMatrix:
    """Transposes a matrix by swapping what rows and columns are."""
    nrows, ncols = mat.shape
    return DensityMatrix(
        DensityVector(mat.rows[i][j] for i in range(nrows))
        for j in range(ncols)
    )