# CLARIFY -- Framework for Relation Extraction via Distant Supervision

## Data
To run the code, please obtain the data as follows:

##### UMLS
Install the UMLS tools by following the steps [here](http://blog.appliedinformaticsinc.com/getting-started-with-metamorphosys-the-umls-installation-tool/). Once installed, under `INSTALLED_DIR/2019AB/META`, you can find `MRREL.RRF` and `MRCONSO.RRF`, copy the files and place under `data/UMLS`.

##### MEDLINE

Download MEDLINE abstracts `medline_abs.txt` (~25GB) and place under `data/MEDLINE`.

##### Data Creation

1. Process UMLS: `python3 cli/generate-umls-vocab-cli.py`
   - This will create `data/umls_vocab.pkl`.
2. Run `python3 cli/extract-sentences-medline-cli.py`.
   - This will create `data/MEDLINE/medline_unique_sentences.txt`.
3. Link entities with text: `python3 -m cli/link-umls-entities-cli.py`
   - This will create `data/MEDLINE/umls_linked_sentences.jsonl`.
     Each entry in this file is a dict, with an entry `sent` containing the sentence, and an entry `matches`,
     containing entity names as keys, and start and end positions as value.

##### Data Splits

To generate the data splits for the `k-tag` setting, run wit default options as `python3 ./cli/create-splits-cli.py`.
This will take a while for the first time because of generating the one time file `data/MEDLINE/linked_sentences_to_groups.jsonl`.
For next runs, it will use the cached version.
Each entry in `data/MEDLINE/linked_sentences_to_groups.jsonl` is a dict with the following entries:
   - `sent`, a sentence from MEDLINE;
   - `matches` where each key is an entity, and each value is its position (start, end) in the sentence;
   - `groups` a dict with following two entries:
      - `p`: list of strings, e.g. `blood\tleucocytes`
      - `n`: list of strings, e.g. `leucocytes\tpicture`

For `s-tag`, set the flag `k_tag=False` in `config.py`.

For `s-tag+exprels`, additionally set the flag `expand_rels=True`.

## Features

Run `python3 ./cli/create-features-cli.py`. Running the job with multi-processing will be significantly faster.

This will create *feature files*, i.e. `features/train.pt`, `features/dev.pt`, `features/test.pt`.

## Train

Run `python3 cli/train-cli.py`.
