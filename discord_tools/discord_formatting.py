def bold(s):
    return '**' + s + '**'


def italics(s):
    return '*' + s + '*'


def curry_message(s):
    return ":curry: " + s


def curry_format(s, *args):
    return curry_message(s.format(*args))


def get_author(message):
    return str(message.author)[:str(message.author).find('#')]