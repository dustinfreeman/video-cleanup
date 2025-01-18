# video-cleanup

Problem: I had thousands of short videos from various projects throughout my project directories, and wanted to reduce overall size. I had already used tools to find the largest videos, and manually reduced their bitrate. However, this left out the very manby short videos that were at a needlessly high bitrate. Many recording devices and screen capture tools default to recording at high bitrate, but this is rarely needed for long-term archival.

Solution: This is set of scripts to identify all videos of unusually high bitrate, and then replace them with a compressed version, in place. No instructions are provided, since I'm carefully running these step-by-step.

Please let me know if you find these useful, bugfix PRs accepted!
