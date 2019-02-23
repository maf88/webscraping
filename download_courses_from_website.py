# -*- coding: utf-8 -*-
# *******                                                               *******#
# *                     __  ___ ___     ______ ____   ____                  *#
# *                    /  |/  //   |   / ____/( __ ) ( __ )                 *#
# *                   / /|_/ // /| |  / /_   / __  |/ __  |                 *#
# *                  / /  / // ___ | / __/  / /_/ // /_/ /                  *#
# *                 /_/  /_//_/  |_|/_/     \____/ \____/                   *#
# *                                                                         *#
# *                    Copyright © 2019 Antoine Moevus  ALL RIGHTS RESERVED *#
# *******                                                               *******#

"""
A big module to download and save lectures on some kajabi websites. 
"""

import re
import os
import logging

# Web
import urllib3
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.remote_connection import LOGGER

# Types
from typing import List

# Containers
from course import Course as Course
from course import Chapter as Chapter
from course import Lecture as Lecture

#
# INITIALISATION SECTION
#


# Setting Up Logging File
logging.basicConfig(filename="log.log", filemode="w", level=logging.INFO)
logging.captureWarnings(True)
# Selenium
LOGGER.setLevel(logging.INFO)

#
#   Class SECTION
#


class UserPersonalData:
    """ 
    Website and login info for scraping.
    A `user.info` file shoud be present in the current directory.
    """

    def __init__(self):
        if not os.path.exists("./user.info"):
            raise FileNotFoundError("`user.info` was not found.")
        with open("user.info", "r") as user_info:
            line = user_info.readline()
            # Assign user info variables
            self.USERNAME, self.PASSWORD, self.MAIN_URL = line.split(" ")

        self.LOGIN_URL = self.MAIN_URL + "/login"
        self.URL = self.MAIN_URL + "/library"

    def goto_and_sign_into_website_from(self, webdriver: webdriver) -> None:
        """ Log in a website and update the given webdriver"""
        webdriver.get(self.LOGIN_URL)
        webdriver.find_element_by_id("member_email").send_keys(self.USERNAME)
        webdriver.find_element_by_id("member_password").send_keys(self.PASSWORD)
        webdriver.find_element_by_name("commit").click()
        # return self._wdriver


#
#   FUNCTION SECTION
#


def find_the_next_page_element(wdriver, class_ref):
    """
    Find the «Next» button in a page of a chapter
    """
    pagination_element = wdriver.find_element_by_xpath(
        "//div[@class='" + class_ref + "']"
    )
    next_page_element = pagination_element.find_element_by_xpath(
        ".//a[contains(text(), 'Next')]"
    )

    return next_page_element


#
# Getting attributes for a web element
def get_course_attributes(
    course_web_element: "A selenium WebElement object"
) -> (str, str, str):
    """
    """
    we = course_web_element
    title = we.find_element_by_class_name("title").text
    link_id = we.get_attribute("id")
    url = we.find_element_by_tag_name("a").get_attribute("href")
    return (title, link_id, url)

def get_chapter_attributes(
    chapter_web_element: "A selenium WebElement object"
) -> (str, str, str):
    """
    """
    we = chapter_web_element
    title = we.find_element_by_class_name("title").text
    link_id = we.get_attribute("id")
    url = we.get_attribute("href")
    return (title, link_id, url)

def get_lecture_attributes(
    lecture_web_element: "A selenium WebElement object"
) -> (str, str, str):
    """
    """
    we = lecture_web_element
    title = we.find_element_by_xpath(".//h4").text
    link_id = we.get_attribute("id")
    url = we.get_attribute("href")
    return (title, link_id, url)

#
# Helpers for downloading lectures
def fetch_lectures_in_current_page(wdriver) -> List[Lecture]:
    """
    Find all lectures in a page of a chapter. 
    """
    lectures = []
    page_lectures_element = Lecture.fetch_all_referencer_elements(wdriver)
    if len(page_lectures_element) == 0:
        raise Exception("This page shouldn't be scraped because it has no videos.")
    else:
        for element in page_lectures_element:
            title, link_id, url = get_lecture_attributes(element)
            new_lecture = Lecture(title, link_id, url)
            lectures.append(new_lecture)
    return lectures


