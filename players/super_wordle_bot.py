# super_wordle_bot.py 
# 
# An AI player that uses Claude Shannon's entropy equation to limit the search space in the most efficient manner possible
# Tested through every possible solution with 100% accuracy.
# 
# Relevant Sources Used:
# https://youtu.be/fRed0Xmc2Wg?si=crUVxX-jpNyor-G1
# https://youtu.be/v68zYyaEmEA?si=YXYVq7RlAiCpCiMg
# https://youtu.be/YEoCBnQwdzM?si=yykjLpXWW1HUAuQK
# https://youtu.be/sVCe779YC6A?si=BZqYv7czm9YVIiXO
# https://www.sciencedirect.com/topics/engineering/shannon-entropy
# https://tomrocksmaths.com/wp-content/uploads/2023/07/using-information-entropy-to-e28098solve-wordle.pdf
# https://willbeckman.com/wordle.html
#
# Author: Michael Woll

import math

def compute_feedback(guess_word: str, solution_word: str) -> list[str]: 
    """Generate Wordle-style feedback for a guessed word against the solution.

    Parameters
    ----------
    guess_word : str
        The word we guessed.
    solution_word : str
        The word we're testing against the guess.

    Returns
    -------
    list[int]
        A list of five integers representing feedback for each letter in `guess_word`:
        - 2 indicates the letter is correct and in the correct position.
        - 1 indicates the letter is in the solution but in the wrong position.
        - 0 indicates the letter is not in the solution.
        
    Notes
    -----
    - Exact matches `2` are handled first to avoid double-counting letters.
    - After that, misplaced matches `1` are marked, but only if the letter hasn’t already been used up in the solution.
    - Once a letter is matched as either `2` or `1`, it’s removed from consideration to avoid overmatching.
    """
    
    # Convert both words to lists. We do this so we can mark letters as None once they're matched.
    guess_list = list(guess_word)
    solution_list = list(solution_word)

    # Initialize feedback array of size five to mimic word length. Each position will be a 0, 1, or 2, just like the built in feedback system.
    result = [0] * 5

    # Mark all letters in the correct spot with a 2 and remove them from solution_list so that they won't be double counted.
    for i in range(5):
        if guess_list[i] == solution_list[i]:
            result[i] = 2
            solution_list[i] = None
            guess_list[i] = None
        
    # Mark all letters that appear in the solution, but are not in the right spot with a 1 and remove them from solution_list so that we don't double count.
    for i in range(5):
        if guess_list[i] is not None and guess_list[i] in solution_list:  
            result[i] = 1
            # Remove that letter from solution_list so it won't be matched again
            match_index = solution_list.index(guess_list[i])
            solution_list[match_index] = None
            
    return result


def is_consistent(candidate_word: str, guesses: list[str], feedback: list[list[int]]) -> bool:
    """
    Checks if a candidate word fits with all the previous guesses and feedback.

    Parameters
    ----------
    candidate_word : str
        The word we’re testing to see if it could be the solution.
    guesses : list of str
        A list of all the words guessed so far, in the order we guessed them. Each guess lines up with the feedback provided.
        Example: ['guess1', 'guess2', 'guess3']
    feedback : list of list of int
        The feedback for each guess using our previous computer_feedback function
        Example: [[0, 1, 2, 0, 0], [2, 0, 2, 1, 0], [2, 2, 2, 2, 2]]
    
    Returns
    -------
    bool
        Returns True if the `candidate_word` works with all the previous feedback, and False if it doesn’t fit the feedback at all.

    Notes
    -----
    - This function works by pretending the `candidate_word` is the solution and then simulates what the feedback would’ve looked like for each guess.
    - If any simulated feedback doesn’t match the real feedback, the word gets rejected.
    """
    for i, guess in enumerate(guesses):
        # Compute what the feedback WOULD be if 'candidate_word' were the solution
        hypothetical_feedback = compute_feedback(guess, candidate_word)
        # Compare it with actual feedback we got
        if hypothetical_feedback != feedback[i]:
            return False
    return True
    
    
