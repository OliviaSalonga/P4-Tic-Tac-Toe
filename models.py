"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    nbr_wins = ndb.IntegerProperty(required=True, default=0)
    nbr_loses = ndb.IntegerProperty(required=True, default=0)
    nbr_of_moves_on_wins = ndb.IntegerProperty(required=True, default=0)
    winning_percentage_rate = ndb.FloatProperty(required=True, default=0)
    average_game_moves_on_winning_games = ndb.FloatProperty(required=True, default=0)

    def rank_form(self):
        """Returns user rankings"""
        form = UserRankingForm()
        form.name = self.name
        form.nbr_wins = self.nbr_wins
        form.nbr_loses = self.nbr_loses
        form.winning_percentage_rate = self.winning_percentage_rate
        form.average_game_moves_on_winning_games = self.average_game_moves_on_winning_games 
        return form

class UserGame(ndb.Model):
    """User Games"""
    user = ndb.KeyProperty(required=True, kind='User')
    game_key = ndb.KeyProperty(required=True, kind='Game')
    game_over = ndb.BooleanProperty(required=True, default=False)
    win_status = ndb.StringProperty()
    moves_count = ndb.IntegerProperty()

    def to_form(self):
        """Returns user's game infromation"""
        form = UserGameForm()
        form.user_name = self.user.get().name
        form.game_key = self.game_key.urlsafe()
        form.game_over = self.game_over
        form.win_status = self.win_status
        moves_count = self.moves_count
        return form


class Game(ndb.Model):
    """Game object"""
    game_over = ndb.BooleanProperty(required=True, default=False)
    game_moves = ndb.StringProperty(repeated=True)
    x_user = ndb.KeyProperty(required=True, kind='User')
    o_user = ndb.KeyProperty(required=True, kind='User')
    moves_count = ndb.IntegerProperty(required=True)
    game_end_date = ndb.DateProperty()
    history = ndb.PickleProperty(default=[])

    @classmethod
    def new_game(cls, x_user, o_user, game_moves):
        """Creates and returns a new game"""
        game = Game(x_user=x_user,
                    o_user=o_user,
                    game_moves=game_moves,
                    moves_count=0,
                    game_over=False)
        game.put()
        usergame = UserGame(user=x_user, 
                            game_key=game.key,
                            moves_count=0,
                            game_over=False)
        usergame.put()
        usergame = UserGame(user=o_user, 
                            game_key=game.key,
                            moves_count=0,
                            game_over=False)
        usergame.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.x_user_name = self.x_user.get().name
        form.o_user_name = self.o_user.get().name
        form.moves_count = self.moves_count
        form.game_moves = self.game_moves
        form.game_over = self.game_over
        form.game_end_date = str(self.game_end_date)
        form.message = message
        return form

    def end_game(self, winner):
        """Ends the game"""
        items = UserGame.query(UserGame.game_key == self.key)  
        for item in items:
            if (winner):
                user = User.query(User.key == item.user).get()
                if (winner == item.user): 
                    item.win_status = "WIN"
                    user.nbr_wins = user.nbr_wins + 1
                    user.nbr_of_moves_on_wins += self.moves_count
                    user.average_game_moves_on_winning_games = (user.nbr_of_moves_on_wins / user.nbr_wins)
                else:
                    item.win_status = "LOSE"
                    user.nbr_loses = user.nbr_loses + 1
                user.winning_percentage_rate = (user.nbr_wins/(user.nbr_wins + user.nbr_loses)) * 100.0
                user.put()
            else:
                item.win_status = "DRAW"           
            item.moves_count = self.moves_count
            item.game_over = True
            item.put() 
             
        self.game_over = True
        self.game_end_date = date.today()
        self.put()

    def cancel_game(self):
        """Cancel's game by deleting records of the game"""
        ndb.delete_multi(UserGame.query(UserGame.game_key == self.key).fetch(keys_only=True))    

        k = self.key
        k.delete()

    def post_history(self, user, moves_count, move, message):
        """Records game history"""
        self.history.append({'date': date.today(), 
                             'user': user,
                             'moves_count': moves_count,
                             'move': move,
                             'message': message})
        self.put()


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    game_over = messages.BooleanField(2, required=True)
    game_end_date = messages.StringField(3)
    message = messages.StringField(4, required=True)
    x_user_name = messages.StringField(5, required=True)
    o_user_name = messages.StringField(6, required=True)
    moves_count = messages.IntegerField(7)
    game_moves = messages.StringField(8, repeated=True)

class GameForms(messages.Message):
    """Return multiple GameForm"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    x_user_name = messages.StringField(1, required=True)
    o_user_name = messages.StringField(2, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    user_name = messages.StringField(1, required=True)
    move = messages.IntegerField(2, required=True)


class UserGameForm(messages.Message):
    """User to provide information about user's games"""
    user_name = messages.StringField(1, required=True)
    game_key = messages.StringField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    win_status = messages.StringField(4)
    moves_count = messages.IntegerField(5)


class UserGameForms(messages.Message):
    """Return multiple UserGameForm"""
    items = messages.MessageField(UserGameForm, 1, repeated=True)


class UserRankingForm(messages.Message):
    """UserRanking for outbound user's games information"""
    name = messages.StringField(1, required=True)
    nbr_wins = messages.IntegerField(2)
    nbr_loses = messages.IntegerField(3)
    winning_percentage_rate = messages.FloatField(4)
    average_game_moves_on_winning_games = messages.FloatField(5)


class UserRankingForms(messages.Message):
    """Return multiple UserRankingForm"""
    items = messages.MessageField(UserRankingForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
