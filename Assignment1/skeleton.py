import math
import time
import gym
import random
import requests
import numpy as np
import argparse
import sys
from gym_connect_four import ConnectFourEnv

env: ConnectFourEnv = gym.make("ConnectFour-v0")

SERVER_ADDRESS = "https://vilde.cs.lth.se/edap01-4inarow/"
API_KEY = 'nyckel'
STIL_ID = ["er8540ma-s"]  # TODO: fill this list with your stil-id's


def call_server(move):
    res = requests.post(SERVER_ADDRESS + "move",
                        data={
                            "stil_id": STIL_ID,
                            "move": move,  # -1 signals the system to start a new game. any running game is counted as a loss
                            "api_key": API_KEY,
                        })
    # For safety some respose checking is done here
    if res.status_code != 200:
        print("Server gave a bad response, error code={}".format(res.status_code))
        exit()
    if not res.json()['status']:
        print("Server returned a bad status. Return message: ")
        print(res.json()['msg'])
        exit()
    return res


def check_stats():
    res = requests.post(SERVER_ADDRESS + "stats",
                        data={
                            "stil_id": STIL_ID,
                            "api_key": API_KEY,
                        })

    stats = res.json()
    return stats


"""
You can make your code work against this simple random agent
before playing against the server.
It returns a move 0-6 or -1 if it could not make a move.
To check your code for better performance, change this code to
use your own algorithm for selecting actions too
"""


def opponents_move(env):
    env.change_player()  # change to oppoent
    avmoves = env.available_moves()
    if not avmoves:
        env.change_player()  # change back to student before returning
        return -1

    # TODO: Optional? change this to select actions with your policy too
    # that way you get way more interesting games, and you can see if starting
    # is enough to guarrantee a win
    action = random.choice(list(avmoves))

    state, reward, done, _ = env.step(action)
    if done:
        if reward == 1:  # reward is always in current players view
            reward = -1
    env.change_player()  # change back to student before returning
    return state, reward, done

def make_move(state, piece, column):
    for row in range(state.shape[0]-1, -1, -1):
        if state[row, column] == 0:
            state[row, column] = piece
            return

def game_end(state):
    # Win
    if eval_board(state, 1) > 600:
        return 1
    # AI Win
    if eval_board(state, -1) > 600:
        return -1 
    # Draw
    if np.count_nonzero(state == 0) == 0:
        return 0
    return 2

def minimax(state, depth, alpha, beta, maxiPlayer):
    valid_moves = np.where(np.any(state == 0, axis=0))[0]
    is_terminal = game_end(state)

    if is_terminal == -1:
        return (None, 10000000000)
    elif is_terminal == 1:
        return (None, -10000000000)
    elif is_terminal == 0:
        return (None, 0)

    if depth == 0:
        return (None, eval_board(state, -1))
    
   
    if maxiPlayer:
        best_move = random.choice(valid_moves)
        best_eval = -math.inf

        for move in valid_moves:
            state_copy = state.copy()
            make_move(state_copy, -1, move)

            new_eval = minimax(state_copy, depth -1, alpha, beta, False)[1]
            if new_eval > best_eval:
                best_eval = new_eval
                best_move = move
            alpha = max(alpha, best_eval)
            if alpha >= beta:
                break
        return best_move, best_eval

    else:
        best_move = random.choice(valid_moves)
        best_eval = math.inf
        for move in valid_moves:
            state_copy = state.copy()
            make_move(state_copy, 1, move)
            new_score = minimax(state_copy, depth -1, alpha, beta, True)[1]
            if new_score < best_eval:
                best_eval = new_score
                best_move = move
            beta = min(beta, best_eval)
            if alpha >= beta:
                break
        return best_move, best_eval
    

def eval_board(state, piece):
    score = 0
    rows = state.shape[0]
    cols = state.shape[1]

    # Man kan värdera positioner i mitten högre här ifall det inte duger prestandamässigt

    center_column = state[:,3]
    center_pieces = np.count_nonzero(center_column == piece)
    score += center_pieces * 3

    # Kolla horisontellt
    for i in range(rows):
        row = state[i]

        for ii in range(cols - 3):
            window = row[ii:ii+4]
            score += eval_window(window, piece)
    # Kolla vertikalt
    for i in range(cols):
        col = state[:, 1]
        for ii in range(rows - 3):
            window = col[ii:ii+4]
            score += eval_window(window, piece)

    # Kolla diagonalt
    for i in range(rows - 3):
        for ii in range(cols - 3):
            window = [state[i+iii][ii+iii] for iii in range(4)]
            score += eval_window(window, piece)

    for i in range(rows - 3):
        for ii in range(cols-3):
            window = [state[i+3-iii][ii+iii] for iii in range(4)]
            score += eval_window(window, piece)
    return score


