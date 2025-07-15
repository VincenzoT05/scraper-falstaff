from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import random
import os
import pandas as pd

def wait_random():
    time.sleep(random.uniform(2.5, 4.5))


def estrai_email(sp):
    mailto_links = sp.select("a[href^='mailto:']")
    for tag in mailto_links:
        href = tag.get("href", "")
        if "@" in href:
            return href.replace("mailto:", "").split("?")[0].strip()
    return ""


def estrai_indirizzo(sp):
    contenitore = sp.select_one("div.address")
    if not contenitore:
        return ""

    p_tag = contenitore.find("p")
    if not p_tag:
        return ""

    righe = [line.strip() for line in p_tag.get_text(separator="\n").split("\n") if line.strip()]

    righe_indirizzo = []
    for riga in righe:
        if ("@" in riga) or ("+41" in riga) or riga.lower().startswith("tel") or riga.lower().startswith(
                "www") or riga.lower().startswith("http"):
            continue
        righe_indirizzo.append(riga)

    return ", ".join(righe_indirizzo)


def estrai_telefono(sp):
    tag = sp.select_one("span.tel-desktop")
    if tag:
        return tag.get_text(strip=True)
    tag = sp.select_one("a.tel-mobile")
    if tag:
        return tag.get_text(strip=True)
    return ""


def estrai_sito(sp):
    tag = sp.select_one("div.address a[href^='http']")
    if tag and "mailto:" not in tag["href"]:
        return tag["href"]
    return ""


options = ChromeOptions()
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

output_file = "falstaff_bars.xlsx"

data = []

page = 1
totale = 0

while True:
    if page == 1:
        url = "https://www.falstaff.com/ch/bars"
    else:
        url = f"https://www.falstaff.com/ch/bars?page={page}"

    print(f"📄 Caricamento pagina {page}")
    driver.get(url)
    wait_random()

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.select("a.item[href^='/ch/bars/']")
    if not cards:
        print("✅ Nessun altro bar trovato. Fine.")
        break

    links = list(set("https://www.falstaff.com" + card["href"] for card in cards))
    print(f"🔗 {len(links)} BAR trovati nella pagina {page}")

    for i, link in enumerate(links, start=1):
        try:
            driver.get(link)
            wait_random()
            sp = BeautifulSoup(driver.page_source, "html.parser")

            nome = sp.select_one("h1").get_text(strip=True) if sp.select_one("h1") else ""
            indirizzo = estrai_indirizzo(sp)
            telefono = estrai_telefono(sp)
            email = estrai_email(sp)
            sito = estrai_sito(sp)

            data.append({
                "Nome": nome,
                "Indirizzo": indirizzo,
                "Telefono": telefono,
                "Email": email,
                "Sito Web": sito,
                "Link": link
            })
            totale += 1
            print(f"✓ {totale} | {nome}")

        except Exception as e:
            print(f"❌ Errore su {link}: {e}")
            continue

    page += 1

driver.quit()
df = pd.DataFrame(data)
df.to_excel(output_file, index=False)
print(f"✅ Scraping completato. Totale BAR: {totale}")
print(f"Dati salvati in {output_file}")
