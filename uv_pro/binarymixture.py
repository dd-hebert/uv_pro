"""
Estimate the relative amounts of two species in a binary mixture.

@author: David Hebert
"""

import pandas as pd
from scipy.optimize import minimize


class BinaryMixture:
    """
    UV-vis binary mixture solver.

    Attributes
    ----------
    coeff_a_max : float
        The maximum possible coefficient for component A.
    coeff_b_max : float
        The maximum possible coefficient for component B.
    coeff_a : float, optional
        The best-fit scalar coefficient of component A.
    coeff_b : float, optional
        The best-fit scalar coefficient of component A.
    fit : pandas.Series
        The best-fit spectrum from a linear combination of \
        component A and component B.
    """

    def __init__(
        self,
        mixture: pd.Series,
        component_a: pd.Series,
        component_b: pd.Series,
        *,
        coeff_a: float = 0.5,
        coeff_b: float = 0.5,
        window: tuple[int, int] = (300, 1100),
    ) -> None:
        """
        Initialize a :class:`~uv_pro.binarymix.BinaryMixture` and fit a binary mixture model.

        This method fits a linear combination of UV-vis spectra from two pure species, A and B, \
        to the spectrum of a binary mixture to estimate their relative concentrations.

        Fitting is achieved by minimizing the mean squared error (MSE) between the binary mixture \
        and the linear combination of A and B.

        Parameters
        ----------
        mixture : pandas.Series
            The UV-vis spectrum of a binary mixture to fit.
        component_a : pandas.Series
            The UV-vis spectrum of pure species A.
        component_b : pandas.Series
            The UV-vis spectrum of pure species B.
        coeff_a : float, optional
            An initial guess for the scalar coefficient to \
            apply to the spectrum of species A. The defeault is 0.5.
        coeff_b : float, optional
            An initial guess for the scalar coefficient to \
            apply to the spectrum of species B. The defeault is 0.5.
        window : tuple[int, int], optional
            The range of wavelengths (in nm) to use from each spectrum, by default (300, 1100).
        """
        self.mixture = mixture.loc[window[0] : window[1] + 1]
        self.component_a = component_a.loc[window[0] : window[1] + 1]
        self.component_b = component_b.loc[window[0] : window[1] + 1]
        self.coeff_a_max = self.get_max_coefficient(self.component_a)
        self.coeff_b_max = self.get_max_coefficient(self.component_b)
        self.coeff_a, self.coeff_b = self.minimize((coeff_a, coeff_b))

    def get_max_coefficient(self, component: pd.Series) -> float:
        return self.mixture.max() / component.max()

    def linear_combination(self, a: float, b: float) -> pd.Series:
        return a * self.component_a + b * self.component_b

    def difference_spectrum(self) -> pd.Series:
        return self.mixture - self.fit

    def mean_squared_error(self) -> float:
        squared_diffs = self.difference_spectrum() ** 2
        return round(squared_diffs.sum() / len(squared_diffs.index), 5)

    def minimize(self, fit_vars: tuple[float, float]):
        """
        Fit a binary mixture.

        Determine the best fit of a binary mixture by minimizing the \
        mean squared error (MSE) of some linear combination of component A \
        and component B. See :func:`scipy.optimize.minimize`.

        Parameters
        ----------
        fit_vars : tuple[float, float]
            A tuple with initial guesses for the scalar coefficients of \
            component A and component B.
        """

        def fit_mean_squared_error(fit_vars: tuple[float, float]):
            self.fit = self.linear_combination(*fit_vars)
            squared_diffs = self.difference_spectrum() ** 2
            return squared_diffs.sum() / len(squared_diffs.index)

        opt = minimize(
            fit_mean_squared_error,
            fit_vars,
            bounds=[(0, self.coeff_a_max), (0, self.coeff_b_max)],
        )
        return opt.x
