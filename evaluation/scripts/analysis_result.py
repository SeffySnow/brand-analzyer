#!/usr/bin/env python3
"""
Simplified analysis script for token optimization results.
Generates focused plots showing token usage efficiency.
"""

import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

def load_data():
    """Load token optimization results from JSON file."""
    data_path = Path(__file__).parent / "token_optimization_results.json"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    return data

def load_csv_data():
    """Load data from CSV file to verify plotting accuracy."""
    csv_path = Path(__file__).parent.parent / "results" / "token_analysis_results.csv"
    
    if not csv_path.exists():
        print("Warning: CSV file not found. Using JSON data instead.")
        return None
    
    df = pd.read_csv(csv_path)
    print(f"Loaded CSV data with {len(df)} records")
    return df

def process_data(data):
    """Process the raw data into a structured format."""
    processed_rows = []
    
    for test_case in data:
        brand = test_case['test_case']['brand']
        
        # Determine if it's a long or short prompt
        is_long = test_case['test_case'].get('type') == 'long'
        is_short = not is_long
        
        for result in test_case['results']:
            technique = result['variation']
            input_tokens = result['input_tokens']
            output_tokens = result['output_tokens']
            budget_compliance = result['search_budget']['budget_respected']
            
            processed_rows.append({
                'technique': technique,
                'long': 1 if is_long else 0,
                'short': 1 if is_short else 0,
                'brand_name': brand,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'budget_compliance': 1 if budget_compliance else 0,
                'prompt_type': 'long' if is_long else 'short'
            })
    
    return pd.DataFrame(processed_rows)

def calculate_optimization_percentages(df):
    """Calculate token optimization percentages relative to original prompt technique."""
    df = df.copy()
    
    # Initialize the optimization percentage column
    df['token_optimization_percentage'] = 0.0
    
    # For each brand and prompt type combination
    for brand in df['brand_name'].unique():
        for prompt_type in df['prompt_type'].unique():
            brand_type_data = df[(df['brand_name'] == brand) & (df['prompt_type'] == prompt_type)]
            
            # Get original prompt input tokens as baseline
            original_data = brand_type_data[brand_type_data['technique'] == 'Original Prompt']
            if not original_data.empty:
                original_input_tokens = original_data['input_tokens'].iloc[0]
                
                # Calculate percentage for each technique
                for idx, row in brand_type_data.iterrows():
                    if row['technique'] != 'Original Prompt':
                        current_input_tokens = row['input_tokens']
                        # Calculate percentage reduction (positive means reduction, negative means increase)
                        optimization_pct = ((original_input_tokens - current_input_tokens) / original_input_tokens) * 100
                        df.at[idx, 'token_optimization_percentage'] = optimization_pct
    
    return df

def create_plots(df):
    """Create focused plots for token reduction efficiency analysis."""
    # Set up professional plotting style
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Professional color palette
    colors = ['#1e40af', '#dc2626', '#059669']  # Blue, Red, Green
    
    # Create results directory if it doesn't exist
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Calculate total tokens
    df['total_tokens'] = df['input_tokens'] + df['output_tokens']
    
    # Create main efficiency comparison plot
    create_efficiency_overview(df, colors, results_dir)
    
    # Create separate plots for long vs short prompts
    create_long_prompts_analysis(df, colors, results_dir)
    create_short_prompts_analysis(df, colors, results_dir)

