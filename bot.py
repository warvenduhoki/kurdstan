# Бот с поддержкой BIN США и Малайзии
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

# Вероятность выбора Малайзии (остальное – США)
MALAYSIA_PROBABILITY = 0.3   # 30% малайзийских карт

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# ========== BIN СПИСКИ ПО СТРАНАМ ==========
USA_BINS = {
    "MASTERCARD": [
        517805, 553604, 544235, 525470, 542418, 530719,
        531983, 527421, 556787, 521333, 514420, 546213, 531257
    ],
    "VISA": [
        414720, 471692, 476185, 424232, 465861, 428343,
        491956, 450505, 403590, 498405, 412952
    ]
}

# Известные BIN Малайзии (Maybank, CIMB, Public Bank, RHB, Hong Leong)
# Источник: общедоступные данные, проверьте актуальность
MALAYSIA_BINS = {
    "MASTERCARD": [
        552214,  # Maybank
        542908,  # Maybank
        548746,  # CIMB
        553014,  # Public Bank
        521789,  # RHB
        535865,  # Hong Leong
        527044,  # AmBank
        556158,  # Bank Islam
    ],
    "VISA": [
        451654,  # Maybank
        447848,  # CIMB
        456290,  # Public Bank
        462734,  # RHB
        453321,  # Hong Leong
        465955,  # AmBank
        471269,  # Bank Islam
    ]
}

# Банки для атрибутов
BANKS_USA = [
    "CITIBANK", "CHASE BANK", "BANK OF AMERICA", "WELLS FARGO",
    "CAPITAL ONE", "HSBC", "UBS", "COASTAL COMMUNITY BANK",
    "CONTINENTAL BANK", "SCHOOLS FIRST FEDERAL", "US BANK", "PNC"
]
BANKS_MALAYSIA = [
    "MAYBANK", "CIMB BANK", "PUBLIC BANK", "RHB BANK",
    "HONG LEONG BANK", "AMBANK", "BANK ISLAM"
]

CATEGORIES_USA = ["platinum", "signature", "premium", "world", "world elite", "debit enhanced", "standard"]
CATEGORIES_MALAYSIA = ["platinum", "gold", "classic", "world", "signature"]

def random_bin():
    """Выбор BIN из США или Малайзии с заданной вероятностью."""
    if random.random() < MALAYSIA_PROBABILITY:
        country = "MALAYSIA"
        brand = random.choice(["MASTERCARD", "VISA"])
        bin_choice = random.choice(MALAYSIA_BINS[brand])
        bank = random.choice(BANKS_MALAYSIA)
        category = random.choice(CATEGORIES_MALAYSIA)
        country_name = "MALAYSIA"
    else:
        country = "USA"
        brand = random.choice(["MASTERCARD", "VISA"]) if random.random() < 0.7 else "VISA"
        bin_choice = random.choice(USA_BINS[brand])
        bank = random.choice(BANKS_USA)
        category = random.choice(CATEGORIES_USA)
        country_name = "UNITED STATES"
    return bin_choice, brand, bank, category, country_name

# ========== LUHN ==========
def luhn_verify(card_number):
    digits = [int(d) for d in str(card_number)]
    for i in range(len(digits) - 2, -1, -2):
        doubled = digits[i] * 2
        if doubled > 9:
            doubled -= 9
        digits[i] = doubled
    return sum(digits) % 10 == 0

def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return (10 - (checksum % 10)) % 10

def correct_luhn(card_number):
    num_str = str(card_number).strip()
    if len(num_str) != 16 or not num_str.isdigit():
        return None
    if luhn_verify(num_str):
        return num_str
    base = num_str[:15]
    correct_check = luhn_checksum(base)
    return base + str(correct_check)

def generate_card_number(bin_prefix):
    prefix = str(bin_prefix)
    length = 16
    random_part = ''.join([str(random.randint(0, 9)) for _ in range(length - len(prefix) - 1)])
    base = prefix + random_part
    check = luhn_checksum(base)
    full = base + str(check)
    corrected = correct_luhn(full)
    if corrected is None:
        return generate_card_number(bin_prefix)
    return corrected

# ========== ГЕНЕРАЦИЯ КАРТЫ ==========
def random_card():
    bin_choice, brand, bank, category, country = random_bin()
    number = generate_card_number(bin_choice)
    month = f"{random.randint(1, 12):02d}"
    year = f"{random.randint(2027, 2031):02d}"
    cvv = f"{random.randint(100, 999):03d}"
    card_type = random.choice(["credit", "debit"])
    gate = random.choice(["Chaos Auth", "Antipublic", "Premium"])
    status = random.choice(["Private", "Validated"])
    return {
        'number': number,
        'month': month,
        'year': year,
        'cvv': cvv,
        'bank': bank,
        'brand': brand,
        'type': card_type,
        'category': category,
        'country': country,
        'gate': gate,
        'status': status
    }

def format_raw_line(card):
    return (f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}|"
            f"{card['bank']}|{card['brand']}|{card['type']}|{card['category']}|"
            f"{card['country']}|{card['gate']}|{card['status']}")

# ========== БОТ ==========
class CardBot:
    def __init__(self, token, channel):
        self.bot = Bot(token=token)
        self.channel = channel
        self.posted = set()

    async def post_card(self, card):
        corrected = correct_luhn(card['number'])
        if corrected is None:
            logging.error(f"Неверный номер: {card['number']} – пропуск")
            return False
        if corrected != card['number']:
            logging.warning(f"Исправлен {card['number']} -> {corrected}")
            card['number'] = corrected

        line = format_raw_line(card)
        for attempt in range(3):
            try:
                await self.bot.send_message(chat_id=self.channel, text=line, parse_mode=None)
                logging.info(f"Опубликовано: {card['number'][:4]}****{card['number'][-4:]} ({card['country']})")
                self.posted.add(card['number'])
                return True
            except TelegramError as e:
                if "Flood" in str(e):
                    msg = str(e)
                    wait = int(msg.split("retry after ")[1].split()[0]) if "retry after" in msg else 10
                    logging.warning(f"Flood wait {wait}s, retry...")
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
            logging.info(f"=== ЦИКЛ {cycle} СТАРТ ===")
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
