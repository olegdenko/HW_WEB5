import platform
import json
import aiohttp
import asyncio
import sys
from datetime import datetime, timedelta


async def get_exchange(days):
    try:
        exchange_data = []

        async with aiohttp.ClientSession() as session:
            for day in range(days + 1):
                date = datetime.now().date() - timedelta(day)
                date_str = date.strftime("%d.%m.%Y")
                api = f"https://api.privatbank.ua/p24api/exchange_rates?date={date_str}"

                async with session.get(api) as response:
                    data = await response.json()
                    exchange_rates = data.get("exchangeRate", [])
                    eur_rate = next(
                        (rate for rate in exchange_rates if rate["currency"] == "EUR"),
                        None,
                    )
                    usd_rate = next(
                        (rate for rate in exchange_rates if rate["currency"] == "USD"),
                        None,
                    )

                    if eur_rate and usd_rate:
                        day_data = {
                            date_str: {
                                "EUR": {
                                    "sale": eur_rate["saleRate"],
                                    "purchase": eur_rate["purchaseRate"],
                                },
                                "USD": {
                                    "sale": usd_rate["saleRate"],
                                    "purchase": usd_rate["purchaseRate"],
                                },
                            }
                        }
                        exchange_data.append(day_data)

            return json.dumps(exchange_data, indent=2)

    except ValueError:
        return "Network error"


if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        days = 0
        try:
            parts = int(sys.argv[1])
            if parts:
                days = min(int(parts), 10)
        except IndexError:
            print("Please write number")
        print(days)

    r = asyncio.run(get_exchange(days))
    print(r)
