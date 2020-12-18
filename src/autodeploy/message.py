import hmac

""" Message format:
        repo-name \\n
        branch:hashofoldstate:hashofnewstate \\n
        username:person-name:email \\n
        signature
"""


def encode_message(json: dict, key: bytes) -> bytes:
    p = json['pusher']
    n = json['repository']['full_name']
    refstr = f"{json['ref']}:{json['before']}:{json['after']}"
    pusherstr = f"{p['login']}:{p['full_name']}:{p['email']}"
    msg = f'{n}\n{refstr}\n{pusherstr}'
    hm = hmac.new(key, msg.encode('utf8'), digestmod='sha256')
    return f"{msg}\n{hm.hexdigest()}".encode('utf8')


class Message(object):

    repo:     str   # Repo name from cfg-file and webhook
    branch:   str   # branch to act on if not bare
    before:   str   # state we expect the repo to be in before changing
    state:    str   # new state (hash) after commit is applied
    pusher:   str   # username of who pushed
    fullname: str   # real name of who pushed
    email:    str   # email of who pushed
    digest:   str   # signature digest

    @classmethod
    def from_msg(cls, msg: bytes):
        c = cls()
        c.repo, ref, person, c.digest = msg.decode('utf8').split('\n')
        c.branch, c.before, c.state = ref.split(':')
        c.pusher, c.fullname, c.email = person.split(':')
        return c

    def verify(self, key: bytes) -> bool:
        m = f"{self.repo}\n{self.branch}:{self.before}:{self.state}\n"
        m += f"{self.pusher}:{self.fullname}:{self.email}"
        hm = hmac.new(key, m.encode('utf8'), 'sha256')
        return hmac.compare_digest(hm.hexdigest(), self.digest)


if __name__ == "__main__":
    msg = b'refs/heads/xxx:123abc:456ffe\nwillsk:William Strecker-Kellogg:willsk@bnl.gov\n012fffdeadbeef'
    m = Message.from_msg(msg)