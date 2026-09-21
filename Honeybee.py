import time
import sys
import os
import pygame


class KaraokeUI:
    def clear(self):
        # ANSI escape code to clear screen and reset cursor position for smooth redraws
        print("\033[H\033[J", end="")

    def render(self, song_info, lyrics, current_line_idx, visualizer_bars):
        self.clear()

        # Display track metadata
        print(f"🎵 \033[1;33m★ {song_info['artist']} - {song_info['title']} ★\033[0m")
        print(f"   \033[32m♪ {song_info['subtitle']} ♪\033[0m")

        # Display audio visualizer wave effect
        print("\n" + visualizer_bars)
        print("=" * 65)

        # Display lyrics with highlighting for the active line
        start_idx = max(0, current_line_idx - 2)
        end_idx = min(len(lyrics), start_idx + 5)

        for idx in range(start_idx, end_idx):
            line = lyrics[idx]
            if idx == current_line_idx:
                print(f"-> \033[1;32m{line}\033[0m <-")  # Highlight active line in bright green
            else:
                print(f"   \033[90m{line}\033[0m")  # Dim inactive lines

        print("=" * 65)
        print("\033[31m[LIVE]\033[0m Press Ctrl+C to exit.")


def generate_visualizer():
    # Generates a dynamic retro terminal equalizer bar look using block characters
    import random
    chars = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    return "".join(random.choice(chars) for _ in range(35))


def run_karaoke():
    # Initialize Pygame Mixer for audio playback
    pygame.mixer.init()

    # Target audio file matching your file name
    audio_file = "Olivia Rodrigo - honeybee.mp3"
    if os.path.exists(audio_file):
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
    else:
        print(f"Warning: '{audio_file}' not found. Running in silent demo mode.")

    ui = KaraokeUI()

    song_info = {
        "artist": "Olivia Rodrigo",
        "title": "honeybee",
        "subtitle": "honeybee ♪"
    }

    # Timed lyrics for honeybee (timestamps in milliseconds)
    timed_lyrics = [
        (7480, "So I guess that it's true"),
        (10980, "Time can heal even the worst of wounds"),
        (14770, "And the clichés I knew"),
        (18250, "Seem so commonplace when I saw you"),
        (21850, "Let's just walk in the dark"),
        (25450, "Hop the fence in the park"),
        (28990, "Baby boy, honeybee"),
        (32570, "God, I love the way you look at me"),
        (37140, "And it's too hard to describe this"),
        (40960, "In a way that feels honest,"),
        (44610, "but even when I'm quiet"),
        (48380, "I love you, baby, I promise"),
        (51680, "And I hope I never see "),
        (54620, "what your face looks like goin'"),
        (59030, "A face, I swear, that I could"),
        (62140, "spend my whole life knowin'"),
        (64990, "Here's to hopin'... (Instrumental Outro)"),
        (70680, "pick me up, walk me home"),
        (74320, "and it feels like god threw me a bone"),
        (77870, "sticky sweet, tangerine"),
        (81420, "would you sit and keep me company?"),
        (85030, "in the dark, i'm not scared"),
        (88620, "i just reach and you're right there"),
        (92130, "shooting stars, racing cars"),
        (95810, "everything i own just feels like ours"),
        (199999, "......")
    ]

    start_time = time.time()
    current_idx = 0

    try:
        while current_idx < len(timed_lyrics):
            elapsed_ms = int((time.time() - start_time) * 1000)
            target_time, _ = timed_lyrics[current_idx]

            # Check if it's time to move to the next lyric line
            if elapsed_ms >= target_time:
                current_idx += 1

            # Extract just the text strings for rendering
            lyric_texts = [l[1] for l in timed_lyrics]
            visualizer = generate_visualizer()

            ui.render(song_info, lyric_texts, max(0, current_idx - 1), visualizer)

            # Refresh rate delay (~20fps for fluid terminal visualizer movement)
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\033[31mKaraoke stopped by user.\033[0m")
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()


if __name__ == "__main__":
    run_karaoke()