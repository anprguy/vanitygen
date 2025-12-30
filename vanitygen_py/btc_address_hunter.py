#!/usr/bin/env python3
"""
Bitcoin Address Hunter - GPU-Accelerated Address Generator with Balance Checking

This script generates Bitcoin addresses at high speed and checks them against
a list of known funded addresses to find matches.

Features:
- Uses coincurve (Bitcoin Core's libsecp256k1) for 100% correct addresses
- GPU-accelerated random number generation (optional)
- Multi-core CPU address generation
- Efficient bloom filter pre-filtering
- Supports loading addresses from CSV, text files, or Bitcoin Core chainstate

Usage:
    # Load addresses from CSV file and search
    python btc_address_hunter.py --addresses funded_addresses.csv --duration 3600
    
    # Load from Bitcoin Core chainstate
    python btc_address_hunter.py --chainstate ~/.bitcoin/chainstate --duration 3600
    
    # Benchmark mode (no address checking, just speed test)
    python btc_address_hunter.py --benchmark --duration 60

Author: Generated for high-performance Bitcoin address hunting
License: MIT
"""

import argparse
import time
import os
import sys
import signal
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vanitygen_py.hybrid_generator import (
    HybridGenerator, 
    COINCURVE_AVAILABLE,
    OPENCL_AVAILABLE,
    test_coincurve_correctness
)
from vanitygen_py.balance_checker import BalanceChecker


