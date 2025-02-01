Quick Start
===========

After :doc:`installing </installation>` ``uv_pro``, all you need to start 
processing UV-Vis data is a terminal and a file path.


Process UV-Vis Data From a .KD File
-----------------------------------
If you have a .KD file called ``mydata.KD`` located in ``C:\mystuff\UV-Vis Data\``,
you can process this file by opening a terminal and entering the following command::

    uvp process "C:\mystuff\UV-Vis Data\mydata.KD"

The file will automatically be imported, processed, and plotted.

Alternatively, you could open a terminal session inside ``C:\mystuff\UV-Vis Data\`` and use::

    uvp process mydata.KD

.. Note::
    Most subcommands have shorthand alternatives, for example you can use ``p`` or ``proc`` in place
    of ``process``.

.. Note::
    When parsing a .KD file, the experiment's cycle time is automatically detected.

Trim Your Data
--------------
You can trim your data to remove spectra outside a given time range. For example, if you collected
spectra over 2000 seconds but only want to keep the data between 10 seconds and 100 seconds,
you can use ``-tr 10 100`` or ``--trim 10 100``::

    # Trim data, keeping the spectra from 100 to 1000 seconds.
    uvp p "C:\mystuff\UV-Vis Data\mydata.KD" -tr 100 1000

Spectra outside of the time range given with ``trim`` will be removed.

Data Slicing
------------
You can use slicing to reduce the data down to a selection of slices. Slices can be taken at equally- or
unequally-spaced (gradient) intervals (see :func:`slice_spectra <uv_pro.slicing.slice_spectra>`).
For example, if you collected 200 spectra but only want to plot 10, you can use ``-sl 10`` or
``--slice_spectra 10``::

    # Get 10 equally-spaced slices.
    uvp p "C:\mystuff\UV-Vis Data\mydata.KD" -sl 10


Alternatively, unequally-spaced slicing (gradient slicing ``-vsl`` or ``--variable-slice``) can be performed.
Gradient slicing works best in situations where the spectra change very rapidly at the beginning of an
experiment and slowly at the end (or vice versa). For gradient slicing, the step size between slices
is calculated by the equation:

.. math::
    \mathrm{step size} = a * x^b + 1.

Gradient slicing requires two values, a coefficient (*a*) and an exponent (*b*). Use a small coefficient
(<=1) and positive exponent (>1) for spectra that change rapidly in the beginning and slowly at the end.
On the other hand, a large coefficient (>5) and negative exponent (<-1) work best for spectra that change
slowly in the beginning and rapidly at the end.

Example::

    # Take unequally-spaced slices
    uvp p "C:\mystuff\UV-Vis Data\mydata.KD" -vsl 0.5 2


Removing Outliers
-----------------
Often during a UV-Vis experiment, reagents are being added and the solution is being mixed,
for example during a titration experiment. Mixing and adding reagents can cause big spikes or dips
in the absorbance, and these "outlier" spectra should be removed from the final data plot.

``uv_pro`` has 4 parameters which control how outliers are identified and removed from your data:

- `outlier threshold [-ot]`_
- `baseline smoothness [-bs]`_
- `baseline tolerance [-bt]`_
- `low signal window [-lw]`_


outlier threshold [-ot]
```````````````````````
The :func:`outlier_threshold <uv_pro.process.Dataset.__init__>` can be set using the ``-ot`` or
``--outlier-threshold`` argument::

    uvp p "C:\mystuff\UV-Vis Data\mydata.KD" -ot 0.8
    uvp p "C:\mystuff\UV-Vis Data\mydata.KD" --outlier-threshold 0.6

The default :func:`outlier_threshold <uv_pro.process.Dataset.__init__>` is 0.1.

The outlier threshold is a float value from 0 to 1 and is represented by the blue-filled region in the
**Combined Time Traces & Baseline** plot, shown in the image below: 

.. image:: test_data_ot_comparison.png

Points along the **combined time trace** (black line) that fall outside the blue-filled region are
considered :attr:`~uv_pro.process.Dataset.outliers` (marked with red X's in the
:func:`2x2 plot <uv_pro.plots.plot_2x2()>`).

    - *Increasing* the outlier threshold will catch *fewer* outliers.
    - *Decreasing* the outlier threshold will catch *more* outliers.

You can use a large outlier threshold >>1 to guarantee no points are considered outliers.

baseline smoothness [-bs]
`````````````````````````
The :func:`baseline_smoothness <uv_pro.process.Dataset.__init__>` is the smoothness of the
:attr:`~uv_pro.process.Dataset.baseline`, and can be set using the ``-bs`` or ``--baseline-smoothness``
argument::

    # Set baseline smoothness.
    uvp p "C:\mystuff\UV-Vis Data\mydata.KD" -bs 0.1
    uvp p "C:\mystuff\UV-Vis Data\mydata.KD" --baseline-smoothness 1000

Higher ``-bs`` values give smoother baselines. Try values between 0.001 and 10000. The default is 10.
See pybaselines.whittaker_ for more in-depth information. The image below shows how different values
of ``-bs`` affect the :attr:`~uv_pro.process.Dataset.baseline`:

