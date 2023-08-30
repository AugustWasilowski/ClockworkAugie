class MockInteraction:
    def __init__(self, message):
        self.message = message
        self.channel_id = message.channel.id
        self.user_id = message.author.id
        self.response = self.Response(message)
        self.followup = self.Followup(message)

    class Response:
        def __init__(self, message):
            self.message = message

        async def send_message(self, content):
            await self.message.channel.send(content)

    class Followup:
        def __init__(self, message):
            self.message = message

        async def send(self, content=None, *, file=None):
            if file:
                await self.message.channel.send(file=file)
            else:
                await self.message.channel.send(content)