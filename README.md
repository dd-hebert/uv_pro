``uv_pro``
==========
``uv_pro`` is a command line tool for processing UV-Vis data files (.KD or .csv formats) created from the Agilent 845x UV-Vis Chemstation software.

Installation
------------
``uv_pro`` can be installed from [The Python Package Index](https://pypi.org/).

You can install ``uv_pro`` with pip using:

```shell
pip install uv_pro
```

Command Line Interface
----------------------
With ``uv_pro`` installed, you can run the package directly from the command line.

**Process data from a .KD file:**
```shell
uvp -p "path\to\your\data.KD"
```

**Process data from .csv files:**
```shell
uvp -p "path\to\folder\mydatafolder"
```

Command Line Arguments
----------------------
### ``-p``, ``--path`` : string, required
The path to the UV-Vis data, either a .KD file or a folder (.csv format). Should be wrapped in double quotes "".

```shell
uvp -p "C:\\Desktop\\MyData\\myexperiment.KD" # Import from a .KD file
uvp -p "C:\\Desktop\\MyData\\mydatafolder" # Import from .csv files
```

### ``-r, ``-–root_dir`` : string, optional
Set a root directory for where data files are located so you don’t have to type a full file path every time. For example, if all your UV-Vis data is stored inside some directory ``C:\mydata\UV-Vis Data\``, you can set this as the root directory. Then, the path given with -p is assumed to be located inside the root directory.

**Without root directory:**
```
uvp -p "C:\mydata\UV-Vis Data\mydata.KD"
```
Without a root directory, you must type the full path to the data. With a root directory set, the root directory portion of the path can be omitted. The root directory is saved between runs as a ``.pickle`` file.

**With root directory:**
```
# Set the root directory
uvp -r "C:\mydata\UV-Vis Data"

# With the root directory
uvp -p "mydata.KD"
```

### ``-grd``, ``–-get_root_dir`` : flag, optional
Print the current root directory to the console.

```
uvp -grd
```

### ``-crd``, ``-–clear_root_dir`` : flag, optional
Clear the current root directory.

```
uvp -crd
```

### ``-v`` : flag, optional
Enable view only mode. No data processing is performed and a plot of the data set is shown.

```
uvp -p "C:\\Desktop\\MyData\\myfile.KD" -v
```

### ``-ct``, ``--cycle_time`` : integer, optional
Set the cycle time in seconds from the experiment. Only required if you wish to use time (seconds) to trim datasets imported from .csv files. The cycle time is automatically detected when creating a dataset from a .KD file. The default value is 1 (same as using indices). Note: only experiments with a constant cycle time are currently supported.

```
uvp -p "C:\\Desktop\\mydatafolder" -ct 5
```

### ``-t``, ``--trim`` : 2 integers, optional
Use ``-t`` to select a specific portion of a dataset of spectra `first last`. The ``first`` value is the index or time (in seconds) of the first spectrum to select. The ``last`` value is the index or time (in seconds) of the last spectrum to import. Units depend on if a cycle time has been provided. When working with .KD files, cycles time are automatically detected. Set to `None` for no trimming. 

```
# Trim from 50 seconds to 250 seconds
uvp -p "C:\\Desktop\\MyData\\myfile.KD" -t 50 250

# Trim from spectrum 50 to spectrum 250
uvp -p "C:\\Desktop\\MyData\\mydatafolder" -t 50 250

# Trim from 50 seconds to 250 seconds
uvp -p "C:\\Desktop\\MyData\\mydatafolder" -ct 2 -t 50 250
# Datasets created from .csv files require a cycle time to use seconds
```

### ``-ot``, ``--outlier_threshold`` : float between 0 and 1, optional
The threshold by which spectra are considered outliers. Values closer to 0 result in higher sensitivity (more outliers). Values closer to 1 result in lower sensitivity (fewer outliers). The default value is 0.1.

```
uvp -p "C:\\Desktop\\myfile.KD" -ot 0.4
```

### ``-sl``, ``--slice_spectra`` : integer, optional
The number of slices to plot and export. The default is 0, where all spectra are plotted and exported. Example: if the dataset contains 250 spectra and ``-sl`` is 10, then every 25th spectrum will be plotted and exported.

```
uvp -p "C:\\Desktop\\myfile.KD" -sl 15
```

### ``-lam``, ``-–baseline_lambda`` : float, optional
Set the smoothness of the baseline when cleaning data. Higher values give smoother baselines. Try values between 0.001 and 10000. The default is 10. See pybaselines.whittaker.asls() for more information.

### ``-tol``, ``-–baseline_tolerance`` : float, optional
Set the exit criteria for the baseline algorithm. Try values between 0.001 and 10000. The default is 0.1. See pybaselines.whittaker.asls() for more information.

### ``-lsw``, ``-–low_signal_window`` : "narrow" or "wide", optional
Set the width of the low signal outlier detection window. Set to "wide" and points directly neighboring low signal outliers will be labelled as outliers also. Default is "narrow", meaning only low signal outliers themselves are labelled. Set to "wide" if low signals are interfering with the baseline.

### ``-h``, ``--help`` : flag
Use ``-h`` to get help with command line arguments.

```
uvp -h
```

Examples
--------
Import the data from ``myfile.KD``, set the outlier detection to 0.2, trim the data to keep only spectra from 50 seconds to 250 seconds, and show 10 slices:
```
uvp -p "C:\\Desktop\\myfile.KD" -t 50 250 -ot 0.2 -sl 10
```

Import the data from the .csv files in ``mydatafolder``, trim the data to keep only spectra from 20 seconds to 2000 seconds, set the cycle time to 5 seconds, set the outlier detection to 0.2, and show 15 slices:
```
uvp -p "C:\\Desktop\\mydatafolder" -t 20 2000 -ct 5 -ot 0.2 -sl 15
```
