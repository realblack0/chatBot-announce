from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker
import requests
from bs4 import BeautifulSoup
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import logging
from datetime import datetime
import re


# DB
engine = create_engine("sqlite:///private/user_id.db", echo=True)
base = declarative_base()

# DB reset
# base.metadata.drop_all(bind=engine, tables=[Content.__table__])
# engine.execute("DROP TABLE IF EXISTS content;")

# ORM
class User(base):
    __tablename__ = "User"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    subscribe = Column(Boolean)

class Content(base):
    __tablename__ = "Content"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    datetime = Column(DateTime(timezone=True), default=datetime.utcnow)


base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


# Token Read
with open("private/token.txt", 'r') as fp:
    my_token = fp.read()

updater = Updater(token=my_token, use_context=True)


# logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# chat-bot
def start_command(update, context):
    print("/start")
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="처리중입니다.")

    user_id = update.message.chat.id
    username = update.message.chat.username
    last_name = update.message.chat.last_name
    first_name = update.message.chat.first_name

    session = Session()
    if not (user_id,) in session.query(User.user_id).all():
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

    context.bot.send_message(chat_id=user_id,
        text="반갑습니다! 무엇을 도와드릴까요?")

start_handler = CommandHandler("start", start_command)


def get_message(update, context):
    context.bot.send_message(chat_id=update.message.chat.id,
                             text="서울특별시빅데이터캠퍼스 공지사항 수신을 하시려면 \"/subscribe\", " + \
                              "공지사항을 수신하지 않으시려면 \"/unsubscribe\"라고 말씀해주세요." + \
                                "\n 이외 기능은 준비 중입니다.")

message_handler = MessageHandler(Filters.text, get_message)

def subscribe_command(update, context):
    """요청하는 사용자를 공지사항 수신 신청합니다."""
    print("/subscribe")
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="처리중입니다.")

    user_id = update.message.chat.id
    session = Session()
    subs = session.query(User.subscribe).filter(User.user_id == user_id)
    if subs.first()[0] == False:
        subs.update({User.subscribe:True})
        session.commit()
        context.bot.send_message(chat_id=user_id,
                                 text="서울특별시빅데이터캠퍼스 공지사항 수신을 시작합니다.")

    else:
        context.bot.send_message(chat_id=user_id,
                                 text="이미 서울특별시빅데이터캠퍼스 공지사항 수신을 신청하셨습니다.")


    context.bot.send_message(chat_id=user_id,
                             text="처리완료되었습니다.")

subscribe_command = CommandHandler("subscribe", subscribe_command)


def unsubscribe_command(update, context):
    """요청하는 사용자를 공지사항 수신 거부 처리합니다.
       아직 공지사항 수신을 신청하지 않은 사용자에게는 수신 신청이 되어있지 않다는 메시지를 보냅니다."""
    print("/unsubscribe")
    context.bot.send_message(chat_id=update.message.chat.id,
                             text="처리중입니다.")
    user_id = update.message.chat.id

    session = Session()
    subs = session.query(User.subscribe).filter(User.user_id == user_id)
    if subs.first()[0] == True:
        subs.update({User.subscribe:False})
        session.commit()
        context.bot.send_message(chat_id=user_id,
                                     text="서울특별시빅데이터캠퍼스 공지사항 수신을 종료합니다.")
    else:
        context.bot.send_message(chat_id=user_id,
                                 text="아직 서울특별시빅데이터캠퍼스 공지사항 수신 신청이 되어있지 않습니다.")

    context.bot.send_message(chat_id=user_id,
                             text="처리완료되었습니다.")


unsubscribe_command = CommandHandler("unsubscribe", unsubscribe_command)





# Crawler
def check_update(context):
    session = Session()
    url = "https://bigdata.seoul.go.kr/noti/selectPageListNoti.do?r_id=P710"
    previous = session.query(Content.title).order_by(Content.id.desc()).first()

    resp = requests.request("get", url)
    dom = BeautifulSoup(resp.text, "lxml")
    current = dom.select_one(".board_title > a").text.strip()
    if not previous == (current,):
        params = {
            "r_id": "P710",
              "bbs_seq": re.findall(r"fnDetail\('(.+)'\)", dom.select_one(".board_title > a")["onclick"])[0]
        }
        content_url = "?".join([
            "https://bigdata.seoul.go.kr/noti/selectNoti.do",
            requests.compat.urlencode(params)
        ])
        session.add(Content(title=current,
                            url=content_url))
        session.commit()
        for user_id in session.query(User.user_id).filter(User.subscribe==True):
            context.bot.send_message(chat_id=user_id[0],
                text="서울특별시빅데이터캠퍼스에 새로운 공지사항이 게시되었습니다.\n[{}]\n{}".format(current, content_url))


def main():
    j = updater.job_queue
    j.run_repeating(check_update, interval=60, first=0)

    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(message_handler)
    updater.dispatcher.add_handler(subscribe_command)
    updater.dispatcher.add_handler(unsubscribe_command)

    updater.start_polling(timeout=3, clean=True)
    updater.idle()


if __name__ == "__main__":
    main()