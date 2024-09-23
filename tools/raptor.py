#!/usr/bin/env python3

import argparse
import pathlib,os
import pandas as pd
import numpy as np

from raptor_parser import RaptorParser

parser = argparse.ArgumentParser(prog="raptor.py",
        description=
            RaptorParser.__doc__ + \
            \
"""
Example:  $ raptor.py --top --categorize trace.rpd
""",
            formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("rpd_file_name")
parser.add_argument("--variability", "-v", action='store_true',
                    help="show variability")
parser.add_argument("--categorize", "-c", action='store_true',
                    help="Summarize RPD top kernels into categories (ie GEMM, AllReduce, EltWise, Idle)")
parser.add_argument("--category_json", "-C", type=str,
                    default=os.path.join(pathlib.Path(__file__).parent.resolve(), "raptor_cat_vllm.json"),
                    help="File containing category definitions, specified as a JSON-format dictionary.  See tools/raptor_cat_vllm.json for an example.  If a kernel name matches more than one pattern, the LAST match in the file determines the category.")

parser.add_argument("--top", "-t", action='store_true',
                    help="Show top kernel, sorted by TotalDuration")

op_trace_g = parser.add_argument_group('op_trace args:')
op_trace_g.add_argument("--op_trace", "-o", action='store_true',
                    help="Generate a trace for each op")
op_trace_g.add_argument("--op_trace_file", type=str,
                    help="File to use for op trace")
op_trace_g.add_argument("--op_trace_cmd_width", type=int, default=None,
                    help="Width in characters to display the op (kernel) names in the op trace")

roi_g = parser.add_argument_group('Region-of-Interest (ROI) args:')
roi_g.add_argument("--roi_start", "-s", type=str,
                    help="Set ROI start. 0 corresponds to the start of the RPD.  Default is ms, but can specify trailing time units.  If kernel name is specified, use the timestamp of the first instance for the specified kernel. Examples: 123.45, 123.45ms, 123450ns, .12345s, Cijk_")
roi_g.add_argument("--roi_end", "-e", type=str,
                    help="Set Region-of-Interest end. See --start for format.")
roi_g.add_argument("--auto-roi", action='store_true',
                    help="Automatically pick the ROI to include first and last instance of the hottest duration kernel")

display_g = parser.add_argument_group('Display arguments')
display_g.add_argument("--display_cols", type=int, default=60,
                    help="Set display column width")
display_g.add_argument("--display_rows", type=int, default=500,
                    help="Set number of rows")
display_g.add_argument("--float_digits", type=int, default=1,
                    help="Number of digits to print for float values in tables.")

gaps_default = [10, 20, 50, 100, 1000, 10000, 100000]
parser.add_argument("--gaps",
                nargs='+', type=int, metavar="GAP",
                default=gaps_default,
                help = "Size of histogram buckets used for gaps breakdown, specified as a list of micro-second times.  Default="+str(gaps_default));

args=parser.parse_args()

# Set display options:
pd.set_option('display.max_rows', args.display_rows)
pd.options.display.max_colwidth = args.display_cols
pd.set_option('display.float_format', ('{:.%d}'%args.float_digits).format)
pd.set_option('display.float_format', '{:.1}'.format)

if not args.op_trace and not args.top and not args.categorize:
    print ("info: setting --top --categorize --variability")
    args.top = True
    args.categorize = True
    args.variability = True

raptor = RaptorParser(args.rpd_file_name, gaps=args.gaps, 
                      category_json=args.category_json,
                      roi_start=args.roi_start, roi_end=args.roi_end)

raptor.print_timestamps(indent="   ")

if args.auto_roi:
    raptor.set_auto_roi()

if args.categorize: 
    category_df = raptor.get_category_df(raptor.get_top_df())
    print ("\nCategories:")
    print(category_df)

if args.variability: 
    print ("\nVariability:")
    print(raptor.get_variability_df())

if args.top:
    print ("\nTop Kernels:")
    print (raptor.get_pretty_top_df())

if args.op_trace:
    raptor.print_op_trace(outfile=args.op_trace_file, command_print_width=args.op_trace_cmd_width)
