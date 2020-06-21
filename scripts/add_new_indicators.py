import pandas as pd
import yaml
import os

def normalize_indicator_id(inid):
  return inid.strip('.').replace('.', '-')

source = pd.read_excel(
  'new_indicators.xlsx',
  usecols=[1,2,3,4,5,6,7],
  header=None,
  names=[
    'indicator',
    'en-global',
    'en-national',
    'ru-global',
    'ru-national',
    'kk-global',
    'kk-national',
  ],
  skiprows=[0,1,2]
)
for index,row in source.iterrows():
  indicator = normalize_indicator_id(row['indicator'])
  data_path = os.path.join('data', 'indicator_' + indicator + '.csv')
  meta_path = os.path.join('meta', indicator + '.md')
  del row['indicator']

  delete = False
  for prop in row:
    if prop == 'delete':
      delete = True

  if row.isnull().all():
    delete = True

  if delete:
    if os.path.isfile(data_path):
      print('Warning: ' + data_path + ' needs to be deleted.')
    if os.path.isfile(meta_path):
      print('Warning: ' + meta_path + ' needs to be deleted.')

  else:
    parts = indicator.split('-')
    data = 'Year,Units,Value'
    with open(data_path, 'w') as file:
      file.write(data)
    meta = {
      'indicator_number': indicator.replace('-', '.'),
      'goal_number': parts[0],
      'target_number': parts[0] + '.' + parts[1],
      'reporting_status': 'notstarted',
      'indicator_name': 'global_indicators.' + indicator + '-title',
      'indicator_available': 'national_indicators.' + indicator + '-title',
    }
    with open(meta_path, 'w') as file:
      yaml_str = yaml.dump(meta)
      file.write('---' + os.linesep + yaml_str + '---')
