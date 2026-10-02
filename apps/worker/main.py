"""
Plain CLI test harness: make courses, enter a course, record lectures,
transcribe them, and see which lecture audios exist for that course.

Run from the project root:
    python scripts/try_lectures.py
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scipy.io import wavfile

from src.courses.course import Course
from src.lecture_ai.audio.record import AudioRecorder
from src.lecture_ai.audio.segmentation import Transcriber


def course_slug(name):
    """Must match how AudioRecorder.make_filename builds the course part."""
    safe = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_"))
    return safe.strip().replace(" ", "_")


def find_lectures(recorder, course=None):
    """Return saved .wav files for a course (or the course-less ones)."""
    folder = Path(recorder.output_dir)
    if not folder.exists():
        return []
    prefix = f"{course_slug(course.name)}_lecture_" if course else "lecture_"
    return sorted(folder.glob(f"{prefix}*.wav"))


def transcript_path(wav):
    """Transcript lives next to its audio: foo.wav -> foo.txt"""
    return Path(wav).with_suffix(".txt")


def describe(path):
    tag = "  [transcribed]" if transcript_path(path).exists() else ""
    try:
        rate, data = wavfile.read(path)
        return f"{path.name}  ({len(data) / rate:.1f}s){tag}"
    except Exception:
        return f"{path.name}{tag}"


def show_lectures(recorder, course=None):
    """Print the list and return the files so callers can pick by number."""
    label = f"'{course.name}'" if course else "uncategorized recordings"
    files = find_lectures(recorder, course)
    if not files:
        print(f"\nNo lecture audio found for {label}.")
        return files
    print(f"\nLecture audio for {label}:")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {describe(f)}")
    return files


def transcribe_lecture(transcriber, wav):
    print(f"\nTranscribing {Path(wav).name} ...")
    text = transcriber.transcribe_file(wav)
    txt = transcript_path(wav)
    txt.write_text(text)
    print(f"Saved transcript: {txt}\n")
    print(text if text else "(no speech detected)")


def open_lecture(transcriber, files):
    """Show a lecture's transcript, transcribing it first if needed."""
    if not files:
        return
    choice = input("Lecture number: ").strip()
    if not (choice.isdigit() and 1 <= int(choice) <= len(files)):
        print("Invalid number.")
        return
    wav = files[int(choice) - 1]
    txt = transcript_path(wav)
    if txt.exists():
        print(f"\n--- {txt.name} ---\n{txt.read_text()}")
    else:
        transcribe_lecture(transcriber, wav)


def record(recorder, transcriber, course=None):
    """Record with live transcription: each phrase prints once you finish speaking it."""
    transcriber.start()
    recorder.record()
    print("\nRecording + live transcription... press ENTER to stop.\n")
    input()
    try:
        audio = recorder.stop()  # stop audio first so nothing more is fed
    except ValueError:
        transcriber.stop()
        print("Nothing was captured.")
        return

    print("\nFinishing last phrase...")
    text = transcriber.stop()  # flushes the open phrase, waits for the worker
    path = recorder.save(audio, course=course)
    print(f"Saved: {path}")
    transcript_path(path).write_text(text)
    print(f"Saved transcript: {transcript_path(path)}")


def lecture_menu(recorder, transcriber, course=None):
    """What you see after entering a course (or the uncategorized bucket)."""
    title = course.name if course else "Uncategorized"
    while True:
        print(f"\n=== {title} ===")
        files = show_lectures(recorder, course)
        print("\n[r] Record new lecture   [t] Transcribe / view transcript   [b] Back")
        choice = input("> ").strip().lower()
        if choice == "r":
            record(recorder, transcriber, course)
        elif choice == "t":
            open_lecture(transcriber, files)
        elif choice == "b":
            return
        else:
            print("Unknown option.")


def pick_course(courses):
    if not courses:
        print("\nNo courses yet. Create one first.")
        return None
    print("\nCourses:")
    for i, c in enumerate(courses, 1):
        print(f"  {i}. {c.name}")
    choice = input("Enter number or name: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(courses):
        return courses[int(choice) - 1]
    for c in courses:
        if c.name.lower() == choice.lower():
            return c
    print("Course not found.")
    return None


def main():
    transcriber = Transcriber()  # loads models once, reused for every lecture
    recorder = AudioRecorder(on_chunk=transcriber.feed)  # every mic chunk also goes to the transcriber
    courses = []

    while True:
        print("\n--- Main menu ---")
        print("[c] Create course")
        print("[e] Enter course")
        print("[r] Record (no course)")
        print("[u] Uncategorized recordings")
        print("[q] Quit")
        choice = input("> ").strip().lower()

        if choice == "c":
            name = input("Course name: ").strip()
            if not name:
                print("Name can't be empty.")
            elif any(c.name.lower() == name.lower() for c in courses):
                print("That course already exists.")
            else:
                courses.append(Course(name))
                print(f"Created '{name}'.")
        elif choice == "e":
            course = pick_course(courses)
            if course:
                lecture_menu(recorder, transcriber, course)
        elif choice == "r":
            record(recorder, transcriber)
        elif choice == "u":
            lecture_menu(recorder, transcriber)
        elif choice == "q":
            break
        else:
            print("Unknown option.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye.")