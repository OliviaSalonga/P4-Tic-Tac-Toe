Project Design a Game API:  Tic-Tac-Toe
Olivia Salonga (R) Version 1.0 09/26/2016

## Set-Up Instructions:
1.  Download the project
2.  From Google App Engine Launcher, select File > Add Existing Application.  Then, select the directory where the project was downloaded.  Take note of admin port and port information of the project.
3.  From the command line using CMD, run the sciprt below.
    <file path where google_appengine resides>/dev_appserver.py --smtp_host=smtp.gmail.com --smtp_port=25 --smtp_user=<gmail account> --smtp_password=<gmail password> --skip_sdk_update_check=yes --port=<port from step 2> --admin_port=<admin port from step 2> <file path where the project resides>
file path where google_appengine resides:  Example - "c:\Program Files (x86)\Google\google_appengine"
4.  Laund the API Explorer site using "<path-to-Chrome> --user-data-dir=test --unsafely-treat-insecure-origin-as-secure=http://localhost:<port from step 2>"
5. Go to http://localhost:<port from step 2>/_ah/api/explorer (example: http://localhost:8080/_ah/api/explorer ).  Reminder to allow the site to load unsecure scripts.   
6.  Go to http://localhost:<admin port from step 2>/console (example: http://localhost:8000/console) and select Cron to run the Cron job to send emails.  Reminder - The email account used in step 2 must be configured to allow access for less secure apps.  To configure this,  log in to your email account, then, go to https://www.google.com/settings/security/lesssecureapps.
 
##Game Description:
Tic-tac-toe is a e player game, X and O, who take turns marking the spaces in a 3×3 grid. 
Player X always starts the game.  The player who succeeds in placing three of their marks in a horizontal, vertical, or diagonal row wins the game.   

Here is an example game won by the first player, X:
_X_|___|_O_
___|_X_|_O_
   |   | X 

## Score keeping: 
- If a user wins a game, the user gets 1 point in number of wins.  Additionally,  number of moves on wins, winning percentage rate, and average game moves on winning games calculated at the end of the game for the player.  
- If a user loses a game, the user gets 1 point in number of loses. 
- If a game ends in a draw or a game is cancelled, scores remain the same for both players of the game.
- All sores are stored in User model.  

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.
 - index.yaml:  Contains indexes used by the application.
 - settings.py: Contains the web client ID of the project.


##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email  
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name  for x_user, user_name for o_user
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name of x_user and o_user must correspond to an
    existing user - will raise a NotFoundException if not. 
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/make_a_move/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, user_name, move
    - Returns: GameForm with new game state.
    - Description: Accepts game key, move, and user_name.  The game must still be active.  The user_name must exist, must be a player in the game, and must be the next play inline to play.  The move must be available in the game and must be between 0 to 8 which corresponds to the box in tic-tac-toe.  This end point check if the move wins the game.  If the game is won, user ranking is recorded.  Game history is recorded for every move.     
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_games**
    - Path: 'games/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: UserGameForms. 
    - Description: Returns all active games for user (unordered).
    Will raise a NotFoundException if the User does not exist.

 - **cancel_game**
    - Path: 'game/cancel_game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: GameForm with new game state.
    - Description: Cancels game by deleting game record and all other database records related to the game.

 - **get_user_rankings**
    - Path: 'user_rankings'
    - Method: GET
    - Parameters: None
    - Returns: UserRankingForms.
    - Description: Get ranking of all users order by Percentage of Winnings (descending), Number of Wins (descending), and Average game moves on winning games (asending).  Number of Wins is a tie breaker for players with the same Percentage of Winnings.  The player with more games played has a higher ranking.  As a second tie breaker, the player with less Average game moves on winning games has a higher ranking if plays have same Percentage of Winnings and Number of Wins.  User ranking is recorded when a game is won which is checked at make_move endpoint.   

 - **get_user_rankings**
    - Path: 'game/history/{urlsafe_game_key}'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage.
    - Description: Get all game history for every move made for the game.  History is recorded by make_move endpoint.  

##Models Included:
 - **User**
    - Stores unique user_name, email address, and performance ranking information. 
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **UserGame**
    - Records players of the games. Associated with Users model via KeyProperty and Games model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, game_over flag, game end date,   message, x_user name, o_user name, moves count, and game moves).
 - **GameForms**
    - Multiple GameForm container.
 - **NewGameForm**
    - Used to create a new game (x_user name and o_user name)
 - **MakeMoveForm**
    - Inbound make move form (user name and move).
 - **UserGameForm**
    - Representation of a completed game's Score (user_name, game, game over flag, win status, moves count).
 - **UserGameForms**
    - Multiple UserGameForm container.
 - **UserRankingForm**
    - Representation of ranking of users (user name, number of wins, number of loses, winning percentage rate, average game moves on winning games).
 - **UserRankingForms**
    - Multiple UserRankingForm container.
 - **StringMessage**
    - General purpose String container.