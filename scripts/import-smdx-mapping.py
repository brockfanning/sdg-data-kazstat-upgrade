import pandas as pd
import numpy as np
import os
import yaml

disaggregations = {}
codes = None
composite_breakdowns = {}

languages = ['ru', 'kk', 'en']
data_translations = {}
new_translations = {}
for language in languages:
    data_translation_file = os.path.join('translations', language, 'data.yml')
    with open(data_translation_file, 'r', encoding='utf-8') as stream:
        data_translations[language] = yaml.load(stream, Loader=yaml.FullLoader)

russian_inverted = {v: k for k, v in data_translations['ru'].items()}

def parse_code_sheet(df):
    renamed_columns = []
    columns = df.iloc[1]
    last_column = None
    for column in columns:
        if column == 'Name':
            column = last_column + ' ' + 'Name'
        renamed_columns.append(column)
        last_column = column

    df.columns = renamed_columns
    df = df[2:]
    return df

def parse_unit_sheet(df):
    df = df[[3, 4]]
    df.columns = ['from', 'to']
    df = df.iloc[2:]
    df = df.dropna()
    return dict(df.values.tolist())

def stop_at_first_blank_row(df):
    first_empty_row = 0
    for index, row in df.iterrows():
        if pd.isnull(row['Value']):
            first_empty_row = index
            break

    return df.head(first_empty_row)

def get_value_by_label(dimension, label):
    if pd.isnull(dimension):
        raise Exception('Cannot search for null dimension in code list. Label was: ' + str(label))
    if pd.isnull(label):
        raise Exception('Cannot search for null label in code list. Dimension was: ' + str(dimension))
    for _, row in codes.iterrows():
        if pd.isnull(row[dimension]):
            break
        row_value = row[dimension]
        row_label = row[dimension + ' Name']
        if row_label == label:
            return row_value

    raise Exception('Could not find ' + str(dimension) + '/' + str(label) + ' in codes list.')

def update_translations(change_map, group):
    for language in languages:
        if language not in new_translations:
            new_translations[language] = {}
        if group not in new_translations[language]:
            new_translations[language][group] = {}
        for original in change_map:
            changed = change_map[original]
            if original in data_translations[language]:
                new_translations[language][group][changed] = data_translations[language][original]

sheets = pd.read_excel(os.path.join('scripts', 'sdmx-mapping.xlsx'),
    sheet_name=None,
    index_col=None,
    header=None,
    keep_default_na=False,
    na_values=['#REF!', '']
)

codes = parse_code_sheet(sheets['CODES'])
units = parse_unit_sheet(sheets['UNITS'])
del sheets['CODES']
del sheets['UNITS']
columns_renamed = {}

debug = False

for sheet_name in sheets:

    df = sheets[sheet_name]
    disaggregation = df.iloc[0][0]
    df = df.rename(columns=df.iloc[1])
    df = stop_at_first_blank_row(df)
    df = df[2:]

    disaggregations[disaggregation] = {
        'rename': {},
        'remove': [],
        'dimensions': {},
        'translation': {},
    }
    composite_breakdowns[disaggregation] = False
    for idx, row in df.iterrows():
        original_value = row['Value']

        # Because we mistakenly put Russian translations in this spreadsheet, we have to
        # un-translate it here.
        original_value = russian_inverted[original_value]

        dimension = row['Dimension 1']
        value_label = row['Code 1']
        if dimension == 'COMPOSITE_BREAKDOWN':
            composite_breakdowns[disaggregation] = True
        if dimension == '[REMOVE]':
            disaggregations[disaggregation]['remove'].append(original_value)
        else:
            if dimension not in disaggregations[disaggregation]['dimensions']:
                disaggregations[disaggregation]['dimensions'][dimension] = 0
            disaggregations[disaggregation]['dimensions'][dimension] += 1
            try:
                value_code = get_value_by_label(dimension, value_label)
                disaggregations[disaggregation]['rename'][original_value] = dimension + '.' + value_code
                disaggregations[disaggregation]['translation'][original_value] = value_code
            except Exception as e:
                if debug:
                    print('A problem happened while trying to get the code for this row:')
                    print(row)
                    print('The problem was:')
                    print(e)

        if not pd.isnull(row['Dimension 2 (optional)']):
            print('WARNING: NEED TO DEAL WITH DIMENSION 2!!')

    most_common_dimension_name = None
    most_common_dimension_score = 0
    for dimension in disaggregations[disaggregation]['dimensions']:
        if most_common_dimension_name is None:
            most_common_dimension_name = dimension
            most_common_dimension_score = disaggregations[disaggregation]['dimensions'][dimension]
        else:
            this_score = disaggregations[disaggregation]['dimensions'][dimension]
            if this_score > most_common_dimension_score:
                most_common_dimension_name = dimension
                most_common_dimension_score = this_score
    if most_common_dimension_name is None:
        print('Probable dimension appeared to be None: ' + disaggregation)
    if pd.isna(most_common_dimension_name):
        print('Probable dimension appeared to be NaN: ' + disaggregation)
    else:
        columns_renamed[disaggregation] = most_common_dimension_name