def create_efficiency_overview(df, colors, results_dir):
    """Create main efficiency comparison plot regardless of prompt type."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Token Reduction Efficiency Analysis (All Prompt Types)', fontsize=16, fontweight='bold', y=0.95)
    
    # Plot 1: Total tokens by technique
    ax1 = axes[0, 0]
    technique_stats = df.groupby('technique')['total_tokens'].agg(['mean', 'std']).reset_index()
    bars1 = ax1.bar(technique_stats['technique'], technique_stats['mean'], 
                   color=colors, edgecolor='white', linewidth=2, width=0.6)
    ax1.set_title('Average Total Tokens by Technique', fontsize=12, fontweight='bold', pad=15)
    ax1.set_xlabel('Technique', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Total Tokens', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45, labelsize=10)
    ax1.tick_params(axis='y', labelsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (bar, mean_val) in enumerate(zip(bars1, technique_stats['mean'])):
        ax1.text(bar.get_x() + bar.get_width()/2, mean_val + 5, f'{mean_val:.0f}', 
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Plot 2: Token optimization percentage
    ax2 = axes[0, 1]
    opt_data = df[df['technique'] != 'Original Prompt'].copy()
    if not opt_data.empty:
        opt_stats = opt_data.groupby('technique')['token_optimization_percentage'].agg(['mean', 'std']).reset_index()
        bars2 = ax2.bar(opt_stats['technique'], opt_stats['mean'], 
                       color=colors[1:], edgecolor='white', linewidth=2, width=0.6)
        ax2.set_title('Token Optimization Percentage', fontsize=12, fontweight='bold', pad=15)
        ax2.set_xlabel('Technique', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Optimization Percentage (%)', fontsize=12, fontweight='bold')
        ax2.tick_params(axis='x', rotation=45, labelsize=10)
        ax2.tick_params(axis='y', labelsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.7, linewidth=2)
        
        # Add value labels
        for i, (bar, mean_val) in enumerate(zip(bars2, opt_stats['mean'])):
            ax2.text(bar.get_x() + bar.get_width()/2, mean_val + 1, f'{mean_val:.1f}%', 
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Plot 3: Input tokens comparison
    ax3 = axes[1, 0]
    input_stats = df.groupby('technique')['input_tokens'].agg(['mean', 'std']).reset_index()
    bars3 = ax3.bar(input_stats['technique'], input_stats['mean'], 
                   color=colors, edgecolor='white', linewidth=2, width=0.6)
    ax3.set_title('Average Input Tokens by Technique', fontsize=12, fontweight='bold', pad=15)
    ax3.set_xlabel('Technique', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Input Tokens', fontsize=12, fontweight='bold')
    ax3.tick_params(axis='x', rotation=45, labelsize=10)
    ax3.tick_params(axis='y', labelsize=10)
    ax3.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (bar, mean_val) in enumerate(zip(bars3, input_stats['mean'])):
        ax3.text(bar.get_x() + bar.get_width()/2, mean_val + 2, f'{mean_val:.0f}', 
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Plot 4: Output tokens comparison
    ax4 = axes[1, 1]
    output_stats = df.groupby('technique')['output_tokens'].agg(['mean', 'std']).reset_index()
    bars4 = ax4.bar(output_stats['technique'], output_stats['mean'], 
                   color=colors, edgecolor='white', linewidth=2, width=0.6)
    ax4.set_title('Average Output Tokens by Technique', fontsize=12, fontweight='bold', pad=15)
    ax4.set_xlabel('Technique', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Output Tokens', fontsize=12, fontweight='bold')
    ax4.tick_params(axis='x', rotation=45, labelsize=10)
    ax4.tick_params(axis='y', labelsize=10)
    ax4.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (bar, mean_val) in enumerate(zip(bars4, output_stats['mean'])):
        ax4.text(bar.get_x() + bar.get_width()/2, mean_val + 5, f'{mean_val:.0f}', 
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Adjust layout and save
    plt.tight_layout()
    plt.subplots_adjust(top=0.90, hspace=0.3, wspace=0.3)
    plt.savefig(results_dir / 'token_efficiency_overview.png', dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    plt.close()

def create_long_prompts_analysis(df, colors, results_dir):
    """Create analysis for long prompts only."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Token Analysis: Long Prompts (All Brands)', fontsize=16, fontweight='bold', y=0.95)
    
    long_data = df[df['long'] == 1]
    
    if not long_data.empty:
        # Plot 1: Total tokens for long prompts
        ax1 = axes[0, 0]
        long_tokens = long_data.groupby('technique')['total_tokens'].agg(['mean', 'std']).reset_index()
        bars1 = ax1.bar(long_tokens['technique'], long_tokens['mean'], 
                       color=colors, edgecolor='white', linewidth=2, width=0.6)
        ax1.set_title('Total Tokens - Long Prompts', fontsize=12, fontweight='bold', pad=15)
        ax1.set_xlabel('Technique', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Total Tokens', fontsize=12, fontweight='bold')
        ax1.tick_params(axis='x', rotation=45, labelsize=10)
        ax1.tick_params(axis='y', labelsize=10)
        ax1.grid(True, alpha=0.3)
        
        for i, (bar, mean_val) in enumerate(zip(bars1, long_tokens['mean'])):
            ax1.text(bar.get_x() + bar.get_width()/2, mean_val + 10, f'{mean_val:.0f}', 
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Plot 2: Optimization percentage for long prompts
        ax2 = axes[0, 1]
        long_opt = long_data[long_data['technique'] != 'Original Prompt']
        if not long_opt.empty:
            long_opt_stats = long_opt.groupby('technique')['token_optimization_percentage'].agg(['mean', 'std']).reset_index()
            bars2 = ax2.bar(long_opt_stats['technique'], long_opt_stats['mean'], 
                           color=colors[1:], edgecolor='white', linewidth=2, width=0.6)
            ax2.set_title('Optimization % - Long Prompts', fontsize=12, fontweight='bold', pad=15)
            ax2.set_xlabel('Technique', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Optimization Percentage (%)', fontsize=12, fontweight='bold')
            ax2.tick_params(axis='x', rotation=45, labelsize=10)
            ax2.tick_params(axis='y', labelsize=10)
            ax2.grid(True, alpha=0.3)
            ax2.axhline(y=0, color='black', linestyle='--', alpha=0.7, linewidth=2)
            
            for i, (bar, mean_val) in enumerate(zip(bars2, long_opt_stats['mean'])):
                ax2.text(bar.get_x() + bar.get_width()/2, mean_val + 1, f'{mean_val:.1f}%', 
                        ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Plot 3: Input tokens for long prompts
        ax3 = axes[1, 0]
        long_input = long_data.groupby('technique')['input_tokens'].agg(['mean', 'std']).reset_index()
        bars3 = ax3.bar(long_input['technique'], long_input['mean'], 
                       color=colors, edgecolor='white', linewidth=2, width=0.6)
        ax3.set_title('Input Tokens - Long Prompts', fontsize=12, fontweight='bold', pad=15)
        ax3.set_xlabel('Technique', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Input Tokens', fontsize=12, fontweight='bold')
        ax3.tick_params(axis='x', rotation=45, labelsize=10)
        ax3.tick_params(axis='y', labelsize=10)
        ax3.grid(True, alpha=0.3)
        
        for i, (bar, mean_val) in enumerate(zip(bars3, long_input['mean'])):
            ax3.text(bar.get_x() + bar.get_width()/2, mean_val + 2, f'{mean_val:.0f}', 
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Plot 4: Output tokens for long prompts
        ax4 = axes[1, 1]
        long_output = long_data.groupby('technique')['output_tokens'].agg(['mean', 'std']).reset_index()
        bars4 = ax4.bar(long_output['technique'], long_output['mean'], 
                       color=colors, edgecolor='white', linewidth=2, width=0.6)
        ax4.set_title('Output Tokens - Long Prompts', fontsize=12, fontweight='bold', pad=15)
        ax4.set_xlabel('Technique', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Output Tokens', fontsize=12, fontweight='bold')
        ax4.tick_params(axis='x', rotation=45, labelsize=10)
        ax4.tick_params(axis='y', labelsize=10)
        ax4.grid(True, alpha=0.3)
        
        for i, (bar, mean_val) in enumerate(zip(bars4, long_output['mean'])):
            ax4.text(bar.get_x() + bar.get_width()/2, mean_val + 5, f'{mean_val:.0f}', 
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.90, hspace=0.3, wspace=0.3)
    plt.savefig(results_dir / 'token_analysis_long_prompts.png', dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    plt.close()

def create_short_prompts_analysis(df, colors, results_dir):
    """Create analysis for short prompts only."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Token Analysis: Short Prompts (All Brands)', fontsize=16, fontweight='bold', y=0.95)
    
    short_data = df[df['short'] == 1]
    
    if not short_data.empty:
        # Plot 1: Total tokens for short prompts
        ax1 = axes[0, 0]
        short_tokens = short_data.groupby('technique')['total_tokens'].agg(['mean', 'std']).reset_index()
        bars1 = ax1.bar(short_tokens['technique'], short_tokens['mean'], 
                       color=colors, edgecolor='white', linewidth=2, width=0.6)
        ax1.set_title('Total Tokens - Short Prompts', fontsize=12, fontweight='bold', pad=15)
        ax1.set_xlabel('Technique', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Total Tokens', fontsize=12, fontweight='bold')
        ax1.tick_params(axis='x', rotation=45, labelsize=10)
        ax1.tick_params(axis='y', labelsize=10)
        ax1.grid(True, alpha=0.3)
        
        for i, (bar, mean_val) in enumerate(zip(bars1, short_tokens['mean'])):
            ax1.text(bar.get_x() + bar.get_width()/2, mean_val + 5, f'{mean_val:.0f}', 
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Plot 2: Optimization percentage for short prompts
        ax2 = axes[0, 1]
        short_opt = short_data[short_data['technique'] != 'Original Prompt']
        if not short_opt.empty:
            short_opt_stats = short_opt.groupby('technique')['token_optimization_percentage'].agg(['mean', 'std']).reset_index()
            bars2 = ax2.bar(short_opt_stats['technique'], short_opt_stats['mean'], 
                           color=colors[1:], edgecolor='white', linewidth=2, width=0.6)
            ax2.set_title('Optimization % - Short Prompts', fontsize=12, fontweight='bold', pad=15)
            ax2.set_xlabel('Technique', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Optimization Percentage (%)', fontsize=12, fontweight='bold')
            ax2.tick_params(axis='x', rotation=45, labelsize=10)
            ax2.tick_params(axis='y', labelsize=10)
            ax2.grid(True, alpha=0.3)
            ax2.axhline(y=0, color='black', linestyle='--', alpha=0.7, linewidth=2)
            
            for i, (bar, mean_val) in enumerate(zip(bars2, short_opt_stats['mean'])):
                ax2.text(bar.get_x() + bar.get_width()/2, mean_val + 1, f'{mean_val:.1f}%', 
                        ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Plot 3: Input tokens for short prompts
        ax3 = axes[1, 0]
        short_input = short_data.groupby('technique')['input_tokens'].agg(['mean', 'std']).reset_index()
        bars3 = ax3.bar(short_input['technique'], short_input['mean'], 
                       color=colors, edgecolor='white', linewidth=2, width=0.6)
        ax3.set_title('Input Tokens - Short Prompts', fontsize=12, fontweight='bold', pad=15)
        ax3.set_xlabel('Technique', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Input Tokens', fontsize=12, fontweight='bold')
        ax3.tick_params(axis='x', rotation=45, labelsize=10)
        ax3.tick_params(axis='y', labelsize=10)
        ax3.grid(True, alpha=0.3)
        
        for i, (bar, mean_val) in enumerate(zip(bars3, short_input['mean'])):
            ax3.text(bar.get_x() + bar.get_width()/2, mean_val + 2, f'{mean_val:.0f}', 
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Plot 4: Output tokens for short prompts
        ax4 = axes[1, 1]
        short_output = short_data.groupby('technique')['output_tokens'].agg(['mean', 'std']).reset_index()
        bars4 = ax4.bar(short_output['technique'], short_output['mean'], 
                       color=colors, edgecolor='white', linewidth=2, width=0.6)
        ax4.set_title('Output Tokens - Short Prompts', fontsize=12, fontweight='bold', pad=15)
        ax4.set_xlabel('Technique', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Output Tokens', fontsize=12, fontweight='bold')
        ax4.tick_params(axis='x', rotation=45, labelsize=10)
        ax4.tick_params(axis='y', labelsize=10)
        ax4.grid(True, alpha=0.3)
        
        for i, (bar, mean_val) in enumerate(zip(bars4, short_output['mean'])):
            ax4.text(bar.get_x() + bar.get_width()/2, mean_val + 5, f'{mean_val:.0f}', 
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.90, hspace=0.3, wspace=0.3)
    plt.savefig(results_dir / 'token_analysis_short_prompts.png', dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    plt.close()

def save_csv(df, filename='token_analysis_results.csv'):
    """Save the processed data to CSV file."""
    # Select and reorder columns as requested
    columns = [
        'technique',
        'long',
        'short', 
        'brand_name',
        'input_tokens',
        'output_tokens',
        'budget_compliance',
        'token_optimization_percentage'
    ]
    
    df_export = df[columns].copy()
    
    # Round the optimization percentage to 2 decimal places
    df_export['token_optimization_percentage'] = df_export['token_optimization_percentage'].round(2)
    
    # Create results directory if it doesn't exist
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Save to CSV in results directory
    filepath = results_dir / filename
    df_export.to_csv(filepath, index=False)
    print(f"Data saved to {filepath}")
    
    return df_export

def print_summary_statistics(df):
    """Print summary statistics."""
    print("\n" + "="*60)
    print("TOKEN ANALYSIS SUMMARY")
    print("="*60)
    
    print("\n1. Token Usage by Technique:")
    technique_stats = df.groupby('technique')[['input_tokens', 'output_tokens']].agg(['mean', 'std'])
    print(technique_stats.round(2))
    
    print("\n2. Token Usage by Brand:")
    brand_stats = df.groupby('brand_name')[['input_tokens', 'output_tokens']].agg(['mean', 'std'])
    print(brand_stats.round(2))
    
    print("\n3. Token Usage by Prompt Length:")
    length_stats = df.groupby('prompt_type')[['input_tokens', 'output_tokens']].agg(['mean', 'std'])
    print(length_stats.round(2))
    
    print("\n4. Budget Compliance by Technique:")
    budget_stats = df.groupby('technique')['budget_compliance'].agg(['mean', 'count'])
    print(budget_stats.round(2))
    
    print("\n5. Token Optimization Percentages:")
    opt_stats = df[df['technique'] != 'Original Prompt'].groupby('technique')['token_optimization_percentage'].agg(['mean', 'std'])
    print(opt_stats.round(2))

def verify_csv_accuracy(df):
    """Verify that CSV data matches the data used for plotting."""
    csv_df = load_csv_data()
    
    if csv_df is None:
        print("Cannot verify - CSV file not found")
        return
    
    print("=== CSV VERIFICATION ===")
    
    # Compare total tokens
    df['total_tokens'] = df['input_tokens'] + df['output_tokens']
    csv_df['total_tokens'] = csv_df['input_tokens'] + csv_df['output_tokens']
    
    # Compare by technique
    df_stats = df.groupby('technique')['total_tokens'].agg(['mean', 'std']).round(2)
    csv_stats = csv_df.groupby('technique')['total_tokens'].agg(['mean', 'std']).round(2)
    
    print("Total tokens by technique comparison:")
    print("Data used for plotting:")
    print(df_stats)
    print("\nCSV data:")
    print(csv_stats)
    
    # Check if they match
    if df_stats.equals(csv_stats):
        print("✅ CSV data matches plotting data perfectly!")
    else:
        print("⚠️  Warning: CSV data differs from plotting data")
    
    print(f"Plotting data: {len(df)} records")
    print(f"CSV data: {len(csv_df)} records")

def main():
    """Main function to run the analysis."""
    try:
        print("Loading token optimization data...")
        data = load_data()
        
        print("Processing data...")
        df = process_data(data)
        
        print("Calculating optimization percentages...")
        df = calculate_optimization_percentages(df)
        
        print("Creating visualizations...")
        create_plots(df)
        
        print("Saving CSV file...")
        csv_df = save_csv(df)
        
        print("Generating summary statistics...")
        print_summary_statistics(df)
        
        print("\nVerifying CSV data matches plotting data...")
        verify_csv_accuracy(df)
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print("Files generated in evaluation/analysis/results/ directory:")
        print("- evaluation/analysis/results/token_efficiency_overview.png (Overall efficiency analysis)")
        print("- evaluation/analysis/results/token_analysis_long_prompts.png (Long prompts analysis)")
        print("- evaluation/analysis/results/token_analysis_short_prompts.png (Short prompts analysis)")
        print("- evaluation/analysis/results/token_analysis_results.csv (Data export)")
        print("\nData overview:")
        print(f"Total records: {len(df)}")
        print(f"Brands: {df['brand_name'].unique()}")
        print(f"Techniques: {df['technique'].unique()}")
        print(f"Prompt types: {df['prompt_type'].unique()}")
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()
