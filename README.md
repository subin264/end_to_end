# end_to_end
Assignment submission

Original data address:
us: https://www.ftc.gov
uk (ico): https://ico.org.uk
uk (cma): https://www.gov.uk/government/organisations/competition-and-markets-authority
de (open legal data): https://openlegaldata.io
de (enforcement tracker): https://www.enforcementtracker.com
au (violation tracker global): https://violationtracker.goodjobsfirst.org
ca (competition bureau): https://competition-bureau.canada.ca
kr (kftc): https://www.ftc.go.kr

### these are the minimum packages used across the pipeline (collection -> processing/eda -> modeling).

- pandas
- numpy
- requests
- beautifulsoup4
- selenium
- webdriver-manager
- pdfplumber
- matplotlib
- seaborn
- openpyxl

## key artifacts used in modeling

- modeling entry point: `03_Modeling/Modeling_code/run_pipeline.py`
- final inputs used by modeling:
- `03_Modeling/Final_use_data/layer1_regulation_metadata.csv`
- `03_Modeling/Final_use_data/layer2_final_data.csv`
- `03_Modeling/Final_use_data/2_mag_layer3_market_talent_2024_fixed.csv`


## 1) processing (build final dataset)

- run the processing script(s) under `02_processing_eda/code/` to convert raw outputs into the unified schema and to build the final dataset.
- expected key output file: `02_processing_eda/03_eda/data/layer2_final_data.csv`

## 2) eda (analysis notebook)

- open and run: `02_processing_eda/03_eda/code/eda_final.ipynb`
- additional working notebook (optional): `02_processing_eda/code/Total_Work_Desk_eda.ipynb`

## 3) modeling (final submission)

- run the code under `03_modeling/` to generate rankings and scenario outputs.

## key outputs

- **final dataset for modeling/eda**: `02_processing_eda/03_eda/data/layer2_final_data.csv`
- **eda figures/logs**: `02_processing_eda/03_eda/eda_results/`
