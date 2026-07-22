from engine.game import main, Game_State
from engine.random_search_bot import Random_Search_Opponent
from engine.bots import Heuristic_Opponent
import random 
import pandas as pd
import os

def run_normal_batch():
    N_GAMES = 1000
    wins = 0
    for i in range(N_GAMES):
        if i%20==0:
            print(f"trial {i}/{N_GAMES}")
        chosen_combo = {
            "swap_margin": 0.9914362231109511,
            "who_has_seen_opponent_card": 3,
            "who_has_seen_my_card": 1,
            "cabo_known_ratio_threshold": 0.613449352799165,
            "cabo_avg_value_threshold": 5.7602470927440885
            }
        random.seed(i+20)
        #print(f"seed chosen for game: {j}")
        fresh_game_state = Game_State(players=[])
        tuned_bot = Random_Search_Opponent(name="Tuned", game_state=fresh_game_state, config=chosen_combo)
        fresh_game_state.players = [
            tuned_bot,
            Heuristic_Opponent("H1", fresh_game_state),
            Heuristic_Opponent("H2", fresh_game_state),
            Heuristic_Opponent("H3", fresh_game_state),
        ]
        winner = main(fresh_game_state)
        if winner == "Tuned":
            wins += 1
    print(f"win rate : {wins/N_GAMES}")

'''
1. Define the function to be optimized.
2. Set search space boundaries.
3. Generate random candidate solutions within the boundaries.
4. Evaluate each candidate using the objective function.
5. Track the best solution found so far.
6. Repeat for a predefined number of iterations.
500 iterations.
'''
def run_random_search_batch():
    search_space = {
        "swap_margin": [0, 3],
        "who_has_seen_opponent_card": [1, 4],
        "who_has_seen_my_card": [1, 4],
        "cabo_known_ratio_threshold": [0.5, 1],
        "cabo_avg_value_threshold": [2, 6],
    }
    N_GAMES = 20
    N_ITERATIONS = 500
    results = []
    best_solution = 0
    best_combo = None
    config_rng = random.Random()
    for i in range(N_ITERATIONS):
        if i%20==0:
            print(f"trial {i}/{N_ITERATIONS}")
        wins = 0
        chosen_combo = {
            "swap_margin": config_rng.uniform(*search_space["swap_margin"]),
            "who_has_seen_opponent_card": config_rng.randint(*search_space["who_has_seen_opponent_card"]),
            "who_has_seen_my_card": config_rng.randint(*search_space["who_has_seen_my_card"]),
            "cabo_known_ratio_threshold": config_rng.uniform(*search_space["cabo_known_ratio_threshold"]),
            "cabo_avg_value_threshold": config_rng.uniform(*search_space["cabo_avg_value_threshold"])
            }
        for j in range(N_GAMES):
            random.seed(j)
            #print(f"seed chosen for game: {j}")
            fresh_game_state = Game_State(players=[])
            tuned_bot = Random_Search_Opponent(name="Tuned", game_state=fresh_game_state, config=chosen_combo)
            fresh_game_state.players = [
                tuned_bot,
                Heuristic_Opponent("H1", fresh_game_state),
                Heuristic_Opponent("H2", fresh_game_state),
                Heuristic_Opponent("H3", fresh_game_state),
            ]
            winner = main(fresh_game_state)
            #print(f" winner: {winner}")
            if winner == "Tuned":
                wins += 1
        current_solution = wins/N_GAMES
        results.append({**chosen_combo, "win_rate": current_solution, "trial": i})
        if best_solution < current_solution:
            best_solution = current_solution
            best_combo = chosen_combo
    print(f"best combo: {best_combo}")
    print(f"best win rate : {best_solution}")

    os.makedirs("game_logs/random_search_opponent/summary_combos", exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv("game_logs/random_search_opponent/summary_combos/search_results.csv", index=False)

if __name__ == "__main__":
    run_normal_batch()
