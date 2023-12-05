import logging

import requests

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import BoundFilter




API_TOKEN = "6450261705:AAEEK-cb51mOI0h0n6u82Fvp63GOwH4IVII"

# Configure logging
logging.basicConfig(level=logging.INFO)


class LinkStates(StatesGroup):
    username = State()
    password = State()




class IsLinkedFilter(BoundFilter):
    key = "linked"

    def __init__(self, linked: bool):
        self.linked = linked

    async def check(self, message: types.Message):
        telegram_id = message.from_id
        payload = {"telegram_id": telegram_id}
        r = requests.get("http://127.0.0.1:5000/check_tg", params=payload)
        content = r.json()
        return content.get("status", False) is self.linked

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.filters_factory.bind(IsLinkedFilter)



@dp.message_handler(commands=["start"], linked=False)
async def start1(message: types.Message):
    await message.answer("Сперва зареіструйтеся (/link)")
    await message.answer("Привіт, це бот гаманець\n/wallet - кошелек\n/link - логин\n/add_tg - Закинуть деньги\n/spend_money - Тратить деньги\n/transfer - отправить деньги")





@dp.message_handler(commands=["link"], linked=False)
async def link(message: types.Message, state: FSMContext):
    await message.answer("Ваш логін на сайті: ")
    await LinkStates.username.set()


@dp.message_handler(state=LinkStates.username, content_types=[types.ContentType.TEXT])
async def process_username(message: types.Message, state: FSMContext):
    username = message.text
    await state.update_data(username=username)
    await message.answer("Чудово! Тепер введіть ваш пароль: ")
    await LinkStates.password.set()


@dp.message_handler(content_types=[types.ContentType.TEXT], state=LinkStates.password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text
    async with state.proxy() as data:
        username = data.get("username")
    telegram_id = message.from_id

    data = {
        "username": username,
        "password": password,
        "telegram_id": telegram_id,
    }

    r = requests.post("http://127.0.0.1:5000/link_tg", data=data)
    response = r.json()
    msg = response.get("message") or response.get("error")
    await message.answer(msg)
    await state.finish()

@dp.message_handler(commands=["unlink"], linked=True)
async def unlink(message: types.Message):
    data = {"telegram_id": message.from_id}
    r = requests.get("http://127.0.0.1:5000/unlink", params=data)
    await message.answer("Ви успішно відв'язалися")



@dp.message_handler(commands=["wallet"], linked=True)
async def show_wallet(message: types.Message):
    data = {"telegram_id": message.from_id}
    r = requests.get("http://127.0.0.1:5000/wallet_tg", params=data)
    r1 = requests.get("http://127.0.0.1:5000/tran", params=data)
    response = r.json()
    response1 = r1.json()
    balance = response.get("balance")
    tran = response1.get("tran")
    await message.answer(f"Баланс - {balance}")
    for trans in tran:
        await message.answer(f"{trans[2]} - {trans[4]}\n Описание - {trans[3]}")


class AddMoney(StatesGroup):
    waiting_for_amount = State()

@dp.message_handler(commands=['add_tg'])
async def start(message: types.Message):
    await message.reply("Привет! Я могу помочь вам пополнять кошелек. Введите сумму для пополнения:")

    await AddMoney.waiting_for_amount.set()

@dp.message_handler(state=AddMoney.waiting_for_amount, content_types=types.ContentTypes.TEXT)
async def process_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['amount'] = message.text

        telegram_id = message.from_user.id

        payload = {
            "amount": data['amount'],
            "telegram_id": telegram_id
        }

        response = requests.post(f"http://127.0.0.1:5000/add_tg", json=payload)

        if response.status_code == 200:
            response_data = response.json()
            await message.reply(response_data["message"])
        else:
            await message.reply("Произошла ошибка при пополнении кошелька.")

        await state.finish()


@dp.message_handler(commands=['spend_money'], linked=True)
async def spend_money_start(message: types.Message):
    await message.reply("Введіть суму та опис для витрати в форматі: сума. опис")


@dp.message_handler(lambda message: ',' in message.text)
async def spend_money_process(message: types.Message):
    data = message.text.split(',')
    
    if len(data) != 2:
        await message.reply("Некоректний формат. Введіть суму та опис через крапку.")
        return

    amount_text, description = data
    amount_text = amount_text.strip()
    description = description.strip()

    try:
        amount = float(amount_text)
    except ValueError:
        await message.reply("Введіть коректну суму")
        return

    if amount <= 0:
        await message.reply("Сума повинна бути більше нуля")
        return

    telegram_id = message.from_user.id

    data = {
        "amount": amount,
        "description": description,
        "telegram_id": telegram_id
    }
    response = requests.post('http://127.0.0.1:5000/spend_tg', json=data)

    if response.status_code != 200:
        await message.reply("Сталася помилка під час запиту. Спробуйте пізніше.")
        return

    result = response.json()
    print(result)
    if "error" in result:
        error_message = result.get("error")
        await message.reply(f"Помилка: {error_message}")
    elif "message" in result:
        success_message = result.get("message")
        await message.reply(success_message)




class TransferState(StatesGroup):
    awaiting_username = State()  
    awaiting_transfer_amount = State()

@dp.message_handler(commands=["transfer"], linked=True)
async def cmd_transfer(message: types.Message, state: FSMContext):
    await message.answer("Введіть користувача для переказу")
    await TransferState.awaiting_username.set()

@dp.message_handler(state=TransferState.awaiting_username)
async def process_username(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["username"] = message.text
    await message.answer("Введіть суму переказу")
    await TransferState.awaiting_transfer_amount.set()

@dp.message_handler(lambda message: not message.text.startswith("/"), state=TransferState.awaiting_transfer_amount)
async def process_transfer_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["transfer_amount"] = message.text

        telegram_id = message.from_user.id

        payload = {
            "username": data["username"],
            "transfer_amount": data["transfer_amount"],
            "telegram_id": telegram_id
        }

        response = requests.post('http://127.0.0.1:5000/transfer_money_tg', json=payload)

        result = response.json()
        print(result)
        if "error" in result:
            error_message = result.get("error")
            await message.reply(f"Помилка: {error_message}")
        elif "message" in result:
            success_message = result.get("message")
            await message.reply(success_message)
        



    await state.finish()







if __name__ == "__main__":
    executor.start_polling(dp)
