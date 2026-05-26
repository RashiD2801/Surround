"""
Krakow PM2.5 Dataset Cleaning Script
=====================================
Cleans krakow_ml_dataset.csv following the 8-step cleaning workflow.

Based on:
- krakow_dataset_overview.docx
- krakow_feature_engineering_guide.docx
- data-cleaning-log.md
- problem-brief-v2.md

Run from project root:
    python clean_krakow_dataset.py

Output:
    krakow_ml_dataset_CLEANED.csv    (ready for model training)
    cleaning_report.txt               (summary of what was done)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

INPUT_FILE = "krakow_ml_dataset.csv"
OUTPUT_FILE = "krakow_ml_dataset_CLEANED.csv"
REPORT_FILE = "cleaning_report.txt"

# Date range for project (from problem-brief-v2.md)
PROJECT_START_YEAR = 2019
PROJECT_END_YEAR = 2024

# COVID exclusion window (from data-cleaning-log.md)
COVID_EXCLUDE_START = '2020-03-15'
COVID_EXCLUDE_END = '2020-05-31'

# Lag feature cold start period
LAG_COLD_START_DAYS = 14

# High-missingness threshold for dropping features
HIGH_MISSING_THRESHOLD = 0.50  # Drop if >50% missing

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def log_step(step_num, title, message):
    """Print and store log message"""
    header = f"\n{'='*80}\nSTEP {step_num}: {title}\n{'='*80}"
    print(header)
    print(message)
    return f"{header}\n{message}\n"


def reconstruct_date(df):
    """Reconstruct date column from year and day_of_year"""
    df = df.copy()
    df['date'] = pd.to_datetime(
        df['year'].astype(int).astype(str) + '-01-01'
    ) + pd.to_timedelta(df['day_of_year'] - 1, unit='D')
    return df


# ═══════════════════════════════════════════════════════════════════════════
# MAIN CLEANING PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def clean_dataset(input_path):
    """
    Execute 8-step cleaning workflow.
    Returns: (cleaned_df, report_text)
    """
    report = []
    report.append(f"KRAKOW PM2.5 DATASET CLEANING REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Input file: {input_path}")
    report.append("=" * 80 + "\n")
    
    # ───────────────────────────────────────────────────────────────────────
    # LOAD DATA
    # ───────────────────────────────────────────────────────────────────────
    
    print(f"\n🔄 Loading {input_path}...")
    df = pd.read_csv(input_path)
    
    initial_shape = df.shape
    initial_rows = len(df)
    
    report.append(f"INITIAL DATASET")
    report.append(f"  Shape: {df.shape}")
    report.append(f"  Rows: {initial_rows:,}")
    report.append(f"  Columns: {df.shape[1]}")
    report.append(f"  Date range (years): {df['year'].min()} to {df['year'].max()}")
    report.append("")
    
    # ───────────────────────────────────────────────────────────────────────
    # STEP 1: Filter Date Range (2019-2024)
    # ───────────────────────────────────────────────────────────────────────
    
    before_step1 = len(df)
    df = df[(df['year'] >= PROJECT_START_YEAR) & 
            (df['year'] <= PROJECT_END_YEAR)].copy()
    removed_step1 = before_step1 - len(df)
    
    msg = (f"Filtered to project scope: {PROJECT_START_YEAR}-{PROJECT_END_YEAR}\n"
           f"  Before: {before_step1:,} rows\n"
           f"  After:  {len(df):,} rows\n"
           f"  Removed: {removed_step1:,} rows ({removed_step1/before_step1*100:.1f}%)\n"
           f"  Reason: Data outside project timeframe (2016-2018 pre-study, 2025-2026 future)")
    report.append(log_step(1, "FILTER DATE RANGE", msg))
    
    # ───────────────────────────────────────────────────────────────────────
    # STEP 2: Handle Target Variable (PM2.5)
    # ───────────────────────────────────────────────────────────────────────
    
    pm25_missing = df['pm25'].isna().sum()
    pm25_missing_pct = pm25_missing / len(df) * 100
    
    # Check for negatives
    pm25_negative = (df['pm25'] < 0).sum() if df['pm25'].notna().any() else 0
    
    before_step2 = len(df)
    df = df.dropna(subset=['pm25']).copy()
    removed_step2 = before_step2 - len(df)
    
    # Clip negatives if any
    if (df['pm25'] < 0).any():
        df['pm25'] = df['pm25'].clip(lower=0)
    
    msg = (f"Dropped rows with missing PM2.5 (target variable)\n"
           f"  PM2.5 missing before: {pm25_missing:,} ({pm25_missing_pct:.1f}%)\n"
           f"  Negative values found: {pm25_negative}\n"
           f"  Before: {before_step2:,} rows\n"
           f"  After:  {len(df):,} rows\n"
           f"  Removed: {removed_step2:,} rows\n"
           f"  Reason: Cannot train on rows without target variable")
    report.append(log_step(2, "HANDLE TARGET VARIABLE (PM2.5)", msg))
    
    # ───────────────────────────────────────────────────────────────────────
    # STEP 3: Handle Lag Features Cold Start
    # ───────────────────────────────────────────────────────────────────────
    
    before_step3 = len(df)
    df = df.iloc[LAG_COLD_START_DAYS:].reset_index(drop=True)
    removed_step3 = before_step3 - len(df)
    
    # Check remaining missingness in lag features
    lag_cols = [c for c in df.columns if 'lag' in c or 'roll' in c or 'std' in c]
    lag_missing = df[lag_cols].isnull().sum().sum()
    
    msg = (f"Removed cold start period for lag features\n"
           f"  Cold start period: {LAG_COLD_START_DAYS} days\n"
           f"  Before: {before_step3:,} rows\n"
           f"  After:  {len(df):,} rows\n"
           f"  Removed: {removed_step3:,} rows\n"
           f"  Remaining missing in lag features: {lag_missing:,}\n"
           f"  Reason: Lag features need historical data to compute")
    report.append(log_step(3, "HANDLE LAG FEATURES", msg))
    
    # ───────────────────────────────────────────────────────────────────────
    # STEP 4: Exclude COVID Period
    # ───────────────────────────────────────────────────────────────────────
    
    # Reconstruct date column
    df = reconstruct_date(df)
    
    before_step4 = len(df)
    covid_mask = (df['date'] >= COVID_EXCLUDE_START) & (df['date'] <= COVID_EXCLUDE_END)
    removed_step4 = covid_mask.sum()
    df = df[~covid_mask].copy()
    
    msg = (f"Excluded COVID lockdown period\n"
           f"  Period: {COVID_EXCLUDE_START} to {COVID_EXCLUDE_END}\n"
           f"  Before: {before_step4:,} rows\n"
           f"  After:  {len(df):,} rows\n"
           f"  Removed: {removed_step4:,} rows\n"
           f"  Reason: Traffic -40%, PM2.5 -30% during lockdown (not representative)")
    report.append(log_step(4, "EXCLUDE COVID PERIOD", msg))
    
    # ───────────────────────────────────────────────────────────────────────
    # STEP 5: Drop High-Missing Features
    # ───────────────────────────────────────────────────────────────────────
    
    # Check missingness for each column
    missing_pct = df.isnull().sum() / len(df)
    high_missing_cols = missing_pct[missing_pct > HIGH_MISSING_THRESHOLD].index.tolist()
    
    # Always check CO specifically (documented as 65% missing)
    if 'co' in df.columns and 'co' not in high_missing_cols:
        co_missing_pct = df['co'].isna().sum() / len(df)
        if co_missing_pct > 0.50:
            high_missing_cols.append('co')
    
    dropped_cols = []
    drop_details = []
    for col in high_missing_cols:
        missing_count = df[col].isna().sum()
        missing_pct_val = missing_count / len(df) * 100
        dropped_cols.append(col)
        drop_details.append(f"    {col}: {missing_count:,} missing ({missing_pct_val:.1f}%)")
        df = df.drop(columns=[col])
    
    msg = (f"Dropped features with >{HIGH_MISSING_THRESHOLD*100:.0f}% missing values\n"
           f"  Columns dropped: {len(dropped_cols)}\n")
    if dropped_cols:
        msg += "\n".join(drop_details)
    else:
        msg += "    (None - all features have <50% missingness)"
    msg += f"\n  Reason: High missingness adds noise without signal"
    report.append(log_step(5, "DROP HIGH-MISSING FEATURES", msg))
    
    # ───────────────────────────────────────────────────────────────────────
    # STEP 6: Handle Other Pollutant Missing Values
    # ───────────────────────────────────────────────────────────────────────
    
    pollutant_cols = ['pm10', 'o3', 'no2', 'so2']
    pollutant_cols = [c for c in pollutant_cols if c in df.columns]
    
    imputation_details = []
    total_imputed = 0
    for col in pollutant_cols:
        missing = df[col].isna().sum()
        if missing > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            total_imputed += missing
            imputation_details.append(
                f"    {col}: {missing:,} missing → filled with median ({median_val:.2f})"
            )
    
    msg = (f"Imputed missing values in pollutant features with median\n"
           f"  Total values imputed: {total_imputed:,}\n")
    if imputation_details:
        msg += "\n".join(imputation_details)
    else:
        msg += "    (No imputation needed - all pollutant columns complete)"
    msg += f"\n  Reason: These are features (not targets), median imputation acceptable"
    report.append(log_step(6, "HANDLE OTHER POLLUTANT MISSING VALUES", msg))
    
    # ───────────────────────────────────────────────────────────────────────
    # STEP 7: Check for Extreme Values
    # ───────────────────────────────────────────────────────────────────────
    
    extreme_threshold = 200  # µg/m³
    extreme = df[df['pm25'] > extreme_threshold]
    
    msg = (f"Checked for extreme PM2.5 values (>{extreme_threshold} µg/m³)\n"
           f"  Extreme values found: {len(extreme)}\n")
    
    if len(extreme) > 0:
        extreme_summary = extreme.groupby('month')['pm25'].agg(['count', 'mean', 'max'])
        msg += f"\n  Breakdown by month:\n"
        for month, row in extreme_summary.iterrows():
            msg += f"    Month {int(month)}: {int(row['count'])} days, "
            msg += f"mean={row['mean']:.1f}, max={row['max']:.1f}\n"
        msg += (f"  Decision: KEPT (these are real winter pollution events)\n"
                f"  Note: Krakow has severe winter pollution; values >200 are uncommon but real")
    else:
        msg += "    (No extreme values found)\n"
        msg += f"  All PM2.5 values are within reasonable range (<{extreme_threshold} µg/m³)"
    
    report.append(log_step(7, "CHECK FOR EXTREME VALUES", msg))
    
    # ───────────────────────────────────────────────────────────────────────
    # STEP 8: Final Cleanup and Save
    # ───────────────────────────────────────────────────────────────────────
    
    # Drop the reconstructed date column (not a model feature)
    if 'date' in df.columns:
        df = df.drop(columns=['date'])
    
    # Reset index
    df = df.reset_index(drop=True)
    
    # Final statistics
    final_shape = df.shape
    final_missing = df.isnull().sum()
    cols_with_missing = final_missing[final_missing > 0]
    
    msg = (f"Final cleanup and preparation for model training\n"
           f"  Dropped temporary 'date' column (reconstructed for COVID filter)\n"
           f"  Reset index\n"
           f"  Final shape: {final_shape}\n"
           f"  Columns with remaining missing values: {len(cols_with_missing)}\n")
    
    if len(cols_with_missing) > 0:
        msg += "\n  Remaining missingness:\n"
        for col, missing in cols_with_missing.items():
            msg += f"    {col}: {missing:,} ({missing/len(df)*100:.2f}%)\n"
    else:
        msg += "    ✅ No missing values remain!\n"
    
    report.append(log_step(8, "FINAL CLEANUP", msg))
    
    # ───────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ───────────────────────────────────────────────────────────────────────
    
    total_removed = initial_rows - len(df)
    retention_rate = len(df) / initial_rows * 100
    
    summary = f"\n{'='*80}\n"
    summary += "CLEANING SUMMARY\n"
    summary += f"{'='*80}\n"
    summary += f"Initial rows:        {initial_rows:>8,}\n"
    summary += f"Final rows:          {len(df):>8,}\n"
    summary += f"Rows removed:        {total_removed:>8,} ({total_removed/initial_rows*100:.1f}%)\n"
    summary += f"Retention rate:      {retention_rate:>7.1f}%\n"
    summary += f"\n"
    summary += f"Initial columns:     {initial_shape[1]:>8,}\n"
    summary += f"Final columns:       {final_shape[1]:>8,}\n"
    summary += f"Columns dropped:     {initial_shape[1] - final_shape[1]:>8,}\n"
    summary += f"\n"
    summary += f"Date range:          {df['year'].min()}-{df['year'].max()}\n"
    summary += f"Target completeness: 100% (all rows have PM2.5)\n"
    summary += f"\n"
    summary += "BREAKDOWN OF REMOVED ROWS:\n"
    summary += f"  Step 1 (date filter):     {removed_step1:>6,} rows\n"
    summary += f"  Step 2 (missing PM2.5):   {removed_step2:>6,} rows\n"
    summary += f"  Step 3 (lag cold start):  {removed_step3:>6,} rows\n"
    summary += f"  Step 4 (COVID period):    {removed_step4:>6,} rows\n"
    summary += f"  {'─'*40}\n"
    summary += f"  Total:                    {total_removed:>6,} rows\n"
    
    print(summary)
    report.append(summary)
    
    return df, "\n".join(report)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*80)
    print("KRAKOW PM2.5 DATASET CLEANING")
    print("="*80)
    print(f"Input:  {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Report: {REPORT_FILE}")
    
    # Check if input file exists
    if not Path(INPUT_FILE).exists():
        print(f"\n❌ ERROR: Input file '{INPUT_FILE}' not found!")
        print("   Please ensure krakow_ml_dataset.csv is in the current directory.")
        exit(1)
    
    # Run cleaning pipeline
    try:
        df_cleaned, report_text = clean_dataset(INPUT_FILE)
        
        # Save cleaned dataset
        df_cleaned.to_csv(OUTPUT_FILE, index=False)
        print(f"\n✅ Saved cleaned dataset: {OUTPUT_FILE}")
        print(f"   Shape: {df_cleaned.shape}")
        
        # Save report
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"✅ Saved cleaning report: {REPORT_FILE}")
        
        # Final validation
        print(f"\n{'='*80}")
        print("VALIDATION CHECKS")
        print(f"{'='*80}")
        
        checks_passed = []
        checks_failed = []
        
        # Check 1: No missing PM2.5
        if df_cleaned['pm25'].isna().sum() == 0:
            checks_passed.append("✅ No missing PM2.5 values")
        else:
            checks_failed.append(f"❌ {df_cleaned['pm25'].isna().sum()} missing PM2.5 values remain")
        
        # Check 2: Date range correct
        if df_cleaned['year'].min() >= PROJECT_START_YEAR and df_cleaned['year'].max() <= PROJECT_END_YEAR:
            checks_passed.append(f"✅ Date range correct ({PROJECT_START_YEAR}-{PROJECT_END_YEAR})")
        else:
            checks_failed.append(f"❌ Date range incorrect: {df_cleaned['year'].min()}-{df_cleaned['year'].max()}")
        
        # Check 3: COVID period excluded
        df_with_date = reconstruct_date(df_cleaned)
        covid_mask = (df_with_date['date'] >= COVID_EXCLUDE_START) & (df_with_date['date'] <= COVID_EXCLUDE_END)
        if covid_mask.sum() == 0:
            checks_passed.append("✅ COVID period excluded")
        else:
            checks_failed.append(f"❌ {covid_mask.sum()} rows from COVID period remain")
        
        # Check 4: No negative PM2.5
        if (df_cleaned['pm25'] >= 0).all():
            checks_passed.append("✅ No negative PM2.5 values")
        else:
            checks_failed.append(f"❌ {(df_cleaned['pm25'] < 0).sum()} negative PM2.5 values")
        
        # Check 5: Reasonable row count
        if len(df_cleaned) > 1000:
            checks_passed.append(f"✅ Reasonable sample size ({len(df_cleaned):,} rows)")
        else:
            checks_failed.append(f"❌ Sample size too small ({len(df_cleaned):,} rows)")
        
        # Print checks
        for check in checks_passed:
            print(check)
        for check in checks_failed:
            print(check)
        
        if len(checks_failed) == 0:
            print(f"\n{'='*80}")
            print("🎉 ALL VALIDATION CHECKS PASSED!")
            print(f"{'='*80}")
            print(f"\nYour cleaned dataset is ready for model training.")
            print(f"Next steps:")
            print(f"  1. Run exploratory data analysis on {OUTPUT_FILE}")
            print(f"  2. Perform train/test split (chronological, not random)")
            print(f"  3. Train baseline models (Linear → Random Forest → XGBoost)")
            print(f"  4. Evaluate with MAE, RMSE, R²")
        else:
            print(f"\n{'='*80}")
            print("⚠️  SOME VALIDATION CHECKS FAILED")
            print(f"{'='*80}")
            print(f"Review the issues above before proceeding to modeling.")
        
    except Exception as e:
        print(f"\n❌ ERROR during cleaning: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
