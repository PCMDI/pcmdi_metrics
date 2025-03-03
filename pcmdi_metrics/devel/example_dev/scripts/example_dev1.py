#!/usr/bin/env python
import argparse
import sys

from pcmdi_metrics.example_dev import example

parser = argparse.ArgumentParser(description="Adds two integers")
parser.add_argument("numbers", nargs=2, type=float, help="two numbers to add")

args = parser.parse_args(sys.argv[1:])
s = example(args.numbers[0], args.numbers[1])

print("Result:", s)
