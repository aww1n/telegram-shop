from aiogram.fsm.state import State, StatesGroup


class SearchState(StatesGroup):
    query = State()


class FilterState(StatesGroup):
    min_price = State()
    max_price = State()
