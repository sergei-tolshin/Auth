import string
from secrets import choice


def generate_random_string():
    alphabet = string.ascii_letters + string.digits
    return ''.join(choice(alphabet) for _ in range(16))


def send_fake_email(email, psw):
    with open('fake_email', 'a', encoding='utf-8') as file:
        file.write(f'{email} --- {psw}\n')
