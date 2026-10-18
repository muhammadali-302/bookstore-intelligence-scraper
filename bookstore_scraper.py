# Assignment 2 - The Bookstore Intelligence Mission
# Part 1: scrape https://books.toscrape.com/ and save competitor_books.csv
# Part 2: answer the business questions from the scraped data

import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt

BASE_URL = "https://books.toscrape.com/catalogue/"
PAGE_URL = "https://books.toscrape.com/catalogue/page-{}.html"

# The site stores ratings as words, so we convert them to numbers
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

# Number of pages to scrape (5 = bonus 1, 50 = boss level: whole catalogue)
NUM_PAGES = 5


# =====================================================
# PART 1 - SCRAPING
# =====================================================
def scrape_page(page_number):
    """Scrape one catalogue page and return a list of book records."""
    url = PAGE_URL.format(page_number)
    response = requests.get(url)
    response.encoding = "utf-8"          # fixes the weird symbol before the price
    soup = BeautifulSoup(response.text, "html.parser")

    books = []
    # every book sits inside <article class="product_pod">
    for card in soup.find_all("article", class_="product_pod"):
        title = card.h3.a["title"]
        price_text = card.find("p", class_="price_color").text
        price = float(price_text.replace("£", "").strip())

        # rating is in the class name, e.g. class="star-rating Three"
        rating_word = card.find("p", class_="star-rating")["class"][1]
        rating = RATING_MAP[rating_word]

        availability = card.find("p", class_="instock availability").text.strip()

        # bonus 2: product page URL
        link = BASE_URL + card.h3.a["href"].replace("catalogue/", "")

        books.append({
            "Title": title,
            "Price": price,
            "Rating": rating,
            "Availability": availability,
            "URL": link,
        })
    return books


all_books = []
for page in range(1, NUM_PAGES + 1):
    page_books = scrape_page(page)
    print(f"Page {page}: {len(page_books)} books")
    all_books.extend(page_books)

df = pd.DataFrame(all_books)
print(df.head())
print(df.dtypes)
print("Total rows:", len(df))

df.to_csv("competitor_books.csv", index=False)
print("Saved competitor_books.csv")


# =====================================================
# PART 2 - INTELLIGENCE ANALYSIS
# =====================================================
priciest = df.loc[df["Price"].idxmax()]
print("\n1. Most expensive:", priciest["Title"], "- £", priciest["Price"])

cheapest = df.loc[df["Price"].idxmin()]
print("2. Cheapest:", cheapest["Title"], "- £", cheapest["Price"])

print("3. Average price: £", round(df["Price"].mean(), 2))

five_star = df[df["Rating"] == 5]
print("4. Number of 5-star books:", len(five_star))

in_stock_pct = (df["Availability"] == "In stock").mean() * 100
print("5. Percent in stock:", round(in_stock_pct, 1), "%")

print("6. Top 5 highest-rated books (ties broken by lower price):")
top5 = df.sort_values(["Rating", "Price"], ascending=[False, True]).head(5)
print(top5[["Title", "Price", "Rating"]].to_string(index=False))

cheap5 = five_star.loc[five_star["Price"].idxmin()]
print("7. Cheapest 5-star book:", cheap5["Title"], "- £", cheap5["Price"])

# ---------- Bonus 3 and 4: rating counts and bar chart ----------
counts = df["Rating"].value_counts().sort_index()
print("\nBooks per rating level:")
print(counts)

counts.plot(kind="bar")
plt.title("Number of books per star rating")
plt.xlabel("Star rating")
plt.ylabel("Number of books")
plt.tight_layout()
plt.savefig("rating_counts.png")

# ---------- CEO challenge: best total stars for £100 ----------
# Each book can be bought once. We work in pence so the maths is exact.
# best[m] = most stars we can get while spending at most m pence.
budget = 10000
prices = (df["Price"] * 100).round().astype(int).tolist()
ratings = df["Rating"].tolist()

best = [0] * (budget + 1)
chosen = [[] for _ in range(budget + 1)]
for i in range(len(df)):
    for m in range(budget, prices[i] - 1, -1):
        if best[m - prices[i]] + ratings[i] > best[m]:
            best[m] = best[m - prices[i]] + ratings[i]
            chosen[m] = chosen[m - prices[i]] + [i]

picked = df.iloc[chosen[budget]]
print("\nCEO £100 challenge - selected books:")
print(picked[["Title", "Price", "Rating"]].to_string(index=False))
print("Total cost: £", round(picked["Price"].sum(), 2))
print("Total rating score:", picked["Rating"].sum())
