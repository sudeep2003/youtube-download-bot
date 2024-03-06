#!/usr/bin/env python
# pylint: disable=unused-argument

import logging
import os

from dotenv import load_dotenv
from pytube import YouTube, extract
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    filters,
    PicklePersistence,
    ConversationHandler)

load_dotenv()
TOKEN = os.getenv('TOKEN')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

URLL, SELECT = range(2)


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        f"Hello {update.effective_user.first_name}!\n\nTo download audio from a Youtube video:\n1. Send '/download'\n2. Send the Youtube video url\n3. Select the audio stream to download.\nor\nSend '/cancel' to cancel the operation.",
        reply_markup=ReplyKeyboardMarkup(
            [['/download']], one_time_keyboard=True
        ))
    print(f"{update.effective_user.first_name} --> starting")


async def get_url(update: Update, context: CallbackContext):
    print(f"{update.effective_user.first_name} --> getting url")
    await update.message.reply_text("Send your Youtube Video url:", reply_markup=ReplyKeyboardRemove())
    return URLL


async def download_audio(update: Update, context: CallbackContext):
    print(f"{update.effective_user.first_name} --> downloading audio")
    url = update.message.text
    # print(url)
    # video_id = ""
    try:
        video_id = extract.video_id(url)
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Invalid url. Try again.")
        print(f'An error occurred while extracting the video ID: {e}')
        return ConversationHandler.END
    # print(video_id)
    if video_id is None:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Unable to extract audio from the URL.")
        return ConversationHandler.END

    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="Founding the audio steams...")
    yt = YouTube(f"https://youtube.com/watch?v={video_id}")
    audio_streams = yt.streams.filter(only_audio=True)
    # print(audio_streams)
    if not audio_streams:
        await context.bot.send_message(chat_id=chat_id, text="No audio streams available for this video.")
        return ConversationHandler.END

    await context.bot.send_message(chat_id=chat_id, text=f"Select audio stream (1-{len(audio_streams)}):\n" + "\n".join(
        f"{i + 1}. {stream.abr} kbps - {stream.default_filename}" for i, stream in enumerate(audio_streams)),
                                   reply_markup=ReplyKeyboardMarkup(
                                       [[str(i + 1) for i in range(len(audio_streams))]], one_time_keyboard=True
                                   ))
    context.user_data["audio_streams"] = audio_streams
    context.user_data["chat_id"] = chat_id
    return SELECT


async def select_audio_stream(update: Update, context: CallbackContext):
    print(f"{update.effective_user.first_name} --> selecting audio stream")
    try:
        msg = update.message.text
        # print(msg)
        stream_num = int(msg)
        audio_streams = context.user_data["audio_streams"]
        if 1 <= stream_num <= len(audio_streams):
            context.user_data["stream_num"] = stream_num
            await context.bot.send_message(chat_id=context.user_data["chat_id"], text="Downloading audio...",
                                           reply_markup=ReplyKeyboardRemove())
            audio_stream = audio_streams[stream_num - 1]
            audio_file = audio_stream.download(output_path="./download", )
            await context.bot.send_audio(chat_id=context.user_data["chat_id"], audio=open(audio_file, "rb"))
            os.remove(audio_file)
            await context.bot.send_message(chat_id=context.user_data["chat_id"],
                                           text="Message downloaded and sent successfully.",
                                           reply_markup=ReplyKeyboardMarkup([['/download']], one_time_keyboard=True))
            print(f"{update.effective_user.first_name} --> downloaded")
            del context.user_data["audio_streams"]
            del context.user_data["chat_id"]
            del context.user_data["stream_num"]
            return ConversationHandler.END
        else:
            await context.bot.send_message(chat_id=context.user_data["chat_id"], text="Invalid stream number.")
    except ValueError:
        await context.bot.send_message(chat_id=context.user_data["chat_id"], text="Invalid input.")
    except Exception as e:
        await context.bot.send_message(chat_id=context.user_data["chat_id"], text="Error: %s" % str(e))

    await update.message.reply_text("Send your Youtube Video url:", reply_markup=ReplyKeyboardRemove())
    return URLL


async def cancel(update: Update, context: CallbackContext):
    print(f"{update.effective_user.first_name} --> cancelling")
    user_data = context.user_data
    chat_id = user_data.get("chat_id")
    if chat_id:
        await context.bot.send_message(chat_id=chat_id, text="Operation cancelled.", reply_markup=ReplyKeyboardMarkup(
            [['/download']], one_time_keyboard=True
        ))
    if "audio_streams" in user_data:
        del user_data["audio_streams"]
    if "chat_id" in user_data:
        del user_data["chat_id"]
    if "stream_num" in user_data:
        del user_data["stream_num"]
    return ConversationHandler.END


def main():
    persistence = PicklePersistence(filepath="audioDownloadingBot")
    application = Application.builder().token(TOKEN).concurrent_updates(True).persistence(persistence).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("download", get_url)],
        states={
            URLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio)],
            SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_audio_stream)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="my_conversation",
        persistent=True,
    ))
    application.run_polling()


if __name__ == '__main__':
    main()
