# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import logging
import endpoints
import re
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from settings import WEB_CLIENT_ID

from models import UserGame, User, Game  
from models import StringMessage, NewGameForm, GameForm, GameForms, \
    MakeMoveForm, UserGameForm, UserGameForms, UserRankingForm, UserRankingForms
from utils import get_by_urlsafe

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID
NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

MEMCACHE_MOVES = 'MOVES'

@endpoints.api(name='tictactoe', version='v1',
    allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
    scopes=[EMAIL_SCOPE])
class TicTacToeApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if not re.search(r'[\w.-]+@[\w.-]+.\w+',request.email):
            raise endpoints.ConflictException(
                    'Email address must be valid!')
        if User.query(User.name == request.user_name).fetch(keys_only=True):
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        x_user = User.query(User.name == request.x_user_name).get()
        o_user = User.query(User.name == request.o_user_name).get()
        if not x_user:
            raise endpoints.NotFoundException(
                    'X User with that name does not exist!')
        if not o_user:
            raise endpoints.NotFoundException(
                    'O User with that name does not exist!')
        game_moves = ['B','B','B','B','B','B','B','B','B']    
        game = Game.new_game(x_user.key, o_user.key, game_moves)
        return game.to_form('Good luck playing Guess a Number!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('You got game!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/make_a_move/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""

        # Checks if game request is valid
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')

        #  Checks if user request is valid
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'User with that name does not exist!')
        if user.key != game.x_user and user.key != game.o_user: 
            raise endpoints.NotFoundException(
                    'User is not a player of the game!')

        # Checks if move is valid    
        tmp_moves_count = game.moves_count + 1 
        if tmp_moves_count % 2 == 0 and user.key != game.o_user:  #Even move means o_user move
            msg = 'Move rejected.  Next move must be from o_user.'
            game.post_history(user.key, tmp_moves_count, request.move, msg)
            raise endpoints.NotFoundException(msg)
        if tmp_moves_count % 2 != 0 and user.key != game.x_user:  #Odd move means x_user move
            msg = 'Move rejected.  Next move must be from x_user.'
            game.post_history(user.key, tmp_moves_count, request.move, msg)
            raise endpoints.NotFoundException(msg)
        move_int = int(request.move)
        if move_int < 0 or move_int > 8:
            msg = 'Invalid row move! Choose 0 to 8.'
            game.post_history(user.key, tmp_moves_count, request.move, msg)
            raise endpoints.NotFoundException(msg)
        if game.game_moves[move_int] != 'B':
            msg = 'Move is not longer available.'
            game.post_history(user.key, tmp_moves_count, request.move, msg)
            return game.to_form(msg)

        # Process move        
        game.moves_count += 1 
        if user.key == game.x_user: 
            game.game_moves[move_int] = "X"
        else: 
            game.game_moves[move_int] = "O"   
        if self._check_winning_combination(game.game_moves):
            msg = 'You win!'
            game.post_history(user.key, game.moves_count, request.move, msg)
            winner = user.key
            game.end_game(winner)
            return game.to_form(msg)
        if game.moves_count >= 9:
            msg = 'Game over! No winner.'
            game.post_history(user.key, game.moves_count, request.move, msg)
            winner = ""
            game.end_game(winner)
            return game.to_form(msg)
        else:
            msg = 'No winner yet.  Good luck on your next move.'
            game.post_history(user.key, game.moves_count, request.move, msg)
            game.put()
            return game.to_form(msg)      


    def _check_winning_combination(self, game_moves):
      """Checks if the winning combination is found."""
      if game_moves[0] != 'B':
          if game_moves[0] == game_moves[1] and game_moves[0] == game_moves[2]:
              return True
          if game_moves[0] == game_moves[3] and game_moves[0] == game_moves[6]:
              return True    
          if game_moves[0] == game_moves[4] and game_moves[0] == game_moves[8]:
              return True

      if game_moves[1] != 'B':
          if game_moves[1] == game_moves[4] and game_moves[1] == game_moves[7]:
              return True

      if game_moves[2] != 'B':
          if game_moves[2] == game_moves[5] and game_moves[2] == game_moves[8]:
              return True

      if game_moves[3] != 'B':
          if game_moves[3] == game_moves[4] and game_moves[3] == game_moves[5]:
              return True        

      if game_moves[6] != 'B':
          if game_moves[6] == game_moves[7] and game_moves[6] == game_moves[8]:
              return True 
          if game_moves[6] == game_moves[4] and game_moves[6] == game_moves[2]:
              return True            
      return False          

    @endpoints.method(response_message=UserGameForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        usergames = UserGame.query(UserGame.game_over == True)
        return UserGameForms(items=[usergame.to_form() for usergame in usergames])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=UserGameForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        usergames = UserGame.query(UserGame.user == user.key, UserGame.game_over == True)
        return UserGameForms(items=[usergame.to_form() for usergame in usergames])

    @endpoints.method(response_message=StringMessage,
                      path='games/average_moves',
                      name='get_average_moves',
                      http_method='GET')
    def get_average_moves(self, request):
        """Get the cached average moves"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES) or '')

    @staticmethod
    def _cache_average_moves():
        """Populates memcache with the average moves of active Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_moves = sum([game.moves_count for game in games])
            average = float(total_moves)/count
            memcache.set(MEMCACHE_MOVES,
                         'The average moves is {:.2f}'.format(average))

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=UserGameForms,
                      path='games/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all active games of user"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        usergames = UserGame.query(UserGame.user == user.key, UserGame.game_over == False)
        return UserGameForms(items=[usergame.to_form() for usergame in usergames])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/cancel_game/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """Cancel game."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        if game.game_over:     
            raise endpoints.NotFoundException('Can not cancel game.  Game is over.')

        game.cancel_game()
        return game.to_form('Game cancelled!')

    @endpoints.method(response_message=UserRankingForms,
                      path='user_rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Get user rankings."""
        users = User.query().order(-User.winning_percentage_rate, -User.nbr_wins, User.average_game_moves_on_winning_games)
        return UserRankingForms(items=[user.rank_form() for user in users])   

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/history/{urlsafe_game_key}',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Get history of game."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.history: 
                return StringMessage(message=str(game.history))
            else:
                return StringMessage('No game history found.')     
        else:
            raise endpoints.NotFoundException('Game not found!')    

api = endpoints.api_server([TicTacToeApi])
