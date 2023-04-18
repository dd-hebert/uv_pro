``uv_pro``
==========
``uv_pro`` is an all-in-one script for processing UV-Vis data files (.KD or .csv formats) created from the Agilent 845x UV-Vis Chemstation software. Spectra are imported, bad spectra (e.g., spectra collected during mixing) are removed, and the cleaned data is exported to a folder inside the user provided file path. Change the settings and provide arguments with the command line.

Required Command Line Arguments (argparse)
------------------------------------------
The global parameters are used when running ``uv_pro.py`` from the terminal (see ``main()``). Edit these with a text editor.

### ``-p``, ``--path`` : string
The path to the UV-Vis data, either a .KD file or a folder (.csv format). Should be wrapped in double quotes "".

```
python uv_pro.py "C:\\Desktop\\MyData\\myexperiment.KD" # Import from a .KD file
python uv_pro.py "C:\\Desktop\\MyData\\mydatafolder" # Import from .csv files
```

Optional Command Line Arguments (argparse)
------------------------------------------
### ``-v`` : (flag)
Enable view only mode. No data processing is performed and a plot of the data set is shown.

```
python uv_pro.py "C:\\Desktop\\MyData\\myfile.KD" -v
```

### ``-t``, ``--trim`` : 2 integers
Use ``-t`` to select a specific portion of a dataset of spectra `first last`. The ``first`` value is the index or time (in seconds) of the first spectrum to select. The ``last`` value is the index or time (in seconds) of the last spectrum to import. Set to `None` for no trimming. 

```
python uv_pro.py "C:\\Desktop\\MyData\\myfile.KD" -t 50 250
```

### ``-ct``, ``--cycle_time`` : integer
Set the cycle time in seconds from the experiment. Only required if you wish to use time (seconds) to trim datasets imported from .csv files. The cycle time is automatically detected when creating a dataset from a .KD file. The default value is 1 (same as using indexes). Note: only experiments with a constant cycle time are currently supported.

```
python uv_pro.py "C:\\Desktop\\myfile.KD" -ct 5
```

### ``-ot``, ``--outlier_threshold`` : float between 0 and 1
The threshold by which spectra are considered outliers. Values closer to 0 result in higher sensitivity (more outliers). Values closer to 1 result in lower sensitivity (fewer outliers). The default value is 0.1.

```
python uv_pro.py "C:\\Desktop\\myfile.KD" -ot 0.4
```

### ``-sl``, ``--slice_spectra`` : integer
The number of spectra to show. The default is 0, where all spectra are shown. Cuts the list of {spectra} into evenly-sized pieces. Example: if {spectra} contains 100 spectra and {num_spectra} is 10, then every tenth spectrum will be plotted.

```
python uv_pro.py "C:\\Desktop\\myfile.KD" -sl 15
```

### ``-h``, ``--help`` : flag
Use ``-h`` to get help with command line arguments.

```
python uv_pro.py -h
```

Examples
------------------------------------------
Import the data from ``myfile.KD``, set the outlier detection to 0.2, trim the data to keep only spectra from 50 seconds to 250 seconds, and show 10 slices:
```
python uv_pro.py "C:\\Desktop\\myfile.KD" -t 50 250 -ot 0.2 -sl 10
```

Import the data from the csv files in ``mydatafolder``, trim the data to keep only spectra from 50 seconds to 250 seconds, set the cycle time to 5 seconds, set the outlier detection to 0.2, and show 10 slices:
```
python uv_pro.py "C:\\Desktop\\mydatafolder" -t 50 250 -ct 5 -ot 0.2 -sl 10
```
