#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import TicTacToeApi

from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to Users when it is thier turn to make a move.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        games = Game.query(Game.game_over == False)
        for game in games: 
            if (game.moves_count + 1) % 2 == 0: # o_user is the next move
                user_to_email = game.o_user
                opponent_user = game.x_user
            else: # x_user is the next move     
                user_to_email = game.x_user
                opponent_user = game.o_user
            user = User.query(User.key == user_to_email).get()
            opponent = User.query(User.key == opponent_user).get()
            subject = 'This is a reminder!'
            if game.moves_count == 0:
                body = 'Hello {}, Make your first move!'.format(user.name) 
            else:
                body = 'Hello {}, {} just made move.  It is your turn to win the game!'.format(user.name, opponent.name)
            # This will send test emails, the arguments to send_mail are:
            # from, to, subject, body
            mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user.email,
                           subject,
                           body)

class UpdateAverageMoves(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        TicTacToeApi._cache_average_moves()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_moves', UpdateAverageMoves),
], debug=True)
