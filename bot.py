# Telegram card generator – guaranteed Luhn-valid cards
# Channel: @iraq647
# Run: python bot.py

import asyncio
import logging
import random
from telegram import Bot
from telegram.error import TelegramError

# ================= CONFIG =================
BOT_TOKEN = "8616925469:AAEA8xFaOdViyN06g1PETOKacQHkAsmJx9o"
CHANNEL_ID = "@iraq647"
CARDS_PER_RUN = 10000
SLEEP_INTERVAL_SECONDS = 7
POST_DELAY_SECONDS = 5

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# ========== LUHN CORE (with auto-correction) ==========
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
    """Fix the last digit to make the number Luhn-valid."""
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

# ========== RANDOM BIN (no fixed list) ==========
def random_bin():
    brand = random.choice(["VISA", "MASTERCARD"])
    if brand == "VISA":
        bin_int = random.randint(400000, 499999)
    else:
        bin_int = random.randint(510000, 559999)
    bank = random.choice(["UNKNOWN BANK", "RANDOM BANK", "GENERIC BANK"])
    country = random.choice(["UNITED STATES", "MALAYSIA", "UNITED KINGDOM", "CANADA"])
    return bin_int, brand, bank, country

# ========== CARD GENERATION ==========
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

# ========== BOT ==========
class CardBot:
    def __init__(self, token, channel):
        self.bot = Bot(token=token)
        self.channel = channel
        self.posted = set()

    async def post_card(self, card):
        # 1) Correct Luhn if needed
        corrected = correct_luhn(card['number'])
        if corrected is None:
            logging.error(f"Unfixable: {card['number']} – skipping")
            return False
        if corrected != card['number']:
            logging.warning(f"Corrected {card['number']} -> {corrected}")
            card['number'] = corrected

        # 2) Final verification
        if not luhn_verify(card['number']):
            logging.error(f"Still invalid: {card['number']} – skipping")
            return False

        line = format_raw_line(card)
        for attempt in range(3):
            try:
                await self.bot.send_message(chat_id=self.channel, text=line, parse_mode=None)
                logging.info(f"Posted: {card['number'][:4]}****{card['number'][-4:]} ({card['country']})")
                self.posted.add(card['number'])
                return True
            except TelegramError as e:
                if "Flood" in str(e):
                    msg = str(e)
                    wait = int(msg.split("retry after ")[1].split()[0]) if "retry after" in msg else 10
                    logging.warning(f"Flood wait {wait}s, retry...")
                    await asyncio.sleep(wait)
                else:
                    logging.error(f"Error: {e}")
                    await asyncio.sleep(5)
                    break
        return False

    async def run_single_cycle(self, count, delay):
        cards = [random_card() for _ in range(count)]
        random.shuffle(cards)
        # Filter out any card that is not Luhn-valid (should be none)
        valid_cards = [c for c in cards if luhn_verify(c['number'])]
        logging.info(f"Generated {len(cards)} cards, valid: {len(valid_cards)}")
        for idx, card in enumerate(valid_cards, 1):
            if card['number'] in self.posted:
                continue
            success = await self.post_card(card)
            if idx % 100 == 0:
                logging.info(f"Progress: {idx}/{len(valid_cards)}")
            await asyncio.sleep(delay if success else delay * 2)
        self.posted.clear()
        logging.info(f"Cycle done: {len(valid_cards)} cards.")

    async def run_forever(self, cards_per_cycle, cycle_delay, post_delay):
        cycle = 0
        while True:
            cycle += 1
            logging.info(f"=== CYCLE {cycle} START ===")
            await self.run_single_cycle(cards_per_cycle, post_delay)
            logging.info(f"=== CYCLE {cycle} DONE. Sleeping {cycle_delay}s ===")
            await asyncio.sleep(cycle_delay)

async def main():
    bot = CardBot(BOT_TOKEN, CHANNEL_ID)
    await bot.run_forever(CARDS_PER_RUN, SLEEP_INTERVAL_SECONDS, POST_DELAY_SECONDS)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped.")
