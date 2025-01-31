# utils.py
# Python library of utility functions related to Wordle game.
#
# Author: Matthew Eicholtz

import base64
from colorama import init, Fore, Style
from datetime import datetime
import importlib
import os
import pdb
from pynput import keyboard
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.realpath(__file__))
init(autoreset=True) # required for colored text using colorama library

def get_feedback(guess, secret):
    """Check whether the guess matches the secret word, providing feedback about each letter.
    
    Parameters
    ----------
    guess : str
        Word that the player guesses.
    secret : str
        Word that the player is trying to guess.

    Returns
    -------
    feedback: list
        A list of integers, one per letter in the guess, to indicate if the letter is correct (2),
        almost correct (1), or incorrect (0).
    """
    # Check for valid inputs
    if not isinstance(guess, str) or not isinstance(secret, str):
        raise TypeError("inputs must be strings")
    elif len(guess) != len(secret):
        raise ValueError("length of inputs must be equal")

    # Ignore case
    guess = guess.lower()
    secret = secret.lower()

    # Initialize feedback
    n = len(guess)
    feedback = [0] * n  # assume no letters match at first

    # Find correct letters
    for i in range(n):
        if guess[i] == secret[i]:
            feedback[i] = 2
    
    # Find almost correct letters (exists in the secret, but in a different position)
    letters = ''.join([letter for letter, match in zip(secret, feedback) if not match])
    for i in range(n):
        if feedback[i] != 2 and guess[i] in letters:
            feedback[i] = 1
            j = letters.index(guess[i])
            letters = letters[:j] + letters[j+1:]
    
    return feedback

def get_key(debug=False):
    """Wait for the user to press a key. Valid options include a letter, Backspace, Enter, or Escape key.
    
    Parameters
    ----------
    debug : bool, optional (default=False)
        Flag to show internal information about the key that was pressed.

    Returns
    -------
    key: str
        A string indicating what was pressed.
    """
    with keyboard.Events() as events:
        for event in events:
            if isinstance(event, keyboard.Events.Release):
                # Show what was pressed, if requested
                if debug:
                    print(event.key)

                # Check for valid key presses and output accordingly
                if hasattr(event.key, 'char') and event.key.char in 'abcdefghijklmnopqrstuvwxyz':
                    return event.key.char.upper()
                elif event.key == keyboard.Key.backspace:
                    return 'backspace'
                elif event.key == keyboard.Key.enter:
                    return 'enter'
                elif event.key == keyboard.Key.esc:
                    return 'esc'

def get_version():
    """Retrieve the current git hash to use as a 'version' number."""
    try:
        version = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except:
        version = 'WARNING: Could not access version of code using \'git rev-parse --short HEAD\' command'
        
    return version

def load_player(name):
    """Load an AI player from file.
    
    Parameters
    ----------
    name : str
        Filename in 'players' directory for the AI player to load.

    Returns
    -------
    player : importlib module (or 0 for error)
        Module of AI player that must contain a function called "choice".
        If the player was not loaded correctly, the output will be 0.
    """
    if name is not None:
        print(f"Loading AI player: {name}")
        try:
            sys.path.append(os.path.join(ROOT, 'players')) # add directory containing AI player to system path
            player = importlib.import_module(name)
        except ImportError:
            print(Fore.RED + f"\tERROR: Cannot import AI player")
            return 0

        if not hasattr(player, 'choice'):
            print(Fore.RED + f"\tERROR: This AI player does not have a 'choice' function")
            return 0

        return player
    else:
        print(Fore.RED + f"\tERROR: No AI player name was provided. Check inputs.")
        return 0

def print_title():
    """Show the header for the game."""
    print()
    print('  WORDLE')
    print('=' * 10, end=" ")
    print("Remaining Letters...")

def print_word(word='', feedback=[], remaining=''):
    """Print a word, leaving blanks for missing letters.

    Parameters
    ----------
    word : str, optional
        Word to display. Default is an empty string (only display blanks).
    feedback : list, optional
        A list of integers, one per letter in the word, to indicate if the letter is correct (2),
        almost correct (1), or incorrect (0). If provided, the feedback affects the color of each
        printed letter. Default is an empty list (no feedback to show).
    remaining : str, optional
        String containing the remaining letters that could be in the word.
        By default, this argument is empty.
    """
    print('\r', end='') # move the cursor to the left of the line
    if len(feedback) == 0: # show the word as the user is typing it
        print(*word.upper(), sep=' ', end=' ' if len(word) > 0 else '')
        print('_ ' * (5 - len(word)), end='') # add blanks for missing letters
    else: # show the word with colored feedback after the user submitted it
        for i in range(5):
            if feedback[i] == 2: # correct
                print(Fore.GREEN + word[i] + ' ', end='')
            elif feedback[i] == 1: # almost correct
                print(Fore.YELLOW + word[i] + ' ', end='')
            elif feedback[i] == 0: # incorrect
                print(Fore.WHITE + word[i] + ' ', end='')
        Style.RESET_ALL
    print(' ' + remaining, end=' ')

def read_words(file, header=False, sep='\n', encoded=False):
    """Return a list of uppercase words from file.
    
    Parameters
    ----------
    file : str
        The file to read from.
    header : bool, optional (default=False)
        Does the file contain a single-line header?
    sep : str, optional (default='\\n')
        Separator between words in the file.
    encoded : bool, optional (default=False)
        Is the file encoded? If True, assume Base64 encoding.

    Returns
    -------
    words: list
        A list of uppercase words.
    """
    # Read raw data from file
    with open(file, 'r') as f:
        if header: # does the file contain a header? (e.g. number of words listed)
            n = int(f.readline())
        data = f.read()

    # Decode, if necessary
    if encoded:
        data = base64.b64decode(data).decode('utf-8')
    
    # Convert to a list of uppercase words
    words = data.upper().split(sep)  # make list of words

    return words

