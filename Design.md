(1)  What additional properties did you add to your models and why?

For User model, the additional properties added are: number of wins, number of loses, number of moves on wins, winning percentage rate, and average game moves on winning games.  These properties were added to determine user ranking.  The user ranking endpoints requires index on winning percentage rate, number of wins, and average game moves on winning games to sort the user by performance.  The data mentioned are updated when a game ends.  Data is recorded for both the users that are playing the game.  These data are not affected by games that ended with a draw or when games are cancelled.  Winning percentage rate calculation is number of wins / (number of wins + number of loses).   Average games moves on winning games calculation is number of moves on wins / number of wins.  Customer is ranked using winning percentage rate, number of wins, and average game moves on winning games, in the order it is mentioned.  When 2 players have the same winning percentage rate, the player with more wins has a higher ranking.  When 2 player have the same winning percentage rate and number of wins, the player with less moves to win a game has a higher ranking. 

In Game model, the additional properties added are: moves made in the game, the X user, the O user, moves count, game end date, and history.  History, move count and, moves made in the game is updated for every move made by a player.  Game end date is updated once the game ends.  Game record is deleted when game is cancelled.  History is record when a player makes a move whether it is an accepted move or not.  History includes date of the move, the user who made the move, the move count of the current move, the move, and message.  Moves made in the game was added to the model to record that current move state of the game.  X user and O user are the players of the game.  Game end date is an important information to know when the game ended.  History is added to the model since it is easy to link and retrieve the information to the game and it does not required any special processing.       

UserGame model is a new model added. The purpose of this model is to record the players of the game and other status information.  It records the players of the game, game over status, win status of the player (win, lose, draw), and number of moves made in the game when it ended.  This model is created when a new game is created.  Data is deleted when a game is cancelled.  Data is updated once game is ended.  It includes recording of a game that ended in a draw.  It also includes information when user loses a game.  Although, game loses information is not used by any end points, I believe this is important information to record to get the full picture of the game and in case this information is needed in the future.  There is a need to add UserGame model to easily retrive game information for the users.  This model specifically used for the following end points: get user games endpoint, get scores, and get user scores.  This end points requires index on game and on user.            


(2) What were some of the trade-offs or struggles you faced when implementing the new game logic?

- Many endpoint requirements require redesign of the models
- Aggregate data (example: winning percentage rate) must be calculated and stored.  This means more processing time when storing data.  However, processing time when retrieving data is faster.
- Storing application settings using the Google App Engine Launcher does not work.  I needed to run dev_appserver.py from the command line.  I needed to set the application setting for sending email.
  





