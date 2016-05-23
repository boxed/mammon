import datetime
import exceptions


class AccessDeniedException(exceptions.Exception):
    user = None
    obj = None
    command = None
    args = None

    def __init__(self, user, obj, command, comment = ''):
        self.user = user
        self.obj = obj
        self.command = command
        self.comment = comment
        self.args = {'user': user, 'obj': obj, 'command': command, 'comment': comment}


def age(bday, d=datetime.date.today()):
    return (d.year - bday.year) - int((d.month, d.day) < (bday.month, bday.day))