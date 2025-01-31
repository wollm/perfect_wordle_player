# wordle.py 
# Command-line interface version of Wordle powered by Python.
#
# Can you correctly guess a 5-letter word in 6 chances?
#
# Author: Matthew Eicholtz
# Inspired by: https://www.nytimes.com/games/wordle/index.html

import argparse
from colorama import init, Fore, Style
import os
import pdb
import random
import stats
import sys
import time
from tqdm import tqdm
import utils

ROOT = os.path.dirname(os.path.realpath(__file__)) # root directory of repo
SECRETWORDS = os.path.join(ROOT, "data", "secret.txt")
MAXATTEMPTS = 6  # how many total guesses are allowed?
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'  # valid letters to guess

parser = argparse.ArgumentParser(description="Play Wordle in Python!")
parser.add_argument('-ai', metavar='player', type=str, help='name of AI file containing choice function')
parser.add_argument('-n', metavar='num_games', type=int, help='number of games to play', default=1)
parser.add_argument('--secret', metavar='word', type=str, help='hardcoded secret word to test')
parser.add_argument('--seed', metavar='s', type=int, help='seed for random number generation, defaults to system time')
parser.add_argument('--stats', metavar='filename', type=str, help='name of stats file, defaults to stats.txt', default='stats.txt')
parser.add_argument('--fast', action='store_true', help='flag to speed up the game (AI only)')
parser.add_argument('--superfast', action='store_true', help='flag to eliminate any printed display during the game (AI only)')
parser.add_argument('--play_all', action='store_true', help='flag to play all possible secret words')
parser.add_argument('--practice', action='store_true', help='flag to not track stats for this game')
parser.add_argument('--show_fails', action='store_true', help='flag to display the secret words that were missed after all games are complete')
parser.add_argument('--version', action='version', version=utils.get_version())

def main(args):
    # Setup
    init(autoreset=True)  # required for colored text

    if args.seed is None:
        random.seed() # use current system time for randomness
    else:
        random.seed(args.seed) # use seed provided by user
    
    if args.fast:
        delay = 0
    else:
        delay = 1

    if args.secret is not None and (len(args.secret) != 5 or len(set(args.secret.upper()) - set(ALPHABET)) != 0):
        print(Fore.RED + f'ERROR: Invalid input argument for --secret. Must be a 5-letter word.')
        return 0

    if args.play_all and (args.n > 1):
        print(Fore.RED + f'ERROR: Invalid set of input arguments. Cannot set -n if using --play_all.')
        return 0
    
    # Load AI player (if provided)
    player = utils.load_player(args.ai) if args.ai else 0

    # Read word lists from file
    vocabulary = utils.read_words(os.path.join(ROOT, "data", "vocabulary.txt"))
    secret_word_list = utils.read_words(os.path.join(ROOT, "data", "secret.txt"), encoded=True)

    # Play the game
    failures = [] # keep track of which secret words were missed
    if args.play_all:
        args.n = len(secret_word_list)
    for i in tqdm(range(args.n)) if args.superfast else range(args.n):
        # Set the secret word
        if args.secret is not None: # use the word provided by the user
            secret = args.secret.upper()
        elif args.play_all: # iterate through the entire secret word list
            secret = secret_word_list[i]
        else: # pick randomly
            secret = random.choice(secret_word_list)
        
        # Who is playing?
        if player == 0:  # human player
            outcome = play(secret, vocabulary)
        else: # AI player
            # outcome = watch(secret, vocabulary, player, delay, verbose=not args.superfast)
            outcome = watch(secret, vocabulary.copy(), player, delay, verbose=not args.superfast)
        
        # Was the word missed?
        if outcome <= 0:
            failures.append(secret)

        # Update statistics file
        if outcome != -1 and not args.practice:  # only update if user didn't quit
            utils.update_stats(outcome, file=os.path.join("data", args.stats))

    # Show updated stats if not practicing
    if not args.practice:
        stats.load(os.path.join("data", args.stats))

    # Show failed words, if requested
    if args.show_fails and len(failures) > 0:
        print("\nFAILED WORDS")
        print("=" * 12)
        failures.sort()
        print(*failures, sep='\n')
        print()
        fails_file = os.path.join("data", "fails.txt")
        with open(fails_file, 'w') as f:
            print(*failures, sep='\n', file=f)

