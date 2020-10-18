from sdg.open_sdg import open_sdg_build

def alter_meta(metadata):
    indicator_id = metadata['indicator_number']
    id_parts = indicator_id.split('.')
    is_global_indicator = len(id_parts) == 3
    metadata['is_global_indicator'] = is_global_indicator
    return metadata

def alter_data(data):
    rename_columns = {
        'UNIT_MEASURE': 'Units',
        'SERIES': 'Series',
    }
    return data.rename(columns=rename_columns)

open_sdg_build(config='config_data.yml', alter_meta=alter_meta, alter_data=alter_data)
