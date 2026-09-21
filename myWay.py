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
    audio_file = "06 Frank Sinatra - My Way.mp3"
    if os.path.exists(audio_file):
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
    else:
        print(f"Warning: '{audio_file}' not found. Running in silent demo mode.")

    ui = KaraokeUI()

    song_info = {
        "artist": "Frank Sinatra",
        "title": "My Way",
        "subtitle": "Expanded Edition ♪"
    }

    # Timed lyrics for honeybee (timestamps in milliseconds)
    timed_lyrics = [
        (6250, "And now, the end is near"),
        (11850, "And so I face the final curtain"),
        (18840, "My friend, I'll say it clear"),
        (24110, "I'll state my case, of which I'm certain"),
        (31140, "I've lived a life that's full"),
        (37000, "I traveled each and every highway"),
        (43500, "And more, much more than this"),
        (48900, "I did it my way"),
        (56360, "Regrets, I've had a few"),
        (62120, "But then again, too few to mention"),
        (68990, "I did what I had to do"),
        (74880, "And saw it through without exemption"),
        (81480, "I planned each charted course"),
        (87060, "Each careful step along the byway"),
        (94190, "And more, much more than this"),
        (99240, "I did it my way"),
        (105700, "Yes, there were times, I'm sure you knew"),
        (112530, "When I bit off more than I could chew"),
        (118700, "But through it all, when there was doubt"),
        (125240, "I ate it up and spit it out"),
        (131200, "I faced it all, and I stood tall"),
        (137750, "And did it my way"),
        (143610, "I've loved, I've laughed and cried"),
        (150010, "I've had my fill, my share of losing"),
        (157020, "And now, as tears subside"),
        (162740, "I find it all so amusing"),
        (169500, "To think I did all that"),
        (175690, "And may I say, not in a shy way"),
        (182640, "Oh, no, oh, no, not me"),
        (188520, "I did it my way"),
        (193720, "For what is a man, what has he got?"),
        (200880, "If not himself, then he has naught"),
        (206560, "To say the things he truly feels"),
        (213810, "And not the words of one who kneels"),
        (220590, "The record shows I took the blows"),
        (227170, "And did it my way"),
        (253680, "Yes, it was my way")
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