def play(secret, vocabulary):
    """Play Wordle using a secret word and a list of acceptable guesses.

    Parameters
    ----------
    secret : str
        Word that the player is attempting to guess.
    vocabulary : list of str
        List of strings comprising valid guesses during the game.
    """
    utils.print_title()
    utils.print_word(remaining=ALPHABET)

    guesses, feedback = [''], []  # known information
    leftovers = ALPHABET  # remaining letters
    gameover = False
    while not gameover:
        key = utils.get_key()
        if key in ALPHABET and len(guesses[-1]) < 5: # add letter to current word
            guesses[-1] += key
            utils.print_word(guesses[-1], remaining=leftovers)
        elif key == 'backspace':  # erase a letter
            guesses[-1] = guesses[-1][:-1]
            utils.print_word(guesses[-1], remaining=leftovers)
        elif key == 'enter':  # submit word if finished
            if len(guesses[-1]) < 5:
                msg = "Not enough letters"
                print(Fore.RED + msg, end='')
                Style.RESET_ALL
                time.sleep(1)
                print('\b' * len(msg) + " " * len(msg) + '\b' * len(msg), end='')
            elif guesses[-1] not in vocabulary:
                msg = "Not in word list"
                print(Fore.RED + msg, end='')
                Style.RESET_ALL
                time.sleep(1)
                print('\b' * len(msg) + " " * len(msg) + '\b' * len(msg), end='')
            else:
                # Check guess
                f = utils.get_feedback(guesses[-1], secret)
                feedback.append(f)

                # Show feedback as colored text
                utils.print_word(guesses[-1], feedback[-1], leftovers)

                # Check endgame conditions
                if sum(f) == 5 * 2: # the correct guess will have feedback=2 for all 5 letters
                    gameover = True
                    msg = ["Genius", "Magnificent", "Impressive", "Splendid", "Great", "Phew"]
                    print(Fore.CYAN + '\n' + msg[len(guesses) - 1])
                    Style.RESET_ALL
                    return len(guesses)
                elif len(guesses) == 6:
                    gameover = True
                    print(Fore.RED + f'\nGAME OVER: The correct word was {secret}')
                    Style.RESET_ALL
                    return 0
                else:
                    # Start new guess
                    print()
                    leftovers = utils.remove_letters(leftovers, guesses[-1], feedback[-1])
                    guesses.append('')
                    utils.print_word(guesses[-1], remaining=leftovers)

        elif key == 'esc':  # quit game
            gameover = True
            print("\nThanks for playing.")
            return -1

def watch(secret, vocabulary, player, delay=1, verbose=True):
    """Play Wordle using a secret word, a list of acceptable guesses, and an AI player.

    Parameters
    ----------
    secret : str
        Word that the player is attempting to guess.
    vocabulary : list of str
        List of strings comprising valid guesses during the game.
    player : module
        AI player module that must include a function called choice.
    delay : float, optional
        Number of seconds to wait between guesses. Default is 1.
    """
    if verbose:
        utils.print_title()
        utils.print_word(remaining=ALPHABET)

    guesses, feedback = [], []  # known information
    leftovers = ALPHABET  # remaining letters
    gameover = False
    while not gameover:
        if len(guesses) == 2:
            with open("C:\\Users\\Aiden\\AI_Wordle_Project\\csc3510-s25-project1-mike-you-re-late\\data\\dumb.txt", "a") as log_file:
                log_file.write(f"{guesses[1]}, ")
        # Ask AI player for next guess
        guess = player.choice(vocabulary, guesses, feedback)
        guesses.append(guess)
        
        if verbose:
            try:
                utils.print_word(guesses[-1], remaining=leftovers)
            except:
                pdb.set_trace()
            time.sleep(delay)

        if guesses[-1] not in vocabulary:
            if verbose:
                print(Fore.RED + "Not in word list", end='')
                print('\nThanks for playing')
            return -1
        else:
            # Check guess
            f = utils.get_feedback(guesses[-1], secret)
            feedback.append(f)

            # Show feedback as colored text
            if verbose:
                utils.print_word(guesses[-1], feedback[-1], leftovers)

            # Check endgame conditions
            if sum(f) == 5 * 2: # the correct guess will have feedback=2 for all 5 letters
                gameover = True
                if verbose:
                    msg = ["Genius", "Magnificent", "Impressive", "Splendid", "Great", "Phew"]
                    print(Fore.CYAN + '\n' + msg[len(guesses) - 1])
                    Style.RESET_ALL
                return len(guesses)
            elif len(guesses) == 6:
                gameover = True
                if verbose:
                    print(Fore.RED + f'\nGAME OVER: The correct word was {secret}')
                    Style.RESET_ALL
                return 0
            else:
                # Start new guess
                if verbose:
                    print()
                leftovers = utils.remove_letters(leftovers, guesses[-1], feedback[-1])

if __name__ == "__main__":
    main(parser.parse_args())
