from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
import config
import database.service as db
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import io

bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


class States(StatesGroup):
    uni_name = State()
    main_menu = State()
    universities = State()
    teachers = State()
    subjects = State()
    add_university = State()
    add_teacher = State()
    delete_university = State()
    delete_teacher = State()
    delete_subject = State()
    selected_university = State()
    selected_teacher = State()
    selected_subject = State()
    change_university_name = State()
    add_subject_to_university = State()
    delete_subject_from_university = State()
    add_teacher_to_subject = State()
    add_profile_photo = State()
    add_review_photo = State()

    user_universities = State()
    selected_user_university = State()
    selected_user_subject = State()
    selected_user_teacher = State()


# ______________________________________________________________________________________________________________________
# Логика для админа: Базовые кнопки
@dp.message_handler(commands=['start'], state="*")
async def on_start(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["current_state"] = States.main_menu.state
    await States.main_menu.set()

    if message.from_user.id in config.ADMINS:
        if message.text == "/start":
            text = f"Привет, администратор {message.from_user.first_name}! Я бот MentorBot :)"
        else:
            text = "Вы вернулись назад :)"
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Университеты")
        button2 = types.KeyboardButton("Учителя")
        button3 = types.KeyboardButton("Предметы")
        keyboard.add(button1, button2, button3)
        await message.answer(text, reply_markup=keyboard)
    else:
        if message.text == "/start":
            text = (f"Привет, {message.from_user.first_name}! Я бот MentorBot :)\n"
                    f"Я помогу тебе найти учителя по предмету, который ты изучаешь в университете.\n"
                    f"Нажми на 'Выбрать университет', чтобы начать.")
            user = await db.get_user_by_username(message.from_user.username)
            if user is None:
                await db.create_user(message.from_user.username)

        else:
            text = "Хочешь еще поискать учителя? Нажимай 'Выбрать университет' :)"

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Выбрать университет")
        keyboard.add(button1)
        await message.answer(text, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Назад", state="*")
async def get_back(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        previous_state = data.get("previous_state")

        if previous_state == States.main_menu.state or previous_state is None:
            await on_start(message, state=state)


@dp.message_handler(lambda message: message.text == "Университеты", state="*")
async def get_universities(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.main_menu.state
        await States.universities.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить университет")
        button2 = types.KeyboardButton("Назад")
        keyboard.add(button1, button2)

        universities = await db.get_all_universities()
        if universities:
            universities_text = "Список университетов:\n"
            for university in universities:
                keyboard.add(types.KeyboardButton(university[0]))
            await message.answer(universities_text, reply_markup=keyboard)
        else:
            await message.answer("Список университетов пуст.", reply_markup=keyboard)
    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Учителя", state="*")
async def get_teachers(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.main_menu.state
        await States.teachers.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        teachers = await db.get_all_teachers()
        if teachers:
            teachers_text = "Список учителей:\n"
            for teacher in teachers:
                keyboard.add(types.KeyboardButton(teacher[0]))

            await message.answer(teachers_text, reply_markup=keyboard)
        else:
            await message.answer("Список учителей пуст.", reply_markup=keyboard)
    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Предметы", state="*")
async def get_subjects(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.main_menu.state
        await States.subjects.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        subjects = await db.get_all_subjects()
        if subjects:
            subjects_text = "Список предметов:\n"
            seen_subjects = set()
            for subject in subjects:
                if subject[0] not in seen_subjects:
                    keyboard.add(types.KeyboardButton(subject[0]))
                    seen_subjects.add(subject[0])

            await message.answer(subjects_text, reply_markup=keyboard)
        else:
            await message.answer("Список предметов пуст.", reply_markup=keyboard)
    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Отзывы", state=[States.selected_user_teacher, States.selected_teacher])
async def get_reviews(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        teacher_name = data["selected_teacher"]
        selected_teacher_id = data["selected_teacher_id"]
        data["previous_state"] = States.main_menu.state

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton("Назад")
    keyboard.add(button)

    teacher_text = f'Отзывы учителя {teacher_name}\n'
    await message.answer(teacher_text, reply_markup=keyboard)

    review_photos = await db.get_review_photos(selected_teacher_id)
    if review_photos:
        for photo_data in review_photos:
            with io.BytesIO(photo_data) as photo_file:
                await message.answer_photo(photo_file)
    else:
        await message.answer("Отзывы отсутствуют.")


# ______________________________________________________________________________________________________________________
# Кнопки добавления
@dp.message_handler(lambda message: message.text == "Добавить университет", state="*")
async def add_university(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.main_menu.state
        await States.add_university.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        await message.answer("Введите название университета:", reply_markup=keyboard)
    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Добавить предмет", state=States.selected_university)
async def add_subject(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.main_menu.state
        await States.add_subject_to_university.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        await message.answer("Введите имя предмета:", reply_markup=keyboard)
    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Добавить учителя", state=States.selected_subject)
async def add_teacher(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.main_menu.state
        await States.add_teacher_to_subject.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        await message.answer("Введите имя учителя, его Username и ID в Telegram: (Имя, Username, ID)", reply_markup=keyboard)
    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Добавить фото профиля", state=States.selected_teacher)
async def add_profile_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["previous_state"] = States.main_menu.state
    await States.add_profile_photo.set()
    await message.answer("Пожалуйста, загрузите фото профиля.")


@dp.message_handler(lambda message: message.text == "Добавить отзывы", state=States.selected_teacher)
async def add_review_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["previous_state"] = States.main_menu.state
    await States.add_review_photo.set()
    await message.answer("Пожалуйста, загрузите фото отзыв.")


# ______________________________________________________________________________________________________________________
# Кнопки удаления
@dp.message_handler(lambda message: message.text == "Удалить университет", state=States.selected_university)
async def delete_university(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            selected_university = data["university_selected"]
            selected_university_id = data["selected_university_id"]
            data["previous_state"] = States.main_menu.state

        delete_status = await db.delete_university_by_id(selected_university_id)

        if delete_status:
            await message.answer(f"Университет {selected_university} успешно удален.")
        else:
            await message.answer(f"Произошла ошибка при удалении университета {selected_university}.")

        await get_back(message, state=state)
    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Удалить предмет", state=States.selected_subject)
async def delete_subject(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            selected_subject = data["subject_selected"]
            selected_subject_id = data["selected_subject_id"]
            data["previous_state"] = States.main_menu.state

        delete_status = await db.delete_subject_by_id(selected_subject_id)

        if delete_status:
            await message.answer(f"Предмет {selected_subject} успешно удален.")
        else:
            await message.answer(f"Произошла ошибка при удалении предмета {selected_subject}.")

        await get_back(message, state=state)
    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Удалить учителя", state=States.selected_teacher)
async def delete_teacher(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            selected_teacher = data["selected_teacher"]
            selected_teacher_id = data["selected_teacher_id"]
            data["previous_state"] = States.main_menu.state

        delete_status = await db.delete_teacher_by_id(selected_teacher_id)

        if delete_status:
            await message.answer(f"Учитель {selected_teacher} успешно удален.")
        else:
            await message.answer(f"Произошла ошибка при удалении учителя {selected_teacher}.")

        await get_back(message, state=state)

    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Удалить фото профиля", state=States.selected_teacher)
async def delete_profile_photo(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            selected_teacher = data["selected_teacher"]
            selected_teacher_id = data["selected_teacher_id"]
            data["previous_state"] = States.main_menu.state

        delete_status = await db.delete_profile_photo(selected_teacher_id)

        if delete_status:
            await message.answer(f"Фото профиля учителя {selected_teacher} успешно удалено.")
        else:
            await message.answer(f"Произошла ошибка при удалении фото профиля учителя {selected_teacher}.")

        await get_back(message, state=state)

    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Удалить отзывы", state=States.selected_teacher)
async def delete_review_photo(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            selected_teacher = data["selected_teacher"]
            selected_teacher_id = data["selected_teacher_id"]
            data["previous_state"] = States.main_menu.state

        delete_status = await db.delete_review_photos(selected_teacher_id)

        if delete_status:
            await message.answer(f"Фото отзывов учителя {selected_teacher} успешно удалено.")
        else:
            await message.answer(f"Произошла ошибка при удалении фото отзывов учителя {selected_teacher}.")

        await get_back(message, state=state)

    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


# ______________________________________________________________________________________________________________________
# Функицонал добавления
@dp.message_handler(state=States.add_university)
async def save_university(message: types.Message, state: FSMContext):
    university_name = message.text
    async with state.proxy() as data:
        data["previous_state"] = States.main_menu.state

    if message.from_user.id in config.ADMINS:
        if await db.get_university_by_name(university_name):
            await message.answer("Такой университет уже существует!")
            await add_university(message, state=state)
        else:
            await db.add_university(university_name)
            await message.answer(f"Университет {university_name} был успешно добавлен!")

        await get_back(message, state=state)

    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message, state=state)


@dp.message_handler(state=States.add_subject_to_university)
async def save_subject(message: types.Message, state: FSMContext):
    subject_name = message.text

    async with state.proxy() as data:
        selected_university_id = data["selected_university_id"]
        data["previous_state"] = States.main_menu.state

    if message.from_user.id in config.ADMINS:
        add_status = await db.add_subject(subject_name, selected_university_id)
        if add_status:
            await message.answer(f"Предмет {subject_name} успешно добавлен.")
        else:
            await message.answer(f"Произошла ошибка при добавлении предмета {subject_name}.")

    await get_back(message, state=state)


@dp.message_handler(state=States.add_teacher_to_subject)
async def save_teacher(message: types.Message, state: FSMContext):
    teacher_name, teacher_telegram_username, teacher_telegram_id = message.text.split(", ")

    async with state.proxy() as data:
        selected_subject_id = data["selected_subject_id"]
        data["previous_state"] = States.main_menu.state

    if message.from_user.id in config.ADMINS:
        add_status = await db.add_teacher(teacher_name, teacher_telegram_username, teacher_telegram_id, selected_subject_id)
        if add_status:
            await message.answer(f"Учитель {teacher_name} успешно добавлен.")
        else:
            await message.answer(f"Произошла ошибка при добавлении учителя {teacher_name}.")

    await get_back(message, state=state)


@dp.message_handler(content_types=['photo'], state=States.add_profile_photo)
async def upload_profile_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)

    file_path = file.file_path
    byte_stream = await bot.download_file(file_path)

    image_data = byte_stream.getvalue()

    async with state.proxy() as data:
        teacher_id = data['selected_teacher_id']

    success = await db.add_profile_photo(teacher_id, image_data)

    if success:
        await message.answer("Фото профиля учителя успешно загружено и сохранено.")
    else:
        await message.answer("Ошибка при сохранении фото профиля учителя.")

    await States.selected_teacher.set()


@dp.message_handler(content_types=['photo'], state=States.add_review_photo)
async def upload_review_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)

    file_path = file.file_path
    byte_stream = await bot.download_file(file_path)

    image_data = byte_stream.getvalue()

    async with state.proxy() as data:
        teacher_id = data['selected_teacher_id']

    success = await db.add_review_photo(teacher_id, image_data)

    if success:
        await message.answer("Фото отзыва успешно загружено и сохранено.")
    else:
        await message.answer("Ошибка при сохранении фото отзыва.")

    await States.selected_teacher.set()


# ______________________________________________________________________________________________________________________
# Выбранный университет, предмет
@dp.message_handler(state=States.universities)
async def selected_university(message: types.Message, state: FSMContext):
    university_name = message.text
    university_id = await db.get_university_by_name(university_name)

    if university_id:
        async with state.proxy() as data:
            data["selected_university"] = university_name
            data["selected_university_id"] = university_id
            data["previous_state"] = States.main_menu.state
        await States.selected_university.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить предмет")
        button2 = types.KeyboardButton("Удалить университет")
        button4 = types.KeyboardButton("Назад")
        keyboard.add(button1, button2, button4)

        subjects = await db.get_subjects_by_university(university_id)
        subjects_text = "Список предметов для университета {}:\n".format(university_name)
        for subject in subjects:
            keyboard.add(types.KeyboardButton(subject[0]))

        await message.answer(subjects_text, reply_markup=keyboard)
        await States.selected_university.set()
    else:
        await message.answer("Выберите существующий университет из списка.")


@dp.message_handler(state=[States.selected_university, States.subjects])
async def selected_subject(message: types.Message, state: FSMContext):
    subject_name = message.text
    subject_id = await db.get_subject_by_name(subject_name)

    if subject_id:
        async with state.proxy() as data:
            data["selected_subject"] = subject_name
            data["selected_subject_id"] = subject_id
            data["previous_state"] = States.main_menu.state
        await States.selected_subject.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить учителя")
        button2 = types.KeyboardButton("Удалить предмет")
        button3 = types.KeyboardButton("Назад")
        keyboard.add(button1, button2, button3)

        teachers = await db.get_teachers_by_subject(subject_id)
        teacher_text = "Список учителей {}:\n".format(subject_name)
        for teacher in teachers:
            keyboard.add(types.KeyboardButton(teacher[0]))

        await message.answer(teacher_text, reply_markup=keyboard)
    else:
        await message.answer("Выберите учителя из списка.")


@dp.message_handler(state=[States.selected_subject, States.teachers])
async def selected_teacher(message: types.Message, state: FSMContext):
    teacher_name = message.text
    teacher_data = await db.get_teacher_by_name(teacher_name)

    if teacher_data:
        async with state.proxy() as data:
            data["selected_teacher"] = teacher_name
            data["selected_teacher_id"] = teacher_data[1]
            data["previous_state"] = States.main_menu.state
        await States.selected_teacher.set()

        teacher_text = "Вы выбрали учителя {}.\n".format(teacher_name)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Удалить учителя")
        button2 = types.KeyboardButton("Добавить фото профиля")
        button3 = types.KeyboardButton("Удалить фото профиля")
        button4 = types.KeyboardButton("Добавить отзывы")
        button5 = types.KeyboardButton("Удалить отзывы")
        button6 = types.KeyboardButton("Отзывы")
        button7 = types.KeyboardButton("Назад")
        keyboard.add(button1, button2, button3, button4, button5, button6, button7)

        await message.answer(teacher_text, reply_markup=keyboard)

        photo_data = await db.get_profile_photo(teacher_data[1])
        if photo_data:
            with io.BytesIO(photo_data) as photo_file:
                await message.answer_photo(photo_file)
        else:
            await message.answer("Фотография профиля учителя отсутствует.")

    else:
        await message.answer("Ошибка, такого учителя не существует.")


# ______________________________________________________________________________________________________________________
# Логика для пользователя
@dp.message_handler(lambda message: message.text == "Выбрать университет", state="*")
async def user_get_universities(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["previous_state"] = States.main_menu.state
    await States.user_universities.set()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Назад")
    keyboard.add(button1)

    universities = await db.get_all_universities()
    if universities:
        universities_text = "Нажми на свой университет:\n"
        for university in universities:
            keyboard.add(types.KeyboardButton(university[0]))
        await message.answer(universities_text, reply_markup=keyboard)
    else:
        await message.answer("Список университетов пуст.", reply_markup=keyboard)


@dp.message_handler(state=States.user_universities)
async def selected_user_university(message: types.Message, state: FSMContext):
    university_name = message.text
    university_id = await db.get_university_by_name(university_name)

    if university_id:
        async with state.proxy() as data:
            data["selected_university"] = university_name
            data["selected_university_id"] = university_id
            data["previous_state"] = States.user_universities.state
        await States.selected_user_university.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        subjects = await db.get_subjects_by_university(university_id)
        subjects_text = "Выбери предмет своего университета {}:\n".format(university_name)
        for subject in subjects:
            keyboard.add(types.KeyboardButton(subject[0]))

        await message.answer(subjects_text, reply_markup=keyboard)
    else:
        await message.answer("Выберите существующий университет из списка.")


@dp.message_handler(state=States.selected_user_university)
async def selected_user_subject(message: types.Message, state: FSMContext):
    subject_name = message.text
    subject_id = await db.get_subject_by_name(subject_name)

    if subject_id:
        async with state.proxy() as data:
            data["selected_subject"] = subject_name
            data["selected_subject_id"] = subject_id
            data["previous_state"] = States.user_universities.state
        await States.selected_user_subject.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        teachers = await db.get_teachers_by_subject(subject_id)
        teacher_text = "Выбери подходящего учителя {}:\n".format(subject_name)
        for teacher in teachers:
            keyboard.add(types.KeyboardButton(teacher[0]))

        await message.answer(teacher_text, reply_markup=keyboard)
    else:
        await message.answer("Выберите учителя из списка.")


@dp.message_handler(state=States.selected_user_subject)
async def selected_user_teacher(message: types.Message, state: FSMContext):
    teacher_name = message.text
    teacher_data = await db.get_teacher_by_name(teacher_name)

    if teacher_data:
        async with state.proxy() as data:
            data["selected_teacher"] = teacher_name
            data["selected_teacher_id"] = teacher_data[1]
            data["previous_state"] = States.user_universities.state
        await States.selected_user_teacher.set()

        keyboard2 = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button2 = types.KeyboardButton("Назад")
        button3 = types.KeyboardButton("Отзывы")
        keyboard2.add(button2, button3)

        teacher_text = f'Вы выбрали учителя {teacher_name}\n'
        await message.answer(teacher_text, reply_markup=keyboard2)

        photo_data = await db.get_profile_photo(teacher_data[1])
        url = f"https://t.me/{teacher_data[0]}"
        keyboard1 = types.InlineKeyboardMarkup(resize_keyboard=True)
        button1 = types.InlineKeyboardButton("Написать учителю", url=url)
        keyboard1.add(button1)

        if photo_data:
            with io.BytesIO(photo_data) as photo_file:
                await message.answer_photo(photo_file, reply_markup=keyboard1)
        else:
            await message.answer("Фотография профиля учителя отсутствует.", reply_markup=keyboard1)

    else:
        await message.answer("Ошибка, такого учителя не существует.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)


