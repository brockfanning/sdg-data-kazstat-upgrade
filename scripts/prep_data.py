import os
import sdg

inputs = []

# Use .md files for metadata
meta_pattern = os.path.join('meta', '*-*.md')
meta_input = sdg.inputs.InputYamlMdMeta(path_pattern=meta_pattern)

data_pattern = os.path.join('data', '*-*.csv')
data_input = sdg.inputs.InputCsvData(path_pattern=data_pattern)

# Combine these inputs into one list.
inputs = [data_input, meta_input]

# Use the Prose.io file for the metadata schema.
schema_path = os.path.join('_prose.yml')
schema = sdg.schemas.SchemaInputOpenSdg(schema_path=schema_path)

# Pull in translations.
translations = [
    # Pull in translations from the two usual repositories.
    sdg.translations.TranslationInputSdgTranslations(source='https://github.com/open-sdg/translations-open-sdg.git', branch='master'),
    sdg.translations.TranslationInputSdgTranslations(source='https://github.com/open-sdg/translations-un-sdg.git', tag='1.0.0-rc1'),
    # Also pull in translations from the 'translations' folder in this repo.
    sdg.translations.TranslationInputYaml(source='translations')
]

# Create an "output" from these inputs and schema, for JSON for Open SDG.
opensdg_output = sdg.outputs.OutputOpenSdg(
    inputs,
    schema,
    translations=translations
)

# Create an output for GeoJSON as well.
geojson_output = sdg.outputs.OutputGeoJson(
    inputs,
    schema,
    translations=translations,
    name_property='kzName',
    id_property='kzCode'
)
