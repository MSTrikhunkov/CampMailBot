from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from states import Form, PrinterForm
import os
import json
import yaml
from datetime import datetime
from openpyxl import Workbook


from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext
from states import Form

MAILS_PATH = 'mails'
TEMP_DIR = 'tmp'
CONFIG = 'config/config.yaml'

def get_router(shared_data):
    router = Router()

    @router.message(F.text == "/start")
    async def start_handler(message: Message, state: FSMContext):

        user_id = message.from_user.id
        printer_ids = []
        async with shared_data['lock']:
            printer_ids = [item['id'] for item in shared_data['config']['printers']]

        if user_id in printer_ids:
            await message.answer("Добро пожаловать в панель администратора локации.")
            await state.set_state(PrinterForm.mainMenue)
            await process_printer_mainMenue(message, state)
            return



        await message.answer("Привет! Я помогу отправить письмо")
        await state.set_state(Form.location)

        # Получаем список локаций из shared_data
        async with shared_data['lock']:
            location_names = [item['name'] for item in shared_data['config']['locations']]

        # Отправляем клавиатуру с локациями
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=name)] for name in location_names],
            resize_keyboard=True
        )
        await message.answer("Выбери локацию:", reply_markup=keyboard)

    @router.message(Form.location)
    async def process_location(message: Message, state: FSMContext):
        if message.text is None or message.text == "":
            return
        
        async with shared_data['lock']:
            location_names = [item['name'] for item in shared_data['config']['locations']]

        # Проверка ввода
        if message.text not in location_names:
            await message.answer("Пожалуйста, выбери локацию из предложенных кнопок.")
            return

        await state.update_data(location=message.text)
        await state.set_state(Form.mailto)

        await message.answer(f"Локация «{message.text}» выбрана. Теперь напиши адресата.", 
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад ⬅️")]
                ]
            ))   

    @router.message(Form.mailto)
    async def process_mailto(message: Message, state : FSMContext):
        if message.text is None or message.text == "":
            return
        if message.text == "Назад ⬅️":
            await state.update_data(location="")
            await state.set_state(Form.location)
            # Получаем список локаций из shared_data
            async with shared_data['lock']:
                location_names = [item['name'] for item in shared_data['config']['locations']]

            # Отправляем клавиатуру с локациями
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=name)] for name in location_names],
                resize_keyboard=True
            )
            await message.answer("Выбери локацию:", reply_markup=keyboard)
            return


        await state.update_data(mailto = message.text)
        await state.set_state(Form.group)
        await message.answer(f"Адресат: «{message.text}». Теперь напиши отряд.", 
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад ⬅️")]
                ]
            )
        )
    
    @router.message(Form.group)
    async def process_group(message : Message, state : FSMContext):
        if message.text is None or message.text == "":
            return
        
        if message.text == "Назад ⬅️":
            await state.update_data(mailto="")
            await state.set_state(Form.mailto)
            await message.answer(f"Напиши адресата.", 
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад ⬅️")]
                ]
            ))
            return


        await state.update_data(group = message.text)
        await state.set_state(Form.mailfrom)
        await message.answer(f"Выбран отряд: «{message.text}». Теперь укажи отправителя", reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад ⬅️")]
                ]
            )
        )
    
    @router.message(Form.mailfrom)
    async def process_mailfrom(message: Message, state : FSMContext):
        if message.text is None or message.text == "":
            return
        
        if message.text == "Назад ⬅️":
            await state.update_data(group="")
            await state.set_state(Form.group)
            await message.answer(f"Напиши отряд.", 
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                       [KeyboardButton(text="Назад ⬅️")]
                    ]
                )
            )
            return
 
        await state.update_data(mailfrom = message.text)
        await state.set_state(Form.mailcontent)
        await message.answer(f"Выбран отправитель: «{message.text}». Теперь напиши письмо", 
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад ⬅️")]
                ]
            )
        )

    @router.message(Form.mailcontent)
    async def process_mailcontent(message : Message, state : FSMContext):
        if message.text is None or message.text == "":
            return
        
        if message.text == "Назад ⬅️":
            await state.update_data(mailfrom="")
            await state.set_state(Form.mailfrom)
            await message.answer(f"Укажи отправителя", 
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="Назад ⬅️")]
                    ]
                )
            )
            return

        
        await state.update_data(mailcontent = message.text)
        data = await state.get_data()
        await state.set_state(Form.approveSent)
        await message.answer(
        f"""
Локация:                {data['location']}
Получатель:          {data['mailto']}
Отряд:                    {data['group']}
Отправитель:        {data['mailfrom']}
Текст Письма:
```
{data['mailcontent']}
```
        """,
        parse_mode="MarkdownV2",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Назад ⬅️")],
                [KeyboardButton(text="Подтвердить отправку ✅")]
            ],
            resize_keyboard=True
            )
        )

    @router.message(Form.approveSent)
    async def process_approveSent(message : Message, state : FSMContext):
        if message.text is None or message.text == "":
            return
        
        if message.text == "Назад ⬅️":
            await state.update_data(mailcontent = "")
            await state.set_state(Form.mailcontent)
            await message.answer(f"Напиши письмо", 
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="Назад ⬅️")]
                    ]
                )
            )
            return
        
        if not message.text == "Подтвердить отправку ✅":
            await message.answer("Пожалуйста, подтвердите отправку",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="Назад ⬅️")],
                        [KeyboardButton(text="Подтвердить отправку ✅")]
                    ],
                    resize_keyboard=True
                )
            )
            return

        # Write to Journal
        data = await state.get_data()

        user_id = message.from_user.id
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        mail_id = f"{user_id}_{timestamp}"

        async with shared_data['lock']:
            filename = None
            for item in shared_data['config']['locations']:
                if item['name'] == data['location']:
                    filename = f"{MAILS_PATH}{os.sep}{item['file']}"

            if filename is not None:
                with open(filename, 'r', encoding="utf-8") as f:
                    file_data = json.load(f)

                file_data[mail_id] = data

                with open(filename, 'w') as f:
                    json.dump(file_data, f, indent=2, ensure_ascii=False)


        await message.answer("Письмо успешно отправлено! ✅", 
            reply_markup = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="/start")]
                ],
                resize_keyboard=True
            )
        )
        await state.clear()


    @router.message(PrinterForm.mainMenue)
    async def process_printer_mainMenue(message : Message, state : FSMContext):
        
        if message.text == 'Скачать полученные письма':
            await state.set_state(PrinterForm.printMails)
            await process_printer_printMails(message, state)
            return
        elif message.text == 'Забанить пользователя 🚫':
            await message.answer("Введите id пользователя для бана", 
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="Назад ⬅️")]
                    ],
                resize_keyboard=True
                )
            )
            await state.set_state(PrinterForm.enterUserForBan)
            return

        current_location = None
        async with shared_data['lock']:
            for item in shared_data['config']['printers']:
                if item['id'] == message.from_user.id:
                    current_location = item['location']

        await message.answer(f"Локация «{current_location}». Выберите действие.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Скачать полученные письма")],
                    [KeyboardButton(text="Забанить пользователя 🚫")]
                ],
                resize_keyboard=True
            )
        )
    
    @router.message(PrinterForm.printMails)
    async def process_printer_printMails(message: Message, state : FSMContext):
        curent_location = None
        current_file = None
        bDataFound = True
        mail_data = dict()
        async with shared_data['lock']:
            for item in shared_data['config']['printers']:
                if item['id'] == message.from_user.id:
                    current_location = item['location']
            
            for item in shared_data['config']['locations']:
                if item['name'] == current_location:
                    current_file = item['file']

            if not os.path.exists(f'{MAILS_PATH}{os.sep}{current_file}'):
                bDataFound = False

            try: 
                with open(f'{MAILS_PATH}{os.sep}{current_file}', 'r', encoding='utf-8') as f:
                    mail_data = json.load(f)
                if len(mail_data) == 0:
                    bDataFound = False
                with open(f'{MAILS_PATH}{os.sep}{current_file}', 'w') as f:
                    f.write('{}')
            except Exception as e:
                print(e)
                bDataFound = False

        if not bDataFound:
            await message.answer(f"В локации «{current_location}» новых писем нет.")
            await state.set_state(PrinterForm.mainMenue)
            return
        
        wb = Workbook()
        sheet = wb.active
        #sheet.title = curent_location

        # Create Header
        sheet['A1'] = "ID"
        sheet['B1'] = 'Локация'
        sheet['C1'] = 'Кому'
        sheet['D1'] = 'Отряд'
        sheet['E1'] = 'От кого'
        sheet['F1'] = 'Текст письма'

        current_line = 2
        for key in mail_data.keys():
            sheet[f"A{current_line}"] = key.split('_')[0]
            sheet[f"B{current_line}"] = mail_data[key]['location']
            sheet[f"C{current_line}"] = mail_data[key]['mailto']
            sheet[f"D{current_line}"] = mail_data[key]['group']
            sheet[f"E{current_line}"] = mail_data[key]['mailfrom']
            sheet[f"F{current_line}"] = mail_data[key]['mailcontent']
            current_line += 1

        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filepath = f'{TEMP_DIR}{os.sep}{timestamp}.xlsx'
        wb.save(filepath)
        doc = FSInputFile(filepath)
        await message.answer_document(doc, caption=f"Вот выгрузка. Найдено писем: {len(mail_data)}")
        os.remove(filepath)
        await state.set_state(PrinterForm.mainMenue)

    @router.message(PrinterForm.enterUserForBan)
    async def process_printer_enterUserForBan(message : Message, state: FSMContext):

        if message.text is None or message.text == "" or message.text == "Назад ⬅️":
            await state.clear()
            await state.set_state(PrinterForm.mainMenue)
            await process_printer_mainMenue(message, state)
            return

        await state.update_data(userid=message.text)
        await message.answer(f"Укажите причину бана пользователя с id: {message.text}", 
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Назад ⬅️")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(PrinterForm.enterBanReason)

    @router.message(PrinterForm.enterBanReason)
    async def process_printer_enterBanReason(message : Message, state: FSMContext):
        if message.text is None or message.text == "" or message.text == "Назад ⬅️":
            await state.clear()
            await state.set_state(PrinterForm.mainMenue)
            await process_printer_mainMenue(message, state)
            return
        
        await state.set_state(PrinterForm.confirmBan)
        await state.update_data(reason=message.text)
        data = await state.get_data()
        await message.answer(f"Пользователь {data['userid']} будет забанен по причине {data['reason']}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=
                [
                    [KeyboardButton(text="Подтвердить бан ✅")],
                    [KeyboardButton(text="Отмена бана 🚫")],
                ],
                resize_keyboard=True
            ) 
        )

    @router.message(PrinterForm.confirmBan)
    async def process_printer_confirmBan(message : Message, state : FSMContext):
        data = await state.get_data()
        if message.text == "Подтвердить бан ✅":
            

            new_entry = { "id" : int(data['userid']), "reason": data['reason']}

            async with shared_data['lock']:
                banned = shared_data['config']['banned']
                banned.append(new_entry)

                with open (CONFIG, 'w') as f:
                    yaml.dump(shared_data['config'], f, allow_unicode=True)

            message.answer(f"Пользователь {data['userid']} был заблокирован!")

        else:
            message.answer(f"Пользователь {data['userid']} был помилован")
        
        await state.clear()
        await state.set_state(PrinterForm.mainMenue)
        await process_printer_mainMenue(message, state)


    return router
            



