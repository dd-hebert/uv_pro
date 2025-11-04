![Banner logo](/docs/banner_logo1.png?raw=true "Banner Logo")
=============================================================

``uv_pro`` is a feature-rich command line tool for processing UV-Vis data files (``.KD`` format) created from the Agilent 845x UV-Vis Chemstation software.

Key Features
------------
✅ Parse ``.KD`` files and export as ``.csv``

✅ UV-vis data processing (truncate and slice datasets, extract time traces)

✅ Outlier detection tools

✅ Interactive plotting with Matplotlib

✅ Peak detection

✅ Batch export of spectra to .csv files

✅ Kinetic analysis (exponential fitting, initial rates)

✅ Binary mixture fitting

✅ Figure creation tools

Contents
--------
- [Installation](#installation)
- [Command Line Interface](#command-line-interface)
- [Command Line Arguments](#command-line-arguments)
- [Examples](#examples)
- [File Paths & Root Directory](#file-paths--root-directory)
- [Multiview Mode](#multiview-mode)
- [Uninstall](#uninstall)

Installation
------------
Clone this repo and use [setuptools](https://setuptools.pypa.io/en/latest/userguide/quickstart.html) and [build](https://pypi.org/project/build/) to build the package (``python -m build``) then use pip to install the resulting ``.whl`` file.

Command Line Interface
----------------------
With ``uv_pro`` installed, you can run the script directly from the command line using the ``uvp`` shortcut. To begin processing data, use ``p`` and specify the path to your data:

```
uvp p path\to\your\data.KD
```

**Tip:** You can use shorter paths by setting a [**root directory**](#file-paths--root-directory) or by simply opening a terminal session inside the same directory as your data files.

Command Line Arguments
----------------------
- [Data Processing Args (process, proc, p)](#data-processing-args-process-proc-p)
- [Batch Exporting Args (batch)](#batch-exporting-args-batch)
- [Peak Detection Args (peaks)](#peak-detection-args-peaks)
- [Binary Mixture Fitting Args (binmix)](#binary-mixture-fitting-args-binmix)
- [User Config Args (config, cfg)](#user-config-args-config-cfg)
- [Other Args](#other-args-and-subcommands)

### Data Processing Args (process, proc, p)
Process UV-vis data with the ``process`` subcommand.

**Usage:**
``uvp process <path> <options>``, ``uvp proc <path> <options>``, or ``uvp p <path> <options>``

#### ``path`` : string, required
The path to a .KD file. You have three options for specifying the path: you can use a **path relative to the current working directory**, an **absolute path**, or a **path relative to the root directory** (if one has been set).

#### ``-bs``, ``-–baseline-smoothness`` : float, optional
Set the smoothness of the baseline (for outlier detection). Higher values give smoother baselines. Try values between 0.001 and 10000. The default is 10. See [pybaselines.whittaker.asls()](https://pybaselines.readthedocs.io/en/latest/algorithms/whittaker.html#asls-asymmetric-least-squares) for more information.

#### ``-bt``, ``-–baseline-tolerance`` : float, optional
Set the exit criteria for the baseline algorithm. Try values between 0.001 and 10000. The default is 0.1. See pybaselines.whittaker.asls() for more information.

#### ``-c``, ``--colormap`` : str, optional
Set the colormap for the processed spectra plot. Accepts any built-in Matplotlib colormap name. See [Matplotlib colormaps](https://matplotlib.org/stable/tutorials/colors/colormaps.html) for more information on colormap options. Default is 'default'.

#### ``-fx``, ``--fit-exponential`` : flag, optional
Perform an exponential fitting of time traces. You must specify the wavelengths to fit with the ``-tt`` argument. 

#### ``-lw``, ``-–low-signal-window`` : narrow, wide, or none, optional
Set the width of the low signal outlier detection window. Set to ``wide`` if low signals are interfering with the baseline. The default is ``narrow``. If set to ``none``, low signal outlier detection is skipped. This is useful when processing spectra with very low absorbance across a majority of measured wavelengths.

#### ``-ne``, ``--no-export`` : flag, optional
Bypass the data export prompt at the end of the script.

#### ``-ot``, ``--outlier-threshold`` : float between 0 and 1, optional
The threshold by which spectra are considered outliers. Values closer to 0 will produce more outliers, while values closer to 1 will produce fewer outliers. A value of 1 will produce no outliers. The default value is 0.1.

#### ``-qf``, ``--quick-fig`` : flag, optional
Generate (and optionally export) a quick figure with a custom plot title and other settings.

#### ``-sl``, ``--slice`` : integer, optional
Reduce the dataset down to a number of equally-spaced "slices". Example: if a dataset contains 250 spectra and ``-sl`` is 10, then every 25th spectrum will be plotted and exported. The default is ``None``, where *all* spectra are plotted and exported (no slicing).

#### ``-ssl``, ``--specific-slice`` : abritrary number of floats, optional
Select spectra slices at specific times. The default is ``None``, where *all* spectra are plotted and exported (no slicing).

#### ``-tr``, ``--trim`` : 2 integers, optional
Remove spectra outside a given time range. The first integer is the beginning of the time range and the second integer is the end.

```
# Trim before 50 seconds and after 250 seconds
uvp p C:\\Desktop\\MyData\\myfile.KD -tr 50 250
```

#### ``-tt``, ``--time-traces`` : arbitrary number of ints, optional
Get time traces for the specified wavelengths. These time traces are independent from the time traces used for outlier detection.

#### ``-ti``, ``--time-trace-interval`` : int, optional
Set the time trace wavelength interval (in nm). An interval of 20 would create time traces like: (window min, window min + 20, ... , window max - 20, window max). Smaller intervals may result in increased loading times. Default is 10. These time traces are used for outlier detection.

#### ``-tw``, ``--time-trace-window`` : int int, optional
Set the time trace wavelength range (min, max) (in nm). The default is (300, 1060). These time traces are used for outlier detection.

#### ``-v`` : flag, optional
Enable *view-only* mode. No data processing is performed and a plot of the data is shown.

#### ``-vsl``, ``--variable-slice`` : float float, optional
Reduce the dataset down to a number of unequally-spaced "slices". Takes two float values ``coefficient`` and ``exponent``. The step size between slices is calculated by the formula ``step_size = coefficient*x^exponent + 1``. This option allows you to create slices with progressively changing intervals, based on the power function defined by the coefficient and exponent. This slicing mode is ideal when there are rapid changes in absorbance at the beginning or end of the experiment, such as a fast decay.  

Use a small coefficient (<=1) and positive exponent (>1) when slicing spectra that change rapidly in the beginning and slowly at the end. Large coefficients (>5) and negative exponents (<-1) work best for spectra that change slowly in the beginning and rapidly at the end. The default is ``None``, where *all* spectra are plotted or exported (no slicing).

___
### Batch Exporting Args (batch)
Batch export UV-vis data from .KD files in the current working directory. Currently, only batch exporting of time traces is supported.

**Usage:** ``uvp batch <wavelengths> <options>``

#### ``wavelengths`` : arbitrary number of ints, required
A list of time trace wavelengths (in nm) to export.

#### ``-f``, ``--search_filters`` : arbitrary number of strings, optional
A sequence of search filter strings. For example, passing ``-f copper A`` will select .KD files which contain 'copper' OR 'A' in their filename. Passing no filters selects all .KD files in the current working directory.

___
### Peak Detection Args (peaks)
Find peaks in UV-vis spectra with the ``peaks`` subcommand.

**Usage:**
``uvp peaks <path> <options>``

#### ``path`` : str, required
A path to a UV-vis Data File (.KD format).

#### ``-conc``, ``--concentration`` : float, optional
The molar concentration of the species in the spectrum. Used for calculating molar absorptivity (ε). Default is None.

#### ``-dist``, ``--distance`` : int, optional
Set the minimum distance between peaks (in nm). Default is 10. Only used with ``localmax`` method.

#### ``--max_iter`` : int, optional
The max number of peak finding iterations. The default is 1000. Only used with ``localmax`` method.

#### ``--method`` : str, optional
The peak detection method: either ``localmax`` or ``deriv``. Default is ``localmax``.

#### ``-num``, ``--num_peaks`` : int, optional
The number of peaks that should be found. Default is 0 (find all peaks). Only used with ``localmax`` method.

#### ``-prom``, ``--prominance`` : float, optional
Set the minimum peak prominance. Default is 0. Only used with ``localmax`` method.

#### ``-pwin``, ``--peak_window`` : 2 integers, optional
Set the (min, max) peak detection window (in nm). Search for peaks within the given wavelength range. Default is None (search whole spectrum).

#### ``-swin``, ``--smooth_window`` : int, optional
Set the Savitzky-Golay smoothing window. Default is 15. See [scipy.signal.savgol_filter()](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.savgol_filter.html#savgol-filter) for more information.

___
### Binary Mixture Fitting Args (binmix)
Estimate the relative concentrations of two species in a binary mixture with the ``binmix`` subcommand.

**Usage:**
``uvp binmix <path> <component_a> <component_b> <options>``

#### ``path`` : str, required
Path to a UV-vis data file (.csv format) of one or more binary mixture spectra.

#### ``component_a`` : str, required
Path to a UV-vis spectrum (.csv format) of pure component "A".

#### ``component_b`` : str, required
Path to a UV-vis spectrum (.csv format) of pure component "B".

#### ``-a``, ``--molarity_a`` : float, optional
Specify the concentration (in M) of pure component "A".

#### ``-b``, ``--molarity_b`` : float, optional
Specify the concentration (in M) of pure component "B".

#### ``-cols``, ``--columns`` : arbitrary number of str, optional
Specify the columns of the binary mixture .csv file to perform fitting on. Provide the label (header) for each column. Default is None (fit all columns).

#### ``-icols``, ``--index_columns`` : arbitrary number of ints, optional
Specify the columns of the binary mixture .csv file to perform fitting on. Provide the index for each column. Default is None (fit all columns).

#### ``-win``, ``--window`` : int int, optional
Set the range of wavelengths (in nm) to use from the given spectra for fitting. Default is (300, 1100).

#### ``-i``, ``--interactive`` : flag, optional
Enable interactive mode. Show an interactive matplotlib figure of the binary mixture fitting.

___
### User Config Args (config, cfg)
View, edit, or reset user-configured settings with the ``config`` subcommand.

**Usage:**
``uvp config <option>`` or ``uvp cfg <option>``

Current user-configurable settings:

- ``root_directory`` - A base directory which contains UV-vis data files. Set a root directory to enable the use of shorter, relative file paths.

- ``plot_size`` - The size of the 2-by-2 plot shown after data processing. Two integers: ``WIDTH HEIGHT``

- ``primary_color`` - The main color used in terminal output. Can be set to any of the 8 basic ANSI colors.

#### ``--delete`` : flag, optional
Delete the config file and directory. The config file is located in ``.config/uv_pro/`` inside the user's home directory.

#### ``-e``, ``--edit`` : flag, optional
Edit configuration settings. Will prompt the user for a selection of configuration settings to edit.

#### ``-l``, ``--list`` : flag, optional
Print the current configuration settings to the console.

#### ``-r``, ``--reset`` : flag, optional
Reset configuration settings back to their default value. Will prompt the user for a selection of configuration settings to reset.

### Other args and subcommands
Other miscellaneous args and subcommands.
___
#### ``-h``, ``--help`` : flag, optional
Use ``-h`` to get help with command line arguments. Get help for specific commands with ``uvp <command> -h``.

#### ``browse``, ``br`` : subcommand
Interactively pick a .KD file from the terminal. The file is opened in *view-only* mode. The file must be located somewhere inside the root directory. Usage: ``uvp browse`` or ``uvp br``.

#### ``tree`` : subcommand
Print the root directory file tree to the console. Usage: ``uvp tree``.

#### ``--list-colormaps`` : flag, optional
List available colormaps. Usage: ``uvp --list-colormaps``.

Examples
--------
Process the data in ``myfile.KD``, set the outlier detection to 0.2, trim the data to keep the spectra from 50 seconds to 250 seconds, and show 10 slices:
```
uvp p C:\\Desktop\\myfile.KD -tr 50 250 -ot 0.2 -sl 10
```
Process the data in ``somefile.KD``, trim the data to keep the spectra from 20 seconds to 120 seconds, show 15 slices, get time traces for 390, 450, 670 nm, and fit an exponential function to the specified time traces:
```
uvp p C:\\Desktop\\data\\somefile.KD -tr 20 120 -sl 15 -tt 390 450 670 -fx
```

File Paths & Root Directory
---------------------------
``uv_pro`` is flexible in handling file paths. When you give a path at the terminal, you can provide a full absolute path:
```
uvp p C:\full\path\to\your\data\file.KD
```
Alternatively, you can open a terminal session inside a directory containing a data file and use a relative path:
```
# Current working directory = C:\full\path\to\your\data
uvp p file.KD
```

Setting a root directory can simplify file path entry. For instance, if you store all your UV-Vis data files in a common folder, you can designate it as the root directory. Subsequently, any path provided with ``process`` can be given relative to the root directory.

***Without* root directory:**
```
# Must type full file path
uvp p "C:\mydata\UV-Vis Data\mydata.KD"
```

Without a root directory, you must type the full path ``"C:\mydata\UV-Vis Data\mydata.KD"`` to the data. 

***With* root directory:**
```
# Set the root directory.
uvp config -edit

# Select the root directory setting and enter the desired path, for example:
"C:\mydata\UV-Vis Data"

# Now, a shorter relative path can be used.
uvp p mydata.KD
```

With a root directory set, for example ``"C:\mydata\UV-Vis Data"``, you can omit that part of the path and just give a relative path ``mydata.KD``. The root directory is saved between runs in a config file.

Multiview Mode
--------------
You can open multiple .KD files (in *view-only* mode) simultaneously with the ``multiviewer`` subcommand. Navigate to a directory containing .KD files and run the command:
```
uvp mv -f some search filters
```

The script will open .KD files which contain any of the supplied search filters in *view-only* mode. You can omit the ``-f`` argument to open *all* .KD files in the current working directory.

The default search behavior is an *OR* search. You can use the ``-a`` or ``--and-filter`` argument to perform an *AND* search:
```
uvp mv -f some search filters -a
```

Now only .KD files with contain *all* of the search filters in their name will be opened.

**Examples:**
```
uvp mv -f copper DMF
```
OR search, open .KD files with ``copper`` *OR* ``DMF`` in their filename.

```
uvp mv -f copper DMF TEMPOH -a
```
AND search, open .KD files with ``copper``, ``DMF``, *AND* ``TEMPOH`` in their filename.

Uninstall
---------
To uninstall ``uv_pro``, run the following command:
```
pip uninstall uv_pro
```
Uninstalling ``uv_pro`` does not delete its config file. To delete the config file, first run:
```
uvp config -delete
```
Before uninstalling the package with pip.
