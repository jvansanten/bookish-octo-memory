#!/bin/sh /cvmfs/icecube.opensciencegrid.org/py3-v4.1.1/icetray-start
#METAPROJECT icetray/stable

"""

"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
parser = ArgumentParser(description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('infile', nargs='+')
parser.add_argument('outfile')
args = parser.parse_args()

from icecube import icetray, dataclasses, dataio
from I3Tray import I3Tray

tray = I3Tray()

tray.context['I3FileStager'] = dataio.get_stagers()
tray.Add("I3Reader", filenamelist=args.infile)

from icecube.hdfwriter import I3HDFWriter
tray.Add(I3HDFWriter,
    Keys=["InIcePulses"],
    SubEventStreams=["GEN2"],
    Output=args.outfile,
)

tray.Execute()