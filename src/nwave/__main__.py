class Letter:
    user_text = ''
    code_text = ''

    def __init__(self, code_key, text_key):
        self.code_key = code_key
        self.text_key = text_key

    def get_code(self):
        Letter.code_text += self.code_key
        Letter.code_text += ' '
        return Letter.code_text

    def get_text(self):
        Letter.user_text += self.text_key
        Letter.user_text += ' '


def main():
    lt = Letter('a', 'b')
    print(lt.get_code())