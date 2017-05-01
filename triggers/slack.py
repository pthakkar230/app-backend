from slackclient import SlackClient


def send_message(token, text='', channel='#general'):
    sc = SlackClient(token)
    sc.api_call(
        'chat.postMessage',
        channel=channel,
        text=text,
    )
