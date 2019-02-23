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
All those classes are derived by the abstract class ReferenceContainer.
"""

import re
import os
import logging

# Web
import urllib3


class ReferenceContainer:
    referencer: str = ""

    def __init__(self, title: str, link_id: str, url: str) -> None:
        self.title: str = title
        self.web_id: str = link_id
        self.url: str = url


class Course(ReferenceContainer):
    """ Data structure to get the URL for different courses. """

    referencer: str = "product"

    def __init__(self, title: str, link_id: str, url: str):
        super().__init__(title, link_id, url)
        self.chapters: Chapter = []


class Chapter(ReferenceContainer):
    """ Data structure to store informations about a course's chapter"""

    referencer: str = "category"

    def __init__(self, title: str, link_id: str, url: str):
        super().__init__(title, link_id, url)
        self.lectures: Lecture = []


class Lecture(ReferenceContainer):
    """ Data structure to store info about the lectures in a chapter.
        They reprensent the video to be downloaded. It's the atomic level
    """

    referencer: str = "post"

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

            r = http.request("GET", self._url_to_download)
            if r.status == 200:
                dst = os.path.join(destination_path, filename)
                if overwrite or (not os.path.exists(dst)):
                    with open(dst, "wb") as video:
                        video.write(r.data)
                else:
                    raise FileExistsError("File exists already")

            else:
                raise ConnectionError(
                    "Unbale to connect to the website to download the lecture"
                )


if __name__ == "__main__":
    # Unit test section
    import unittest

    class TestCourseClasses(unittest.TestCase):
        def get_dummy_variables(self) -> (str, str, str):
            """
            Return dummy variables to pass to a ReferenceContainer object's
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
            # init test values
            title, link_id, url = self.get_dummy_variables()

            #
            # Course
            course = Course(title, link_id, url)
            self.assertEqual(course.title, title)
            self.assertEqual(course.web_id, link_id)
            self.assertEqual(course.url, url)

            # Chapter
            course.chapters.append(Chapter(title, link_id, url))
            chapter = course.chapters[0]
            self.assertEqual(chapter.title, title)
            self.assertEqual(chapter.web_id, link_id)
            self.assertEqual(chapter.url, url)

            # Lecture
            chapter.lectures.append(Lecture(title, link_id, url))
            lecture = chapter.lectures[0]
            self.assertEqual(lecture.title, title)
            self.assertEqual(lecture.web_id, link_id)
            self.assertEqual(lecture.url, url)
            self.assertFalse(lecture.url_to_download)

        def test_download(self):
            title, link_id, url = self.get_dummy_variables()
            lecture = Lecture(title, link_id, url)
            # Test
            with self.assertRaises(FileNotFoundError):
                lecture.download_lecture("/tmp/", ".tmp")
            # Test
            lecture.url_to_download = (
                "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"
            )
            lecture.download_lecture("/tmp/", "big_buck_bunny.mp4", True)
            self.assertTrue(os.path.isfile("/tmp/big_buck_bunny.mp4"))

    # Launching test sequence
    unittest.main()