class BitcoinAddressHunter:
    """
    High-performance Bitcoin address hunter.
    
    Generates addresses using the hybrid GPU+coincurve approach and
    checks them against a database of funded addresses.
    """
    
    def __init__(
        self,
        batch_size: int = 50000,
        num_workers: int = None,
        use_gpu: bool = True,
        output_file: str = None,
        verbose: bool = True
    ):
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.use_gpu = use_gpu
        self.output_file = output_file or 'found_addresses.json'
        self.verbose = verbose
        
        self.generator = None
        self.balance_checker = None
        self.running = False
        self.found_addresses = []
        
        # Statistics
        self.start_time = None
        self.addresses_checked = 0
        
    def load_addresses_from_csv(self, filepath: str) -> bool:
        """Load funded addresses from a CSV file."""
        if self.verbose:
            print(f"[Hunter] Loading addresses from CSV: {filepath}")
        
        self.balance_checker = BalanceChecker()
        
        # Try different column names
        for addr_col, bal_col in [('address', 'balance'), ('Address', 'Balance'), ('addr', 'bal')]:
            if self.balance_checker.load_from_csv(filepath, addr_col, bal_col):
                if self.verbose:
                    print(f"[Hunter] Loaded {len(self.balance_checker.address_balances)} addresses")
                return True
        
        print(f"[Hunter] ERROR: Failed to load CSV file")
        return False
    
    def load_addresses_from_file(self, filepath: str) -> bool:
        """Load funded addresses from a text file (one address per line)."""
        if self.verbose:
            print(f"[Hunter] Loading addresses from file: {filepath}")
        
        self.balance_checker = BalanceChecker()
        if self.balance_checker.load_addresses(filepath):
            if self.verbose:
                print(f"[Hunter] Loaded {len(self.balance_checker.funded_addresses)} addresses")
            return True
        
        print(f"[Hunter] ERROR: Failed to load address file")
        return False
    
    def load_addresses_from_chainstate(self, path: str = None) -> bool:
        """Load funded addresses from Bitcoin Core chainstate."""
        if self.verbose:
            print(f"[Hunter] Loading addresses from Bitcoin Core chainstate...")
        
        self.balance_checker = BalanceChecker()
        if self.balance_checker.load_from_bitcoin_core(path):
            count = len(self.balance_checker.address_balances)
            if self.verbose:
                print(f"[Hunter] Loaded {count} addresses from chainstate")
            return True
        
        print(f"[Hunter] ERROR: Failed to load from chainstate")
        return False
    
    def _on_match_found(self, match: dict):
        """Handle a found match."""
        self.found_addresses.append({
            'timestamp': datetime.now().isoformat(),
            **match
        })
        
        # Save to file immediately
        self._save_results()
        
        # Print match
        print("\n" + "=" * 60)
        print("🎯 MATCH FOUND!")
        print("=" * 60)
        print(f"Address: {match['address']}")
        print(f"WIF:     {match['wif']}")
        print(f"PubKey:  {match['pubkey']}")
        print(f"Type:    {match.get('match_type', 'unknown')}")
        print("=" * 60 + "\n")
    
    def _save_results(self):
        """Save found addresses to file."""
        try:
            with open(self.output_file, 'w') as f:
                json.dump({
                    'found_addresses': self.found_addresses,
                    'stats': {
                        'total_checked': self.addresses_checked,
                        'total_found': len(self.found_addresses),
                        'runtime_seconds': time.time() - self.start_time if self.start_time else 0
                    }
                }, f, indent=2)
        except Exception as e:
            print(f"[Hunter] Error saving results: {e}")
    
    def run(self, duration: float = None, prefix: str = ''):
        """
        Run the address hunter.
        
        Args:
            duration: How long to run in seconds (None = forever)
            prefix: Optional vanity prefix to search for
        """
        if not COINCURVE_AVAILABLE:
            print("[Hunter] ERROR: coincurve not installed!")
            print("[Hunter] Install with: pip install coincurve")
            return
        
        # Verify correctness first
        if self.verbose:
            print("\n[Hunter] Verifying cryptographic correctness...")
            if not test_coincurve_correctness():
                print("[Hunter] ERROR: Correctness test failed!")
                return
        
        # Initialize generator
        if self.verbose:
            print("\n[Hunter] Initializing generator...")
        
        self.generator = HybridGenerator(
            prefix=prefix,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            use_gpu=self.use_gpu
        )
        
        # Initialize GPU
        self.generator.init_gpu()
        
        # Set balance checker
        if self.balance_checker:
            self.generator.set_balance_checker(self.balance_checker)
        
        # Setup signal handler
        def signal_handler(sig, frame):
            print("\n[Hunter] Stopping...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start generator
        self.running = True
        self.start_time = time.time()
        self.generator.start()
        
        if self.verbose:
            print("\n[Hunter] Running... Press Ctrl+C to stop\n")
        
        last_status_time = time.time()
        
        try:
            while self.running:
                # Check for duration limit
                if duration and (time.time() - self.start_time) >= duration:
                    print(f"\n[Hunter] Duration limit ({duration}s) reached")
                    break
                
                # Check for results
                result = self.generator.get_result(timeout=0.1)
                if result:
                    self._on_match_found(result)
                
                # Update stats
                stats = self.generator.get_stats()
                self.addresses_checked = stats['total_generated']
                
                # Print status every 5 seconds
                if time.time() - last_status_time >= 5.0:
                    elapsed = time.time() - self.start_time
                    rate = self.addresses_checked / elapsed if elapsed > 0 else 0
                    
                    print(f"[Hunter] Checked: {self.addresses_checked:,} | "
                          f"Rate: {rate:,.0f}/sec | "
                          f"Found: {len(self.found_addresses)} | "
                          f"Time: {elapsed:.0f}s")
                    
                    last_status_time = time.time()
                    
        finally:
            self.generator.stop()
            self._save_results()
            
            # Print final stats
            elapsed = time.time() - self.start_time
            rate = self.addresses_checked / elapsed if elapsed > 0 else 0
            
            print("\n" + "=" * 60)
            print("FINAL RESULTS")
            print("=" * 60)
            print(f"Total addresses checked: {self.addresses_checked:,}")
            print(f"Runtime: {elapsed:.2f} seconds")
            print(f"Average rate: {rate:,.0f} addresses/second")
            print(f"Matches found: {len(self.found_addresses)}")
            print(f"Results saved to: {self.output_file}")
            print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Bitcoin Address Hunter - GPU-accelerated address generator with balance checking'
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('--csv', type=str, help='CSV file with funded addresses')
    input_group.add_argument('--addresses', type=str, help='Text file with addresses (one per line)')
    input_group.add_argument('--chainstate', type=str, nargs='?', const='auto',
                            help='Bitcoin Core chainstate path (or "auto" for auto-detect)')
    input_group.add_argument('--benchmark', action='store_true', help='Benchmark mode (no address checking)')
    
    # Performance options
    parser.add_argument('--batch-size', type=int, default=50000,
                       help='Batch size for key generation (default: 50000)')
    parser.add_argument('--workers', type=int, default=None,
                       help='Number of CPU workers (default: auto)')
    parser.add_argument('--no-gpu', action='store_true',
                       help='Disable GPU acceleration')
    
    # Search options
    parser.add_argument('--prefix', type=str, default='',
                       help='Vanity prefix to search for (e.g., "1BTC")')
    parser.add_argument('--duration', type=float, default=None,
                       help='How long to run in seconds (default: forever)')
    
    # Output options
    parser.add_argument('--output', type=str, default='found_addresses.json',
                       help='Output file for found addresses (default: found_addresses.json)')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    # Create hunter
    hunter = BitcoinAddressHunter(
        batch_size=args.batch_size,
        num_workers=args.workers,
        use_gpu=not args.no_gpu,
        output_file=args.output,
        verbose=not args.quiet
    )
    
    # Load addresses
    if args.csv:
        if not hunter.load_addresses_from_csv(args.csv):
            sys.exit(1)
    elif args.addresses:
        if not hunter.load_addresses_from_file(args.addresses):
            sys.exit(1)
    elif args.chainstate:
        path = None if args.chainstate == 'auto' else args.chainstate
        if not hunter.load_addresses_from_chainstate(path):
            sys.exit(1)
    elif not args.benchmark:
        print("No address source specified. Use --csv, --addresses, --chainstate, or --benchmark")
        print("Run with --help for usage information")
        sys.exit(1)
    
    # Run hunter
    hunter.run(duration=args.duration, prefix=args.prefix)


if __name__ == '__main__':
    main()
