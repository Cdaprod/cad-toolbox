import argparse
from cadtoolbox.apps.openscad import run_openscad

parser = argparse.ArgumentParser()
parser.add_argument("source")
parser.add_argument("output")
parser.add_argument("-D", "--define", action="append", default=[])
args = parser.parse_args()

defines = {}
for item in args.define:
    key, value = item.split("=", 1)
    try:
        value = float(value)
    except ValueError:
        pass
    defines[key] = value

print(run_openscad(args.source, args.output, defines=defines))
