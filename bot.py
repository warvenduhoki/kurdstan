# Бот для автоматической генерации и публикации карт каждые N секунд
# Установка: pip install python-telegram-bot
# Запуск: python bot.py  -> будет работать бесконечно, публикуя 10000 карт каждые 7 секунд (после цикла)

import asyncio
import logging
import randomhhhhh
import time
from telegram import Bot
from telegram.error import TelegramError

# ================= КОНФИГ =================
BOT_TOKEN = "8616925469:AAEA8xFaOdViyN06g1PETOKacQHkAsmJx9o"
CHANNEL_ID = "@DuhokCc"
CARDS_PER_RUN = 10000                # Изменено на 10000 по запросу
SLEEP_INTERVAL_SECONDS = 7           # Интервал между циклами – 7 секунд

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO, handlers=[logging.StreamHandler()])

# ========== ФУНКЦИИ ГЕНЕРАЦИИ BIN ==========
def random_bin():
    """Генерирует случайный 6-значный BIN для Visa (4xxxxx) или MasterCard (51xxxx-55xxxx)"""
    brand = random.choice(["VISA", "MASTERCARD"])
    if brand == "VISA":
        bin_int = random.randint(400000, 499999)
    else:
        bin_int = random.randint(510000, 559999)
    return bin_int, brand

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

def generate_card_number(bin_prefix):
    prefix = str(bin_prefix)
    length = 16
    random_part = ''.join([str(random.randint(0,9)) for _ in range(length - len(prefix) - 1)])
    base = prefix + random_part
    check = luhn_checksum(base)
    return base + str(check)

BANKS = ["CHASE BANK", "BANK OF AMERICA", "CITIBANK", "WELLS FARGO", 
         "CAPITAL ONE", "HSBC", "UBS", "PNC", "SCHOOLS FIRST FEDERAL",
         "CONTINENTAL BANK", "US BANK", "REGIONS BANK", "SUNTRUST"]
CATEGORIES = ["standard", "gold", "platinum", "world", "signature", "premium", "debit enhanced", "classic"]
GATES = ["Antipublic", "Valid", "Premium", "Standard"]
STATUSES = ["Private", "Public", "Validated"]
CARD_TYPES = ["credit", "debit"]

def random_card():
    bin_choice, brand = random_bin()
    number = generate_card_number(bin_choice)
    month = f"{random.randint(1, 12):02d}"
    year = f"{random.randint(2027, 2031):02d}"
    cvv = f"{random.randint(100, 999):03d}"
    bank = random.choice(BANKS)
    category = random.choice(CATEGORIES)
    card_type = random.choice(CARD_TYPES)
    country = "UNITED STATES"
    gate = random.choice(GATES)
    status = random.choice(STATUSES)
    return {
        'number': number, 'month': month, 'year': year, 'cvv': cvv,
        'bank': bank, 'brand': brand, 'type': card_type, 'category': category,
        'country': country, 'gate': gate, 'status': status
    }

def format_raw_line(card):
    return (f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}|"
            f"{card['bank']}|{card['brand']}|{card['type']}|{card['category']}|"
            f"{card['country']}|{card['gate']}|{card['status']}")

class CardBot:
    def __init__(self, token, channel):
        self.bot = Bot(token=token)
        self.channel = channel
        self.posted = set()

    async def post_card(self, card):
        line = format_raw_line(card)
        for attempt in range(3):
            try:
                await self.bot.send_message(chat_id=self.channel, text=line, parse_mode=None)
                logging.info(f"Posted: {card['number'][:4]}****{card['number'][-4:]} | {card['bank']} | {card['category']}")
                self.posted.add(card['number'])
                return True
            except TelegramError as e:
                if "Flood" in str(e):
                    wait = int(str(e).split("retry after ")[1].split()[0]) if "retry after" in str(e) else 10
                    logging.warning(f"Flood wait {wait}s, retrying...")
                    await asyncio.sleep(wait)
                else:
                    logging.error(f"Error: {e}")
                    await asyncio.sleep(5)
                    break
        return False

    async def run_single_cycle(self, count, delay=5):
        cards = [random_card() for _ in range(count)]
        random.shuffle(cards)
        logging.info(f"Cycle: generated {len(cards)} cards.")
        for idx, card in enumerate(cards, 1):
            if card['number'] in self.posted:
                continue
            success = await self.post_card(card)
            # Логируем прогресс каждые 100 карт
            if idx % 100 == 0:
                logging.info(f"Progress: {idx}/{len(cards)} cards posted.")
            await asyncio.sleep(delay if success else delay*2)
        self.posted.clear()
        logging.info(f"Cycle finished: all {len(cards)} cards processed.")

    async def run_forever(self, count, cycle_delay, post_delay=5):
        cycle_number = 0
        while True:
            cycle_number += 1
            logging.info(f"=== STARTING CYCLE {cycle_number} (generating {count} cards) ===")
            await self.run_single_cycle(count, post_delay)
            logging.info(f"=== CYCLE {cycle_number} FINISHED. Sleeping for {cycle_delay} seconds ===")
            await asyncio.sleep(cycle_delay)

async def main():
    bot = CardBot(BOT_TOKEN, CHANNEL_ID)
    await bot.run_forever(CARDS_PER_RUN, SLEEP_INTERVAL_SECONDS, post_delay=5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
