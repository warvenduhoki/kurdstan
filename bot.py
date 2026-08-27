# Бот с фиксированным списком BIN (полная версия)
# Канал: @kurdCcok
# Установка: pip install python-telegram-bot
# Запуск: python bot.py

import asyncio
import logging
import random
from telegram import Bot
from telegram.error import TelegramError

# ================= КОНФИГ =================
BOT_TOKEN = "8616925469:AAEA8xFaOdViyN06g1PETOKacQHkAsmJx9o"
CHANNEL_ID = "@kurdCcok"
CARDS_PER_RUN = 10000
SLEEP_INTERVAL_SECONDS = 7
POST_DELAY_SECONDS = 5

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# ========== ПОЛНЫЙ СПИСОК BIN (включая 519469 и 457553) ==========
BIN_DATA = [
    {"bin": 406179, "bank": "BANK OF AMERICA", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 449370, "bank": "CHASE BANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 415926, "bank": "CITIBANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 512014, "bank": "MAYBANK", "brand": "MASTERCARD", "country": "MALAYSIA"},
    {"bin": 442941, "bank": "BANK OF AMERICA", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 445178, "bank": "WELLS FARGO", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 444426, "bank": "CAPITAL ONE", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 414804, "bank": "CHASE BANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 422400, "bank": "CITIBANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 406189, "bank": "BANK OF AMERICA", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 407077, "bank": "PNC", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 415546, "bank": "US BANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 416900, "bank": "WELLS FARGO", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 486113, "bank": "CIMB BANK", "brand": "VISA", "country": "MALAYSIA"},
    {"bin": 528149, "bank": "PUBLIC BANK", "brand": "MASTERCARD", "country": "MALAYSIA"},
    {"bin": 436572, "bank": "RHB BANK", "brand": "VISA", "country": "MALAYSIA"},
    {"bin": 464413, "bank": "HONG LEONG BANK", "brand": "VISA", "country": "MALAYSIA"},
    {"bin": 426976, "bank": "AMBANK", "brand": "VISA", "country": "MALAYSIA"},
    {"bin": 453808, "bank": "BANK ISLAM", "brand": "VISA", "country": "MALAYSIA"},
    {"bin": 551149, "bank": "MAYBANK", "brand": "MASTERCARD", "country": "MALAYSIA"},
    {"bin": 402888, "bank": "CHASE BANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 415704, "bank": "CITIBANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 514989, "bank": "RHB BANK", "brand": "MASTERCARD", "country": "MALAYSIA"},
    {"bin": 440965, "bank": "BANK OF AMERICA", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 405305, "bank": "WELLS FARGO", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 536478, "bank": "PUBLIC BANK", "brand": "MASTERCARD", "country": "MALAYSIA"},
    {"bin": 454550, "bank": "CAPITAL ONE", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 402831, "bank": "CHASE BANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 412697, "bank": "CITIBANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 551541, "bank": "CIMB BANK", "brand": "MASTERCARD", "country": "MALAYSIA"},
    {"bin": 423698, "bank": "BANK OF AMERICA", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 400518, "bank": "CHASE BANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 536124, "bank": "HONG LEONG BANK", "brand": "MASTERCARD", "country": "MALAYSIA"},
    {"bin": 423862, "bank": "WELLS FARGO", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 440931, "bank": "CAPITAL ONE", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 402140, "bank": "CITIBANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 536319, "bank": "AMBANK", "brand": "MASTERCARD", "country": "MALAYSIA"},
    {"bin": 485170, "bank": "BANK ISLAM", "brand": "VISA", "country": "MALAYSIA"},
    {"bin": 464134, "bank": "MAYBANK", "brand": "VISA", "country": "MALAYSIA"},
    {"bin": 454562, "bank": "BANK OF AMERICA", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 409526, "bank": "CHASE BANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 439497, "bank": "CITIBANK", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 540656, "bank": "PUBLIC BANK", "brand": "MASTERCARD", "country": "MALAYSIA"},
    {"bin": 554337, "bank": "MAYBANK", "brand": "MASTERCARD", "country": "MALAYSIA"},
    {"bin": 447938, "bank": "WELLS FARGO", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 418544, "bank": "CAPITAL ONE", "brand": "VISA", "country": "UNITED STATES"},
    {"bin": 519469, "bank": "UNKNOWN", "brand": "MASTERCARD", "country": "UNITED STATES"},
    {"bin": 457553, "bank": "UNKNOWN", "brand": "VISA", "country": "UNITED STATES"},
]

def random_bin():
    entry = random.choice(BIN_DATA)
    return entry["bin"], entry["brand"], entry["bank"], entry["country"]

# ========== LUHN С АВТОКОРРЕКЦИЕЙ ==========
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
    bin_choice, brand, bank, country = random_bin()
    number = generate_card_number(bin_choice)
    month = f"{random.randint(1, 12):02d}"
    year = f"{random.randint(2027, 2031):02d}"
    cvv = f"{random.randint(100, 999):03d}"
    card_type = random.choice(["credit", "debit"])
    category = random.choice(["platinum", "signature", "premium", "world", "standard"])
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
