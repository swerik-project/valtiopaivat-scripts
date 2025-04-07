#!/usr/bin/env python3
"""
Join the LO map documents to a metadata doc for each repo
"""
from glob import glob
from valtiopy.args import (
    fetch_parser,
    impute_arg_values,
)
import argparse
import os
import pandas as pd




def main(args):
    lo_maps_loc = args.config.ValtiopaivatRecordsPDFLocation
    tei_repos = {
        "records": args.config.ValtiopaivatRecordsTEILocation,
        "handlingar": args.config.ValtiopaivatHandlingarTEILocation,
        "registers": args.config.ValtiopaivatRegistersTEILocation
    }
    doc_types = {
        "hand": "handlingar",
        "ask": "handlingar",
        "bil": "handlingar",
        "prot": "records",
        "ptk": "records",
        "reg": "registers",
        "sis": "registers"
    }
    rows = {
        "handlingar": [],
        "registers": [],
        "records": []
    }
    cols = ["file", "language", "orthography"]
    for lo_map in sorted(glob(f"{lo_maps_loc}/**/lo-map.csv", recursive=True)):
        print(lo_map)
        df = pd.read_csv(lo_map)
        print("  ", cols == df.columns)
        for i, r in df.iterrows():
            dt = r["file"].split("_")[0]
            r["file"] = r["file"].replace(".pdf", "")
            rows[doc_types[dt]].append(list(r))

    for k,v in rows.items():
        df = pd.DataFrame(v, columns=cols)
        df.to_csv(f"{tei_repos[k]}/lo-map.csv", index=False)


if __name__ == '__main__':
    parser = fetch_parser(description=__doc__)
    main(impute_arg_values(parser.parse_args()))

