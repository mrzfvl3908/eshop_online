from melipayamak import Api

username = "989032773908"
password = "8f86a97c-ff42-49c4-a9e6-71ee6dbccfb3"

api = Api(username, password)

sms = api.sms()

to = "09032773908"
_from = "50004001773908"
text = "سلام، این یک پیام تستی از پروژه Django است."

response = sms.send(to, _from, text)
print(response)