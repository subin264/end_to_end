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
