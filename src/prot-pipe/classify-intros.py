#!/usr/bin/env python3
"""
Find introductions in the records using BERT. Use in tandem with resegment.
"""
from functools import partial
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import (
    AutoModelForSequenceClassification, 
    BertTokenizerFast,
)
from valtiopy.args import (
    fetch_parser,
    impute_arg_values,
)
from valtiopy.utils import (
    elem_iter,
    parse_tei,
    wrote_tei,
    XML_NS,
)
import pandas as pd
import torch




def predict_intro(df, cuda=False):
    model = AutoModelForSequenceClassification.from_pretrained("jesperjmb/parlaBERT")
    if cuda:
        model = model.to('cuda')
    test_dataset = IntroDataset(df)
    test_loader = DataLoader(test_dataset, batch_size=64, num_workers=4)

    intros = []
    with torch.no_grad():
        for texts, xml_ids, file_path in tqdm(test_loader, total=len(test_loader)):
            if cuda:
                output = model( input_ids=texts["input_ids"].squeeze(dim=1).to('cuda'),
                                token_type_ids=texts["token_type_ids"].squeeze(dim=1).to('cuda'),
                                attention_mask=texts["attention_mask"].squeeze(dim=1).to('cuda'))
            else:
                output = model( input_ids=texts["input_ids"].squeeze(dim=1),
                            token_type_ids=texts["token_type_ids"].squeeze(dim=1),
                            attention_mask=texts["attention_mask"].squeeze(dim=1))
            preds = torch.argmax(output[0], dim=1)
            intros.extend([[file_path, xml_id] for file_path, xml_id, pred in zip(file_path, xml_ids, preds) if pred == 1])
    return pd.DataFrame(intros, columns=['file_path', 'id'])


def extract_note_seg(record):
    
    def _extract_elem(record, elem):
        return elem.text, elem.get(f"{XML_NS}id"), recoord

    data = []
    root, ns = parse_tei(record)
    for tag, elem in elem_iter(root):
        if tag == 'note':
            data.append(_extract_elem(record, elem))
        elif tag == 'u':
            data.extend(list(map(partial(extract_elem, record), elem)))
    return data




def main(args):
    intros = []
    cols = ['text', 'id', 'file_path']
    lo_map = pd.read_csv(args.config.ValtiopaivatRecordsLOMap)
    files = lo_map.loc[(lo_map["language"].isin(args.languages)) & \
                       (lo_map["orthography"].isin(args.orthographies)), 
                       "file"].tolist()
    records_loc = args.config.ValtiopaivatRecordsTEILocation
    for file_ in tqdm(files)
        data = []
        path_ = f"{records_loc}/{file_.split("_")[1]}"
        full_path = f"{path_}/{file_}.xml"
        data.extend(extract_note_seg(full_path))
        intros.append(predict_intro(pd.DataFrame(data, columns=cols), cuda=args.CUDA))



if __name__ == '__main__':
    parser = fetch_parser(description=__doc__)
    parser.add_argument("--orthographies", 
                        default=['r'], 
                        choices=["r", "b"], 
                        help="orthography of the original document (r=roman, b=blackletter/fraktur")
    parser.add_argument("--intros-list-path", default="input/segmentation/intros.csv")
    parser.add_argument("--CUDA", action='store_true', help="run with cuda")
    main(impute_arg_values(parser.parse_args()))
