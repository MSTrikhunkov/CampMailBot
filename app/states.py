from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    location = State()
    mailto = State()
    group = State()
    mailfrom = State()
    mailcontent = State()
    approveSent = State()

class PrinterForm(StatesGroup):
    mainMenue = State()
    enterUserForBan = State()
    enterBanReason = State()
    confirmBan = State()
    printMails = State()