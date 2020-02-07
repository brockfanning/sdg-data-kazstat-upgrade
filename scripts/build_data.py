import prep_data

languages = ['ru', 'kk', 'en']
prep_data.opensdg_output.execute_per_language(languages)
prep_data.geojson_output.execute_per_language(languages)
