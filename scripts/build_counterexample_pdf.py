# Copyright (c) 2026 Christian Reitwiessner. Apache-2.0.
# Authors: Christian Reitwiessner.
"""Build the counterexample PDF from its authoritative LaTeX source using Tectonic."""
from pathlib import Path
import argparse
import subprocess

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tectonic', default='tectonic', help='Tectonic executable path')
    args = parser.parse_args()
    subprocess.run([args.tectonic, str(ROOT / 'stoc/writeups/submission-1234-counterexample.tex')],
                   check=True)
