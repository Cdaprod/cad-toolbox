import argparse
from cadtoolbox.io.convert import convert

p = argparse.ArgumentParser()
p.add_argument("source")
p.add_argument("output")
args = p.parse_args()
print(convert(args.source, args.output))
