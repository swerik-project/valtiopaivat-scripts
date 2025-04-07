#!/usr/bin/env python3
"""
Find introductions in the protocols. After finding an intro,
tag the next paragraph as an utterance.
"""
from lxml import etree
from tqdm import tqdm
from valtiopy.args import (
    fetch_parser,
    impute_arg_values,
)
from valtiopy.utils import (
    parse_tei,
    write_tei,
    XML_NS
)
import pandas as pd
import warnings




def main(args):
    n = 0
    if args.intros_list_path.endswith(".tsv"):
        intros_df = pd.read_csv(args.intros_list_path, sep='\t')
    else:
        intros_df = pd.read_csv(args.intros_list_path)
    file_paths = list(intros_df["file_path"].unique())
    rows = []
    cols = ["file", "intro_id", "speaker"]
    for f in tqdm(file_paths):
        if "intro" in intros_df.columns:
            elem_ids = intros_df.loc[intros_df["file_path"] == f, ["id", "intro"]]
            elem_ids = list(zip(elem_ids['id'], elem_ids['intro']))
        else:
            elem_ids = intros_df.loc[intros_df["file_path"] == f, "id"].to_list()
            elem_ids = list(zip(elem_ids, None*len(elem_ids)))

        root, ns = parse_tei(f)
        for elem_id in elem_ids:
            elems = root.xpath(f'.//*[@xml:id="{elem_id[0]}"]')
            if len(elems) != 1:
                warnings.warn(f"expected 1 element, found {len(elems)}, skipping {elem_id}")
                n += 1
                continue
            elem = elems[0]
            elem.attrib["type"] = "speaker"
            txt = elem.text
            ix = None
            if txt[-1] != ":" and ":" in txt:
                ix = txt.index(":")
            elif elem_id[1] is not None:
                ix = len(elem_id[1])-1
            if ix:
                intro_txt = txt[:ix+1].strip()
                elem.text = intro_txt
                rest_txt = txt[ix+1:].strip()
                if rest_txt is not None:
                    u = etree.Element(f"{ns['tei_ns']}u")
                    u.attrib["who"] = "unknown"
                    elem.addnext(u)
                    new_seg = etree.SubElement(u, f"{ns['tei_ns']}seg")
                    new_seg.text = rest_txt
                rows.append([f, elem_id, intro_txt])
            else:
                rows.append([f, elem_id, txt])
        write_tei(root, f)

    df = pd.DataFrame(rows, columns=cols)
    df.to_csv(f"{args.intros_list_path[:-4]}-text.csv", index=False)




if __name__ == '__main__':
    parser = fetch_parser(description=__doc__)
    parser.add_argument("--intros-list-path", default="input/segmentation/intros.csv")
    main(impute_arg_values(parser.parse_args()))
