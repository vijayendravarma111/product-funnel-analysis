import sqlite3
import pandas as pd
import numpy as np
import scipy.stats as stats
import os

def load_ab_data(db_path='data/events.db'):
    """
    Loads raw event stream data from SQLite and structures it for A/B testing:
    - User-level conversion: whether they reached the 'purchase' event.
    - User-level time-to-conversion: time between 'view' and 'purchase' for converted users.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}. Please run data generation script first.")
        
    conn = sqlite3.connect(db_path)
    
    # Query 1: Get conversion status for all users
    # Every user has a 'view' event. We check if they also have a 'purchase' event.
    query_users = """
    SELECT 
        user_id,
        ab_group,
        MAX(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) as viewed,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as converted,
        device,
        traffic_source
    FROM events
    GROUP BY user_id, ab_group, device, traffic_source
    """
    df_users = pd.read_sql_query(query_users, conn)
    
    # Query 2: Get time-to-conversion for converted users
    # We find the min view timestamp and min purchase timestamp for each user
    query_times = """
    WITH view_times AS (
        SELECT user_id, MIN(timestamp) as view_time
        FROM events
        WHERE event_type = 'view'
        GROUP BY user_id
    ),
    purchase_times AS (
        SELECT user_id, MIN(timestamp) as purchase_time
        FROM events
        WHERE event_type = 'purchase'
        GROUP BY user_id
    )
    SELECT 
        e.user_id,
        e.ab_group,
        v.view_time,
        p.purchase_time,
        (strftime('%s', p.purchase_time) - strftime('%s', v.view_time)) / 60.0 as time_to_convert_minutes
    FROM events e
    JOIN view_times v ON e.user_id = v.user_id
    JOIN purchase_times p ON e.user_id = p.user_id
    GROUP BY e.user_id, e.ab_group
    """
    df_times = pd.read_sql_query(query_times, conn)
    
    conn.close()
    return df_users, df_times

def run_conversion_chi2(df_users):
    """
    Performs a Chi-Square Test of Independence on conversion rates.
    Returns test statistics, p-value, rates, confidence interval, and interpretation.
    """
    # Create contingency table
    contingency = pd.crosstab(df_users['ab_group'], df_users['converted'])
    
    # Converted & Total counts
    a_conv = contingency.loc['Control A', 1]
    a_total = contingency.loc['Control A'].sum()
    b_conv = contingency.loc['Variant B', 1]
    b_total = contingency.loc['Variant B'].sum()
    
    cr_a = a_conv / a_total
    cr_b = b_conv / b_total
    
    # Chi-square test
    chi2, p_val, dof, expected = stats.chi2_contingency(contingency, correction=True)
    
    # Calculate 95% Confidence Interval for difference in proportions (prop_B - prop_A)
    diff = cr_b - cr_a
    se = np.sqrt((cr_a * (1 - cr_a) / a_total) + (cr_b * (1 - cr_b) / b_total))
    z_crit = stats.norm.ppf(0.975) # ~1.96
    me = z_crit * se
    ci_lower = diff - me
    ci_upper = diff + me
    
    # Relative Lift
    lift = (cr_b - cr_a) / cr_a if cr_a > 0 else 0
    
    significant = p_val < 0.05
    interpretation = (
        "Statistically Significant: There is a significant difference in conversion rates between the groups. "
        "Variant B outperformed Control A." if significant and diff > 0 else
        "Statistically Significant: Control A converted better than Variant B." if significant and diff < 0 else
        "Not Statistically Significant: No sufficient evidence to conclude a difference in conversion rates."
    )
    
    return {
        'cr_a': cr_a,
        'cr_b': cr_b,
        'a_conv': int(a_conv),
        'a_total': int(a_total),
        'b_conv': int(b_conv),
        'b_total': int(b_total),
        'chi2_stat': chi2,
        'p_value': p_val,
        'difference': diff,
        'relative_lift': lift,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'significant': significant,
        'interpretation': interpretation
    }

def run_time_to_conversion_ttest(df_times):
    """
    Performs a Two-Sample Welch's t-test on Time-to-Conversion (minutes).
    Returns test statistics, p-value, means, effect size (Cohen's d), CI of difference, and interpretation.
    """
    times_a = df_times[df_times['ab_group'] == 'Control A']['time_to_convert_minutes'].values
    times_b = df_times[df_times['ab_group'] == 'Variant B']['time_to_convert_minutes'].values
    
    n_a, n_b = len(times_a), len(times_b)
    mean_a, mean_b = np.mean(times_a), np.mean(times_b)
    var_a, var_b = np.var(times_a, ddof=1), np.var(times_b, ddof=1)
    std_a, std_b = np.std(times_a, ddof=1), np.std(times_b, ddof=1)
    
    # Welch's t-test (equal_var=False)
    t_stat, p_val = stats.ttest_ind(times_a, times_b, equal_var=False)
    
    # Cohen's d (pooled standard deviation)
    pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    # Cohen's d: positive means Group A took longer than Group B (which is B being faster/better)
    cohen_d = (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0
    
    # Welch-Satterthwaite degrees of freedom for confidence interval
    se_diff = np.sqrt((var_a / n_a) + (var_b / n_b))
    df = ((var_a / n_a) + (var_b / n_b))**2 / (
        ((var_a / n_a)**2 / (n_a - 1)) + ((var_b / n_b)**2 / (n_b - 1))
    )
    t_crit = stats.t.ppf(0.975, df)
    mean_diff = mean_a - mean_b # Positive means B is faster (takes fewer minutes)
    ci_lower = mean_diff - (t_crit * se_diff)
    ci_upper = mean_diff + (t_crit * se_diff)
    
    significant = p_val < 0.05
    # Since we hope Variant B is FASTER, we hope mean_b < mean_a (mean_diff > 0)
    interpretation = (
        "Statistically Significant: Variant B significantly reduced checkout friction, resulting in a faster time-to-conversion."
        if significant and mean_diff > 0 else
        "Statistically Significant: Variant B took longer to convert than Control A."
        if significant and mean_diff < 0 else
        "Not Statistically Significant: No significant difference in time-to-conversion between groups."
    )
    
    return {
        'n_a': n_a,
        'n_b': n_b,
        'mean_a': mean_a,
        'mean_b': mean_b,
        'std_a': std_a,
        'std_b': std_b,
        't_stat': t_stat,
        'p_value': p_val,
        'mean_difference': mean_diff,
        'cohen_d': cohen_d,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'significant': significant,
        'interpretation': interpretation
    }

if __name__ == "__main__":
    print("="*60)
    print("RUNNING RIGOROUS A/B TEST ANALYTICS")
    print("="*60)
    
    try:
        df_users, df_times = load_ab_data()
        
        # 1. Conversion Rate Chi-Square
        conv_res = run_conversion_chi2(df_users)
        print("\n--- Conversion Rate (Chi-Square Test) ---")
        print(f"Control A Conversion Rate: {conv_res['cr_a']*100:.2f}% ({conv_res['a_conv']}/{conv_res['a_total']})")
        print(f"Variant B Conversion Rate: {conv_res['cr_b']*100:.2f}% ({conv_res['b_conv']}/{conv_res['b_total']})")
        print(f"Absolute Conversion Lift: {conv_res['difference']*100:+.2f}%")
        print(f"Relative Uplift: {conv_res['relative_lift']*100:+.2f}%")
        print(f"Chi-Square Statistic: {conv_res['chi2_stat']:.4f}")
        print(f"p-value: {conv_res['p_value']:.4e}")
        print(f"95% CI of Difference: [{conv_res['ci_lower']*100:.2f}%, {conv_res['ci_upper']*100:.2f}%]")
        print(f"Interpretation: {conv_res['interpretation']}")
        
        # 2. Time-to-Conversion t-test
        time_res = run_time_to_conversion_ttest(df_times)
        print("\n--- Time-to-Conversion (Welch's t-test) ---")
        print(f"Control A Mean Time: {time_res['mean_a']:.2f} minutes (std={time_res['std_a']:.2f}, n={time_res['n_a']})")
        print(f"Variant B Mean Time: {time_res['mean_b']:.2f} minutes (std={time_res['std_b']:.2f}, n={time_res['n_b']})")
        print(f"Friction Reduction (Mean Diff): {time_res['mean_difference']:.2f} minutes faster")
        print(f"t-statistic: {time_res['t_stat']:.4f}")
        print(f"p-value: {time_res['p_value']:.4e}")
        print(f"Effect Size (Cohen's d): {time_res['cohen_d']:.4f}")
        print(f"95% CI of Time Difference: [{time_res['ci_lower']:.2f} mins, {time_res['ci_upper']:.2f} mins]")
        print(f"Interpretation: {time_res['interpretation']}")
        
    except Exception as e:
        print(f"Error executing analysis: {e}")
    print("="*60)
