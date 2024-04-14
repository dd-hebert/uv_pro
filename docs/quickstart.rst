Quick Start
===========

After :doc:`installing </installation>` ``uv_pro``, all you need to start 
processing UV-Vis data is a terminal and a file path.


Process UV-Vis Data From a .KD File
-----------------------------------
If you have a .KD file called ``mydata.KD`` located in ``C:\mystuff\UV-Vis Data\``,
you can process this file by opening a terminal and entering the following command::

    uvp -p "C:\mystuff\UV-Vis Data\mydata.KD"

The file will automatically be imported, processed, and plotted.

Alternatively, you could open a terminal session inside ``C:\mystuff\UV-Vis Data\`` and use::

    uvp -p mydata.KD

.. Note::
    When parsing a .KD file, the experiment's cycle time is automatically detected.

Trim Your Data
--------------
You can ``trim`` your data to keep only a portion between a given interval. For example, if in
an experiment you collected spectra over 2000 seconds, but you only wish you keep the a portion
of the spectra, you can ``trim`` the data with ``-tr`` or ``--trim``::

    # Trim data, keeping the spectra from 100 to 1000 seconds.
    uvp -p "C:\mystuff\UV-Vis Data\mydata.KD" -tr 100 1000

Spectra outside of the time range values given with ``trim`` will be removed.

Removing Outliers
----------------------------
Often during a UV-Vis experiment, reagents are being added and the solution is being mixed,
for example during a titration experiment. Mixing and adding reagents can cause big spikes or dips
in the absorbance, and these "outlier" spectra should be removed from the final data plot.

``uv_pro`` has 4 parameters which control how outliers are identified and removed from your data:

- `outlier threshold [-ot]`_
- `baseline lambda [-bll]`_
- `baseline tolerance [-blt]`_
- `low signal window [-lsw]`_


outlier threshold [-ot]
```````````````````````
The :func:`outlier_threshold <uv_pro.process.Dataset.__init__>` can be set using the ``-ot`` or
``--outlier_threshold`` argument at the terminal::

    uvp -p "C:\mystuff\UV-Vis Data\mydata.KD" -ot 0.8
    uvp -p "C:\mystuff\UV-Vis Data\mydata.KD" --outlier_threshold 0.6

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

baseline lambda [-bll]
``````````````````````
The :func:`baseline_lambda <uv_pro.process.Dataset.__init__>` is the smoothness of the
:attr:`~uv_pro.process.Dataset.baseline`, and can be set using the ``-bll`` or ``--baseline_lambda``
argument at the terminal::

    # Set baseline smoothness.
    uvp -p "C:\mystuff\UV-Vis Data\mydata.KD" -bll 0.1
    uvp -p "C:\mystuff\UV-Vis Data\mydata.KD" --baseline_lambda 1000

Higher ``-bll`` values give smoother baselines. Try values between 0.001 and 10000. The default is 10.
See pybaselines.whittaker_ for more in-depth information. The image below shows how different values
of ``-bll`` affect the :attr:`~uv_pro.process.Dataset.baseline`:

.. image:: B3_lam_comparison.png

Notice that a smaller ``-bll`` value will give a :attr:`~uv_pro.process.Dataset.baseline` which follows
the data more closely but as a result, may also include more undesirable outlier points. Alternatively,
a value of ``-bll`` that is too large will give a :attr:`~uv_pro.process.Dataset.baseline` that is too
smooth and not follow the data closely enough. In general, the ``-bll`` value required to fit the
:attr:`~uv_pro.process.Dataset.baseline` will increase as the number of data points increases.


baseline tolerance [-blt]
`````````````````````````
The :func:`baseline_tolerance <uv_pro.process.Dataset.__init__>` specifies the exit criteria of the
:attr:`~uv_pro.process.Dataset.baseline` detection algorithm (see: pybaselines.whittaker.asls_), and
can be set using the ``-blt`` or ``--baseline_tolerance`` argument at the terminal::

    # Set the baseline tolerance.
    uvp -p mydata.KD -blt 0.01
    uvp -p mydata.KD --baseline_tolerance 10

Try ``-blt`` values between 0.001 and 10000. The default is 0.1.
See pybaselines.whittaker_ for more in-depth information.


low signal window [-lsw]
````````````````````````
The :func:`low_signal_window <uv_pro.process.Dataset.__init__>` sets the width of the low signal detection
window (see: :meth:`~uv_pro.process.Dataset.find_outliers()`). A low signal outlier is a spectrum which has very
low total absorbance across all captured wavelengths, which typically occurs when the sample is removed from the
spectrometer. Removing low signal outliers is important because the baseline algorithm gives
`preferential weighting to negative peaks`__. The presence of negative peaks in your data will significantly affect
the data cleaning routine.
You can set the size of the window using the ``-lsw`` or ``--low_signal_window`` argument at the terminal::

    # Set the low signal outlier window size.
    uvp -p mydata.KD -lsw "wide"
    uvp -p mydata.KD --low_signal_window "narrow"  # default

The default size is ``"narrow"``, meaning only the spectra with low total absorbance are considered
low signal outliers. If the size is set to ``"wide"``, then the spectra immediately neighboring a low signal
outlier are also considered :attr:`~uv_pro.process.Dataset.outliers`. The image below illustrates
the effect of changing the size of the low signal outlier window:

.. image:: C2_lsw_comparison.png

In the left plot, you'll notice that the baseline (depicted as the light blue region) doesn't closely follow
the data due to certain problematic data points, indicated by magenta circles. These points aren't considered
low signal outliers (circled in green). In the right plot, we've adjusted the window size to ``"wide"``.
As a result, the points immediately before and after each low signal outlier are also counted as
:attr:`~uv_pro.process.Dataset.outliers`. Consequently, the :attr:`~uv_pro.process.Dataset.baseline` now follows
the data more closely. However, it's worth noting that several valid data points in this
:class:`~uv_pro.process.Dataset` are still incorrectly classified as
:attr:`~uv_pro.process.Dataset.outliers`. While altering the size of the low signal outlier window has improved
the situation, further adjustments to other :attr:`~uv_pro.process.Dataset.baseline` parameters are needed to
achieve a better fit.

In general, the default ``"narrow"`` window size works well when the dips in the absorbance are sharp. If the
dips are broader, a ``"wide"`` window may be necessary. Keep in mind that using a wider window has a side effect:
more spectra will be categorized as  :attr:`~uv_pro.process.Dataset.outliers` and removed from
the final plot. However, this is primarily a concern when working with smaller datasets that contain fewer spectra.

.. _pybaselines.whittaker: https://pybaselines.readthedocs.io/en/latest/algorithms/whittaker.html
.. _pybaselines.whittaker.asls: https://pybaselines.readthedocs.io/en/latest/algorithms/whittaker.html#asls-asymmetric-least-squares
__ pybaselines.whittaker.asls_

Examples
--------
Import the data from ``myfile.KD``, set the outlier detection to 0.2, trim the data to keep only spectra
from 50 seconds to 250 seconds, and show 10 slices::

    uvp -p C:\Desktop\myfile.KD -tr 50 250 -ot 0.2 -sl 10

Import the data from ``myfile.KD``, trim the data to keep only spectra from 0 seconds to 750 seconds, change baseline
parameters, show 25 slices, and get time traces for 780 nm and 1020 nm::

    uvp -p C:\Desktop\myfile.KD -tr 0 750 -bll 10 -blt 0.1 -sl 25 -tt 780 1020

The arguments are flexible and can be used in basically any order (except ``-p`` which must come first). However, each argument
should only occur once.