# stats.py
# Simple script to display Wordle stats from file.
#
# Author: Matthew Eicholtz

import argparse
from colorama import init, Fore, Style
import os
import pdb

ROOT = os.path.dirname(os.path.realpath(__file__))
init(autoreset=True) # required for colored text using colorama library

parser = argparse.ArgumentParser(description="Check your Wordle stats")
parser.add_argument('-f', metavar='filename', type=str, 
    help='name of stats file to load, defaults to data/stats.txt', 
    default=os.path.join('data', 'stats.txt'))

def load(filename):
    init(autoreset=True) # required for colored text using colorama

    # Read data from stats file
    try:
        with open(filename, "r") as f:
            data = f.read().splitlines() # make list of strings, one per stat line
    except IOError:
        print(Fore.RED + f'ERROR: {filename} does not exist. Check files in directory.')
        Style.RESET_ALL
        return 0

    # Display stats
    print("\nSTATISTICS")
    print("=" * 10)
    for line in data:
        if len(line) == 0: # take care of blank lines (often happens at end of file)
            continue
        stat, value = line.split('=') # expected format is "stat=value"
        print(f'{stat.title()}: {value}')
    guesses = [int(i) for i in value.split(',')]
    if sum(guesses) != 0: # the player has won at least one game
        mean_guess = sum([(i + 1) * x for i, x in enumerate(guesses)]) / sum(guesses)
        print(f"Average Number of Guesses to Solve: {mean_guess:0.2f}")

    # pdb.set_trace()

if __name__ == "__main__":
    args = parser.parse_args()
    load(filename=args.f)
