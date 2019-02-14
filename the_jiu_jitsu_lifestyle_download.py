# -*- coding: utf-8 -*-
#*******                                                               *******#
 #*                     __  ___ ___     ______ ____   ____                  *#
 #*                    /  |/  //   |   / ____/( __ ) ( __ )                 *#
 #*                   / /|_/ // /| |  / /_   / __  |/ __  |                 *#
 #*                  / /  / // ___ | / __/  / /_/ // /_/ /                  *#
 #*                 /_/  /_//_/  |_|/_/     \____/ \____/                   *#
 #*                                                                         *#
 #*                    Copyright © 2018 Antoine Moevus  ALL RIGHTS RESERVED *#
#*******                                                               *******#

import re
import os
# Web
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
# Logging
import logging
logging.basicConfig(filename="log.log",level=logging.DEBUG)


# Load User Personal Data
with open("user.info", 'r') as user_info:
    line = user_info.readline()
    # Assign user info variables
    USERNAME, PASSWORD, MAIN_URL = line.split(" ")

LOGIN_URL = MAIN_URL + "/login"
URL = MAIN_URL  + "/library"

#
#   CLASS SECTION
#

class Course():
    """ Data structure to get the URL for different courses on TJJLS. """
    def __init__(self, title: str, link_id: str, url: str):
        self.title = title
        self.web_id = link_id
        self.url = url
        self.chapters = {}
    
    def get_current_course_name(self):
        pass


class Chapter:
    """ Data structure to store informations about a course's chapter"""
    referencer: str ="category"
    def __init__(self, title: str, 
            link_id: str, 
            url: str):
        self.title = title
        self.web_id = link_id
        self.url = url
 

class Lecture:
    """ Data structure to store info about the lectures in a chapter. 
        They reprensent the video to be downloaded. It's the atomic level
    """
    referencer = "post"

    def __init__(self, title: str, 
            link_id: str, 
            url: str):
        self.title = title
        self.web_id = link_id
        self.url = url
        self._url_to_download: str

    
    @property
    def url_to_download(self):
        return self._url_to_download
    @url_to_download.setter
    def url_to_download(self, url):
        self._url_to_download = url



#
#   FUNCTION SECTION
#


def site_login(driver):
    """ Log in a website through a Selenium webdriver"""
    driver.get(LOGIN_URL)
    driver.find_element_by_id("member_email").send_keys(USERNAME)
    driver.find_element_by_id("member_password").send_keys(PASSWORD)
    driver.find_element_by_name("commit").click()
    return driver

def find_the_next_page_element(wdriver, class_ref):
    """ 
    Find the «Next» button in a page of a chapter 
    """
    pagination_element = \
        (wdriver
          .find_element_by_xpath("//div[@class='" + class_ref + "']"))
    next_page_element = \
        (pagination_element
          .find_element_by_xpath(".//a[contains(text(), 'Next')]"))
    
    return next_page_element

def get_lectures_in_a_pages(wdriver):
    """
    Find all lectures in a page of a chapter
    """
    lectures = []
    ref = Lecture.referencer
    page_lectures_element =  (wdriver
                                .find_elements_by_xpath("//a[starts-with(@id, '"+ref+"-')]"))
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




#
#   MAIN SECTION
#

if __name__ == "__main__":
    wdriver = webdriver.Firefox()
    site_login(wdriver)

    # Check if we are on a good page
    try: 
        wdriver.find_element_by_class_name("library__title")
        logging.info("We're on the good page. Let's continue.")
    except:
        logging.error("We're on the wrong page")
        raise

    # Find all available courses
    courses_element = wdriver.find_elements_by_xpath("//div[starts-with(@id, 'product-')]")
    courses = []
    for ce in courses_element:
        title = ce.find_element_by_class_name("title").text
        # Getting the course unique id and adding it to the course
        link_id = ce.get_attribute("id")
        url = ce.find_element_by_tag_name("a").get_attribute("href")
        
        new_course = Course(title, link_id, url)
        courses.append(new_course)


    #print([{course.web_id: course.url} for course in courses]) #DEBUG

    # For a given course find all the chapter
    course_test = courses[0] #DEBUG instead loop
    wdriver.get(course_test.url)
    try: 
        wdriver.find_element_by_class_name("product-header")
        logging.info("We're on the good page. Let's continue.")
    except:
        logging.error("We're on the wrong page")
        raise
            
    chapters_element = wdriver.find_elements_by_xpath("//a[starts-with(@id, 'category-')]")
    #print(len(chapters_element)) #DEBUG

    chapters = []
    for chapt in chapters_element:
        title = chapt.find_element_by_class_name("title").text
        link_id = chapt.get_attribute("id")
        url = chapt.get_attribute("href")
        new_chapter = Chapter(title,link_id,url)
        chapters.append(new_chapter)
    
    #print([{chapt.title: chapt.url} for chapt in chapters]) #DEBUG


    # Get all lectures
    # The id of the posts are not necessarilly a continuous range. We need
    # to extract them all
    chapter_test = chapters[0]
    wdriver.get(chapter_test.url)

    try:
        # Get videos lecture from the first page
        lectures = []
        lectures += get_lectures_in_a_pages(wdriver)

        # Now that the first page is finished
        # we are going to all the next page
        pagination_html_class = "pagination-custom"
        next_page_element = find_the_next_page_element(wdriver, pagination_html_class)

        while next_page_element.get_attribute("href") is not None:
            # Go to next page
            next_page_element.click()
            # Add all lectures
            lectures += get_lectures_in_a_pages(wdriver)
            # Find the next page button
            next_page_element = find_the_next_page_element(wdriver, pagination_html_class)

            #print([l.url for l in lectures]) # DEBUG
    except:
        raise


    # Now that we have all the lectures of a chapter, 
    # we need to find and set the download link

    for current in lectures:
        wdriver.get(current.url)
        # Get download link
        current.url_to_download = \
            (wdriver
              .find_element_by_xpath("//a[contains(@class,'btn-video-download')]")
              .get_attribute("href"))
    #print(lectures[-1].url_to_download) #DEBUG


    # Create folders per chapters and 
    # Download all videos
    print("Number of videos to download: ", len(lectures) )

"""
#FUTURE For future usage derive class item from refereceable
class Referenceable:
   def __init__(self, title:str, link_id:  str, url:  str):
        self.title = title
        self.web_id = link_id
        self.url = url
"""