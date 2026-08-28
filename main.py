import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, DictProperty
from kivy.clock import Clock  # <--- Imported for timing loops
from kivy.core.audio import SoundLoader


def roll_dice_pool(dice_pool: dict, modifier: int = 0) -> dict:
    all_rolls = {}
    subtotal = 0

    for sides, count in dice_pool.items():
        if count > 0:
            rolls = [random.randint(1, sides) for _ in range(count)]
            all_rolls[f"d{sides}"] = rolls
            subtotal += sum(rolls)

    final_total = subtotal + modifier

    return {
        "rolls_by_die": all_rolls,
        "subtotal": subtotal,
        "modifier": modifier,
        "total": final_total,
    }


class DiceRollerLayout(BoxLayout):
    result_text = StringProperty("Select dice and tap ROLL DICE")
    modifier = NumericProperty(0)

    # Track counts for each die size
    dice_counts = DictProperty({4: 0, 6: 0, 8: 0, 10: 0, 12: 0, 20: 0, 100: 0})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.anim_ticks = 0
        self.max_ticks = 30  # 30 ticks * 0.018s ≈ 0.54s of total roll time
        self.roll_event = None

        self.roll_sound = SoundLoader.load("select_click.wav")

    def change_count(self, sides: int, amount: int):
        current = self.dice_counts[sides]
        self.dice_counts[sides] = max(0, current + amount)

    def change_modifier(self, amount: int):
        self.modifier += amount

    def clear_all(self):
        for sides in self.dice_counts:
            self.dice_counts[sides] = 0
        self.modifier = 0

    def do_roll(self):
        """Entry point when 'ROLL DICE' is tapped."""
        # 1. Quick check: don't animate if no dice are selected
        active_sides = [sides for sides, count in self.dice_counts.items() if count > 0]
        if not active_sides:
            self.result_text = "No dice selected!"
            return

        # 2. Disable roll button via KV id (if present) to prevent spamming mid-roll
        if "roll_btn" in self.ids:
            self.ids.roll_btn.disabled = True

        # 3. Start high-speed slot machine timer (~55 FPS)
        self.anim_ticks = 0
        self.roll_event = Clock.schedule_interval(self._animate_tumble, 0.04)

    def _animate_tumble(self, dt):
        """Fires every 18ms to cycle random bracketed numbers."""
        self.anim_ticks += 1

        # Get all die types currently selected with count > 0
        active_sides = [sides for sides, count in self.dice_counts.items() if count > 0]

        # Pick 1-3 random tumble faces from the active pool to show in the blur display
        tumble_samples = [
            f"🎲 {random.randint(1, random.choice(active_sides))}"
            for _ in range(min(3, len(active_sides)))
        ]

        # Update text to clear bracketed blur
        self.result_text = f"[  {'  |  '.join(tumble_samples)}  ]"

        # Stop animation once max ticks reached
        if self.anim_ticks >= self.max_ticks:
            self._finish_roll()

    def _finish_roll(self):
        """Stops the clock, re-enables controls, and displays actual results."""
        if self.roll_event:
            self.roll_event.cancel()

        if "roll_btn" in self.ids:
            self.ids.roll_btn.disabled = False

        if self.roll_sound:
            self.roll_sound.play()

        # Compute actual roll data using your backend logic
        data = roll_dice_pool(self.dice_counts, self.modifier)

        rolls_str = ", ".join([f"{k}: {v}" for k, v in data["rolls_by_die"].items()])
        mod_str = (
            f" + {data['modifier']}"
            if data["modifier"] >= 0
            else f" - {abs(data['modifier'])}"
        )

        self.result_text = (
            f"Rolls: {rolls_str}\n"
            f"Base Sum: {data['subtotal']}{mod_str}\n"
            f"TOTAL: {data['total']}"
        )


class DiceRollerApp(App):
    def build(self):
        return DiceRollerLayout()


if __name__ == "__main__":
    DiceRollerApp().run()
