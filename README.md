## Videoconverter for entire folders
This tool converts entire folders containing videos on your PC with a simple command line interface.
## Features
1. Conversion of videos in different formats (e.g. different codecs, containers).
2. Ability to convert entire folders containung video files automatically at once.
3. Easy to use with an interactive command line interface
## Quickstart
### Requirements
- [Python](https://www.python.org/downloads/) to run the program
- [ffmpeg](https://ffmpeg.org/download.html) to convert the video files (**Important note: Add ffmpeg and ffprobe to the `path` environment variable.** Since ffmpeg comes usually together with ffprobe, you just have to add the path to the folder containing both executables to your `path`)
### Run the program
- Clone this Repository and extract it into a folder of your choice.
- Launch the `launcher.bat` (Windows) or `launcher.sh` (Linux). This will automatically create a virtual environment with all necessary dependencies python need to run and finally launches the program. Always launch the program via the corresponding launcher.
## Usage
- Launch the program via the corresponding `launcher` file.
- The program will launch and a terminal window will open.
- You have just to answer all of the prompted questions, such as the input path or the output resolution.
- If you wanna render the videos on your GPU (recommended, way faster) select the fastest GPU at the first promped question and confirm GPU usage at the last question.