.. image:: B3_lam_comparison.png

Notice that a smaller ``-bs`` value will give a :attr:`~uv_pro.process.Dataset.baseline` which follows
the data more closely but as a result, may also include more undesirable outlier points. Alternatively,
a value of ``-bs`` that is too large will give a :attr:`~uv_pro.process.Dataset.baseline` that is too
smooth and not follow the data closely enough. The default value works fairly well in most cases.


baseline tolerance [-bt]
````````````````````````
The :func:`baseline_tolerance <uv_pro.process.Dataset.__init__>` specifies the exit criteria of the
:attr:`~uv_pro.process.Dataset.baseline` detection algorithm, and can be set using the ``-bt`` or
``--baseline-tolerance`` argument::

    # Set the baseline tolerance.
    uvp p mydata.KD -bt 0.01
    uvp p mydata.KD --baseline-tolerance 10

Try ``-bt`` values between 0.001 and 10000. The default is 0.1. See pybaselines.whittaker_ for
more in-depth information.


low signal window [-lw]
```````````````````````
The :func:`low_signal_window <uv_pro.process.Dataset.__init__>` sets the width of the low signal detection
window (see: :meth:`~uv_pro.process.Dataset.find_outliers()`). Low signal outliers are spectra with have close to zero
absorbance across all wavelengths. These typically occur if the cuvette is removed from the instrument during data
collection, resulting in an abrupt dip in all time traces. Removing these outliers is important because their presence
can significantly impact the baseline fitting and outlier detection. Low signal outlier detection is not performed by default.

You can set the size of the window using the ``-lw`` or ``--low-signal-window`` argument::

    # Set the low signal outlier window size.
    uvp p mydata.KD -lw wide
    uvp p mydata.KD -lw narrow
    uvp p mydata.KD -lw none  # skip low signal outlier detection (default)

A ``"narrow"`` window size flags the spectra with low absorbance across all wavelengths as low signal outliers
to be removed during data processing. With the ``"wide"`` window size, one spectrum before and after a detected low signal
outlier are also removed. The image below illustrates the effect of changing the size of the low signal outlier window:

.. image:: C2_lsw_comparison.png

In the left plot, notice how the baseline (depicted as the light blue region) doesn't closely follow
the data due to certain problematic data points, shown in the magenta circles. These points aren't considered
low signal outliers (circled in green). In the right plot, we've adjusted the window size to ``"wide"``.
As a result, the points immediately before and after each low signal outlier are also counted as
:attr:`~uv_pro.process.Dataset.outliers`. Consequently, the :attr:`~uv_pro.process.Dataset.baseline` now follows
the data more closely. However, it's worth noting that several valid data points in this
:class:`~uv_pro.process.Dataset` are still incorrectly classified as
:attr:`~uv_pro.process.Dataset.outliers`. While altering the size of the low signal outlier window has improved
the situation, further adjustments to other :attr:`~uv_pro.process.Dataset.baseline` parameters are needed to
achieve a better fit.

In general, a ``"narrow"`` window size works well when the dips in the absorbance are sharp. If the
dips are more broad, a ``"wide"`` window may be necessary. Keep in mind that using a wider window has a side effect:
more spectra will be categorized as  :attr:`~uv_pro.process.Dataset.outliers` and removed from
the final plot. However, this is usually only a concern when working with smaller datasets with few spectra.

.. Note::
    By default, low signal outlier detection is not performed.

Exponential Fitting
-------------------
You can perform exponential fitting on time traces using ``-fx`` or ``--fit-exponential``. The wavelengths to fit must be
given with ``-tt`` or ``--time-traces``::

    # Perform exponential fitting on time traces at 450 nm and 780 nm
    uvp p "C:\mystuff\UV-Vis Data\mydata.KD" -tt 450 780 -fx

Exponential fitting is performed using scipy.optimize.curve_fit_, which attempts to fit the function

.. math::
    \mathrm{Abs}_t = \mathrm{Abs_f} + (\mathrm{Abs_0} - \mathrm{Abs_f})e^{-k_{obs}t}

The fitting parameters are printed to the console and are also displayed in the **Time Traces** subplot
(see :func:`2x2 plot <uv_pro.plots.plot_2x2()>`).

Examples
--------
Import the data from ``myfile.KD``, set the outlier detection to 0.2, trim the data to keep only spectra
from 50 seconds to 250 seconds, and show 10 slices::

    uvp p C:\Desktop\myfile.KD -tr 50 250 -ot 0.2 -sl 10

Import the data from ``myfile.KD``, trim the data to keep only spectra from 0 seconds to 750 seconds, change baseline
parameters, show 25 slices, and get time traces for 780 nm and 1020 nm::

    uvp p C:\Desktop\myfile.KD -tr 0 750 -bs 10 -bt 0.1 -sl 25 -tt 780 1020

The arguments for ``process`` are flexible and can be used in basically any order (except the path which must come first). However, each argument
should only occur once.

.. _pybaselines.whittaker: https://pybaselines.readthedocs.io/en/latest/algorithms/whittaker.html
.. _scipy.optimize.curve_fit: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html