"""
Inter-bank Contagion Mechanism for Financial Crisis ABM.

This module implements counterparty exposure networks and contagion propagation
to simulate systemic risk in the financial system. When a bank fails, losses
propagate to its counterparties based on their exposure levels.

Key concepts:
- Counterparty exposure: Direct lending/borrowing relationships between banks
- Loss propagation: Failed bank's counterparties absorb losses proportional to exposure
- Cascade effects: Secondary failures can trigger further contagion rounds
- Systemic risk: Aggregate fragility of the interconnected banking system

References:
- Allen & Gale (2000): Financial Contagion
- Eisenberg & Noe (2001): Systemic Risk in Financial Systems
- Acemoglu et al. (2015): Systemic Risk and Stability in Financial Networks
"""

import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from abm.agents import BankAgent

logger = logging.getLogger(__name__)


class ContagionNetwork:
    """
    Manages inter-bank counterparty exposures and contagion propagation.

    The network models bilateral exposures between banks where each bank
    has lending (asset) and borrowing (liability) relationships with others.
    When a bank fails, its creditors (those who lent to it) suffer losses
    proportional to their exposure.

    Attributes:
        banks: List of BankAgent instances in the network.
        n_banks: Number of banks in the network.
        exposure_matrix: NxN matrix where entry [i,j] represents bank i's
                        exposure (lending) to bank j as a fraction of i's capital.
        contagion_factor: Multiplier for loss severity (0-1, default 0.5).
        recovery_rate: Fraction of exposure recovered when counterparty fails (0-1).
        cascade_history: List tracking cascade rounds and affected banks.
    """

    def __init__(
        self,
        banks: List['BankAgent'],
        exposure_matrix: Optional[np.ndarray] = None,
        contagion_factor: float = 0.5,
        recovery_rate: float = 0.4,
        network_type: str = "random"
    ):
        """
        Initialize the contagion network.

        Args:
            banks: List of BankAgent instances.
            exposure_matrix: Optional pre-defined NxN exposure matrix.
                           If None, generates based on network_type.
            contagion_factor: Severity multiplier for contagion losses (0-1).
                            Higher values mean more severe propagation.
            recovery_rate: Fraction of exposure recovered in bankruptcy (0-1).
                         Lower values mean higher losses for creditors.
            network_type: Type of network topology if generating matrix.
                        Options: "random", "core_periphery", "ring", "complete"
        """
        self.banks = banks
        self.n_banks = len(banks)
        self.contagion_factor = contagion_factor
        self.recovery_rate = recovery_rate
        self.cascade_history: List[Dict[str, Any]] = []

        # Build name-to-index mapping
        self.bank_index: Dict[str, int] = {
            bank.name: i for i, bank in enumerate(banks)
        }

        # Initialize exposure matrix
        if exposure_matrix is not None:
            if exposure_matrix.shape != (self.n_banks, self.n_banks):
                raise ValueError(
                    f"Exposure matrix shape {exposure_matrix.shape} doesn't match "
                    f"number of banks ({self.n_banks})"
                )
            self.exposure_matrix = exposure_matrix.copy()
        else:
            self.exposure_matrix = self._generate_exposure_matrix(network_type)

        logger.info(
            f"ContagionNetwork initialized: {self.n_banks} banks, "
            f"contagion_factor={contagion_factor}, recovery_rate={recovery_rate}, "
            f"network_type={network_type}"
        )

    def _generate_exposure_matrix(self, network_type: str) -> np.ndarray:
        """
        Generate an exposure matrix based on the specified network topology.

        Args:
            network_type: Type of network structure to generate.

        Returns:
            NxN numpy array of exposure fractions.
        """
        n = self.n_banks
        matrix = np.zeros((n, n))

        if network_type == "random":
            # Random sparse network with varying exposure levels
            # Each bank has exposure to 30-60% of other banks
            np.random.seed(42)  # Reproducibility
            for i in range(n):
                # Number of counterparties (30-60% of other banks)
                n_counterparties = np.random.randint(
                    max(1, int(0.3 * (n - 1))),
                    min(n - 1, int(0.6 * (n - 1))) + 1
                )
                # Select random counterparties
                others = [j for j in range(n) if j != i]
                counterparties = np.random.choice(others, n_counterparties, replace=False)
                # Assign random exposure levels (5-20% of capital per counterparty)
                for j in counterparties:
                    matrix[i, j] = np.random.uniform(0.05, 0.20)

        elif network_type == "core_periphery":
            # Core-periphery structure: few highly connected core banks,
            # many periphery banks connected mainly to core
            n_core = max(2, n // 3)
            core_banks = list(range(n_core))
            periphery_banks = list(range(n_core, n))

            # Core banks fully connected to each other (high exposure)
            for i in core_banks:
                for j in core_banks:
                    if i != j:
                        matrix[i, j] = np.random.uniform(0.15, 0.25)

            # Periphery banks connected to core (moderate exposure)
            for i in periphery_banks:
                for j in core_banks:
                    matrix[i, j] = np.random.uniform(0.08, 0.15)
                    matrix[j, i] = np.random.uniform(0.03, 0.08)

            # Sparse connections among periphery
            for i in periphery_banks:
                # Connect to 1-2 other periphery banks
                others = [p for p in periphery_banks if p != i]
                if others:
                    n_connections = min(2, len(others))
                    counterparties = np.random.choice(others, n_connections, replace=False)
                    for j in counterparties:
                        matrix[i, j] = np.random.uniform(0.03, 0.08)

        elif network_type == "ring":
            # Ring network: each bank connected to neighbors
            for i in range(n):
                next_bank = (i + 1) % n
                prev_bank = (i - 1) % n
                matrix[i, next_bank] = np.random.uniform(0.10, 0.20)
                matrix[i, prev_bank] = np.random.uniform(0.10, 0.20)

        elif network_type == "complete":
            # Complete network: all banks connected (distributed risk)
            exposure_per_bank = 0.40 / (n - 1)  # Total exposure capped at 40%
            for i in range(n):
                for j in range(n):
                    if i != j:
                        matrix[i, j] = exposure_per_bank * np.random.uniform(0.8, 1.2)

        else:
            raise ValueError(f"Unknown network type: {network_type}")

        return matrix

    def get_exposure(self, bank_name: str, counterparty_name: str) -> float:
        """
        Get bank's exposure to a specific counterparty.

        Args:
            bank_name: Name of the bank with exposure.
            counterparty_name: Name of the counterparty.

        Returns:
            Exposure as fraction of bank's capital.
        """
        i = self.bank_index.get(bank_name)
        j = self.bank_index.get(counterparty_name)
        if i is None or j is None:
            return 0.0
        return self.exposure_matrix[i, j]

    def get_total_exposure(self, bank_name: str) -> float:
        """
        Get bank's total exposure to all counterparties.

        Args:
            bank_name: Name of the bank.

        Returns:
            Total exposure as fraction of capital.
        """
        i = self.bank_index.get(bank_name)
        if i is None:
            return 0.0
        return np.sum(self.exposure_matrix[i, :])

    def get_counterparty_risk(self, bank_name: str) -> float:
        """
        Get how much other banks are exposed to this bank.

        This measures the systemic importance of the bank - how much
        damage its failure would cause to the system.

        Args:
            bank_name: Name of the bank.

        Returns:
            Sum of all other banks' exposures to this bank.
        """
        j = self.bank_index.get(bank_name)
        if j is None:
            return 0.0
        return np.sum(self.exposure_matrix[:, j])

    def propagate_failure(self, failed_bank: 'BankAgent') -> List[str]:
        """
        Propagate losses from a failed bank to its counterparties.

        When a bank fails, its creditors lose money proportional to their
        exposure minus any recovery. This can trigger cascade failures if
        losses push other banks below the failure threshold.

        Args:
            failed_bank: The BankAgent that has failed.

        Returns:
            List of bank names affected (suffered losses) by this failure.
        """
        failed_name = failed_bank.name
        failed_idx = self.bank_index.get(failed_name)

        if failed_idx is None:
            logger.warning(f"Bank {failed_name} not found in contagion network")
            return []

        affected_banks = []
        losses_applied = {}

        # Find all banks with exposure to the failed bank
        for i, bank in enumerate(self.banks):
            if i == failed_idx or bank.failed:
                continue

            exposure = self.exposure_matrix[i, failed_idx]
            if exposure > 0:
                # Calculate loss: exposure * (1 - recovery_rate) * contagion_factor * capital
                loss_fraction = exposure * (1 - self.recovery_rate) * self.contagion_factor
                capital_loss = loss_fraction * bank.capital

                # Apply loss to bank
                bank.capital -= capital_loss

                # Also reduce liquidity proportionally (fire sale effect)
                liquidity_loss = loss_fraction * 0.5  # Half the loss impacts liquidity
                bank.liquidity = max(0, bank.liquidity - liquidity_loss)

                affected_banks.append(bank.name)
                losses_applied[bank.name] = {
                    "capital_loss": capital_loss,
                    "liquidity_loss": liquidity_loss,
                    "exposure": exposure
                }

                logger.info(
                    f"Contagion: {bank.name} lost {capital_loss:.2f}B capital "
                    f"(exposure={exposure:.1%} to {failed_name})"
                )

        # Record this propagation round
        self.cascade_history.append({
            "trigger": failed_name,
            "affected": affected_banks,
            "losses": losses_applied,
            "round": len(self.cascade_history) + 1
        })

        return affected_banks

    def run_cascade(self, initial_failure: 'BankAgent') -> Dict[str, Any]:
        """
        Run full cascade propagation from an initial failure.

        This method propagates losses iteratively until no more banks fail
        or all banks have failed. Each round:
        1. Propagate losses from newly failed banks
        2. Check for secondary failures
        3. Repeat until stable

        Args:
            initial_failure: The bank that triggered the cascade.

        Returns:
            Dictionary with cascade statistics:
            - total_rounds: Number of propagation rounds
            - total_failures: Total banks failed (including initial)
            - cascade_failures: Banks that failed due to contagion
            - affected_banks: All banks that suffered losses
            - history: Detailed round-by-round history
        """
        cascade_failures = []
        all_affected = set()
        current_failures = [initial_failure]
        round_num = 0
        max_rounds = self.n_banks  # Safety limit

        logger.info(f"Starting cascade from {initial_failure.name}")

        while current_failures and round_num < max_rounds:
            round_num += 1
            new_failures = []

            # Propagate losses from all currently failing banks
            for failed_bank in current_failures:
                affected = self.propagate_failure(failed_bank)
                all_affected.update(affected)

            # Check for secondary failures
            for bank in self.banks:
                if bank.failed:
                    continue

                # Get effective liquidity considering market conditions
                model = getattr(bank, 'model', None)
                if model:
                    market_ctx = getattr(model, 'market_context', {})
                    liquidity_factor = market_ctx.get('liquidity', 1.0)
                else:
                    liquidity_factor = 1.0

                effective_liquidity = bank.liquidity * liquidity_factor
                failure_threshold = bank.config.get('failure_threshold', 0.03)

                # Check failure conditions
                if effective_liquidity < failure_threshold or bank.capital < 0:
                    bank.fail()
                    new_failures.append(bank)
                    cascade_failures.append(bank.name)
                    logger.warning(
                        f"CASCADE FAILURE: {bank.name} failed in round {round_num} "
                        f"(capital={bank.capital:.1f}B, liquidity={effective_liquidity:.3f})"
                    )

            current_failures = new_failures

        result = {
            "total_rounds": round_num,
            "total_failures": 1 + len(cascade_failures),  # Initial + cascade
            "cascade_failures": cascade_failures,
            "affected_banks": list(all_affected),
            "history": self.cascade_history.copy()
        }

        logger.info(
            f"Cascade complete: {result['total_rounds']} rounds, "
            f"{result['total_failures']} total failures "
            f"({len(cascade_failures)} from contagion)"
        )

        return result

    def calculate_systemic_risk(self) -> float:
        """
        Calculate overall systemic risk of the network.

        Systemic risk is measured as a combination of:
        1. Network density: How interconnected the banks are
        2. Concentration: Whether exposures are concentrated on few banks
        3. Average exposure: Overall exposure levels

        Returns:
            Systemic risk score between 0 (low) and 1 (high).
        """
        if self.n_banks == 0:
            return 0.0

        # 1. Network density: fraction of possible connections that exist
        n_possible = self.n_banks * (self.n_banks - 1)
        n_actual = np.count_nonzero(self.exposure_matrix)
        density = n_actual / n_possible if n_possible > 0 else 0

        # 2. Concentration: Herfindahl index of counterparty risk
        # High concentration means a few banks are very interconnected
        column_sums = np.sum(self.exposure_matrix, axis=0)
        total_exposure = np.sum(column_sums)
        if total_exposure > 0:
            shares = column_sums / total_exposure
            herfindahl = np.sum(shares ** 2)
            # Normalize: min is 1/n (equal), max is 1 (single bank)
            concentration = (herfindahl - 1/self.n_banks) / (1 - 1/self.n_banks) if self.n_banks > 1 else 0
        else:
            concentration = 0

        # 3. Average exposure per bank
        avg_exposure = np.mean(np.sum(self.exposure_matrix, axis=1))
        exposure_score = min(avg_exposure / 0.5, 1.0)  # Cap at 50% average

        # 4. Weighted combination
        # Density and exposure increase risk, concentration amplifies it
        base_risk = 0.4 * density + 0.4 * exposure_score
        amplified_risk = base_risk * (1 + 0.5 * concentration)

        systemic_risk = min(amplified_risk, 1.0)

        logger.debug(
            f"Systemic risk: {systemic_risk:.3f} "
            f"(density={density:.3f}, concentration={concentration:.3f}, "
            f"avg_exposure={avg_exposure:.3f})"
        )

        return systemic_risk

    def get_most_systemically_important(self, top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Identify the most systemically important banks.

        A bank is systemically important if its failure would cause
        significant losses to the system (high counterparty risk).

        Args:
            top_n: Number of top banks to return.

        Returns:
            List of (bank_name, importance_score) tuples, sorted by importance.
        """
        importance_scores = []

        for bank in self.banks:
            if bank.failed:
                continue

            # Counterparty risk: how much others are exposed to this bank
            counterparty_risk = self.get_counterparty_risk(bank.name)

            # Own exposure: how much this bank is exposed (vulnerability)
            own_exposure = self.get_total_exposure(bank.name)

            # Importance = high counterparty risk, weighted by capital
            importance = counterparty_risk * (bank.capital / 100.0)

            importance_scores.append((bank.name, importance))

        # Sort by importance (descending)
        importance_scores.sort(key=lambda x: x[1], reverse=True)

        return importance_scores[:top_n]

    def get_network_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive network statistics.

        Returns:
            Dictionary with network metrics.
        """
        alive_banks = [b for b in self.banks if not b.failed]
        failed_banks = [b for b in self.banks if b.failed]

        return {
            "n_banks": self.n_banks,
            "n_alive": len(alive_banks),
            "n_failed": len(failed_banks),
            "systemic_risk": self.calculate_systemic_risk(),
            "network_density": np.count_nonzero(self.exposure_matrix) / (self.n_banks * (self.n_banks - 1)) if self.n_banks > 1 else 0,
            "avg_exposure": float(np.mean(np.sum(self.exposure_matrix, axis=1))),
            "max_exposure": float(np.max(np.sum(self.exposure_matrix, axis=1))),
            "contagion_factor": self.contagion_factor,
            "recovery_rate": self.recovery_rate,
            "cascade_rounds": len(self.cascade_history),
            "most_important": self.get_most_systemically_important(3)
        }

    def reset_cascade_history(self):
        """Clear the cascade history for a new simulation."""
        self.cascade_history = []


def create_exposure_matrix_from_data(
    banks: List['BankAgent'],
    exposure_data: Dict[str, Dict[str, float]]
) -> np.ndarray:
    """
    Create an exposure matrix from explicit exposure data.

    Args:
        banks: List of BankAgent instances.
        exposure_data: Dictionary mapping bank_name -> {counterparty: exposure_fraction}.

    Returns:
        NxN numpy array of exposure fractions.
    """
    n = len(banks)
    bank_index = {bank.name: i for i, bank in enumerate(banks)}
    matrix = np.zeros((n, n))

    for bank_name, exposures in exposure_data.items():
        i = bank_index.get(bank_name)
        if i is None:
            continue
        for counterparty, exposure in exposures.items():
            j = bank_index.get(counterparty)
            if j is not None:
                matrix[i, j] = exposure

    return matrix
