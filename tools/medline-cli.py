#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import gzip
from xml.dom import minidom
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
from tqdm import tqdm
import jsonlines

from typing import List, Dict, Any

import logging

logger = logging.getLogger(os.path.basename(sys.argv[0]))


def parse(path: str) -> List[Dict[str, Any]]:
    logger.debug(f'Processing {path} ..')
    with gzip.open(path, 'r') as f:
        content = f.read()
    # return [content]
    dom = minidom.parseString(content)
    a_lst = dom.getElementsByTagName("Article")
    res = []
    for a in a_lst:
        entry = {}
        at = a.getElementsByTagName("ArticleTitle")[0]
        at_text = at.firstChild
        if at_text is not None:
            if hasattr(at_text, 'data'):
                entry['title'] = at_text.data
            else:
                print('at_text has no data', path)
        ab_lst = a.getElementsByTagName("AbstractText")
        abstract_lst = []
        for ab in ab_lst:
            ab_text = ab.firstChild
            ab_label = ab.getAttribute('Label')
            ab_nlm_category = ab.getAttribute('NlmCategory')
            abstract = {}
            if ab_text is not None:
                if hasattr(ab_text, 'data'):
                    abstract['text'] = ab_text.data
                else:
                    print('ab_text has no data', path)
            if ab_label is not None and len(ab_label) > 0:
                abstract['label'] = ab_label
            if ab_nlm_category is not None and len(ab_nlm_category) > 0:
                abstract['nlm_category'] = ab_nlm_category
            if len(abstract) > 0:
                abstract_lst += [abstract]
        entry['abstract'] = abstract_lst
        res += [entry]
    return res


def main(argv):
    parser = argparse.ArgumentParser('MEDLINE', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('paths', type=str, nargs='+', help='Paths')
    parser.add_argument('--threads', '-t', type=int, default=multiprocessing.cpu_count(), help='Threads')

    parser.add_argument('--jsonl', type=str, default='medline.jsonl', help='JSONL output')
    parser.add_argument('--text', type=str, default=None, help='JSONL output')

    args = parser.parse_args(argv)

    jsonl_path = args.jsonl
    text_path = args.jsonl

    with ProcessPoolExecutor(max_workers=args.threads) as e:
        entry_lst = [entry for el in list(tqdm(e.map(parse, args.paths), total=len(args.paths))) for entry in el]

    if jsonl_path is not None:
        with jsonlines.open(jsonl_path, 'w') as f:
            f.write_all(entry_lst)

    if text_path is not None:
        with open(text_path, 'w') as f:
            for entry in entry_lst:
                for abstract in entry['abstract']:
                    if 'text' in abstract:
                        f.write(str(bytes(abstract['text'], 'utf-8')) + '\n')


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main(sys.argv[1:])
