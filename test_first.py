from bccdata import MMChar


def test_char():
    aTuple = ("a", "A")
    for a in aTuple:
        for offs in range(26):
            value = MMChar.convTo(chr(ord(a) + offs))
            assert value - MMChar.convTo(a) == offs
