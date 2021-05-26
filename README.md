# IceTray in a nutshell

IceTray is IceCube's processing framework, used for both data (online at Pole, and offline in the North) and simulation. The code lives [on GitHub](https://github.com/icecube/icetray) and [documentation on docs.icecube.aq](https://docs.icecube.aq/icetray/main/).

## Preliminaries: connecting to IceCube interactive nodes

Code snippets in the tutorial below are intended to be executed on interactive nodes at WIPAC, since they use the Lustre filesystem at `/data/user`.

### WIPAC

If you have not already done so, you may want to set up ssh tunnelling can connect directly to hosts behind the WIPAC firewall. Something like the following should be in your .ssh/config:

```ssh-config
Host pub*.icecube.wisc.edu
   ProxyJump none

Host *.icecube.wisc.edu
   User your_user_name
   ProxyJump pub.icecube.wisc.edu
```

where `your_user_name` is your WIPAC login. This causes e.g. `ssh cobalt05.icecube.wisc.edu` to proxy its connections through `pub.icecube.wisc.edu`. You may also wish to [set up public key authentication](https://www.ssh.com/academy/ssh/copy-id) so that you don't have to type your password when logging in. In short:

```console
> ssh-keygen
> ssh-copy-id pub.icecube.wisc.edu
```

This will generate a public/private keypair, and copy the public key to your ~/.ssh directory on the remote system to it can be used to authenticate you. You should protect your private key with a passphrase; otherwise, your key can be stolen and used to impersonate you. You can [use ssh-agent to avoid re-typing your password every time you need your ssh key](https://www.freecodecamp.org/news/the-ultimate-guide-to-ssh-setting-up-ssh-keys/).

### DESY Zeuthen

The setup for DESY Zeuthen is similar:

```ssh-config
Host pub*.zeuthen.desy.de transfer.zeuthen.desy.de transfer.ifh.de
        ProxyJump none

Host *.ifh.de *.zeuthen.desy.de
        User your_user_name
        GSSAPIAuthentication yes
        GSSAPIDelegateCredentials yes
        ProxyJump pub2.zeuthen.desy.de
```

Note that home directories are stored in AFS, so you can't use standard public key authentication. Before connecting, you need to create a Kerberos token on your local machine with `kinit your_user_name@IFH.DE`, where `your_user_name` is your DESY username. Note that the capitalization in `IFH.DE` is important. Thereafter, e.g. `ssh ice-wgs1.ifh.de` will use your local Kerberos token to authenticate, and proxy connections through `pub2.zeuthen.desy.de`. The token will expire after 25 hours by default; you can renew it while it is still valid with `kinit -R`.

## Frames

All data exchange in IceTray goes through [I3Frame](https://docs.icecube.aq/icetray/main/projects/icetray/classes/i3frame.html#i3frame-reference). This is essentially a big dictionary, tagged with a "stop" (more on that later). An IceTray script consists of a chain of modules that, when given a frame, can take objects it contains, perform some calculation, and add the result as a new object.

### Frame types (stops)

Each frame has a type, encoded as a single character. The most common ones are:

- G (Geometry): Information about the detector layout.
- C (Calibration): A grab-bag of calibration contants for transforming digital values to physical units.
- D (DetectorStatus): The detector configuration, e.g. trigger conditions and DAC settings that control the HV and discriminator levels.

Since each data-taking run (or simulation configuration) has a unique set of GCD frames, you will typically have a single GCD file, separate from your remaining data (more on I3 files below).

- Q (DAQ): Data collected during a single global trigger. The Q frame (and any following P frames) are an "event."
- P (Physics): A *view* into the proceeding Q frame with a particular data selection. For IceCube, this is typically used to select only the parts of the event related to a relativistic particle, like a muon or a neutrino-induced shower, as opposed to niche triggers designed to find sub-relativistic monopoles or collect pure noise for calibration studies. For Gen2, these are typically used to create separate views for Gen2+IceCube and IceCube-only, in order to directly compare reconstruction performance on the same simulated event.

### Frame mixing

Different frame types hold different types of information. Within an IceTray session, objects from each stop are "mixed" into all following frames. This means that, for example, a P frame will appear to contain all the objects natively in that frame, plus any from preceding Q, G, C, and D frames. This allows you to find all the relevant information for a particular frame in the frame itself.

## I3 files

An "I3" file is just a sequence of frames written to disk, one after the other. They have no internal structure beyond the frames, and can be trivially concatenated or split on a frame boundary. The names of these files typically end in the extension ".i3", but since much of the information in them is highly compressible, you will typically find them compressed with gzip (.i3.gz) or bzip2 (.i3.bz2). IceTray transparently handles compression and decompression for you.

## Pre-built metaprojects

Builds of IceTray are distributed via [CVMFS](https://cernvm.cern.ch/fs/), a read-only, cache-friendly, distributed filesystem developed for the LHC Computing Grid. At Linux systems at sites where CVMFS is available (e.g. UW-Madison, DESY-Zeuthen, any site that also does LHC computing), you can enter an environment where IceTray is installed with:

```console
> /cvmfs/icecube.opensciencegrid.org/py3-v4.1.1/icetray-env icetray/stable
************************************************************************
*                                                                      *
*                   W E L C O M E  to  I C E T R A Y                   *
*                                                                      *
*               Version icetray.stable     git:f5d21802                *
*                                                                      *
*                You are welcome to visit our Web site                 *
*                        http://icecube.umd.edu                        *
*                                                                      *
************************************************************************

Icetray environment has:
   I3_SRC       = /cvmfs/icecube.opensciencegrid.org/py3-v4.1.1/RHEL_7_x86_64/metaprojects/icetray/stable
   I3_BUILD     = /cvmfs/icecube.opensciencegrid.org/py3-v4.1.1/RHEL_7_x86_64/metaprojects/icetray/stable
```

Here, `/cvmfs/icecube.opensciencegrid.org/` is the IceCube namespace, `py3-v4.1.1` is the toolset (analogous to a Python virtualenv), and `icetray/stable` is the metaproject. There are specialized configurations of IceTray for online processing and filtering at Pole (pnf), offline processing (IceRec), and simulation (IceSim), but since they are, for the most part, subsets of the main IceTray project, you can use icetray/stable for most one-off tasks. Note that icetray/stable is rebuilt every time [icecube/icetray main](https://github.com/icecube/icetray) is updated (and its unit tests pass), so you should use a tagged release for tasks you want to be reproducible.

## Browsing I3 files

IceTray ships with a console-based file browser, `dataio-shovel`. For example, from a shell with the IceTray environment loaded (see above), `dataio-shovel /data/user/ayovych/simulation/reco/1.0x/0000000-0000999/Sunflower_350m_pDOM_1.0x_MuonGun.021489.000099_baseproc.i3.bz2` will show the following view:

```
┌─ I3 Data Shovel ─────────────────────────────────────── Press '?' for help ──┐
│                                                                              │
│ Name                    Type                                    Bytes        │
│ CalibratedWaveformRange I3TimeWindow                            48           │
│ CalibratedWaveforms     I3Map<OMKey, vector<I3Waveform> >       2802307      │
│ CalibrationErrata       I3Map<OMKey, I3TimeWindowSeries>        2409         │
│ CleanIceTopRawData      I3Map<OMKey, vector<I3DOMLaunch> >      46           │
│ CleanInIceRawData       I3Map<OMKey, vector<I3DOMLaunch> >      264022       │
│ I3EventHeader           I3EventHeader                           99           │
│ I3MCTree                TreeBase::Tree<I3Particle, I3Particl... 461134       │
│ I3MCTree_preMuonProp    TreeBase::Tree<I3Particle, I3Particl... 298          │
│ I3RecoPulseSeriesMap... I3Map<OMKey, vector<I3RecoPulse> >      3390         │
│ I3RecoPulseSeriesMap... I3TimeWindow                            48           │
│ IceCubePulses           I3Map<OMKey, vector<I3RecoPulse> >      72636        │
│ IceCubePulsesTimeRange  I3TimeWindow                            48           │
│ InIcePulses             I3RecoPulseSeriesMapUnion               96           │
│ InIceRawData            I3Map<OMKey, vector<I3DOMLaunch> >      264022       │
│                         [scroll down for more]                               │
│──────────────────────────────────────────────────────────────────────────────│
│       Key: 7/24                           StartTime: 2011-05-15 16:51:29 UTC │
│     Frame: 1/8 (12%)                       Duration: 30825.7 ns              │
│      Stop: DAQ                                                               │
│ Run/Event: 99/0                           .                                  │
│  SubEvent: (n/a)                      QPPQPPQP                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

You can use the arrow keys to move from frame to frame, `Enter` to show a text representation of the object, and `i` to drop into an iPython session with the current frame in scope as `frame`.

## Event data

### Pulses

There are a few different kinds of event data to be aware of. The most fundamental is `I3RecoPulseSeriesMap`, printed in the view above as `I3Map<OMKey, vector<I3RecoPulse>>`<sup>[[1]](#type-names)</sup>. Each `I3RecoPulseSeries` is a linear decomposition of the digitized waveform recorded by each optical module (OM). It has the following properties:

- time<sup>[[2]](#property-casing)</sup>: the leading-edge time of the pulse<sup>[[3]](#i3-units)</sup>
- width: the granularity of the linear decomposition, i.e. the minimum interval between pulses
- charge: the amplitude of the pulse, in photoelectrons. This is an estimate of the integrated photocathode current between time and time+width, and related to the rate of optical photons striking the photocathode.
- flags: a bitfield that is used to record provenance information for the pulse

<a name="type-names">[1]</a>: There are two different naming conventions here. Each item in the frame is backed by a C++ object, and `I3Map<OMKey, vector<I3RecoPulse>>` is the object's class. It is an `I3Map` (a subclass of `std::map`, conceptually similar to a Python `dict`) whose keys are of type `OMKey` and values of type `std::vector<I3RecoPulse>` (conceptually similar to a Python `list` of `I3RecoPulse` objects). The "pretty" name `I3RecoPulseSeriesMap` should be read right-to-left: a `Map` (implicitly, with keys of type `OMKey`) to a `Series` (vector) of `I3RecoPulse`.

<a name="property-casing">[2]</a>: In the C++ interface, and the string representations printed by `dataio-shovel`, properties are usually written in CamelCase, while in Python they are accessed in snake_case. For example, in C++ you would have a method `obj.GetSomeProperty()`, which would be printed as `SomeProperty`, and would be accessed in Python as `obj.some_property`.

<a name="i3-units">[3]</a>: All times in (triggered) IceCube frame are ns after the start of the global trigger readout window. In untriggered (simulated) data, times are also in nanoseconds, but w.r.t. some arbitrary zero point (usually, the vertex time of the primary particle). The trigger time itself is in `I3EventHeader`. Distances are in meters, energies are in GeV, and charges in units of e. The units are self-consistent, which has some odd side-effects, for example that ~7 mV amplitude of a single-PE PMT pulse is given as 7e-12 gigavolts. See also: [docs](https://docs.icecube.aq/icetray/main/projects/icetray/i3units.html)

There are a few alternate representations `I3RecoPulseSeriesMap` that may be stored in the frame to save memory and disk space:

- `I3SuperDST`: a lossily-compressed representation of an `I3RecoPulseSeriesMap` (on in IceCube data)
- `I3RecoPulseSeriesMapUnion`: represents the union of two `I3RecoPulseSeriesMap`s in the frame
- `I3RecoPulseSeriesMapMask`: a sub-selection of elements from an `I3RecoPulseSeriesMap`

These can be chained, e.g. you may see a mask that refers to a union which in turn refers to more masks. 

### I3EventHeader

The event header exists in both Q and P frames, but only in triggered data. It has the following properties:

- start_time: the time of the trigger start, in DAQ time (the year, and 1/10 ns clock ticks since the beginning of the year). This is most useful for converting local directions into sky directions.
- end_time: the time of the trigger end, in DAQ time.
- run_id (Q and P): in data, the identifier of the ~8-hour data-taking run. In simulation, an identifier for file<sup>[[3]](#simulation-file)</sup>.
- event_id (Q and P): a running index of the trigger since the run (or simulation file) began.
- sub_event_stream (P only): the name of the view this P frame represents, e.g. in Gen2 simulation "IC86_SMT8" or "GEN2".
- sub_event_id (P only): the index of the view within the sub_event_stream. For example, if there are two "IC86_SMT8" views derived from the same Q frame, their `I3EventHeader`s will have the same 

<a name="simulation-file">[4]</a>: A simulation set is typically run N times, each with a diffent pseudorandom number sequence. Since these "files" are independent, they can be created in parallel.

The `I3EventHeader` is most important as a unique identifier for events, and can be used to associate data when converted to tabular form (see tableio, below).

### Particles

Relativistic particles are represented by `I3Particle`. This has the following properties, not all of which are defined in all cases:

- pos: a 3-position, relative to the origin of the IceCube coordinate system (where z=0 is 1950 m below the surface)
- time: a time, when the particle was at position `pos`
- dir: a direction in the same coordinate system. The zenith is the angle of the direction the particle *came* from (i.e. astronomical convention) w.r.t. the positive z axis, and the azimuth is w.r.t. the x axis. The x,y,z components of `I3Direction`, on the other hand, are a unit vector pointing the direction the particle is *going*.
- energy: the kinetic energy of the particle in GeV
- length: the distance from `pos` to the point where the particle stopped or decayed (mostly for MC particles)
- type: for MC particles, the particle type as an enum whose values follow the [PDG coding scheme](https://pdg.lbl.gov/2019/reviews/rpp2019-rev-monte-carlo-numbering.pdf)
- location: general classification of location (mostly used to route MC particles to different parts of the simulation)
- shape: general classification of hit pattern, e.g. StoppingTrack, Cascade (mostly for reconstructed particles)
- status: result of likelihood minimization (for reconstructed particles)
- id: a globally unique identifier for the particle

Simulation modules use `I3Particle`s (in particular, `I3MCTree`, a container of `I3Particle`s with parent-child relationships) to store information about the particles that induced a particular simulated detector response. Conversely, reconstruction modules store their estimates of the underlying particle properties in `I3Particle`s, though usually as top-level particles in the frame. Some reconstructions come with algorithm-specific information (e.g. the number of minimizer iterations for a likelihood based reconstruction); these are typically stored as the name of the output particle with "Params" appended, e.g. "LineFit" and "LineFitParams."

## Tabular data from I3 files with tableio

I3 files are quite flexible, but that flexibility comes at the cost of speed: you can't seek to an arbitrary frame without reading every frame before it, and you can't read only a subset of the data in each frame. Tabular formats like HDF5 are much faster for reading subsets of data (e.g. when plotting only a few observables), and easier to integrate with standard tools like Numpy, Matplotlib, and Pandas. IceTray can write to tabular formats like HDF5 (or ROOT, or CSV, if you're into that) using the built-in tableio framework.

### Anatomy of an IceTray script

To write to HDF5, you have to write your first IceTray script. A basic script consists of a few common elements.

1. The "shebang" line. Instead of the usual `#!/usr/bin/env python`, this uses the `icetray-start` script that ships on CVMFS. This is similar to the `icetray-env` script you saw earlier, but designed to work as an interpreter. This sets up a toolset (py3-v4.1.1) as well as a metaproject environment (icetray/stable), and then invokes `python`. See also: [Self-contained IceTray scripts](https://docs.icecube.aq/icetray/main/info/cvmfs.html#self-contained-icetray-scripts).

```sh
#!/bin/sh /cvmfs/icecube.opensciencegrid.org/py3-v4.1.1/icetray-start
#METAPROJECT icetray/stable
```

2. Set up an `ArgumentParser`. This lets you pass command-line arguments to your script, so you can adjust its behavior, e.g. set input and output file names, without editing the file every time. Here we add positional arguments such that the last argument is treated as the output file name, and all previous arguments as input file names, e.g. `./dump.py infile1.i3. infile2.i3 outfile.hdf5`. See also: [argparse docs](https://docs.python.org/3/library/argparse.html).

```python
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
parser = ArgumentParser(description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('infile', nargs='+')
parser.add_argument('outfile')
args = parser.parse_args()
```

3. Standard IceTray imports. You need `icetray` to interact with core objects like I3Frame, `dataclasses` to read standard objects like `I3Particle` and `I3RecoPulse`, and `dataio` to handle files.

```python
from icecube import icetray, dataclasses, dataio
```

4. Set up an I3Tray. This is the session that you will use to build a chain of modules that will process frames in sequence.

```python
from I3Tray import I3Tray
tray = I3Tray()
```

5. Set up a file reader. `tray.Add()` adds elements to the tray. The first argument is the name of an `I3Module`, the basic processing unit in IceTray, and the keyword arguments are configuration parameters. `I3Modules` modules recieve `I3Frame`s, add new objects to them, and then send them to the next module in the chain. The first module in the chain (or "driving" module) is special; it *creates* frames. `I3Reader` reads the files given in the parameter `FileNameList` (parameter names are case-insensitive), and sends each frame down the chain as it is read.

```python
tray.Add("I3Reader", filenamelist=args.infile)
```

6. Set up the body of the processing chain. In the example below, we use a Python object as the first argument to the tray instead of a string. `HDFWriter` is a *tray segment*, a function that adds other modules to the tray. Just like a named module, though, it takes parameters as keyword arguments. In this case, we tell `I3HDFWriter` to write the object stored at key "InIcePulses" in frames with `sub_event_stream == "GEN2"` to a table named "InIcePulses" in an HDF5 file at the path given by the last command-line argument.

```python
from icecube.hdfwriter import I3HDFWriter
tray.Add(I3HDFWriter,
    Keys=["InIcePulses"],
    SubEventStreams=["GEN2"],
    Output=args.outfile,
)
```

7. Execute the tray. Everything up to now has been setup[^boilerplate]; if you ended the script here it would not do anything. `tray.Execute()` invokes the driving module to get a frame, then passes it to each module in the order in which they were added to the tray. This is repeated until the driving module returns a null frame (i.e. the input files have been read).

```
tray.Execute()
```

[^boilerplate]: You may have noticed that there is a great deal of "boilerplate" code to write before you get to the actual body of the IceTray script. I find it convenient to configure snippets in my editor so that I don't have to type these every time. The attached `python.json` is a snippet configuration for [VSCode](https://code.visualstudio.com/docs/editor/userdefinedsnippets). The internal syntax of these snippets is in Textmate format, and they can be used in [TextMate](https://macromates.com/manual/en/snippets), [SublimeText](https://sublime-text-unofficial-documentation.readthedocs.io/en/stable/extensibility/snippets.html), [Atom](https://atom.io/packages/snippets), or even [Vim](https://www.vim.org/scripts/script.php?script_id=2540).

### tableio example

When you the example script `dump.py`, you should see something like:

```console
> ./dumpy.py /data/user/ayovych/simulation/reco/1.0x/0000000-0000999/Sunflower_350m_pDOM_1.0x_MuonGun.021489.000099_baseproc.i3.bz2 Sunflower_350m_pDOM_1.0x_MuonGun.021489.000099_baseproc.hdf5
NOTICE (I3Tray): I3Tray finishing... (I3Tray.cxx:511 in void I3Tray::Execute(unsigned int))
WARN (I3TableWriter): 1 SubEventStreams ['IC86_SMT8',] were seen but not booked because they were not passed as part of the 'SubEventStreams' parameter of I3TableWriter (which was configured as ['GEN2',]). To book events from these streams, add them to the 'SubEventStreams' parameter of I3TableWriter. (I3TableWriter.cxx:479 in void I3TableWriter::Finish())
```

You can verify the contents of the file with the `h5ls` utility:

```console
> h5ls Sunflower_350m_pDOM_1.0x_MuonGun.021489.000099_baseproc.hdf5
InIcePulses              Dataset {95866/Inf}
__I3Index__              Group
```

#### Exercises:

1. Modify dump.py, adding a command-line argument to set the `SubEventStreams` parameter of `I3HDFWriter`. You should be able to specify either of ("GEN2", "IC86_SMT8"), and if you pass no argument, you should get both streams. What happens to the number of rows displayed in `h5ls`?

2. Add a command-line argument to set the `Keys` parameter of `I3HDFWriter`. Which other objects can you write to the HDF5 file? You may need to use `dataio-shovel` to find out the names of objects. `icetray-inspect` will tell you which parameters `I3Module`s and tray segments support, e.g. `icetray-inspect hdfwriter` to see all `I3Module`s and tray segments defined in the `hdfwriter` module.

### Summarizing and visualizing data with Pandas

[Pandas](https://pandas.pydata.org) is an incredibly useful package for data analysis. It provides a `DataFrame` object that is similar to a Numpy `ndarray` (which it uses internally), but can be indexed with arbitrary labels rather than just integer offsets. This makes it easy to manipulate and combine irregularly-shaped data without ever having to write an explicit loop. To read the HDF5 table you just created into a `DataFrame`:

```python
import tables
import pandas as pd
with tables.open_file("Sunflower_350m_pDOM_1.0x_MuonGun.021489.000099_baseproc.hdf5") as f:
    pulses = pd.DataFrame(f.root.InIcePulses.read())
```

You can use the `head()` method to print out the first few rows, and the `columns` property to see the column names:

```pycon
In [8]: pulses.head()
Out[8]:
   Run  Event  SubEvent    ...             time     width    charge
0   99      0         0    ...     20566.108505  6.250000  1.130296
1   99      0         0    ...     20776.956348  6.250000  1.758343
2   99      0         0    ...     20978.594113  6.250000  0.636451
3   99      0         0    ...     21275.058408  6.250000  1.004061
4   99      0         0    ...     14201.731693  0.833511  0.957578

[5 rows x 12 columns]
In [9]: pulses.columns
Out[9]:
Index(['Run', 'Event', 'SubEvent', 'SubEventStream', 'exists', 'string', 'om',
       'pmt', 'vector_index', 'time', 'width', 'charge'],
      dtype='object')
```

You see the actual properties of each pulse (time, width, charge), preceded by a number of indexing columns. This is how `tableio` flattens hierarchical data into a table: every element is a row, and those rows can be grouped together by the values of the remaining columns to reassociate them. For example, to get the total charge per event, you could do:

```pycon
In [10]: pulses.groupby(["Run", "Event", "SubEvent"])["charge"].sum()
Out[10]:
Run  Event  SubEvent
99   0      0             2643.572806
     1      0           265994.732366
     2      0            28094.514560
Name: charge, dtype: float64
```

`groupby` creates a `DataFrameGroupBy` expression, `["charge"]` selects the charge column, and `sum()` sums over groups. The result a `Series` with a [multi-level index](https://pandas.pydata.org/pandas-docs/stable/user_guide/advanced.html?highlight=multi%20level%20indexes#multiindex-advanced-indexing) given by the grouping columns. You can find more explanation and examples of `groupby` in the [pandas documentation](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.groupby.html).

#### Exercises:

1. Use Pandas to calculate the ratio of total collected charge (from InIcePulses.charge) to muon energy (from MCMuon.energy). There is only one MCMuon per frame, but multiple corresponding entries in InIcePulses. You may want to use [DataFrame.set_index()](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.set_index.html) to create multi-level indexes directly.








