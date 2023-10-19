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
    university_selected = State()
    change_university_name = State()
    add_subject_to_university = State()
    delete_subject_from_university = State()


@dp.message_handler(commands=['start'], state="*")
async def on_start(message: types.Message, state: FSMContext):
    if message.from_user.id == config.ADMIN_ID:
        async with state.proxy() as data:
            data["current_state"] = States.main_menu.state
        await States.main_menu.set()

        if message.text == "/start":
            text = "Привет, администратор! Я бот MentorBot :)"
        else:
            text = "Вы вернулись назад :)"
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Университеты")
        button2 = types.KeyboardButton("Учителя")
        button3 = types.KeyboardButton("Предметы")
        keyboard.add(button1, button2, button3)
        await message.answer(text, reply_markup=keyboard)
    else:
        pass


@dp.message_handler(lambda message: message.text == "Назад", state="*")
async def get_back(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        previous_state = data.get("previous_state")
        print(previous_state)

        if previous_state == States.universities.state:
            await get_universities(message, state=state)
        elif previous_state == States.teachers.state:
            await get_teachers(message, state=state)
        elif previous_state == States.subjects.state:
            await get_subjects(message, state=state)
        elif previous_state == States.main_menu.state or previous_state is None:
            await on_start(message, state=state)


@dp.message_handler(lambda message: message.text == "Университеты", state="*")
async def get_universities(message: types.Message, state: FSMContext):
    if message.from_user.id == config.ADMIN_ID:
        async with state.proxy() as data:
            print(data.get("current_state"))
            data["previous_state"] = data.get("current_state")
            data["current_state"] = States.universities.state
        await States.universities.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить университет")
        button3 = types.KeyboardButton("Назад")
        keyboard.add(button1, button3)

        universities = await db.get_all_universities()
        if universities:
            universities_text = "Список университетов:\n"
            for university in universities:
                keyboard.add(types.KeyboardButton(university[0]))
            await message.answer(universities_text, reply_markup=keyboard)
        else:
            await message.answer("Список университетов пуст.", reply_markup=keyboard)
    else:
        await message.answer("Вы не являетесь администратором!")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Учителя", state="*")
async def get_teachers(message: types.Message, state: FSMContext):
    if message.from_user.id == config.ADMIN_ID:
        async with state.proxy() as data:
            data["previous_state"] = data.get("current_state")
            data["current_state"] = States.teachers.state
        await States.teachers.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить учителя")
        button3 = types.KeyboardButton("Назад")
        keyboard.add(button1, button3)

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
    if message.from_user.id == config.ADMIN_ID:
        async with state.proxy() as data:
            data["previous_state"] = data.get("current_state")
            data["current_state"] = States.subjects.state
        await States.subjects.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить учителя")
        button3 = types.KeyboardButton("Назад")
        keyboard.add(button1, button3)

        subjects = await db.get_all_subjects()
        if subjects:
            subjects_text = "Список предметов:\n"
            for subject in subjects:
                keyboard.add(types.KeyboardButton(subject[0]))

            await message.answer(subjects_text, reply_markup=keyboard)
        else:
            await message.answer("Список предметов пуст.", reply_markup=keyboard)
    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message)


@dp.message_handler(lambda message: message.text == "Добавить университет", state="*")
async def add_university(message: types.Message, state: FSMContext):
    if message.from_user.id == config.ADMIN_ID:
        async with state.proxy() as data:
            data["previous_state"] = data.get("current_state")
            data["current_state"] = States.add_university.state
        await States.add_university.set()

        await message.answer("Введите название университета:")


@dp.message_handler(state=States.add_university)
async def save_university(message: types.Message, state: FSMContext):
    university_name = message.text
    async with state.proxy() as data:
        data["previous_state"] = States.main_menu.state
        data["current_state"] = States.add_university.state

    if message.from_user.id == config.ADMIN_ID:
        if await db.get_university_by_name(university_name):
            await message.answer("Такой университет уже существует!")
            await add_university(message, state=state)
        else:
            await db.add_university(university_name)
            await message.answer(f"Университет {university_name} был успешно добавлен!")

    else:
        await message.answer("Вы не являетесь администратором.")
        await on_start(message, state=state)


@dp.message_handler(state=States.universities)
async def selected_university(message: types.Message, state: FSMContext):
    university_name = message.text
    university_id = await db.get_university_by_name(university_name)

    if university_id:

        async with state.proxy() as data:
            data["selected_university"] = university_name
            data["selected_university_id"] = university_id
            data["previous_state"] = data.get("current_state")
            data["current_state"] = States.universities.state

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить предмет")
        button2 = types.KeyboardButton("Удалить университет")
        button4 = types.KeyboardButton("Назад")
        keyboard.add(button1, button2, button4)

        subjects = await db.get_subjects_by_university(university_id)
        subjects_text = "Список предметов для университета {}:\n".format(university_name)
        for subject in subjects:
            subjects_text += "- {}\n".format(subject[0])

        await message.answer(subjects_text, reply_markup=keyboard)
        await States.university_selected.set()
    else:
        await message.answer("Выберите существующий университет из списка.")


@dp.message_handler(lambda message: message.text == "Удалить университет", state=States.university_selected)
async def delete_university(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        selected_university = data.get("selected_university")
        data["previous_state"] = data.get("current_state")

        university_id = await db.get_university_by_name(selected_university)

        delete_status = await db.delete_university_by_id(university_id)
        if delete_status:
            await message.answer(f"Университет {selected_university} успешно удален.")
        else:
            await message.answer(f"Произошла ошибка при удалении университета {selected_university}.")

        await get_back(message, state=state)


@dp.message_handler(lambda message: message.text == "Добавить предмет", state="*")
async def add_university(message: types.Message, state: FSMContext):
    if message.from_user.id == config.ADMIN_ID:
        async with state.proxy() as data:
            data["previous_state"] = data.get("current_state")
            data["current_state"] = States.add_subject_to_university.state
        await States.add_subject_to_university.set()

        await message.answer("Введите имя предмета:")


@dp.message_handler(state=States.add_subject_to_university)
async def save_subject(message: types.Message, state: FSMContext):
    subject_name = message.text

    async with state.proxy() as data:
        selected_university = data.get("selected_university")
        university_id = await db.get_university_by_name(selected_university)
        data["previous_state"] = States.universities.state

    if message.from_user.id == config.ADMIN_ID:
        add_status = await db.add_subject(subject_name, university_id)
        if add_status:
            await message.answer(f"Предмет {subject_name} успешно добавлен.")
        else:
            await message.answer(f"Произошла ошибка при добавлении предмета {subject_name}.")





# @dp.message_handler(lambda message: message.text == "Добавить учителя", state="*")
# async def add_university(message: types.Message, state: FSMContext):
#     if message.from_user.id == config.ADMIN_ID:
#         async with state.proxy() as data:
#             data["previous_state"] = data.get("current_state")
#             data["current_state"] = States.add_teacher.state
#         await States.add_teacher.set()
#
#         await message.answer("Введите имя учителя:")





if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)


