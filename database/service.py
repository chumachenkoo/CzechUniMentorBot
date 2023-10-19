from database.models import User, University, Teacher, Subject, Session
import asyncpg
from config import DB_URL


async def get_database_connection():
    connection = await asyncpg.connect(DB_URL)
    session = Session()
    return connection, session


async def create_user(telegram_id):
    connection, session = await get_database_connection()

    try:
        new_user = User(telegram_id=telegram_id)
        session.add(new_user)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        await connection.close()


async def add_university(name):
    connection, session = await get_database_connection()
    try:
        new_university = University(name=name)
        session.add(new_university)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        await connection.close()


async def add_subject(subject_name, university_id):
    connection, session = await get_database_connection()
    try:
        new_subject = Subject(name=subject_name, university_id=university_id)
        session.add(new_subject)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        await connection.close()


async def add_teacher(teacher_name, telegram_id, subject_id):
    connection, session = await get_database_connection()
    try:
        new_teacher = Teacher(name=teacher_name, telegram_id=telegram_id, subject_id=subject_id)
        session.add(new_teacher)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        await connection.close()


async def get_all_universities():
    all_universities = []
    connection, session = await get_database_connection()

    try:
        universities = session.query(University).all()
        for uni in universities:
            all_universities.append((uni.name, uni.id))
        return all_universities
    finally:
        await connection.close()
        session.close()


async def get_all_teachers():
    all_teachers = []
    connection, session = await get_database_connection()

    try:
        teachers = session.query(Teacher).all()
        for teacher in teachers:
            all_teachers.append((teacher.name, teacher.id, teacher.telegram_id, teacher.subject_id))
        return all_teachers
    finally:
        await connection.close()
        session.close()


async def get_all_subjects():
    all_subjects = []
    connection, session = await get_database_connection()

    try:
        subjects = session.query(Subject).all()
        if subjects:
            for subject in subjects:
                all_subjects.append((subject.name, subject.id, subject.university_id))
            return all_subjects
        else:
            return []
    finally:
        await connection.close()
        session.close()


async def get_university_by_name(name):
    connection, session = await get_database_connection()

    try:
        university = session.query(University).filter(University.name == name).first()
        if university:
            return university.id
        else:
            return None
    finally:
        await connection.close()
        session.close()


async def get_subjects_by_university(university_id):
    subjects_by_teacher = []
    connection, session = await get_database_connection()

    try:
        subjects = session.query(Subject).filter(Subject.university_id == university_id).all()
        if subjects:
            for subject in subjects:
                subjects_by_teacher.append((subject.name, subject.id, subject.university_id))
            return subjects_by_teacher
        else:
            return []
    finally:
        await connection.close()
        session.close()


async def get_teachers_by_subject(subject_id):
    teachers_by_subject = []
    connection, session = await get_database_connection()

    try:
        teachers = session.query(Teacher).filter(Teacher.subject_id == subject_id).all()
        if teachers:
            for teacher in teachers:
                teachers_by_subject.append((teacher.name, teacher.id, teacher.telegram_id, teacher.subject_id))
            return teachers_by_subject
        else:
            return []
    finally:
        await connection.close()
        session.close()


async def delete_subject(subject_id):
    connection, session = await get_database_connection()

    try:
        subject = session.query(Subject).filter(Subject.id == subject_id).first()
        if subject:
            session.delete(subject)
            session.commit()
        else:
            raise ValueError(f"Subject with ID {subject_id} not found.")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        await connection.close()


async def delete_university_by_id(university_id):
    connection, session = await get_database_connection()

    try:
        university = session.query(University).filter(University.id == university_id).first()
        if university:
            session.delete(university)
            session.commit()
            return True
        else:
            raise ValueError(f"University with ID {university_id} not found.")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        await connection.close()


async def delete_teacher(teacher_id):
    connection, session = await get_database_connection()

    try:
        teacher = session.query(Teacher).filter(Teacher.id == teacher_id).first()
        if teacher:
            session.delete(teacher)
            session.commit()
            return True
        else:
            raise ValueError(f"Teacher with ID {teacher_id} not found.")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        await connection.close()

