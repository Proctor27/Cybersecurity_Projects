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
    audio_file = "Mina - Ancora, ancora, ancora (Radio Edit Mark Ronson Remix).mp3"
    if os.path.exists(audio_file):
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
    else:
        print(f"Warning: '{audio_file}' not found. Running in silent demo mode.")

    ui = KaraokeUI()

    song_info = {
        "artist": "Mina",
        "title": "Ancora, ancora, ancora",
        "subtitle": "Radio Edit Mark Ronson Remix ♪"
    }

    # Timed lyrics for honeybee (timestamps in milliseconds)
    timed_lyrics = [
        (1707, "Se vuoi andare, ti capisco"),
        (21310, "Se mi lasci ti tradisco, sì"),
        (29730, "Ma se dormo sul tuo petto"),
        (33930, "Di amarti io non smetto, no"),
        (42220, "Se vuoi andare, ti capisco"),
        (46390, "Se mi lasci ti tradisco, sì"),
        (54790, "Ma se dormo sul tuo petto"),
        (58980, "Di amarti io non smetto, no"),
        (65160, "Io ti chiedo ancora"),
        (69420, "Il tuo corpo ancora"),
        (73540, "Le tue braccia ancora"),
        (77680, "Di abbracciarmi ancora"),
        (82200, "Di amarmi ancora"),
        (86120, "Di pigliarmi ancora"),
        (90010, "Farmi morire ancora"),
        (94420, "Perché ti amo ancora"),
        (125800, "Confusione la tua mente"),
        (129870, "Quando ama completamente, sì"),
        (138280, "Con le sue percezioni"),
        (142450, "Mette a punto le mie inclinazioni perché"),
        (148360, "Io ti chiedo ancora"),
        (152880, "La tua bocca ancora"),
        (157230, "Le tue mani ancora"),
        (161190, "Sul mio collo ancora"),
        (165460, "Di restare ancora"),
        (169630, "Consumarmi ancora"),
        (173630, "Perché ti amo ancora"),
        (177950, "Ancora, ancora, ancora")
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