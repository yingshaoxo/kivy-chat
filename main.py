import sys

if sys.version_info > (3, 5): # determine if it's py3 or py2
    from asyncio_main import ChatApp
else:
    from asyncore_main import ChatApp

ChatApp().run()
