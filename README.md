``uv_pro``
==========
``uv_pro`` is a command line tool for processing UV-Vis data files (.KD or .csv formats) created from the Agilent 845x UV-Vis Chemstation software.

Installation
------------
``uv_pro`` can be installed directly from this repo using pip:

```
pip install git+https://github.com/dd-hebert/uv_pro.git
```

Command Line Interface
----------------------
With ``uv_pro`` installed, you can run the script directly from the command line using the ``uvp`` shortcut. To begin processing data, use ``-p`` and specify the path to your data:

**Process .KD file:**
```
uvp -p path\to\your\data.KD
```

**Process .csv files:**
```
uvp -p path\to\folder\mydatafolder
```

**Tip:** You can use shorter paths by setting a **root directory** or by simply opening a terminal session inside the same folder as your data files.


Command Line Arguments
----------------------
#### ``-p``, ``--path`` : string, required
The path to the UV-Vis data, either a .KD file or a folder (with .csv files). You have three options for specifying the path: you can use a path relative to your current working directory, an absolute path, or a path relative to the root directory (if one has been set).

___

#### ``-crd``, ``-–clear_root_dir`` : flag, optional
Reset the root directory back to the default location (in the user's home directory).

#### ``-ct``, ``--cycle_time`` : integer, optional
Set the cycle time in seconds from the experiment. See ``--trim`` argument for more details. Note: The cycle time is automatically detected when creating a dataset from a .KD file. Only experiments with a constant cycle time are currently supported.

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

#### ``-ot``, ``--outlier_threshold`` : float between 0 and 1, optional
The threshold by which spectra are considered outliers. Values closer to 0 result in higher sensitivity (more outliers). Values closer to 1 result in lower sensitivity (fewer outliers). A value of 1 will result in no outliers. The default value is 0.1.

#### ``-rd``, ``-–root_dir`` : string, optional
Set the root directory so you don’t have to type full length file paths. For example, if all your UV-Vis data files are stored inside a common folder, you can set it as the root directory. Then, the path you give with ``-p`` is assumed to be inside the root directory. With a root directory set, you'll no longer have to type the root directory portion of the file path.

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

#### ``-sec``, ``--use_seconds`` : flag, optional
Use seconds instead of spectrum #'s when trimming data.

#### ``-sl``, ``--slice_spectra`` : integer, optional
The number of spectrum slices to plot and export. The default is 0, where *all* spectra are plotted and exported. Example: if a dataset contains 250 spectra and ``-sl`` is 10, then every 25th spectrum would be plotted and exported.

#### ``-t``, ``--trim`` : 2 integers, optional
Use ``-t`` to select a specific portion of spectra. The first integer is the first spectrum to select and the second integer is the last spectrum to select. By default, trim uses spectrum #'s (indices). If ``-sec`` is also given, then trim will use seconds (time). Note: A cycle time ``-ct`` must be provided in order to use seconds to trim a dataset created from .csv files.

```
# Trim from spectrum 50 to spectrum 250
uvp -p C:\\Desktop\\MyData\\myfile.KD -t 50 250

# Trim from 50 seconds to 250 seconds
uvp -p C:\\Desktop\\MyData\\myfile.KD -t 50 250 -sec

# Trim from 50 seconds to 250 seconds
uvp -p C:\\Desktop\\MyData\\mydatafolder -ct 2 -t 50 250 -sec
# Datasets created from .csv files require a cycle time to use seconds
```

#### ``-tol``, ``-–baseline_tolerance`` : float, optional
Set the exit criteria for the baseline algorithm. Try values between 0.001 and 10000. The default is 0.1. See pybaselines.whittaker.asls() for more information.

#### ``-tr``, ``--tree`` : flag, optional
Print the ``root_directory`` file tree to the console.

#### ``-v`` : flag, optional
Enable view only mode. No data processing is performed and a plot of the data is shown.

Examples
--------
Import the data from ``myfile.KD``, set the outlier detection to 0.2, trim the data to keep the 50th spectrum to the 250th spectrum, and show 10 slices:
```
uvp -p C:\\Desktop\\myfile.KD -t 50 250 -ot 0.2 -sl 10
```

Import the data from the .csv files in ``mydatafolder``, trim the data to keep only spectra from 20 seconds to 2000 seconds, set the cycle time to 5 seconds, set the outlier detection to 0.2, and show 15 slices:
```
uvp -p C:\\Desktop\\mydatafolder -t 20 2000 -sec -ct 5 -ot 0.2 -sl 15
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
