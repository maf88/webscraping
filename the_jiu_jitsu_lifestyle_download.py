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
A big module to download and save. 
"""

import re
import os
import logging

# Web
import urllib3
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.remote_connection import LOGGER


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

# Load User Personal Data
with open("user.info", "r") as user_info:
    line = user_info.readline()
    # Assign user info variables
    USERNAME, PASSWORD, MAIN_URL = line.split(" ")

LOGIN_URL = MAIN_URL + "/login"
URL = MAIN_URL + "/library"

#
#   FUNCTION SECTION
#


def goto_and_sign_into_website_from(webdriver):
    """ Log in a website through a Selenium webdriver"""
    webdriver.get(LOGIN_URL)
    webdriver.find_element_by_id("member_email").send_keys(USERNAME)
    webdriver.find_element_by_id("member_password").send_keys(PASSWORD)
    webdriver.find_element_by_name("commit").click()
    return webdriver


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


def fetch_lectures_in_current_page(wdriver):
    """
    Find all lectures in a page of a chapter
    """
    lectures = []
    ref = Lecture.referencer
    page_lectures_element = wdriver.find_elements_by_xpath(
        "//a[starts-with(@id, '" + ref + "-')]"
    )
    if len(page_lectures_element) == 0:
        raise Exception("This page shouldn't be loaded because it has no videos.")
    else:
        for lecture in page_lectures_element:
            title = lecture.find_element_by_xpath(".//h4").text
            link_id = lecture.get_attribute("id")
            url = lecture.get_attribute("href")
            new_lecture = Lecture(title, link_id, url)
            lectures.append(new_lecture)
    return lectures


def fetch_all_lectures_data(wdriver, chapter):
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


#
#   MAIN SECTION
#

if __name__ == "__main__":
    print("Starting program.")
    wdriver = webdriver.Firefox()
    goto_and_sign_into_website_from(wdriver)

    # Check if we are on a good page
    try:
        wdriver.find_element_by_class_name("library__title")
        logging.info("We signed in successfuly. Let's continue.")
    except:
        logging.error("Unsucceful signing in…")
        raise
    print("Successfully signed in.")

    # Find all available courses
    print("Retrieving all courses...", end=" ")
    ref = Course.referencer
    courses_element = wdriver.find_elements_by_xpath(
        "//div[starts-with(@id, '" + ref + "-')]"
    )
    courses = []
    for ce in courses_element:
        title = ce.find_element_by_class_name("title").text
        # Getting the course unique id and adding it to the course
        link_id = ce.get_attribute("id")
        url = ce.find_element_by_tag_name("a").get_attribute("href")

        new_course = Course(title, link_id, url)
        courses.append(new_course)

    # For a given course find all the chapter
    print("... and all chapters...", end=" ")
    for course in courses:  # DEBUG instead loop
        wdriver.get(course.url)
        try:
            wdriver.find_element_by_class_name("product-header")
            logging.info("We're on the good page. Let's continue.")
        except:
            logging.warning("We're on the wrong page")
            raise
        ref = Chapter.referencer
        chapters_element = wdriver.find_elements_by_xpath(
            "//a[starts-with(@id, '" + ref + "-')]"
        )

        chapters = []
        for chapt in chapters_element:
            title = chapt.find_element_by_class_name("title").text
            link_id = chapt.get_attribute("id")
            url = chapt.get_attribute("href")
            new_chapter = Chapter(title, link_id, url)
            chapters.append(new_chapter)
        course.chapters = chapters

    logging.debug([{chapt.title: chapt.url} for chapt in courses[0].chapters])
    logging.debug([{chapt.title: chapt.url} for chapt in courses[1].chapters])

    # Fetch all lectures
    # The id of the posts are not necessarilly regularely increased. We need
    # to extract them all individually
    print("... and all lecturses.")
    try:
        [
            [fetch_all_lectures_data(wdriver, chapter) for chapter in course.chapters]
            for course in courses
        ]
    except Exception:
        raise
    wdriver.quit()
    print("Exiting website.")

    # Create folder structure for all courses and chapters
    print("Creating folder structure if necessary.", end="\t")
    paths = []
    for course in courses:
        course_name = course.title
        for chapter in course.chapters:
            chapter_name = chapter.title
            for i, lecture in enumerate(chapter.lectures):
                path = course_name + "/" + chapter_name
                # Replace all the " " and unwanted character for "_"
                path = re.sub(r"[^\w\d\/\:\.-]", "_", path)
                filename = (
                    "%0*d" % (3, i) + "_" + re.sub(r"[^\w\d-]", "_", lecture.title)
                )
                path = (
                    "./BJJ/" + path + "/" + filename + ".m4v"
                )  # TODO: extract dynamically the extension
                paths.append(path)
    logging.debug(str(paths))
    print("Done.")

    # Download all videos
    print("Downloading all videos", end="\t")
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

print("Program finished. Done!. Exiting.")
