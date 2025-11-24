from abm.model import FinancialCrisisModel
import matplotlib.pyplot as plt
import pandas as pd
import logging
import argparse

# Configure logging to show agent decisions
logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_experiment(liquidity_factor=0.30, weeks=12, shock_week=5, k_chunks=5, crisis_volatility=0.80,
                   start_year=2008, initial_capital=100.0, initial_liquidity=0.30, failure_threshold=0.03):
    print("Starting Information Asymmetry Experiment...")
    print(f"Liquidity Factor: {liquidity_factor}")
    print(f"Crisis Volatility: {crisis_volatility:.0%}")
    print(f"Simulation Weeks: {weeks}")
    print(f"Shock Week: {shock_week}")
    print(f"RAG Chunks: {k_chunks}")
    print("Group A (Agents 0-4): Insiders (RAG=True)")
    print("Group B (Agents 5-9): Noise Traders (RAG=False)")

    # Initialize model with 10 banks
    model = FinancialCrisisModel(
        n_banks=10,
        use_slm=True,
        liquidity_factor=liquidity_factor,
        shock_week=shock_week,
        k_chunks=k_chunks,
        crisis_volatility=crisis_volatility,
        start_year=start_year,
        initial_capital=initial_capital,
        initial_liquidity=initial_liquidity,
        failure_threshold=failure_threshold
    )

    # Track survival
    history = []

    # Run simulation
    for step in range(weeks):
        print(f"\n--- Week {step + 1} ---")
        model.step()

        # Collect stats
        alive_insiders = sum(1 for a in model.agents if a.use_rag and not a.failed)
        alive_noise = sum(1 for a in model.agents if not a.use_rag and not a.failed)

        # Track decisions by group
        insider_defensive = sum(1 for a in model.agents if a.use_rag and not a.failed and a.last_action == 'DEFENSIVE')
        insider_maintain = sum(1 for a in model.agents if a.use_rag and not a.failed and a.last_action == 'MAINTAIN')
        noise_defensive = sum(1 for a in model.agents if not a.use_rag and not a.failed and a.last_action == 'DEFENSIVE')
        noise_maintain = sum(1 for a in model.agents if not a.use_rag and not a.failed and a.last_action == 'MAINTAIN')

        # Calculate systemic risk (% of banks failed)
        total_banks = len(list(model.agents))
        failed_banks = sum(1 for a in model.agents if a.failed)
        systemic_risk = failed_banks / total_banks if total_banks > 0 else 0.0

        # Log shock event (actual shock happens in model.step())
        if step == shock_week - 1:  # shock_week is 1-indexed
            logging.info("\n!!! LEHMAN SHOCK TRIGGERED !!!")
            logging.info("Insiders should be querying RAG for crisis context...")

        # Log decisions this week
        logging.info(f"Decisions - Insiders: DEF={insider_defensive} MAIN={insider_maintain} | Noise: DEF={noise_defensive} MAIN={noise_maintain}")

        history.append({
            'Week': step + 1,
            'Insiders_Alive': alive_insiders,
            'Noise_Alive': alive_noise,
            'Insider_Defensive': insider_defensive,
            'Insider_Maintain': insider_maintain,
            'Noise_Defensive': noise_defensive,
            'Noise_Maintain': noise_maintain,
            'Systemic_Risk': systemic_risk
        })
        
        if alive_insiders == 0 and alive_noise == 0:
            print("All banks failed!")
            break

    # Results
    df = pd.DataFrame(history)
    print("\n--- Experiment Results ---")
    print(df.tail())

    # Save results with liquidity factor in filename
    output_file = f"results/experiment_lf_{liquidity_factor:.2f}.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Information Asymmetry Experiment')
    parser.add_argument('--liquidity-factor', type=float, default=0.30,
                        help='Liquidity factor during crisis (0.10-0.50, default: 0.30)')
    parser.add_argument('--weeks', type=int, default=12,
                        help='Number of simulation weeks (default: 12)')
    parser.add_argument('--shock-week', type=int, default=5,
                        help='Week when Lehman shock occurs (default: 5)')
    parser.add_argument('--k-chunks', type=int, default=5,
                        help='Number of RAG chunks to retrieve (default: 5)')
    parser.add_argument('--crisis-volatility', type=float, default=0.80,
                        help='Market volatility during crisis (0.0-1.0, default: 0.80)')
    parser.add_argument('--start-year', type=int, default=2008,
                        help='Start year of simulation (default: 2008)')
    parser.add_argument('--initial-capital', type=float, default=100.0,
                        help='Initial capital in billions (default: 100.0)')
    parser.add_argument('--initial-liquidity', type=float, default=0.30,
                        help='Initial liquidity ratio (default: 0.30)')
    parser.add_argument('--failure-threshold', type=float, default=0.03,
                        help='Liquidity threshold for bank failure (default: 0.03)')
    args = parser.parse_args()

    run_experiment(
        liquidity_factor=args.liquidity_factor,
        weeks=args.weeks,
        shock_week=args.shock_week,
        k_chunks=args.k_chunks,
        crisis_volatility=args.crisis_volatility,
        start_year=args.start_year,
        initial_capital=args.initial_capital,
        initial_liquidity=args.initial_liquidity,
        failure_threshold=args.failure_threshold
    )
