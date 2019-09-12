from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
# import requests
# from bs4 import BeautifulSoup
# import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

# DB
engine = create_engine("sqlite:///private/user_id.db", echo=True)
base = declarative_base()

# ORM
class User(base):
    __tablename__ = "User"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    subscribe = Column(Boolean)

base.metadata.create_all(engine)

# base.metadata.drop_all(bind=engine, tables=[User.__table__])

Session = sessionmaker(bind=engine)
session = Session()

# Token Read
with open("private/token.txt", 'r') as fp:
    my_token = fp.read()

updater = Updater(token=my_token, use_context=False)

# chat-bot
def start_command(bot, update):
    user_id = update.message.chat.id
    username = update.message.chat.username
    last_name = update.message.chat.last_name
    first_name = update.message.chat.first_name

    if not user_id in session.query(User.user_id):
        session.add(
            User(
                user_id=user_id,
                username=username,
                last_name=last_name,
                first_name=first_name,
                subscribe=False
            )
        )
        session.commit()

    update.message.reply_text("반갑습니다! 무엇을 도와드릴까요?")

start_handler = CommandHandler("start", start_command)


def get_message(bot, update):
    update.message.reply_text("서울특별시빅데이터캠퍼스 공지사항 수신을 하시려면 \"/subscribe 수신\", " + \
                              "공지사항을 수신하지 않으시려면 \"/unsubscribe\"라고 말씀해주세요." + \
                                "\n 이외 기능은 준비 중입니다.")

message_handler = MessageHandler(Filters.text, get_message)

def subscribe_command(bot, update):
    """요청하는 사용자를 공지사항 수신 신청합니다."""
    user_id=update.message.chat.id
    subs = session.query(User.subscribe).filter(User.user_id == user_id)
    if subs.first()[0] == False:
        subs.update({User.subscribe:True})
        session.commit()
        update.message.reply_text("서울특별시빅데이터캠퍼스 공지사항 수신을 시작합니다.")

    else:
        update.message.reply_text("이미 서울특별시빅데이터캠퍼스 공지사항 수신을 신청하셨습니다.")


subscribe_command = CommandHandler("subscribe", subscribe_command)


def unsubscribe_command(bot, update):
    """요청하는 사용자를 공지사항 수신 거부 처리합니다.
       아직 공지사항 수신을 신청하지 않은 사용자에게는 수신 신청이 되어있지 않다는 메시지를 보냅니다."""
    user_id = update.message.chat.id
    subs = session.query(User.subscribe).filter(User.user_id == user_id)
    if subs.first()[0] == True:
        subs.update({User.subscribe:False})
        session.commit()
        update.message.reply_text("서울특별시빅데이터캠퍼스 공지사항 수신을 종료합니다.")
    else:
        update.message.reply_text("아직 서울특별시빅데이터캠퍼스 공지사항 수신 신청이 되어있지 않습니다.")


unsubscribe_command = CommandHandler("unsubscribe", unsubscribe_command)


updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(message_handler)
updater.dispatcher.add_handler(subscribe_command)
updater.dispatcher.add_handler(unsubscribe_command)


def main():
    updater.start_polling(timeout=3, clean=True)
    updater.idle()


if __name__ == "__main__":
    main()