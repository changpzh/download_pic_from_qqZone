import queue


class SimpleQueue:
    """
    q = SimpleQueue(['a','b','c','d','e'])
    q.empty(): check queue is empty or not, return True or False
    q.get(): left pop remove and return an item from the queue.
    q.fetch(num=2): left pop remove and return a given length of list from the queue.
    q.put('h'): right push an item to the queue.
    q.show(): list all queue items
    q.length(): return length of queue
    """

    def __init__(self, arr):
        self.s_q = queue.Queue()
        for item in arr:
            self.s_q.put(item)

    def empty(self):
        return self.s_q.empty()

    def get(self):
        if self.s_q.empty():
            return None
        return self.s_q.get()

    def fetch(self, num=1):
        values = []
        for _ in range(num):
            if not self.empty():
                values.append(self.get())
        return values

    def put(self, msg):
        if msg:
            self.s_q.put(msg)

    def show(self):
        print(self.s_q.queue)

    def length(self):
        return self.s_q.qsize()