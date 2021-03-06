import re
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext


import data_store

POSTMAN_TOKEN = "5021417711:AAGaKk3OkyKeuIfTxONoO-69tcLYJOAIA4g"


class TeleBot():
    def __init__(self):
        self.updater = Updater(POSTMAN_TOKEN)

        self.updater.dispatcher.add_handler(
            CommandHandler("subscribe", self.subscribe, pass_job_queue=True))
        self.updater.dispatcher.add_handler(
            CommandHandler("unsubscribe", self.unsubscribe, pass_job_queue=True))
        self.updater.dispatcher.add_handler(
            CommandHandler("update", self.get_update))

    def start(self):
        self.updater.start_polling()
        self.updater.idle()

    def subscribe(self, update: Update, cb_context: CallbackContext):
        """Called when telegram receives the "/subscribe" command
           Adds user who sent it to the subscribers list, notifying
           them of the latest info received every 15 minutes 

        Args:
            update (Update): The message received on Telegram
            cb_context (CallbackContext): Context to be passed into repeating method
        """

        pattern = r"\/subscribe\s*(\d+)(\s\d+)?"
        try:
            chat_id = update.message.chat_id
            search = re.search(pattern, update.message.text)
            learn_id = search.group(1)
            msg = data_store.add_subscriber(learn_id, chat_id)

            if "is now subscribed" in msg:
                interval = (int(search.group(2))
                            if search.group(2) else 15) * 60

                cb_context.job_queue.run_repeating(
                    self.send_update, interval,
                    context=[chat_id, learn_id],
                    name=f"sub{chat_id}{learn_id}"
                )

            update.message.reply_text(msg)

        except:
            update.message.reply_text("Error with your message")

    def unsubscribe(self, update: Update, cb_context: CallbackContext):
        """Called when telegram receives the "/unsubscribe" command
           Removes user who sent it from the subscribers list, stopping
           notifications of the latest info received every 30 minutes 

        Args:
            update (Update): The message received on Telegram
            cb_context (CallbackContext): Context to be passed into repeating method
        """
        pattern = r"\/unsubscribe\s*(\w*)"
        try:
            learn_id = re.search(pattern, update.message.text).group(1)
            chat_id = update.message.chat_id

            msg = data_store.del_subscriber(learn_id, chat_id)
            update.message.reply_text(msg)

            jobs = cb_context.job_queue.get_jobs_by_name(
                f"sub{chat_id}{learn_id}")

            for job in jobs:
                job.schedule_removal()

        except:
            update.message.reply_text("Error with your message")

    def get_update(self, update: Update, cb_context: CallbackContext):
        """Called when telegram receives the "/update" command
           Sends the user the latest info received from training

        Args:
            update (Update): The message received on Telegram
            cb_context (CallbackContext): Context to be passed into repeating method
        """

        pattern = r"\/update\s*(\w*)"
        try:
            learn_id = re.search(pattern, update.message.text).group(1)
            msg = data_store.get_learning_state(learn_id)
            update.message.reply_text(msg)
        except:
            update.message.reply_text("Error with your message")

    def send_update(self, cb_context: CallbackContext):
        """Repeating method, will call itself every 30 minutes if user subscribes
           to a particular learning session

        Args:
            cb_context (CallbackContext): Context passed from subscribe() method
        """

        chat_id, learn_id = cb_context.job.context
        state = data_store.get_learning_state(learn_id)

        if not state == "":
            cb_context.bot.send_message(chat_id=chat_id, text=state)
        else:
            cb_context.bot.send_message(
                chat_id=chat_id,
                text="There have been no updates"
            )

    @staticmethod
    def end_session(learn_id: str):
        MSG_TEMPLATE = f"https://api.telegram.org/bot{POSTMAN_TOKEN}/sendMessage"
        subscribers = data_store.get_subscribers(learn_id)

        for chat_id in subscribers:
            requests.post(MSG_TEMPLATE, data={
                "chat_id": chat_id,
                "text": f"Learning session {learn_id} has ended"
            })


if __name__ == "__main__":
    bot = TeleBot()
    bot.start()
