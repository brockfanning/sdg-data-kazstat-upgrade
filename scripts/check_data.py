import prep_data

valid = prep_data.opensdg_output.validate()
if not valid:
  raise Exception('There were validation errors. See output above.')