columns_renamed_translation_keys = {}
for disaggregation in columns_renamed:
    if disaggregation and columns_renamed[disaggregation]:
        translation_key = 'codelist.' + columns_renamed[disaggregation]
        columns_renamed_translation_keys[disaggregation] = translation_key

composite_breakdown_collisions = {}
for filename in os.listdir('data'):
    df = pd.read_csv(os.path.join('data', filename), dtype='str')
    if df.empty:
        continue
    composite_breakdowns_used = []
    for column in df.columns:
        if column in disaggregations:
            if disaggregations[column]['remove']:
                # Clear any cell that contains a "removed" value.
                df[column].mask(df[column].isin(disaggregations[column]['remove']), np.NaN, inplace=True)
            if disaggregations[column]['rename'] and column in df.columns:
                df[column] = df[column].map(disaggregations[column]['rename'])
                if column in composite_breakdowns and composite_breakdowns[column]:
                    composite_breakdowns_used.append(column)
                # Update translations too.
                update_translations(disaggregations[column]['translation'], columns_renamed[column])
        elif column == 'Units':
            df[column] = df[column].map(units)
            update_translations(units, 'Units')

    # Rename the columns.
    new_column_occurences = {}
    old_columns = list(df.columns)
    for old_column in old_columns:
        if old_column in columns_renamed_translation_keys:
            new_column = columns_renamed_translation_keys[old_column]
            if new_column not in new_column_occurences:
                new_column_occurences[new_column] = [old_column]
            else:
                if old_column not in new_column_occurences[new_column]:
                    new_column_occurences[new_column].append(old_column)
    for new_column in new_column_occurences:
        if len(new_column_occurences[new_column]) > 1:
            #print('uhoh - ' + filename)
            #print('new column: ' + new_column)
            #print('old_columns:')
            #print(new_column_occurences[new_column])
            merge_to = None
            for column in new_column_occurences[new_column]:
                if merge_to is None:
                    merge_to = column
                    continue
                df[merge_to] = df[merge_to].combine_first(df[column])
                df.drop(column, axis=1, inplace=True)
            #print('merged columns')
            #print(list(df.columns))
    #print(new_column_occurences)
    df = df.rename(columns=columns_renamed_translation_keys)
    update_translations(columns_renamed, 'codelist')

    if len(composite_breakdowns_used) > 1:
        for composite_breakdown_used in composite_breakdowns_used:
            if composite_breakdown_used not in composite_breakdown_collisions:
                composite_breakdown_collisions[composite_breakdown_used] = 1
            else:
                composite_breakdown_collisions[composite_breakdown_used] += 1
        print('WARNING: ' + filename + ' uses COMPOSITE_BREAKDOWN in ' + str(len(composite_breakdowns_used)) + ' columns:')
        print(composite_breakdowns_used)

    # Drop empty columns.
    df.dropna(how='all', axis=1, inplace=True)
    # Write to disk.
    df.to_csv(os.path.join('data', filename), index=False)

#print(composite_breakdown_collisions)
for language in languages:
    for group in new_translations[language]:
        new_translation_file = os.path.join('translations', language, group + '.yml')
        with open(new_translation_file, 'w') as file:
            yaml.dump(new_translations[language][group], file, sort_keys=True, encoding='utf-8', allow_unicode=True)
