from aiogram.fsm.state import State, StatesGroup


class ProductCreate(StatesGroup):
    photos = State()
    name = State()
    short_description = State()
    description = State()
    price = State()
    category = State()
    characteristics = State()
    article = State()
    stock = State()
    preview = State()


class CategoryCreate(StatesGroup):
    name = State()


class CategoryRename(StatesGroup):
    name = State()


class CsvImport(StatesGroup):
    document = State()


class ProductEdit(StatesGroup):
    price = State()
    stock = State()
    value = State()
    photo = State()


class ProductBulk(StatesGroup):
    ids = State()
    action = State()
    value = State()
    confirm = State()
