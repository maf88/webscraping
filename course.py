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
Module containing the class object for handling a course.
The objects are:
    + Course
    + Chapters
    + Lectures
A course contains chapters, and a chapter contains lectures.
All those classes are derived by the abstract class ReferencerContainer.
"""

import re
import os
import logging

# Web
import urllib3
from selenium import webdriver


class ReferencerContainer:
    referencer: str = ""
    xpath: str = ""

    def __init__(self, title: str, link_id: str, url: str) -> None:
        self.title: str = title
        self.web_id: str = link_id
        self.url: str = url

    @classmethod
    def fetch_all_referencer_elements(cls, wdriver: webdriver) -> list:
        """
        """
        return wdriver.find_elements_by_xpath(cls.xpath)


class Course(ReferencerContainer):
    """ Data structure to get the URL for different courses. """

    referencer = "product"
    xpath = "//div[starts-with(@id, '" + referencer + "-')]"

    def __init__(self, title: str, link_id: str, url: str):
        super().__init__(title, link_id, url)
        self.chapters: Chapter = []


class Chapter(ReferencerContainer):
    """ Data structure to store informations about a course's chapter"""

    referencer = "category"
    xpath = "//a[starts-with(@id, '" + referencer + "-')]"

    def __init__(self, title: str, link_id: str, url: str):
        super().__init__(title, link_id, url)
        self.lectures: Lecture = []


class Lecture(ReferencerContainer):
    """ Data structure to store info about the lectures in a chapter.
        They reprensent the video to be downloaded. It's the atomic level
    """

    referencer: str = "post"
    xpath = "//a[starts-with(@id, '" + referencer + "-')]"

    def __init__(self, title: str, link_id: str, url: str):
        super().__init__(title, link_id, url)
        self._url_to_download: str = None

    @property
    def url_to_download(self):
        return self._url_to_download

    @url_to_download.setter
    def url_to_download(self, url):
        self._url_to_download = url

    def download_lecture(self, destination_path, filename, overwrite=False):
        """ Download the lecture to the destination folder path """
        with urllib3.PoolManager() as http:
            if self._url_to_download is None:
                msg = "There is no download link for this lecture: " + filename
                logging.warning(msg)
                raise FileNotFoundError(msg)

            dst = os.path.join(destination_path, filename)
            if overwrite or (not os.path.exists(dst)):
                r = http.request("GET", self._url_to_download)
                if r.status == 200:
                    with open(dst, "wb") as video:
                        video.write(r.data)
                else:
                    raise ConnectionError(
                        "Unbale to connect to the website to download the lecture"
                    )
            else:
                logging.warning("File '" + str(filename) + "' exists already.")


if __name__ == "__main__":
    # Unit test section
    import unittest

    class TestCourseClasses(unittest.TestCase):
        def get_dummy_variables(self) -> (str, str, str):
            """
            Return dummy variables to pass to a ReferencerContainer object's
            constructor
            """
            title = "Title"
            link_id = "123"
            url = "https://www.lipsum.com/"
            return (title, link_id, url)

        def test_static_variables(self):
            self.assertEqual(Course.referencer, "product")
            self.assertEqual(Chapter.referencer, "category")
            self.assertEqual(Lecture.referencer, "post")

        def test_objects_creation(self):
            def _test_basic_attributes(object: ReferencerContainer) -> None:
                self.assertEqual(object.title, title)
                self.assertEqual(object.web_id, link_id)
                self.assertEqual(object.url, url)

            # init test values
            title, link_id, url = self.get_dummy_variables()

            #
            # Course
            course = Course(title, link_id, url)
            _test_basic_attributes(course)

            # Chapter
            course.chapters.append(Chapter(title, link_id, url))
            chapter = course.chapters[0]
            _test_basic_attributes(chapter)


            # Lecture
            chapter.lectures.append(Lecture(title, link_id, url))
            lecture = chapter.lectures[0]
            _test_basic_attributes(lecture)
            self.assertFalse(lecture.url_to_download)

        def test_download(self):
            title, link_id, url = self.get_dummy_variables()
            lecture = Lecture(title, link_id, url)
            # Test 1
            with self.assertRaises(FileNotFoundError):
                lecture.download_lecture("/tmp/", ".tmp")
            # Test 2
            lecture.url_to_download = (
                "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"
            )
            lecture.download_lecture("/tmp/", "big_buck_bunny.mp4", True)
            self.assertTrue(os.path.isfile("/tmp/big_buck_bunny.mp4"))

    # Launching test sequence
    unittest.main()
