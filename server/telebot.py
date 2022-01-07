import re
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
        pattern = r"\/subscribe\s*(\w*)"
        try:
            learn_id = re.search(pattern, update.message.text).group(1)
            msg = data_store.add_subscriber(
                learn_id, update.message.from_user.name)
            update.message.reply_text(msg)

            if "is now subscribed" in msg:
                cb_context.job_queue.run_repeating(
                    self.send_update, 1800,
                    context=[update.message.chat_id, learn_id],
                    name=f"sub{update.message.from_user.name}{learn_id}"
                )
        except:
            update.message.reply_text("Error with your message")

    def unsubscribe(self, update: Update, cb_context: CallbackContext):
        pattern = r"\/unsubscribe\s*(\w*)"
        try:
            learn_id = re.search(pattern, update.message.text).group(1)
            msg = data_store.del_subscriber(
                learn_id,
                update.message.from_user.name
            )
            update.message.reply_text(msg)

            jobs = cb_context.job_queue.get_jobs_by_name(
                f"sub{update.message.from_user.name}{learn_id}")

            for job in jobs:
                job.schedule_removal()

        except:
            update.message.reply_text("Error with your message")

    def get_update(self, update: Update, cb_context: CallbackContext):
        pattern = r"\/update\s*(\w*)"
        try:
            learn_id = re.search(pattern, update.message.text).group(1)
            msg = data_store.get_learning_state(learn_id)
            update.message.reply_text(msg)
        except:
            update.message.reply_text("Error with your message")

    def send_update(self, cb_context: CallbackContext):
        chat_id, learn_id = cb_context.job.context

        state = data_store.get_learning_state(learn_id)

        if not state == "":
            cb_context.bot.send_message(chat_id=chat_id, text=state)
        else:
            print("Empty state")


bot = TeleBot()
bot.start()
