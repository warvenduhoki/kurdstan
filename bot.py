# Бот для генерации и публикации карт с гарантией прохождения Luhn
# Установка: pip install python-telegram-bot
# Запуск: python bot.py

import asyncio
import logging
import random
from telegram import Bot
from telegram.error import TelegramError

# ================= КОНФИГ =================
BOT_TOKEN = "8616925469:AAEA8xFaOdViyN06g1PETOKacQHkAsmJx9o"
CHANNEL_ID = "@DuhokCc"
CARDS_PER_RUN = 10000
SLEEP_INTERVAL_SECONDS = 7
POST_DELAY_SECONDS = 5

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# ========== LUHN АЛГОРИТМ (ПОЛНАЯ ПРОВЕРКА) ==========
def luhn_verify(card_number):
    """Проверяет, проходит ли полный номер карты проверку Luhn."""
    digits = [int(d) for d in str(card_number)]
    # Удваиваем каждую вторую цифру, начиная справа
    for i in range(len(digits) - 2, -1, -2):
        doubled = digits[i] * 2
        if doubled > 9:
            doubled = doubled - 9
        digits[i] = doubled
    total = sum(digits)
    return total % 10 == 0

def luhn_checksum(card_number):
    """Вычисляет контрольную цифру Luhn для первых 15 цифр."""
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return (10 - (checksum % 10)) % 10

def generate_card_number(bin_prefix):
    """Генерирует 16-значный номер, гарантированно проходящий Luhn."""
    prefix = str(bin_prefix)
    length = 16
    random_part = ''.join([str(random.randint(0, 9)) for _ in range(length - len(prefix) - 1)])
    base = prefix + random_part          # первые 15 цифр
    check = luhn_checksum(base)          # вычисляем 16-ю цифру
    full = base + str(check)
    # Двойная проверка – если вдруг ошибка, перегенерируем
    if not luhn_verify(full):
        logging.error(f"Сгенерирован невалидный номер: {full} – перегенерация")
        return generate_card_number(bin_prefix)  # рекурсия для гарантии
    return full

# ========== ФУНКЦИЯ ИСПРАВЛЕНИЯ НЕВАЛИДНОГО НОМЕРА ==========
def correct_luhn(card_number):
    """
    Принимает номер карты (16 цифр) и возвращает исправленный номер,
    проходящий Luhn, изменяя последнюю цифру.
    Если номер уже валиден – возвращает его без изменений.
    """
    num_str = str(card_number)
    if len(num_str) != 16 or not num_str.isdigit():
        return None
    if luhn_verify(num_str):
        return num_str
    # Берём первые 15 цифр и вычисляем правильную контрольную цифру
    base = num_str[:15]
    correct_check = luhn_checksum(base)
    corrected = base + str(correct_check)
    return corrected

def random_bin():
    """Генерирует случайный 6-значный BIN для Visa (4xxxxx) или MasterCard (51xxxx-55xxxx)."""
    brand = random.choice(["VISA", "MASTERCARD"])
    if brand == "VISA":
        bin_int = random.randint(400000, 499999)
    else:
        bin_int = random.randint(510000, 559999)
    return bin_int, brand

# ========== АТРИБУТЫ КАРТ ==========
BANKS = [
    "CHASE BANK", "BANK OF AMERICA", "CITIBANK", "WELLS FARGO",
    "CAPITAL ONE", "HSBC", "UBS", "PNC", "SCHOOLS FIRST FEDERAL",
    "CONTINENTAL BANK", "US BANK", "REGIONS BANK", "SUNTRUST"
]
CATEGORIES = ["standard", "gold", "platinum", "world", "signature", "premium", "debit enhanced", "classic"]
GATES = ["Antipublic", "Valid", "Premium", "Standard"]
STATUSES = ["Private", "Public", "Validated"]
CARD_TYPES = ["credit", "debit"]

def random_card():
    """Генерирует одну запись карты."""
    bin_choice, brand = random_bin()
    number = generate_card_number(bin_choice)
    month = f"{random.randint(1, 12):02d}"
    year = f"{random.randint(2027, 2031):02d}"
    cvv = f"{random.randint(100, 999):03d}"
    return {
        'number': number,
        'month': month,
        'year': year,
        'cvv': cvv,
        'bank': random.choice(BANKS),
        'brand': brand,
        'type': random.choice(CARD_TYPES),
        'category': random.choice(CATEGORIES),
        'country': "UNITED STATES",
        'gate': random.choice(GATES),
        'status': random.choice(STATUSES)
    }

def format_raw_line(card):
    return (f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}|"
            f"{card['bank']}|{card['brand']}|{card['type']}|{card['category']}|"
            f"{card['country']}|{card['gate']}|{card['status']}")

# ========== КЛАСС БОТА ==========
class CardBot:
    def __init__(self, token, channel):
        self.bot = Bot(token=token)
        self.channel = channel
        self.posted = set()

    async def post_card(self, card):
        # Дополнительная проверка перед отправкой – если невалидный, пропускаем
        if not luhn_verify(card['number']):
            logging.error(f"Luhn FAILED для {card['number']} – пропуск")
            return False

        line = format_raw_line(card)
        for attempt in range(3):
            try:
                await self.bot.send_message(chat_id=self.channel, text=line, parse_mode=None)
                logging.info(f"Опубликовано: {card['number'][:4]}****{card['number'][-4:]} | {card['bank']} | {card['category']}")
                self.posted.add(card['number'])
                return True
            except TelegramError as e:
                if "Flood" in str(e):
                    msg = str(e)
                    if "retry after" in msg:
                        wait = int(msg.split("retry after ")[1].split()[0])
                    else:
                        wait = 10
                    logging.warning(f"Flood wait {wait}s, повтор...")
                    await asyncio.sleep(wait)
                else:
                    logging.error(f"Ошибка: {e}")
                    await asyncio.sleep(5)
                    break
        return False

    async def run_single_cycle(self, count, delay):
        cards = [random_card() for _ in range(count)]
        random.shuffle(cards)
        logging.info(f"Сгенерировано {len(cards)} карт.")
        for idx, card in enumerate(cards, 1):
            if card['number'] in self.posted:
                continue
            success = await self.post_card(card)
            if idx % 100 == 0:
                logging.info(f"Прогресс: {idx}/{len(cards)}")
            await asyncio.sleep(delay if success else delay * 2)
        self.posted.clear()
        logging.info(f"Цикл завершён: {len(cards)} карт.")

    async def run_forever(self, cards_per_cycle, cycle_delay, post_delay):
        cycle = 0
        while True:
            cycle += 1
            logging.info(f"=== СТАРТ ЦИКЛА {cycle} ({cards_per_cycle} карт) ===")
            await self.run_single_cycle(cards_per_cycle, post_delay)
            logging.info(f"=== ЦИКЛ {cycle} ЗАВЕРШЁН. Сон {cycle_delay}с ===")
            await asyncio.sleep(cycle_delay)

async def main():
    bot = CardBot(BOT_TOKEN, CHANNEL_ID)
    await bot.run_forever(CARDS_PER_RUN, SLEEP_INTERVAL_SECONDS, POST_DELAY_SECONDS)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен.")
