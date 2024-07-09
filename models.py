from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker



Base = declarative_base()


class Users(Base):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    chat_id = Column(Integer, unique=True)

    def __str__(self):
        return f'{self.id} ({self.username}) : {self.first_name} {self.last_name}'


class Words(Base):
    __tablename__ = 'Words'

    id = Column(Integer, primary_key=True)
    target_word = Column(String(50), nullable=False)
    russian_word = Column(String(50), nullable=False)

    def __str__(self):
        return f'{self.id} ({self.russian_word}): {self.target_word} '


class UserWords(Base):
    __tablename__ = 'UserWords'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('Users.id', ondelete='CASCADE'), nullable=False)
    word_id = Column(Integer, ForeignKey('Words.id', ondelete='CASCADE'), nullable=False)

    user = relationship('Users', backref='words')
    word = relationship('Words', backref='users')

    def __str__(self):
        return f'{self.id} ({self.user_id}): {self.word_id}'
    

def create_tables(engine):
    Base.metadata.create_all(engine)
    print('Таблицы созданы')

def drop_tables(engine):
    Base.metadata.drop_all(engine)
    print('Таблицы удалены')

def fill_words(session, user__id):
    words_data = [
        {'target_word': 'World', 'russian_word': 'Мир 🌍'},
        {'target_word': 'Green', 'russian_word': 'Зеленый 🟢'},
        {'target_word': 'Car', 'russian_word': 'Машина 🚗'},
        {'target_word': 'Tree', 'russian_word': 'Дерево 🌳'},
        {'target_word': 'Hello', 'russian_word': 'Привет 👋'},
        {'target_word': 'Goodbye', 'russian_word': 'Прощай 👋'},
        {'target_word': 'House', 'russian_word': 'Дом 🏠'},
        {'target_word': 'Cat', 'russian_word': 'Кошка 🐱'},
        {'target_word': 'Dog', 'russian_word': 'Собака 🐶'},
        {'target_word': 'Bird', 'russian_word': 'Птица 🐦'},
    ]

    # Добавляем слова в таблицу Words
    for word_data in words_data:
        word = Words(**word_data)
        session.add(word)
        session.commit()
        user_word = UserWords(user_id=user__id, word_id=word.id)
        session.add(user_word)

    # Получение всех слов из таблицы Words
    # words = session.query(Words).all()
    # print()


    # Связываем слова с текущим пользователем
    # for word in words:
    #     user_word = UserWords(user_id=user__id, word_id=word.id)
    #     session.add(user_word)

    session.commit()
    print('В базу данных добавлено 10 слов')