from langchain_core.messages.base import BaseMessage

# Assuming 'type' is a string that describes the type of message, replace 'YOUR_TYPE_HERE' with the correct type
message = BaseMessage(type="YOUR_TYPE_HERE", content="Hello, World!")
print(message)