def fetch_all_lectures_data(wdriver, chapter) -> None:
    """
    For a given chapter fetch all lectures information:
    title, link id, url and download url.
    """
    wdriver.get(chapter.url)
    lectures = []
    try:
        # Get videos lecture from the first page
        lectures += fetch_lectures_in_current_page(wdriver)
        # Now that the first page is finished
        # we are going to all the next page
        pagination_html_class = "pagination-custom"
        next_page_element = find_the_next_page_element(wdriver, pagination_html_class)
        while next_page_element.get_attribute("href") is not None:
            # Go to next page
            next_page_element.click()
            # Add all lectures
            lectures += fetch_lectures_in_current_page(wdriver)
            # Find the next page button
            next_page_element = find_the_next_page_element(
                wdriver, pagination_html_class
            )
    except NoSuchElementException:
        # There are no others pages in this chapters
        # Therefore we already got all the videos
        pass
    except:
        raise
    # Now that we have all the lectures of a chapter,
    # we need to find and set the download link
    for current in lectures:
        wdriver.get(current.url)
        # Get download link
        try:
            current.url_to_download = wdriver.find_element_by_xpath(
                "//a[contains(@class,'btn-video-download')]"
            ).get_attribute("href")
        except NoSuchElementException:
            current.url_to_download = None
        except:
            raise
    if lectures:
        chapter.lectures = lectures
    else:
        raise FileNotFoundError("There were no lectures in this chapter.")


def create_formated_path(titles: (str, str, str, int)) -> str:
    rootdir = "./BJJ/"
    ext = ".m4v"  # TODO: extract dynamically the extension
    path = titles[0] + "/" + titles[1]
    # Replace all the " " and unwanted character for "_"
    path = re.sub(r"[^\w\d\/\:\.-]", "_", path)
    filename = "%0*d" % (3, titles[3]) + "_" + re.sub(r"[^\w\d-]", "_", titles[2])
    return rootdir + path + "/" + filename + ext


#
#   MAIN SECTION
#

if __name__ == "__main__":

    def print_next_on_same_line(msg: str):
        print(msg, end=" ", flush=True)

    print("Starting program...")
    wdriver = webdriver.Firefox()
    user_info = UserPersonalData()
    user_info.goto_and_sign_into_website_from(wdriver)

    # Check if we are on a good page
    try:
        wdriver.find_element_by_class_name("library__title")
        logging.info("We signed in successfuly. Let's continue.")
    except:
        logging.error("Unsucceful signing in…")
        raise
    print("Successfully signed in.")

    # Find all available courses
    print_next_on_same_line("Retrieving all courses...")
    courses_element = Course.fetch_all_referencer_elements(wdriver)

    courses = []
    for element in courses_element:
        title, link_id, url = get_course_attributes(element)

        new_course = Course(title, link_id, url)
        courses.append(new_course)

    # For a given course find all the chapter
    print_next_on_same_line("... and all chapters...")
    for course in courses:  # DEBUG instead loop
        wdriver.get(course.url)
        try:
            wdriver.find_element_by_class_name("product-header")
            logging.info("We're on the good page. Let's continue.")
        except:
            logging.warning("We're on the wrong page")
            raise
        chapters_element = Chapter.fetch_all_referencer_elements(wdriver)

        chapters = []
        for element in chapters_element:
            title, link_id, url = get_chapter_attributes(element)
            new_chapter = Chapter(title, link_id, url)
            chapters.append(new_chapter)
        course.chapters = chapters

    logging.debug([{chapt.title: chapt.url} for chapt in courses[0].chapters])
    logging.debug([{chapt.title: chapt.url} for chapt in courses[1].chapters])

    # Find and fetch all lectures
    # The id of the posts are not necessarilly regularely increased. We need
    # to extract them all individually
    print_next_on_same_line("... and all lectures ...")
    try:
        [
            [
                fetch_all_lectures_data(wdriver, chapter) 
                for chapter in course.chapters
            ]
            for course in courses
        ]
    except Exception:
        raise
    print("Done.")
    wdriver.quit()
    print("Exiting website.")

    # Create folder structure for all courses and chapters
    print_next_on_same_line("Creating folder structure if necessary...")
    paths = []
    for course in courses:
        for chapter in course.chapters:
            for i, lecture in enumerate(chapter.lectures):
                path = create_formated_path(
                    (course.title, chapter.title, lecture.title, i)
                )
                paths.append(path)
    logging.debug(str(paths))
    print("Done.")

    # Download all videos
    print_next_on_same_line("Downloading all videos")
    path_it = iter(paths)
    for course in courses:
        for chapter in course.chapters:
            for the_lecture in chapter.lectures:
                try:
                    dirname, filename = os.path.split(next(path_it))
                except:
                    raise  # EOL
                for path in paths:
                    try:
                        os.makedirs(os.path.dirname(path))
                    except FileExistsError:
                        pass
                logging.info("\t".join(("Downloading", dirname, filename)))
                try:
                    the_lecture.download_lecture(dirname, filename, False)
                except FileExistsError:
                    pass
                except FileNotFoundError:
                    pass
                except:
                    raise
    print("Done.")

print("Program finished. Exiting!")
