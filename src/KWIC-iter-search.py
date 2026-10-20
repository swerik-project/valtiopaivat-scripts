#!/usr/bin/env python3
"""
Iterate over documents and search for anything.
"""
from datetime import datetime
from glob import glob
from tqdm import tqdm
from trainerlog import get_logger
from valtiopy.utils import (
    elem_iter,
    parse_tei,
)
import argparse
import pandas as pd
import re




logger = get_logger(name="KWIC")
DATETIMESTRING = datetime.now().strftime("%Y%m%d-%H%M%S")


def format_text(text):
    """
    removes parlaclarin-specific text formatting
    """
    lines = text.split('\n')
    return ' '.join([l.strip() for l in lines])


def append_matches(matches, counter, rows,
                   record, elem_id, elem_type,
                   who, txt, context, facs, line_number):
    """
    append search hits to results table
    """
    for m in matches:
        counter += 1
        s = m.start()
        e = m.end()
        left = txt[s-context:s]
        right = txt[e:e+context]
        prot = record.split('/')[-1][:-4]
        gh = f"https://github.com/swerik-project/riksdagen-records/blob/{args.branch}/{record}/#L{line_number}"
        if args.print or args.print_only:
            tqdm.write(f'{prot}: {txt[s-context:s]} --| {m.group(0)} |-- {txt[e:e+context]}')
        row = [record, elem_id, elem_type, who, s, e, left, m.group(0), right, facs, gh]
        rows.append(row)
    return rows, counter




def main(args):
    match_counter = 0
    rows = []
    cols = ["record", "elem_id", "elem_type", "who",
            "match_start", "match_end", "left_context",
            "match", "right_context", "facs", "github"]

    if args.keyword:
        pattern = re.compile(rf'\b\S*{args.keyword}\S*\b', re.IGNORECASE)
    elif args.regex_keyword:
        pattern = re.compile(rf'{args.regex_keyword}')
    elif args.regex_fromfile:
        with open(args.regex_fromfile, 'r') as rq:
            pattern = re.compile(rf"{rq.read().strip()}")

    search_u = True
    search_note = True

    if args.segment != False and args.note != False:
        search_u = args.segment
        search_note = args.note

    records = sorted(glob(f"{args.data_path}/*/*.xml"))

    if args.estate:
        records = [record for record in records if any(estate in record for estate in args.estate)]

    if args.start:
        records = [record for record in records if int(args.start) <= int(record.split('/')[-2][:4])]
        records = [record for record in records if int(args.end) >= int(record.split('/')[-2][:4])]

    for record in tqdm(records):
        root, ns = parse_tei(record)
        facs = None
        for tag, elem in elem_iter(root):
            if tag == "u" and search_u:
                who = elem.attrib.get("who")
                for subelem in elem:
                    line_number = subelem.sourceline
                    subelem_id = subelem.attrib.get(f'{ns["xml_ns"]}id')
                    txt = format_text(subelem.text)
                    matches = re.finditer(pattern, txt)
                    rows, match_counter = append_matches(matches, match_counter, rows,
                                                         record, elem_id, "seg", who,
                                                         txt, args.context, facs, line_number)
            elif tag == "note" and search_note:
                line_number =  elem.sourceline
                elem_id = elem.attrib.get(f'{ns["xml_ns"]}id')
                txt = format_text(elem.text)
                matches = re.finditer(pattern, txt)
                rows, match_counter = append_matches(matches, match_counter, rows,
                                                     record, elem_id, "note", None,
                                                     txt, args.context, facs, line_number)
            elif tag == "pb":
                facs = elem.attrib.get("facs")


    logger.info("Search done")
    if not args.print_only:
        logger.info("Writing file...")
        df = pd.DataFrame(rows, columns=cols)
        df.to_csv(f"{args.out_path}/{args.out_file}_{dts}.tsv", sep="\t", index=False)


    logger.info("---")
    logger.info(f"----> {match_counter} matches found")
    logger.info("---")




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-path",
                        default="valtiopaivat-records/data",
                        help="Path to the data")
    parser.add_argument("-s", "--start",
                        default=None,
                        help="Earliest records to search")
    parser.add_argument("-e", "--end",
                        default=None,
                        help="Latest record to search")
    parser.add_argument("--estate",
                        default=None,
                        nargs="+",
                        choices=[
                            "adeln",     # Nobility
                            "bonde",     # Peasants
                            "borgare",   # Bourgeoisie
                            "papisto",   # Clergy
                            "prester",   # Clergy
                            "talonpojat" # Peasants
                        ],
                        help="Limit search to specified estates.")
    parser.add_argument("-S", "--segment",
                        action="store_true",
                        help="Search only in utterance segments.")
    parser.add_argument("-n", "--note",
                        action="store_true",
                        help="Search only in notes.")
    parser.add_argument("-k", "--keyword",
                        type=str,
                        default=None,
                        help="Search term")
    parser.add_argument("-r", "--regex-keyword",
                        type=str,
                        default=None,
                        help="Regular expression search term.\nWrap expression in single quotes, e.g. '\\bHerr\\S*\\b'.")
    parser.add_argument("-Q", "--regex-fromfile",
                        default=None,
                        help="Read in a regex query from a file.")
    parser.add_argument("-C", "--context",
                        type=int,
                        default=45,
                        help="N characters to the left & right of match in results file.")
    parser.add_argument("-O", "--out-path",
                        type=str,
                        default=".",
                        help="output folder")
    parser.add_argument("-o", "--out-file",
                        type=str,
                        default="KWIC-results",
                        help="Name of output file @ --out-path")
    parser.add_argument("-b", "--branch",
                        type=str,
                        default="dev",
                        help="Github branch (for links in the output csv).")
    parser.add_argument("-p", "--print",
                        action="store_true",
                        help="Print matches to stdout.")
    parser.add_argument("-P", "--print-only",
                        action="store_true",
                        help="Print matches to stdout; no output file.")
    args = parser.parse_args()
    if not (args.start == args.end):
        logger.error(f"set both --start and --end or neither")
        raise ValueError("can't set start or end")
    test = [args.keyword == None, args.regex_keyword == None, args.regex_fromfile == None]
    if test.count(True) != 2:
        logger.error("\n\tYou have to EITHER provide a keyword, a regex-keyword, or read a regex query from file.\n\n")
        parser.print_help()
    else:
        main(args)
