from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
import config
import database.service as db
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

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
        else:
            text = "Хочешь еще поискать учителя? Нажимай 'Выбрать университет' :)"

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Выбрать университет")
        keyboard.add(button1)
        await message.answer(text, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Главная", state="*")
async def get_back(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["previous_state"] = States.main_menu.state
    await States.main_menu.set()
    await on_start(message, state=state)


#Тут вопрос, если вся эта логика нужна, если Назад только на универы и главную ведет
@dp.message_handler(lambda message: message.text == "Назад", state="*")
async def get_back(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        previous_state = data.get("previous_state")
        print(previous_state)

        if previous_state == States.universities.state:
            await get_universities(message, state=state)
        if previous_state == States.user_universities.state:
            await user_get_universities(message, state=state)
        # elif previous_state == States.teachers.state:
        #     await get_teachers(message, state=state)
        # elif previous_state == States.subjects.state:
        #     await get_subjects(message, state=state)
        # elif previous_state == States.university_selected.state:
        #     await selected_university(message, state=state)
        # elif previous_state == States.subject_selected.state:
        #     await selected_subject(message, state=state)

        elif previous_state == States.main_menu.state or previous_state is None:
            await on_start(message, state=state)


@dp.message_handler(lambda message: message.text == "Университеты", state="*")
async def get_universities(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.main_menu.state
        await States.universities.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить университет")
        button3 = types.KeyboardButton("Главная")
        keyboard.add(button1, button3)

        universities = await db.get_all_universities()
        if universities:
            universities_text = "Список университетов:\n"
            for university in universities:
                keyboard.add(types.KeyboardButton(university[0]))
            await message.answer(universities_text, reply_markup=keyboard)
        else:
            await message.answer("Список университетов пуст.", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Учителя", state="*")
async def get_teachers(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.main_menu.state

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        teachers = await db.get_all_teachers()
        if teachers:
            teachers_text = "Список учителей:\n"
            for teacher in teachers:
                teachers_text += "- {}\n".format(teacher[0])

            await message.answer(teachers_text, reply_markup=keyboard)
        else:
            await message.answer("Список учителей пуст.", reply_markup=keyboard)
    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Предметы", state="*")
async def get_subjects(message: types.Message, state: FSMContext):
    # if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.main_menu.state

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        subjects = await db.get_all_subjects()
        if subjects:
            subjects_text = "Список предметов:\n"
            seen_subjects = set()
            for subject in subjects:
                if subject[0] not in seen_subjects:
                    subjects_text += "- {}\n".format(subject[0])
                    seen_subjects.add(subject[0])

            await message.answer(subjects_text, reply_markup=keyboard)
        else:
            await message.answer("Список предметов пуст.", reply_markup=keyboard)


# ______________________________________________________________________________________________________________________
# Кнопки добавления
@dp.message_handler(lambda message: message.text == "Добавить университет", state="*")
async def add_university(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.universities.state
        await States.add_university.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        await message.answer("Введите название университета:", reply_markup=keyboard)
    else:
        pass


@dp.message_handler(lambda message: message.text == "Добавить предмет", state=States.selected_university)
async def add_university(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.universities.state
        await States.add_subject_to_university.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        await message.answer("Введите имя предмета:", reply_markup=keyboard)
    else:
        pass


@dp.message_handler(lambda message: message.text == "Добавить учителя", state=States.selected_subject)
async def add_university(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        async with state.proxy() as data:
            data["previous_state"] = States.universities.state
        await States.add_teacher_to_subject.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        await message.answer("Введите имя учителя и  его ID в Telegram: (Имя, ID)", reply_markup=keyboard)


# ______________________________________________________________________________________________________________________
# Кнопки удаления
@dp.message_handler(lambda message: message.text == "Удалить университет", state=States.selected_university)
async def delete_university(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        selected_university = data.get("university_selected")

    university_id = await db.get_university_by_name(selected_university)
    delete_status = await db.delete_university_by_id(university_id)

    if delete_status:
        await message.answer(f"Университет {selected_university} успешно удален.")
    else:
        await message.answer(f"Произошла ошибка при удалении университета {selected_university}.")

    await get_universities(message, state=state)


@dp.message_handler(lambda message: message.text == "Удалить предмет", state=States.selected_subject)
async def delete_subject(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        selected_subject = data.get("subject_selected")

    subject_id = await db.get_subject_by_name(selected_subject)
    delete_status = await db.delete_subject_by_id(subject_id)

    if delete_status:
        await message.answer(f"Предмет {selected_subject} успешно удален.")
    else:
        await message.answer(f"Произошла ошибка при удалении предмета {selected_subject}.")

    await get_universities(message, state=state)


@dp.message_handler(lambda message: message.text == "Удалить учителя", state=States.selected_teacher)
async def delete_teacher(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        selected_teacher = data.get("selected_teacher")

    teacher_id = await db.get_teacher_by_name(selected_teacher)
    delete_status = await db.delete_teacher_by_id(teacher_id)

    if delete_status:
        await message.answer(f"Учитель {selected_teacher} успешно удален.")
    else:
        await message.answer(f"Произошла ошибка при удалении учителя {selected_teacher}.")

    await get_universities(message, state=state)


# ______________________________________________________________________________________________________________________
# Функицонал добавления
@dp.message_handler(state=States.add_university)
async def save_university(message: types.Message, state: FSMContext):
    university_name = message.text
    async with state.proxy() as data:
        data["previous_state"] = States.universities.state

    if message.from_user.id in config.ADMINS:
        if await db.get_university_by_name(university_name):
            await message.answer("Такой университет уже существует!")
            await add_university(message, state=state)
        else:
            await db.add_university(university_name)
            await message.answer(f"Университет {university_name} был успешно добавлен!")
            await on_start(message, state=state)

    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message, state=state)


@dp.message_handler(state=States.add_subject_to_university)
async def save_subject(message: types.Message, state: FSMContext):
    subject_name = message.text

    async with state.proxy() as data:
        selected_university = data.get("selected_university")
        data["previous_state"] = States.universities.state
    university_id = await db.get_university_by_name(selected_university)

    if message.from_user.id in config.ADMINS:
        add_status = await db.add_subject(subject_name, university_id)
        if add_status:
            await message.answer(f"Предмет {subject_name} успешно добавлен.")
        else:
            await message.answer(f"Произошла ошибка при добавлении предмета {subject_name}.")


@dp.message_handler(state=States.add_teacher_to_subject)
async def save_teacher(message: types.Message, state: FSMContext):
    teacher_name, teacher_id = message.text.split(", ")

    async with state.proxy() as data:
        selected_subject = data.get("selected_subject")
        data["previous_state"] = States.universities.state

    subject_id = await db.get_subject_by_name(selected_subject)
    print(teacher_name, teacher_id, subject_id)

    if message.from_user.id in config.ADMINS:
        add_status = await db.add_teacher(teacher_name, teacher_id, subject_id)
        if add_status:
            await message.answer(f"Учитель {teacher_name} успешно добавлен.")
        else:
            await message.answer(f"Произошла ошибка при добавлении учителя {teacher_name}.")
        return await get_back(message, state=state)


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
            data["previous_state"] = States.universities.state
        await States.selected_university.set()
        print()

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


@dp.message_handler(state=States.selected_university)
async def selected_subject(message: types.Message, state: FSMContext):
    subject_name = message.text
    subject_id = await db.get_subject_by_name(subject_name)

    if subject_id:
        async with state.proxy() as data:
            data["selected_subject"] = subject_name
            data["previous_state"] = States.universities.state
        await States.selected_subject.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить учителя")
        button2 = types.KeyboardButton("Удалить предмет")
        button4 = types.KeyboardButton("Назад")
        keyboard.add(button1, button2, button4)

        teachers = await db.get_teachers_by_subject(subject_id)
        teacher_text = "Список учителей {}:\n".format(subject_name)
        for teacher in teachers:
            keyboard.add(types.KeyboardButton(teacher[0]))

        await message.answer(teacher_text, reply_markup=keyboard)
        await States.selected_subject.set()
    else:
        await message.answer("Выберите учителя из списка.")


@dp.message_handler(state=States.selected_subject)
async def selected_teacher(message: types.Message, state: FSMContext):
    teacher_name = message.text
    teacher_id = await db.get_teacher_by_name(teacher_name)

    if teacher_id:
        async with state.proxy() as data:
            data["selected_teacher"] = teacher_name
            data["previous_state"] = States.universities.state
        await States.selected_teacher.set()

        teacher_text = "Вы выбрали учителя {}.\n".format(teacher_name)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Удалить учителя")
        button2 = types.KeyboardButton("Назад")
        keyboard.add(button1, button2)

        await message.answer(teacher_text, reply_markup=keyboard)
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
    button1 = types.KeyboardButton("Главная")
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
    teacher_id = await db.get_teacher_by_name(teacher_name) 

    if teacher_id:
        async with state.proxy() as data:
            data["selected_teacher"] = teacher_name
            data["previous_state"] = States.user_universities.state
        await States.selected_user_teacher.set()

        teacher_text = "Вы выбрали учителя {}.\n".format(teacher_name)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Назад")
        keyboard.add(button1)

        await message.answer(teacher_text, reply_markup=keyboard)
    else:
        await message.answer("Ошибка, такого учителя не существует.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)


