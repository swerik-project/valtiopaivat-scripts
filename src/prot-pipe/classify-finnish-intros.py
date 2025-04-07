#!/usr/bin/env python3
from tqdm import tqdm
from valtiopy.args import (
    fetch_parser,
    impute_arg_values,
)
from valtiopy.utils import (
    elem_iter,
    parse_tei,
    write_tei,
    XML_NS,
)
import pandas as pd
import re

pat = re.compile(r'[A-ZÀ-Þ][a-zß-ÿ]{4,20}\s([A-ZÀ-Þ]\.\s)?[A-ZÀ-Þ][a-zß-ÿ]{4,20}:')
pat2 = re.compile(r'([A-ZÀ-Þ][a-zß-ÿ]{4,20}\s([A-ZÀ-Þ]\.\s)?[A-ZÀ-Þ][a-zß-ÿ]{4,20})(:|\s[a-zß-ÿ]{2,})')

def main(args):
    I = 0
    #N = 0
    rows = []
    cols = ["file_path", "intro", "id"]
    lo_map = pd.read_csv(args.config.ValtiopaivatRecordsLOMap)
    files = lo_map.loc[(lo_map["language"].isin(args.languages)) & \
                       (lo_map["orthography"].isin(args.orthographies)),
                       "file"].tolist()
    records_loc = args.config.ValtiopaivatRecordsTEILocation
    for file_ in tqdm(files):
        print(file_)
        year = file_.split('/')[2][:4]
        chamber = file_.split('_')[-2]
        root, ns = parse_tei(file_)
        notes = root.findall(f".//{ns['tei_ns']}note")
        for note in notes:
            t = ' '.join([_.strip() for _ in note.text.strip().splitlines() if _.strip() != ''])
            if chamber == "talonpojat" and int(year) < 1885:
                m = pat2.match(t)
                if m:
                    print("INTRO:", m.group(0), t[:50])
                    rows.append([file_, m.group(1), note.attrib[f"{ns['xml_ns']}id"]])
                    I += 1
                #else:
                #    print("XXX Not INTRO:", t[:50])
                #    rows.append(["NOT_INTRO", None, t[:90]])
                #    N += 1
            else:
                m = pat.match(t)
                if m:
                    print("INTRO:", m.group(0), t[:50])
                    rows.append([file_, m.group(0), note.attrib[f"{ns['xml_ns']}id"]])
                    I += 1
                #else:
                #    print("XXX Not INTRO:", t[:50])
                #    rows.append(["NOT_INTRO", None, t[:90]])
                #    N += 1

    print(f"\n\n\nIntros: {I}")#\nNot Intros: {N}\n\n")



    df = pd.DataFrame(rows, columns=cols)
    df.to_csv(args.intros_list_path, sep="\t", index=False)

    #dfs = df.sample(n=100)
    #fs.to_csv(args.intros_list_path.replace(".tsv", "_100-sample.tsv"), sep='\t', index=False)




if __name__ == '__main__':
    parser = fetch_parser(description=__doc__)
    parser.add_argument("--orthographies",
                        default=['r'],
                        choices=["r", "b"],
                        help="orthography of the original document (r=roman, b=blackletter/fraktur")
    parser.add_argument("--intros-list-path", default="input/segmentation/finnish-intros.tsv")
    parser.add_argument("--CUDA", action='store_true', help="run with cuda")
    main(impute_arg_values(parser.parse_args()))
