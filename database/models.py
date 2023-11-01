from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from config import DB_URL


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_username = Column(String, unique=True, nullable=False)


class University(Base):
    __tablename__ = 'universities'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class Subject(Base):
    __tablename__ = 'subjects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    university_id = Column(Integer, ForeignKey('universities.id'))
    university = relationship('University', backref='subjects')


class Teacher(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    telegram_username = Column(String, unique=True, nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    subject = relationship('Subject', backref='teachers')

    profile_photo = relationship('ProfilePhoto', uselist=False, backref='teacher')
    review_photos = relationship('ReviewPhoto', backref='teacher')


class ProfilePhoto(Base):
    __tablename__ = 'profile_photos'
    id = Column(Integer, primary_key=True)
    image_data = Column(LargeBinary, nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id'))


class ReviewPhoto(Base):
    __tablename__ = 'review_photos'
    id = Column(Integer, primary_key=True)
    image_data = Column(LargeBinary, nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id'))


engine = create_engine(DB_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
