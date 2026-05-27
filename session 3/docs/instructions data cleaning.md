📋 INSTRUCTIONS: How to Clean Your Krakow Dataset
⚡ Quick Start (For the Impatient)
bash# 1. Put the script and data in the same folder
# 2. Run this command:
python clean_krakow_dataset.py
Done! Your cleaned dataset will be saved as krakow_ml_dataset_CLEANED.csv.

📝 Detailed Instructions
Prerequisites
You need:

✅ Python 3.7 or higher
✅ pandas library (pip install pandas)
✅ numpy library (pip install numpy)

Check if you have them:
bashpython --version
python -c "import pandas; print(pandas.__version__)"
python -c "import numpy; print(numpy.__version__)"

Step 1: Organize Your Files
Create a folder and put these files in it:
your_project_folder/
├── krakow_ml_dataset.csv          ← Your original data (the one you uploaded)
└── clean_krakow_dataset.py        ← The cleaning script I created
Important: The script looks for krakow_ml_dataset.csv in the same folder. If your file has a different name, either:

Option A: Rename it to krakow_ml_dataset.csv
Option B: Edit line 28 in the script: INPUT_FILE = "your_actual_filename.csv"


Step 2: Run the Script
Windows:
cmdcd path\to\your_project_folder
python clean_krakow_dataset.py
Mac/Linux:
bashcd /path/to/your_project_folder
python clean_krakow_dataset.py

Step 3: Watch the Output
The script will print progress updates like this:
================================================================================
KRAKOW PM2.5 DATASET CLEANING
================================================================================
Input:  krakow_ml_dataset.csv
Output: krakow_ml_dataset_CLEANED.csv
Report: cleaning_report.txt

🔄 Loading krakow_ml_dataset.csv...

================================================================================
STEP 1: FILTER DATE RANGE
================================================================================
Filtered to project scope: 2019-2024
  Before: 3,744 rows
  After:  2,940 rows
  Removed: 804 rows (21.5%)
  ...

[... more steps ...]

================================================================================
CLEANING SUMMARY
================================================================================
Initial rows:            3,744
Final rows:              2,100
Rows removed:            1,644 (43.9%)
Retention rate:           56.1%
...

✅ Saved cleaned dataset: krakow_ml_dataset_CLEANED.csv
✅ Saved cleaning report: cleaning_report.txt

Step 4: Check Your Results
After the script finishes, you'll have 3 new files:

krakow_ml_dataset_CLEANED.csv ← Your cleaned dataset (USE THIS for modeling)
cleaning_report.txt ← Detailed log of what was done
Console output ← Summary printed to screen


🔍 What the Script Does (8 Steps)
StepWhat It DoesWhy1Filters to 2019-2024Removes data outside project scope2Drops rows with missing PM2.5Can't train without target variable3Removes first 14 daysLag features need history4Excludes COVID period (Mar-May 2020)Abnormal traffic/pollution5Drops features >50% missingCO column has 65% missing6Fills missing pollutants with medianAcceptable for features7Checks for extreme valuesKeeps real winter pollution spikes8Final cleanupPrepares for modeling

✅ Validation Checks
The script automatically validates:

✅ No missing PM2.5 values remain
✅ Date range is 2019-2024
✅ COVID period (Mar-May 2020) excluded
✅ No negative PM2.5 values
✅ Sample size >1000 rows

If all checks pass, you'll see:
🎉 ALL VALIDATION CHECKS PASSED!

📊 Expected Results
Before cleaning:

Rows: ~3,744
Missing PM2.5: 988 (26.4%)
Date range: 2016-2026
Columns: 87

After cleaning:

Rows: ~2,100-2,400 (depends on your data)
Missing PM2.5: 0 (0%)
Date range: 2019-2024 (minus COVID period)
Columns: ~86 (CO dropped if >50% missing)


🐛 Troubleshooting
Error: "Input file not found"
❌ ERROR: Input file 'krakow_ml_dataset.csv' not found!
Solution: Make sure:

The file is in the same folder as the script
The filename is exactly krakow_ml_dataset.csv
You're running the script from the correct folder


Error: "No module named 'pandas'"
ModuleNotFoundError: No module named 'pandas'
Solution: Install pandas:
bashpip install pandas numpy

Error: "Permission denied"
PermissionError: [Errno 13] Permission denied: 'krakow_ml_dataset_CLEANED.csv'
Solution: Close Excel or any program that has the file open, then run again.

Error: "'charmap' codec can't encode character"
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'
Solution: This is a Windows encoding issue. Fix line 363 in the script:
Change:
pythonwith open(REPORT_FILE, 'w') as f:
To:
pythonwith open(REPORT_FILE, 'w', encoding='utf-8') as f:
Or download the fixed version from the outputs folder.

Warning: "SOME VALIDATION CHECKS FAILED"
Solution: Check the console output to see which checks failed. Common issues:

Sample size too small → Check if your data has enough valid PM2.5 readings
COVID period not excluded → Check date reconstruction logic
Negative PM2.5 → Check for data quality issues


📈 Next Steps After Cleaning
Once you have krakow_ml_dataset_CLEANED.csv:

Exploratory Data Analysis

python   import pandas as pd
   df = pd.read_csv('krakow_ml_dataset_CLEANED.csv')
   print(df.describe())
   df['pm25'].hist(bins=50)

Train/Test Split

python   # Time-based split (NEVER random for time series!)
   train = df[df['year'] <= 2023]
   test = df[df['year'] >= 2024]

Train Baseline Model

python   from sklearn.ensemble import GradientBoostingRegressor
   # ... (see your krakow_pipeline.py for example)

Evaluate

MAE (Mean Absolute Error)
RMSE (Root Mean Squared Error)
R² (Explained Variance)




🆘 Need Help?
If something goes wrong:

Check the cleaning report: cleaning_report.txt has detailed logs
Look at console output: Shows exactly what happened at each step
Common issue: Make sure your CSV has the expected column names


📌 Key Reminders

✅ Never impute the target (PM2.5) — drop rows instead
✅ Use time-based splits — don't randomly shuffle time series data
✅ Keep extreme values — Krakow has real winter pollution spikes >200 µg/m³
✅ Document everything — the cleaning report is your audit trail