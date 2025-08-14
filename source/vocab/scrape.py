import requests
from bs4 import BeautifulSoup
import csv

def scrape_level(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        print(f"Failed to fetch: {url}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("table tr")
    data = []
    for tr in rows:
        cols = tr.find_all("td")
        if len(cols) >= 5:
            kanji = cols[1].get_text(strip=True).replace(";",",")
            onyomi = cols[2].get_text(strip=True).replace(";",",")
            kunyomi = cols[3].get_text(strip=True).replace(";",",")
            meaning = cols[4].get_text(strip=True).replace(";",",")
            if kanji:
                data.append({
                    "kanji": kanji + "%@",
                    "onyomi": onyomi + "%@",
                    "kunyomi": kunyomi + "%@",
                    "meaning": meaning + "%@"
                })
    return data

def main():
    for level in [5, 4, 3, 2, 1]:
        print(f"\n==== JLPT N{level} ====")
        all_data = []

        # Page 1 (base URL)
        base_url = f"https://jlptsensei.com/jlpt-n{level}-kanji-list/"
        all_data.extend(scrape_level(base_url))

        # Paginated pages (start from page 2)
        page = 2
        while True:
            paged_url = f"https://jlptsensei.com/jlpt-n{level}-kanji-list/page/{page}/"
            print(f"Scraping {paged_url} …")
            entries = scrape_level(paged_url)
            if not entries:
                print(f"No more pages for JLPT N{level}. Stopping at page {page}.")
                break
            all_data.extend(entries)
            page += 1

        # Write CSV
        output_file = f"jlpt_kanji_list_N{level}.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["kanji", "onyomi", "kunyomi", "meaning"])
            writer.writeheader()
            writer.writerows(all_data)

        print(f"✅ Wrote {len(all_data)} entries to {output_file}")

if __name__ == "__main__":
    main()
