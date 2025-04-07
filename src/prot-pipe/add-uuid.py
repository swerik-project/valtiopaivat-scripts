"""
Add a randomly generated UUID to all elements in the XML ID field that are currently missing one.
"""
from lxml import etree
from pathlib import Path
from pyriksdagen.utils import fetch_ns
from valtiopy.args import (
    fetch_parser,
    impute_arg_values,
)
from valtiopy.utils import (
    elem_iter,
    get_formatted_uuid,
    #get_data_location,
    parse_tei,
    #protocol_iterators,
    write_tei,
)
from tqdm import tqdm
import argparse
import multiprocessing
import sys



def parse_tei_id_fix(_path, get_ns=True) -> tuple:

    """

    Parse a protocol, return root element (and namespace defnitions).

    Args:
        _path (str): path to tei-xml doc
        get_ns (bool): also return namespace dict

    Returns:
        tuple/etree._Element: root and an optional namespace dict
    """
    parser = etree.XMLParser(remove_blank_text=True, recover=True)
    root = etree.parse(_path, parser).getroot()
    if get_ns:
        ns = fetch_ns()
        return root, ns
    else:
        return root


def add_protocol_id(protocol, args):
    ids = set()
    num_ids = 0

    if args.fix_duplicate_ids:
        root, ns = parse_tei_id_fix(protocol)
    else:
        root, ns = parse_tei(protocol)

    body = root.find(f".//{ns['tei_ns']}body")
    if body is None:
        print(protocol)
    else:
        divs = body.findall(f"{ns['tei_ns']}div")
        for div in divs:
            protocol_id = Path(protocol).stem
            seed = f"{protocol_id}\n{' '.join(div.itertext())}"
            x = div.attrib.get(f"{ns['xml_ns']}id", get_formatted_uuid(seed))
            div.attrib[f"{ns['xml_ns']}id"] = x
            num_ids += 1
            ids.add(x)


            for elem in tqdm(div):
                if elem.text is not None:
                    seed = seed + elem.text
                else:
                    seed = seed + elem.tag
                if elem.tag.endswith("u"):
                    for subelem in elem:
                        if args.fix_duplicate_ids:
                            x = subelem.attrib[f"{ns['xml_ns']}id"] = get_formatted_uuid(seed)
                        else:
                            x = subelem.attrib.get(f"{ns['xml_ns']}id", get_formatted_uuid(seed))
                    if args.fix_duplicate_ids:
                        x = elem.attrib[f"{ns['xml_ns']}id"] = get_formatted_uuid(seed)
                    else:
                        x = elem.attrib.get(f"{ns['xml_ns']}id", get_formatted_uuid(seed))
                        ids.add(x)
                        num_ids += 1
                    x = elem.attrib.get(f"{ns['xml_ns']}id", get_formatted_uuid(seed))
                    elem.attrib[f"{ns['xml_ns']}id"] = x
                    ids.add(x)
                    num_ids += 1
                elif elem.tag.endswith("note"):
                    if args.fix_duplicate_ids:
                        x = elem.attrib[f"{ns['xml_ns']}id"] = get_formatted_uuid(seed)
                    else:
                        x = elem.attrib.get(f"{ns['xml_ns']}id", get_formatted_uuid(seed))
                    elem.attrib[f"{ns['xml_ns']}id"] = x
                    ids.add(x)
                    num_ids += 1

    write_tei(root, protocol)

    assert len(ids) == num_ids
    return ids, num_ids




def main(args):

    num_ids = 0
    ids = []
    if args.dry_run:
        print(args)
        sys.exit()


    for protocol in tqdm(args.tei_files, total=len(args.tei_files)):
        i, n = add_protocol_id(protocol, args)
        ids += i
        num_ids += n

        assert len(set(ids)) == num_ids




if __name__ == "__main__":
    parser = fetch_parser(description=__doc__)
    parser.add_argument("--orthographies",
                        default=['r'],
                        choices=["r", "b"],
                        help="orthography of the original document (r=roman, b=blackletter/fraktur")
    parser.add_argument("--fix-duplicate-ids", action='store_true')
    parser.add_argument("-n", "--dry-run", action='store_true')
    main(impute_arg_values(parser.parse_args()))
