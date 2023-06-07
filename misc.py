import time, random

def welcome_message():
    current_hour = int(time.strftime('%H'))

    phrase_1 = ['hej', 'tja', 'tjena', 'hallåj', 'tjabba', 'yo']

    if current_hour < 5 or current_hour >= 19:
        phrase_1 = ['god kväll']
    
    elif 5 <= current_hour <= 9:
        phrase_1 = ['god morgon']

    else:
        phrase_1 = ['hej', 'tja', 'tjena', 'hallåj', 'tjabba', 'yo']

    greeting = random.choice(phrase_1)
    return greeting.capitalize()