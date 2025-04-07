#!/usr/bin/env python3
"""
convert alto xml files to basic tei structure
"""
from tqdm import tqdm
from valtiopy.args import (
    fetch_parser,
    impute_arg_values,
)
from valtiopy.curate import (
    dict_to_parlaclarin,
    convert_alto
)
from valtiopy.utils import infer_metadata
import json




def get_alto_packages(alto_files):
    """
    from a list of alto files, returns a set of package names,
    i.e. the directory containing the per-page alto files
    """
    packages = {}
    for f in alto_files:
        package = '/'.join(f.split('/')[:-1])
        if package not in packages:
            packages[package] = [f]
        else:
            packages[package].append(f)
    return packages


def main(args):

    tei_out = {
        "prot": args.config.ValtiopaivatRecordsTEILocation,
        "ptk": args.config.ValtiopaivatRecordsTEILocation,
        "ask": args.config.ValtiopaivatHandlingarTEILocation,
        "hand": args.config.ValtiopaivatHandlingarTEILocation,
        "bil": args.config.ValtiopaivatHandlingarTEILocation,
        "reg": args.config.ValtiopaivatRegistersTEILocation,
        "sis": args.config.ValtiopaivatRegistersTEILocation
    }

    if args.verbose: print("Info: N alto files ==", len(args.alto_files))
    packages = get_alto_packages(args.alto_files)
    if args.verbose: print("Info: N packages ==", len(packages))

    for package, package_files in tqdm(packages.items()):
        data = infer_metadata(package, verbose = args.verbose)
        data["authority"] = args.authority
        data["license"] = "CC0"
        data["license_url"] = "https://creativecommons.org/public-domain/cc0/"
        data["document_title"] = data["filename"]
        data["paragraphs"] = convert_alto(package_files)
        dict_to_parlaclarin(data, f"{tei_out[data['document_type']]}/data/{data['yearstr']}", verbose = args.verbose)




if __name__ == '__main__':
    parser = fetch_parser()
    parser.add_argument("--authority", type=str, default="SWERIK Project, 2023-2027")
    main(impute_arg_values(parser.parse_args()))
