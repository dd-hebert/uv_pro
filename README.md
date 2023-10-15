``uv_pro``
==========
![Banner logo](/docs/banner_logo1.png?raw=true "Banner Logo")

``uv_pro`` is a command line tool for processing UV-Vis data files (.KD format) created from the Agilent 845x UV-Vis Chemstation software.

Contents
--------
- [Installation](#installation)
- [Command Line Interface](#command-line-interface)
- [Command Line Arguments](#command-line-arguments)
- [Examples](#examples)
- [Multiview Mode](#multiview-mode)
- [Uninstall](#uninstall)

Installation
------------
``uv_pro`` can be installed directly from this repo using pip:

```
pip install git+https://github.com/dd-hebert/uv_pro.git
```

Command Line Interface
----------------------
With ``uv_pro`` installed, you can run the script directly from the command line using the ``uvp`` shortcut. To begin processing data, use ``-p`` and specify the path to your data:
```
uvp -p path\to\your\data.KD
```

**Tip:** You can use shorter paths by setting a **root directory** or by simply opening a terminal session inside the same folder as your data files.

Command Line Arguments
----------------------
#### ``-p``, ``--path`` : string, required
The path to a .KD file. You have three options for specifying the path: you can use a path relative to your current working directory, an absolute path, or a path relative to the root directory (if one has been set).

___

#### ``-crd``, ``-–clear_root_dir`` : flag, optional
Reset the root directory back to the default location (in the user's home directory).

#### ``-fp``, ``--file_picker`` : flag, optional
Interactively pick a .KD file from the terminal. The file is opened in view only mode.

#### ``-grd``, ``–-get_root_dir`` : flag, optional
Print the current root directory to the console.

#### ``-h``, ``--help`` : flag
Use ``-h`` to get help with command line arguments.

#### ``-lam``, ``-–baseline_lambda`` : float, optional
Set the smoothness of the baseline when cleaning data. Higher values give smoother baselines. Try values between 0.001 and 10000. The default is 10. See pybaselines.whittaker.asls() for more information.

#### ``-lsw``, ``-–low_signal_window`` : "narrow" or "wide", optional
Set the width of the low signal outlier detection window. Set to "wide" and points which directly neighbor low signal outliers will also be considered outliers. Default is "narrow", meaning only low signal outliers themselves are considered outliers. Set to "wide" if low signals are interfering with the baseline.

#### ``-ne``, ``--no_export`` : flag, optional
Bypass the data export prompt at the end of the script.

#### ``-ot``, ``--outlier_threshold`` : float between 0 and 1, optional
The threshold by which spectra are considered outliers. Values closer to 0 result in higher sensitivity (more outliers). Values closer to 1 result in lower sensitivity (fewer outliers). A value of 1 will result in no outliers. The default value is 0.1.

#### ``-rd``, ``-–root_dir`` : string, optional
Specify a root directory to simplify file path entry. For instance, if you store all your UV-Vis data files in a common folder, you can designate it as the root directory. Subsequently, any path provided with ``-p`` is assumed to be relative to the root directory.

**Without root directory:**
```
# Must type full file path
uvp -p "C:\mydata\UV-Vis Data\mydata.KD"
```

Without a root directory, you must type the full path to the data. 

**With root directory:**
```
# Set the root directory
uvp -rd "C:\mydata\UV-Vis Data"

# Only need short file path
uvp -p mydata.KD
```

By setting a root directory, you can omit the root directory part of the path. The root directory is saved between runs in a config file.

#### ``-sl``, ``--slice_spectra`` : integer, optional
The number of spectrum slices to plot and export. The default is 0, where *all* spectra are plotted and exported. Example: if a dataset contains 250 spectra and ``-sl`` is 10, then every 25th spectrum would be plotted and exported.

#### ``-t``, ``--trim`` : 2 integers, optional
Use ``-t`` to select spectra within a given time range. The first integer is the beginning of the time range and the second integer is the end. The spectra outside the given time range will be removed.

```
# Trim from 50 seconds to 250 seconds
uvp -p C:\\Desktop\\MyData\\myfile.KD -t 50 250
```

#### ``-tol``, ``-–baseline_tolerance`` : float, optional
Set the exit criteria for the baseline algorithm. Try values between 0.001 and 10000. The default is 0.1. See pybaselines.whittaker.asls() for more information.

#### ``-tr``, ``--tree`` : flag, optional
Print the ``root_directory`` file tree to the console.

#### ``-tt``, ``--time_traces`` : arbitrary number of ints, optional
Specify wavelengths to create time traces for.

#### ``-tti``, ``--time_trace_interval`` : int, optional
Set the interval (in nm) when creating time traces for outlier detection. An interval of 20 would create time traces like: (window min, window min + 20, ... , window max - 20, window max). Smaller intervals will increase loading times. Default is 10.

#### ``-ttw``, ``--time_trace_window`` : int int, optional
Set the wavelength range (min, max) (in nm) for time traces during outlier detection. The default is (300, 1060).

#### ``-v`` : flag, optional
Enable view only mode. No data processing is performed and a plot of the data is shown.

Examples
--------
Import the data from ``myfile.KD``, set the outlier detection to 0.2, trim the data to keep the spectra from 50 seconds to 250 seconds, and show 10 slices:
```
uvp -p C:\\Desktop\\myfile.KD -t 50 250 -ot 0.2 -sl 10
```

Multiview Mode
--------------
You can open multiple .KD files (in view-only mode) from the command line at once with the ``Multiviewer`` script. Navigate to a directory containing .KD files and run the command:
```
uvpmv -f some search filters
```

The script will open .KD files which contain any of the supplied search filters in view_only mode.

The default search behavior is an *OR* search. You can use supply the ``-a`` or ``--and_filter`` argument to perform an *AND* search:
```
uvpmv -f some search filters -a
```

Now only .KD files with contain *all* of the search filters in their name will be opened.

**Examples:**
```
uvpmv -f copper DMF
```
OR search, open .KD files with ``copper`` *OR* ``DMF`` in their filename.

```
uvpmv -f copper DMF TEMPOH -a
```
AND search, open .KD files with ``copper``, ``DMF``, *AND* ``TEMPOH`` in their filename.

Uninstall
---------
To uninstall ``uv_pro``, run the following command:
```
pip uninstall uv_pro
```
