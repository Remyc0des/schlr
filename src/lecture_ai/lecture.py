class MyLecture:
    def __init__(self, name, course):
        self.name = name
        self.course = course
        self.transcript = ""
        self.audio_file = None

    def add_lecture(self, text, course=None):
        self.transcript += text
        if course:
            self.course = course

