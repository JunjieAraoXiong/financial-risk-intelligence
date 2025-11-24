import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import re

def analyze_results():
    # Find all result files
    files = glob.glob("results/experiment_lf_*.csv")
    if not files:
        print("No result files found in results/")
        return

    print(f"Found {len(files)} result files.")
    
    # Aggregate data
    summary_data = []
    
    for f in files:
        # Extract liquidity factor from filename
        match = re.search(r'lf_(\d+\.\d+)', f)
        if not match:
            continue
            
        lf = float(match.group(1))
        df = pd.read_csv(f)
        
        # Get final state (last week)
        final = df.iloc[-1]
        
        summary_data.append({
            'Liquidity_Factor': lf,
            'Insiders_Survival': (final['Insiders_Alive'] / 5) * 100, # Assuming 5 agents per group
            'Noise_Survival': (final['Noise_Alive'] / 5) * 100,
            'Insider_Defensive_Rate': final['Insider_Defensive'] / (final['Insider_Defensive'] + final['Insider_Maintain'] + 1e-6),
            'Noise_Defensive_Rate': final['Noise_Defensive'] / (final['Noise_Defensive'] + final['Noise_Maintain'] + 1e-6)
        })
    
    # Create DataFrame and sort by stress (High LF = Low Stress)
    summary_df = pd.DataFrame(summary_data).sort_values('Liquidity_Factor', ascending=False)
    
    print("\n--- Analysis Summary ---")
    print(summary_df)
    
    # Plotting
    plt.figure(figsize=(12, 5))
    
    # Plot 1: Survival Rate
    plt.subplot(1, 2, 1)
    plt.plot(summary_df['Liquidity_Factor'], summary_df['Insiders_Survival'], 'b-o', label='Insiders (RAG)')
    plt.plot(summary_df['Liquidity_Factor'], summary_df['Noise_Survival'], 'r--x', label='Noise Traders')
    plt.title('Survival Rate vs. Liquidity Stress')
    plt.xlabel('Liquidity Factor (Lower = More Stress)')
    plt.ylabel('Survival Rate (%)')
    plt.gca().invert_xaxis() # Stress increases to the right
    plt.legend()
    plt.grid(True)
    
    # Plot 2: Defensive Actions
    plt.subplot(1, 2, 2)
    plt.plot(summary_df['Liquidity_Factor'], summary_df['Insider_Defensive_Rate'], 'b-o', label='Insiders (RAG)')
    plt.plot(summary_df['Liquidity_Factor'], summary_df['Noise_Defensive_Rate'], 'r--x', label='Noise Traders')
    plt.title('Defensive Action Rate vs. Liquidity Stress')
    plt.xlabel('Liquidity Factor')
    plt.ylabel('Defensive Action Rate')
    plt.gca().invert_xaxis()
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    output_path = 'results/analysis_summary.png'
    plt.savefig(output_path)
    print(f"\nAnalysis plot saved to {output_path}")

if __name__ == "__main__":
    analyze_results()
