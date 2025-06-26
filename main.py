import time
from pathlib import Path
from pprint import pprint
from yt_dlp import YoutubeDL as yt
import requests
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


def get_sections(driver: Chrome):
    try:
        bsoup = BeautifulSoup(driver.page_source, "html.parser")
        soup = bsoup.find("div", attrs={"class": "MaxWidthContainer_mwc__ID5AG"})
        sections = soup.find_all("section")[1:]
        return sections
    except Exception as e:
        print(e)


def get_video_by_title(title: str, videos: list):
    video = ""
    for key in videos:
        if videos[key].get("title").lower() == title.lower():
            video = videos[key]
            break
    return video


def get_video_by_section(section_title: str, data: dict):
    videos = []
    for key in data.keys():
        if key.lower() == section_title.lower():
            videos = data[key]
            break
    return videos


def download(video: dict, driver: Chrome):
    path: Path = video.get("location")
    path.parent.mkdir(parents=True, exist_ok=True)
    go_downlod(video.get("link"), path, driver)


def download_by(
    data: dict,
    driver: Chrome,
    by: str = "",
    section_title: str = "",
    video_title: str = "",
):
    videos = get_video_by_section(section_title, data)
    if by == "title":
        video = get_video_by_title(video_title, data)
        download(video, driver)
        return

    for video in videos:
        download(video, driver)


def go_downlod(url: str, path: Path, driver: Chrome):
    driver.get(url)
    time.sleep(2)

    xpath = '//*[@id="alt-play-module"]'
    driver.find_element(By.XPATH, xpath).click()
    time.sleep(33)

    vid = driver.find_element(By.TAG_NAME, "video")
    src = vid.get_dom_attribute("src")

    config = {"outtmpl": str(path), "format": "best"}
    try:
        with yt(config) as video:
            video.download([src])
    except Exception as e:
        print(e)


def scroll_into_view(driver: Chrome, element: WebElement, position: str = "center"):
    script = (
        "arguments[0].scrollIntoView({ behavior: 'smooth', block: '"
        + position
        + "', inline: '"
        + position
        + "' });"
    )

    driver.execute_script(script, element)


def process_path(path: str):
    return path.replace(":", " ").replace("-", "").replace(" ", "_")


if __name__ == "__main__":
    try:
        by = input("Download By: <Section | Title | All>: ")
        dwl_section = dwl_title = ""
        collection = False

        match by.lower():
            case "title":
                dwl_title = input("Title: ").strip()
                dwl_section = input("Section: ").strip()
            case "section":
                dwl_section = input("Section: ").strip()
            case "all":
                collection = True

        # Driver Options
        ops = ChromeOptions()
        ops.add_argument("disable-infobars")
        ops.add_argument("--start-maximized")
        # ops.add_argument("--headless")
        # ops.add_argument("--disable-gpu")
        ops.add_experimental_option("useAutomationExtension", False)
        ops.add_experimental_option("excludeSwitches", ["enable-automation"])
        # ops.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        # Start Selenium Driver
        driver = Chrome(options=ops)
        driver.implicitly_wait(10)

        # Got to website
        driver.get("https://www.nba.com/watch/featured")

        time.sleep(3)

        try:
            if collection:
                footer = driver.find_element(By.TAG_NAME, "footer")
                scroll_into_view(driver, footer)
            else:
                titles = driver.find_elements(By.TAG_NAME, "h1")
                for t in titles:
                    if t.text.strip().find(dwl_title.strip()) == 0:
                        scroll_into_view(driver, t)
        except Exception as e:
            print(e)

        sections = get_sections(driver)
        data = {}

        for section in sections:
            title = section.find("h1").text.strip()
            container = section.find(
                "div", attrs={"class": "CarouselDynamic_track__8ZP27"}
            )
            atrs = {"class": "CarouselDynamic_slide__EX9PK"}
            container = container.find_all("div", attrs=atrs)
            videos = []
            for video in container:
                link = video.find("a").attrs.get("href")
                if "https://" not in link:
                    link = f"https://nba.com{link}"
                video_title = video.find("h3").text.strip()
                location = Path(
                    ".",
                    process_path(title),
                    f"{process_path(video_title)}.mp4",
                )
                videos.append(
                    {
                        "title": video_title,
                        "link": link,
                        "location": location,
                    }
                )

            data[title] = videos

        if collection:
            for key in data.keys():
                for video in data[key]:
                    download(video)
        elif dwl_section is not None:
            download_by(
                data,
                driver=driver,
                section_title=dwl_section,
            )
        elif dwl_title is not None:
            download_by(
                data=data,
                by="title",
                driver=driver,
                section_title=dwl_section,
                video_title=dwl_section,
            )
    except Exception as e:
        print(e)
        driver.quit()
