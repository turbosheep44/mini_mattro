* `game_human.py` is the human playable version of the game. `play_step()` does not take any action and operates similarly to the update function in the old format (found in `store/game.py`). In this case `play_step()` returns a `game_over` variable.
  
* `game_ai.py` is the AI version of the game, where an action is to be given to the `play_step(action)` function. It returns the reward, game_over, and score. 

> The action is in the following format: [ MODE | STATIONS | RAILS]. For example:
>
> ```
>MODE = [1 0 0]
>STATIONS = [1 1 0 0 0 0 0 0]
>RAILS = [1 0 0]
>```
>
>This means: Connect the first and second stations using the first rail.

* `agent.py` runs the training process for `GAME_COUNT` number of games. The most important functions in this class are the `get_state()` and `get_action(state)` functions. Plots from an initiated training process can be found in `plots/*`.