def calculate_entropy(guess_word: str, possible_solutions: list[str]) -> float:
    """
    Calculate the Shannon entropy (in bits) for a given guess word, based on the current set of possible solutions.

    Parameters
    ----------
    guess_word : str
        The word we’re testing to see how much information it gives us about the solution.
    possible_solutions : list of str
        The remaining possible solutions based on our previous calculations and guesses.

    Returns
    -------
    float
        The Shannon entropy for the guess word, measured in bits.
    Notes
    -----
    - This function works by simulating Wordle feedback for `guess_word` against every word in `possible_solutions`.
    - It builds a frequency table (`pattern_counts`), where each unique feedback pattern i.e. (0, 1, 2, 0, 0) is a key, and the value is the number of solutions that produce that feedback.
    - Using this table, it calculates the probability (`probability`) of each feedback pattern and applies the Shannon entropy formula:
    
        H = -sum(p * log2(p))

    - High entropy means the guess splits the solution space evenly across many feedback patterns, giving us the most information (it's a good word to guess). Low entropy means one feedback pattern dominates, providing less information (not as good of a guess).
    """

    # Create a dictionary where the key is the feedback tuple i.e. (0, 1, 1, 2, 2) and the value is the number of possible solutions remaining with that specific feedback pattern against our guess_word.
    pattern_counts = {}

    # For each possible solution, see what feedback pattern we'd get if it were the actual solution.
    # This is the foundation of entropy calculations. This frequency table allows us analyze the spread of feedback patterns and determine how much information each guess gives us.
    # If a guess produces a wide variety of different patterns each with small counts, it more evenly splits the solution space, provides high entropy and is a good guess
    # If a guess produces fewer patterns where one pattern dominates, then it doesn't provide as much information, has low entropy and is thus a worse guess.
    for solution in possible_solutions:
        feedback = tuple(compute_feedback(guess_word, solution))  # make feedback hashable
        if feedback not in pattern_counts:
            pattern_counts[feedback] = 0
        pattern_counts[feedback] += 1

    # Probability of each feedback pattern
    total = len(possible_solutions)
    entropy = 0.0
    for count in pattern_counts.values():
        probability = count / total # Calculate probability of each count.
        entropy -= probability * math.log2(probability) # We are looking for p value that gives us maximal entropy
    return entropy

    
def choice(vocabulary: list[str], guesses: list[str] = [], feedback: list[list[int]] = []) -> str:
    """Guess a word from the available vocabulary, (optionally) using feedback from previous guesses.
    
    Parameters
    ----------
    vocabulary : list of str
        A list of the valid word choices. The output must come from this list.
    guesses : list of str
        A list of the previously guessed words, in the order they were made, e.g. guesses[0] = first guess, guesses[1] = second guess. The length of the list equals the number of guesses made so far. An empty list (default) implies no guesses have been made.
        i.e. ['guess1', 'guess2', 'guess3']
    feedback : list of lists of int
        A list comprising one list per word guess and one integer per letter in that word, to indicate if the letter is correct (2), almost correct (1), or incorrect (0). An empty list (default) implies no guesses have been made.
        i.e. [[0,1,2,0,0], [2,0,2,1,0], [2,2,2,2,2]]

    Returns
    -------
    word : str
        The word chosen by the player for the next guess.
    """
    
    # Use "SOARE" for first guess
    if not guesses:
        return "SOARE" 
    
    
    # Build a list of all possible solutions.
    # For each word in the vocabulary, check if it is still possible for that word to be the answer given what we know, if so add to possible_solutions.
    possible_solutions = [
        word for word in vocabulary 
        if is_consistent(word, guesses, feedback)
    ]

    # If there's only one possible solution left, return it
    if len(possible_solutions) == 1:
        return possible_solutions[0]
    

    # Choose the guess that maximizes entropy
    best_guess = None
    best_entropy = -1

    # Use the entire vocabulary to test our guesses. To go faster we could just use the possible_solutions word list, but our accuracy drops a bit because sometimes the most informative guess isn't always a possible solution (unless we are on our last guess.)
    candidate_guesses = vocabulary if len(guesses) <5 else possible_solutions

    # Loop through each word and calculate its entropy. Then use a max comparison to track the highest entropy and the word that provides it
    for candidate in candidate_guesses:
        entropy = calculate_entropy(candidate, possible_solutions)
        if entropy > best_entropy:
            best_entropy = entropy
            best_guess = candidate

    return best_guess