def remove_letters(alphabet, guess, feedback):
    """Remove letters from the known alphabet using feedback about a guessed word.
    
    Parameters
    ----------
    alphabet : str
        String of letters that are currently valid.
    guess : str
        Word that was guessed.
    feedback: list
        A list of integers, one per letter in the guessed word, to indicate if the letter 
        is correct (2), almost correct (1), or incorrect (0).

    Returns
    -------
    leftovers: str
        String of remaining letters after discarding those guessed with feedback=0.
    """
    used = set([letter for letter, exists in zip(guess, feedback) if exists == 0])
    leftovers = "".join([letter for letter in alphabet if letter not in used])

    return leftovers
                    
def test():
    """Test utility functions for errors."""
    print("!!! TESTING UTILITY FUNCTIONS !!!")

    print('\nTesting get_feedback(guess, secret)')
    print('-----------------------------------')
    print(f'ABC --> XYZ = {get_feedback("ABC", "XYZ")}')
    print(f'TEST --> TEST = {get_feedback("TEST", "TEST")}')
    print(f'ADIEU --> DIALS = {get_feedback("ADIEU", "DIALS")}')
    print(f'ROBOT --> BOUND = {get_feedback("ROBOT", "BOUND")}')

    print('\nTesting get_key(debug=True)')
    print('---------------------------')
    print('Press any key...')
    key = get_key(debug=True)
    print(f'You pressed a valid key: {key}. Exiting test.')

    print('\nTesting get_version()')
    print('---------------------')
    version = get_version()
    print(version)

    print('\nTesting load_player()')
    print('---------------------')
    player = load_player("not a real player name")
    player = load_player("randy")
    print(f'\tRandy chooses: {player.choice(["APPLE", "BANJO", "CANDY"])}')
    player = load_player("robby")
    print(f'\tRobby chooses: {player.choice([])}')

    print('\nTesting read_words(file)')
    print('------------------------')
    words = read_words(os.path.join(ROOT, 'data', 'secret.txt'), encoded=True)
    print(*words[:10], sep=' ', end='...\n')
    print(f'Number of secret words: {len(words)}')
    words = read_words(os.path.join(ROOT, 'data', 'vocabulary.txt'), encoded=False)
    print(*words[:10], sep=' ', end='...\n')
    print(f'Number of vocabulary words: {len(words)}')

    print('\nTesting remove_letters(alphabet, guess, feedback)')
    print('-------------------------------------------------')
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    guess = "ROBOT"
    feedback = get_feedback(guess, "BOUND")
    leftovers = remove_letters(alphabet, guess, feedback)
    print(f"The leftovers after guessing {guess} and receiving {feedback} is:")
    print(leftovers)

    print('\nTesting print_title()')
    print('---------------------')
    print_title()

    print('\nTesting print_word()')
    print('--------------------')
    print_word()
    print()
    print_word(word='ROBOT')
    print()
    print_word(word='ROBOT', feedback=[0, 2, 1, 0, 0])
    print()
    print_word(word='ROBOT', feedback=[0, 2, 1, 0, 0], remaining=alphabet)
    print()

def update_stats(outcome, file=os.path.join("data", "stats.txt")):
    """Update statistics file based on the outcome of a game.
    
    Parameters
    ----------
    outcome : int
        Number of guesses it took to solve the puzzle. Unsolved puzzles will yield outcome=0.
    file : str, optional
        Name of the file to update. Will create file if it does 
        not already exist. Default is "stats.txt".
    """
    # Force input filename to be a .txt file if extension not provided
    if '.' not in file:
        file = file + '.txt'

    # Try to read data from file
    try:
        with open(file, "r") as f:
            data = f.read().splitlines()  # make list of strings, one per stat line
    except IOError:
        print(Fore.YELLOW + f'WARNING: Unable to track stats because {file} does not exist. Creating file now.')
        data = []

    # Load stats into dictionary
    stats = {}
    for line in data:
        if len(line) == 0:  # take care of blank lines (often happens at end of file)
            continue
        with open(file, "r") as f:
            for line in f:
                line = line.strip()  # Remove any leading/trailing whitespace
                if "=" not in line:  # Skip invalid lines
                    continue
                stat, value = line.split('=', 1)  # Ensure only one split

        try:
            stats[stat] = int(value)
        except:  # need something special for floats and lists
            try:
                stats[stat] = float(value)
            except:
                stats[stat] = [int(i) for i in value.split(',')]
    
    # Validate dictionary
    minstats = ['played', 'win percentage', 'current streak', 'max streak', 'guess distribution']
    if set(minstats) > set(stats.keys()):
        print(Fore.YELLOW + f'WARNING: {file} does not contain the correct stats. Resetting file now.')
        stats = dict.fromkeys(minstats, 0)
        stats['guess distribution'] = [0] * 6
    
    # Modify stats based on outcome
    stats['played'] += 1
    if outcome != 0:
        stats['current streak'] += 1
        if stats['current streak'] > stats['max streak']:
            stats['max streak'] = stats['current streak']
        stats['guess distribution'][outcome - 1] += 1
    else:
        stats['current streak'] = 0
    stats['win percentage'] = sum(stats['guess distribution']) / stats['played'] * 100
    
    # Write new stats to file
    with open(file, "w") as f:
        for key, value in stats.items():
            if isinstance(value, list):
                f.write(f'{key}={",".join([str(i) for i in value])}\n')
            elif isinstance(value, float):
                f.write(f'{key}={value:0.3f}\n')
            else:
                f.write(f'{key}={value}\n')

if __name__ == "__main__":
    test()