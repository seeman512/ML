# usage:
#   python3 parse.py log_file.log test|train

import sys
import json
import pandas as pd
import logging


vital_file_path = 'files/{0}_vital.csv'
audio_preview_path = 'files/{0}_audio_preview.csv'
stats_path = 'files/{0}_stats.csv'


def parse(line):
    parts = line.split(' ', 6)
    payload = str(parts[6]).replace("\n", "")
    payload_json = {}

    try:
       payload_json = json.loads(payload)
    except Exception as e:
        pass


    return {'msg_type': parts[5],
           'payload': {'date_time': parts[0] + ' ' + parts[1],
                       **payload_json}}


def main():
    
    log_file_path, set_type = sys.argv[1:]

    df_map = {'cathode:vital-signs': {'df': pd.DataFrame(),
                                      'file': vital_file_path.format(set_type)},
              'device:audio-preview': {'df': pd.DataFrame(),
                                       'file': audio_preview_path.format(set_type)},
              'device:stats': {'df': pd.DataFrame(),
                               'file': stats_path.format(set_type)}}

    i = 0
    with open(log_file_path, 'r') as log_f:

        while True:
            i = i + 1
            line = log_f.readline()
            if not line:
                break

            parsed = parse(line)

            msg_type = parsed['msg_type']
            if msg_type not in df_map:
                continue

            df_map[msg_type]['df'] = pd.concat([df_map[msg_type]['df'],
                                                pd.json_normalize(parsed['payload'])],
                                               ignore_index=True)
            if i > 100:
                pass
                # break

    audio_levels_df = df_map['device:audio-preview']['df']['audioLevelsDb'].astype(str) \
        .apply(lambda x: pd.Series(json.loads(x))).rename(columns={0: 'left', 1: 'right'})
    df_map['device:audio-preview']['df'] = pd.concat([df_map['device:audio-preview']['df'],
                                                      audio_levels_df], axis=1)

    for _, v in df_map.items():
        v['df'].to_csv(v['file'])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(e)