def eval_window(window, piece):
    score = 0

    opponent = 1
    if piece == 1:
        opponent = -1

    count = 0
    countOpponent = 0
    countEmpty = 0

    for val in window:
        if val == piece:
            count += 1
        if val == opponent:
            countOpponent += 1
        if val == 0:
            countEmpty += 1

    if count == 4:
        score += 1000
    elif count == 3 and countEmpty == 1:
        score += 5
    elif count == 2 and countEmpty == 2:
        score += 2

    if countOpponent == 3 and countEmpty == 1:
        score -= 100

    return score


def student_move(state):
    """
    TODO: Implement your min-max alpha-beta pruning algorithm here.
    Give it whatever input arguments you think are necessary
    (and change where it is called).
    The function should return a move from 0-6
    """
    now = time.time()
    res = minimax(state, 5, -math.inf, math.inf, True)[0]
    duration = time.time() - now
    print("Calc Time: ", duration)
    return res


def play_game(vs_server=False):
    """
    The reward for a game is as follows. You get a
    botaction = random.choice(list(avmoves)) reward from the
    server after each move, but it is 0 while the game is running
    loss = -1
    win = +1
    draw = +0.5
    error = -10 (you get this if you try to play in a full column)
    Currently the player always makes the first move
    """

    # default state
    state = np.zeros((6, 7), dtype=int)

    # setup new game
    if vs_server:
        # Start a new game
        # -1 signals the system to start a new game. any running game is counted as a loss
        res = call_server(-1)

        # This should tell you if you or the bot starts
        print(res.json()['msg'])
        botmove = res.json()['botmove']
        state = np.array(res.json()['state'])
        # reset env to state from the server (if you want to use it to keep track)
        env.reset(board=state)
    else:
        # reset game to starting state
        env.reset(board=None)
        # determine first player
        student_gets_move = random.choice([True, False])
        if student_gets_move:
            print('You start!')
            print()
        else:
            print('Bot starts!')
            print()

    # Print current gamestate
    print("Current state (1 are student discs, -1 are servers, 0 is empty): ")
    print(state)
    print()

    done = False
    while not done:
        # Select your move
        stmove = student_move(state)  # TODO: change input here

        # make both student and bot/server moves
        if vs_server:
            # Send your move to server and get response
            res = call_server(stmove)
            print(res.json()['msg'])

            # Extract response values
            result = res.json()['result']
            botmove = res.json()['botmove']
            state = np.array(res.json()['state'])
            # reset env to state from the server (if you want to use it to keep track)
            env.reset(board=state)
        else:
            if student_gets_move:
                # Execute your move
                avmoves = env.available_moves()
                if stmove not in avmoves:
                    print("You tied to make an illegal move! You have lost the game.")
                    break
                state, result, done, _ = env.step(stmove)

            student_gets_move = True  # student only skips move first turn if bot starts

            # print or render state here if you like

            # select and make a move for the opponent, returned reward from students view
            if not done:
                state, result, done = opponents_move(env)

        # Check if the game is over
        if result != 0:
            done = True
            if not vs_server:
                print("Game over. ", end="")
            if result == 1:
                print("You won!")
            elif result == 0.5:
                print("It's a draw!")
            elif result == -1:
                print("You lost!")
            elif result == -10:
                print("You made an illegal move and have lost!")
            else:
                print("Unexpected result result={}".format(result))
            if not vs_server:
                print("Final state (1 are student discs, -1 are servers, 0 is empty): ")
        else:
            print("Current state (1 are student discs, -1 are servers, 0 is empty): ")

        # Print current gamestate
        print(state)
        print()


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-l", "--local", help="Play locally",
                       action="store_true")
    group.add_argument(
        "-o", "--online", help="Play online vs server", action="store_true")
    parser.add_argument(
        "-s", "--stats", help="Show your current online stats", action="store_true")
    args = parser.parse_args()

    # Print usage info if no arguments are given
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.local:
        play_game(vs_server=False)
    elif args.online:
        play_game(vs_server=True)

    if args.stats:
        stats = check_stats()
        print(stats)

    # TODO: Run program with "--online" when you are ready to play against the server
    # the results of your games there will be logged
    # you can check your stats bu running the program with "--stats"


if __name__ == "__main__":
    main()
