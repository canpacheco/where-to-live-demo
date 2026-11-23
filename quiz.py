"""The adaptive quiz: picks each trade-off question from the earlier answers.

The factors are placed one at a time into a ranked list by binary insertion, the way you would
slide a card into a sorted hand. Each question compares the factor being placed with one already
in the list, so six factors are ranked in 8 to 11 questions (about 10), and five in 6 to 8.
Everything is replayed from the seed and the list of answers, so the Back button only has to drop
the last answer.
"""
import math
import random

FACTORS = ["Rent", "Job outlook", "Comfortable weather", "Education", "Culture", "Family"]

# One question per pair of factors. The cards never name a factor.
QUESTIONS = {
    frozenset(["Comfortable weather", "Culture"]): (
        "Saturday is wide open. You're...",
        {"Comfortable weather": "Hiking on a perfect 72-degree day",
         "Culture": "Screaming every word at a Taylor Swift show in a dome"}),
    frozenset(["Rent", "Culture"]): (
        "Pick your home base.",
        {"Rent": "A roomy 2,000-sq-ft house on a sleepy cul-de-sac",
         "Culture": "A 700-sq-ft shoebox above the city's best taco spot"}),
    frozenset(["Job outlook", "Family"]): (
        "Two job offers land in your inbox.",
        {"Job outlook": "$100,000 a year, 1,000 miles from your family",
         "Family": "$60,000 a year, close enough for Sunday dinner"}),
    frozenset(["Job outlook", "Rent"]): (
        "Your paycheck plan?",
        {"Job outlook": "Big raises, but rent eats a third of your pay",
         "Rent": "Slow raises, but rent only nibbles a fifth"}),
    frozenset(["Job outlook", "Education"]): (
        "Your new town is...",
        {"Job outlook": "A boomtown where everyone is hiring",
         "Education": "A brainy college town full of grad students"}),
    frozenset(["Job outlook", "Comfortable weather"]): (
        "Choose your adventure.",
        {"Job outlook": "Your dream job, plus five months of gray slush",
         "Comfortable weather": "An okay job, plus sunshine almost every day"}),
    frozenset(["Job outlook", "Culture"]): (
        "It's Friday night. You're...",
        {"Job outlook": "Working late at a job that's going places",
         "Culture": "Picking between three concerts and a food festival"}),
    frozenset(["Rent", "Education"]): (
        "Your new neighbors are...",
        {"Rent": "Easygoing folks, and your rent is a steal",
         "Education": "Book-club regulars, and your rent is pricier"}),
    frozenset(["Rent", "Comfortable weather"]): (
        "Pick your trade-off.",
        {"Rent": "Cheap rent, but you own three snow shovels",
         "Comfortable weather": "Pricier rent, but it's patio season all year"}),
    frozenset(["Rent", "Family"]): (
        "Every month, you'd rather...",
        {"Rent": "Keep an extra $500 by living far from home",
         "Family": "Pay $500 more to be near your people"}),
    frozenset(["Education", "Comfortable weather"]): (
        "Your new town is famous for...",
        {"Education": "Its library, lectures, and trivia-night champions",
         "Comfortable weather": "Its beaches, sunsets, and flip-flops in February"}),
    frozenset(["Education", "Culture"]): (
        "Your neighbors spend weekends...",
        {"Education": "Taking night classes and arguing about books",
         "Culture": "Hitting art walks and live-music bars"}),
    frozenset(["Education", "Family"]): (
        "Big-move energy?",
        {"Education": "A brainy college town across the country",
         "Family": "A regular town 30 minutes from your family"}),
    frozenset(["Comfortable weather", "Family"]): (
        "Pick your view.",
        {"Comfortable weather": "Perfect weather, 1,000 miles from family",
         "Family": "Meh weather, 20 minutes from home cooking"}),
    frozenset(["Culture", "Family"]): (
        "Your social calendar?",
        {"Culture": "Sold-out shows every weekend, far from home",
         "Family": "Family game night, a short drive away"}),
}

COMFORT_CHOICES = [
    ("Hoodie weather", "45 to 65 degrees", (45, 65)),
    ("Light-jacket weather", "55 to 75 degrees", (55, 75)),
    ("T-shirt weather", "65 to 85 degrees", (65, 85)),
    ("Bring on the heat", "75 to 95 degrees", (75, 95)),
]

PERSONALITIES = {
    "Rent": ("THE PENNY PINCHER", "You would rather keep your gold than hand it to a landlord."),
    "Job outlook": ("THE GOLD RUSHER", "You go where the jobs are booming."),
    "Comfortable weather": ("THE SUN CHASER", "Life is too short for gray slush."),
    "Education": ("THE SCHOLAR", "You want neighbors who never stopped learning."),
    "Culture": ("THE SHOWGOER", "If there is a concert in town, you are already in line."),
    "Family": ("THE HOMEBODY", "Sunday dinner is not negotiable."),
}


def replay(factors, seed, answers):
    """Replays the answers. Returns ("ask", factor_a, factor_b) for the next question,
    or ("done", ranked_factors) when every factor is placed."""
    rng = random.Random(seed)
    queue = rng.sample(factors, len(factors))
    ranked = [queue[0]]
    used = 0
    for item in queue[1:]:
        lo, hi = 0, len(ranked)
        while lo < hi:
            mid = (lo + hi) // 2
            if used == len(answers):
                return ("ask", item, ranked[mid])
            if answers[used] == item:
                hi = mid
            else:
                lo = mid + 1
            used += 1
        ranked.insert(lo, item)
    return ("done", ranked)


def most_questions(factors, seed, answers):
    """The most trade-off questions this visitor can still be asked, counting the ones answered."""
    rng = random.Random(seed)
    queue = rng.sample(factors, len(factors))
    total = 0
    for size in range(1, len(queue)):
        total += math.ceil(math.log2(size + 1))
    return max(total, len(answers) + 1)


def card_order(seed, pair):
    """Puts the two cards of a question in a random but repeatable left and right order."""
    a, b = sorted(pair)
    rng = random.Random(f"{seed}-{a}-{b}")
    return [a, b] if rng.random() < 0.5 else [b, a]


def weights_from_order(ranked):
    """The first factor gets the largest weight, the last gets 1."""
    n = len(ranked)
    return {factor: n - i for i, factor in enumerate(ranked)}
