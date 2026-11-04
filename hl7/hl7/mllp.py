"""Incremental, bounded MLLP decoder; independent of TCP packet boundaries."""
START, END = b'\x0b', b'\x1c\x0d'


def frame(message):
    return START + (message.encode('utf-8') if isinstance(message, str) else message) + END


class Decoder:
    def __init__(self, max_size=1024 * 1024):
        self.buffer = bytearray()
        self.max_size = max_size

    def feed(self, chunk):
        self.buffer.extend(chunk)
        messages = []
        while self.buffer:
            start = self.buffer.find(START)
            if start < 0:
                self.buffer.clear()
                break
            del self.buffer[:start]
            end = self.buffer.find(END, 1)
            nested = self.buffer.find(START, 1)
            if nested >= 0 and (end < 0 or nested < end):
                del self.buffer[:nested]  # resynchronize after a broken frame
                continue
            if end < 0:
                if len(self.buffer) > self.max_size:
                    self.buffer.clear()
                    raise ValueError('MLLP frame exceeds size limit')
                break
            if end > self.max_size:
                self.buffer.clear()
                raise ValueError('MLLP frame exceeds size limit')
            messages.append(bytes(self.buffer[1:end]))
            del self.buffer[:end + 2]
        return messages
