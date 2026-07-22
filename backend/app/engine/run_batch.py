from engine.game import main, Game_State
from engine.random_search_bot import Random_Search_Opponent
from engine.bots import Heuristic_Opponent
import random 

def run_normal_batch():
    N_GAMES = 1000

    for i in range(N_GAMES):
        if i % 100 == 0:
            print(f"game {i}/{N_GAMES}")
        main()

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
    N_ITERATIONS = 10
    best_solution = 0
    best_combo = None
    for i in range(N_ITERATIONS):
        if i % 10 == 0:
            print(f"trial {i}/{N_ITERATIONS}")
        wins = 0
        chosen_combo = {
            "swap_margin": random.uniform(*search_space["swap_margin"]),
            "who_has_seen_opponent_card": random.randint(*search_space["who_has_seen_opponent_card"]),
            "who_has_seen_my_card": random.randint(*search_space["who_has_seen_my_card"]),
            "cabo_known_ratio_threshold": random.uniform(*search_space["cabo_known_ratio_threshold"]),
            "cabo_avg_value_threshold": random.uniform(*search_space["cabo_avg_value_threshold"])
            }
        for j in range(N_GAMES):
            random.seed(j)
            print(f"seed chosen for game: {j}")
            fresh_game_state = Game_State(players=[])
            tuned_bot = Random_Search_Opponent(name="Tuned", game_state=fresh_game_state, config=chosen_combo)
            fresh_game_state.players = [
                tuned_bot,
                Heuristic_Opponent("H1", fresh_game_state),
                Heuristic_Opponent("H2", fresh_game_state),
                Heuristic_Opponent("H3", fresh_game_state),
            ]
            winner = main(fresh_game_state)
            print(f" winner: {winner}")
            if winner == "Tuned":
                wins += 1
        current_solution = wins/20
        if best_solution < current_solution:
            best_solution = current_solution
            best_combo = chosen_combo
    print(f"best combo: {best_combo}")
    print(f"best win rate : {best_solution}")

if __name__ == "__main__":
    run_random_search_batch()
