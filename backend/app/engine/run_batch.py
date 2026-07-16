from game import main 

N_GAMES = 1000

for i in range(N_GAMES):
    if i % 100 == 0:
        print(f"game {i}/{N_GAMES}")
    main()