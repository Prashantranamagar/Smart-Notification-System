class BaseDelivery:
    def send(self, user, message):
        raise NotImplementedError


class InAppDelivery(BaseDelivery):
    def send(self, user, message):
        print(f"[In-App] To {user.username}: {message}")
        return 'sent'  # Stored in DB by Notification model


class EmailDelivery(BaseDelivery):
    def send(self, user, message):
        print
        print(f"[Email] To {user.email}: {message}")
        return 'sent'


class SMSDelivery(BaseDelivery):
    def send(self, user, message):
        print(f"[SMS] To {user.username}: {message}")
        return 'sent'


def get_delivery_handler(channel):
    return {
        'in_app': InAppDelivery(),
        'email': EmailDelivery(),
        'sms': SMSDelivery(),
    }.get(channel, InAppDelivery())