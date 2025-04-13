
import os
import time
import sqlite3
import speech_recognition as sr
from RPLCD.i2c import CharLCD
from fuzzywuzzy import process  # Import fuzzy matching

# Suppress ALSA errors
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["ALSA_CARD"] = "1"  # Set default audio card

# Initialize LCD (I2C address: 0x27)
lcd = CharLCD('PCF8574', 0x27, auto_linebreaks=False)

# Initialize Speech Recognition
r = sr.Recognizer()
mic = sr.Microphone()

def display_on_lcd(line1, line2=""):
    """ Function to display text on LCD """
    lcd.clear()
    lcd.write_string(line1[:16])  # First line (max 16 chars)
    if line2:
        lcd.cursor_pos = (1, 0)
        lcd.write_string(line2[:16])  # Second line (max 16 chars)
    time.sleep(3)  # Show for 3 seconds

def get_all_names():
    """ Fetch all names from the database for fuzzy matching """
    conn = sqlite3.connect("Project.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM contacts")
    names = [row[0].lower() for row in cursor.fetchall()]
    conn.close()
    return names

def search_contact(spoken_name):
    """ Search for the closest matching contact in the database """
    spoken_name = spoken_name.lower()
    names_list = get_all_names()
    best_match, score = process.extractOne(spoken_name, names_list) if names_list else (None, 0)
    
    if best_match and score >= 80:
        conn = sqlite3.connect("Project.db")
        cursor = conn.cursor()
        cursor.execute("SELECT number FROM contacts WHERE LOWER(name) = ?", (best_match,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            number = str(result[0])  # Ensure number is a string
            last_four_digits = number[-4:]  # Get last 4 digits
            return best_match.capitalize(), last_four_digits
    return None

print("Listening...")

while True:
    with mic as source:
        audio = r.listen(source)
    
    try:
        words = r.recognize_google(audio).lower()
        print(f"Recognized: {words}")
        d
        if words == "exit":
            lcd.clear()
            lcd.write_string("Goodbye!")
            time.sleep(2)
            lcd.clear()
            break
        
        if words.startswith("call "):
            spoken_name = words[5:].strip()
            match = search_contact(spoken_name)
            
            if match:
                name, last_four_digits = match
                display_on_lcd(name, f"Dialing {last_four_digits}")
            else:
                display_on_lcd("Contact Not", "Found")
        else:
            display_on_lcd(words)
    
    except sr.UnknownValueError:
        pass  # Ignore unrecognized speech
    except sr.RequestError:
        pass  # Ignore network errors
