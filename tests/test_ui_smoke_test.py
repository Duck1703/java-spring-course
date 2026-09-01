from tools.ui_smoke_test import build_screenshot_command, ws_build_frame, ws_parse_frame


def test_screenshot_command_preserves_the_requested_viewport():
    command = build_screenshot_command(
        "chrome",
        "--user-data-dir=profile",
        ["--window-size=390,844"],
        "mobile.png",
        "http://localhost/index.html",
    )

    assert "--window-size=390,844" in command
    assert command[-2:] == [
        "--screenshot=mobile.png",
        "http://localhost/index.html",
    ]


# ---------------------------------------------------------------------------
# Minimal RFC 6455 WebSocket framing, used to drive Chrome DevTools Protocol
# for true device-metrics emulation (see: on Windows, plain --window-size
# cannot reliably produce an exact 390x844 CSS viewport — see build_mobile
# emulation notes in ui_smoke_test.py). No selenium/websocket-client is
# available in this environment, so the client/server framing is hand-rolled;
# these two pure functions are the part worth unit testing in isolation.
def test_ws_build_frame_masks_the_payload_and_encodes_a_short_length():
    frame = ws_build_frame(b"hi", mask=b"\x01\x02\x03\x04")

    # FIN + text opcode, then masked bit + 2-byte length, then the mask key,
    # then the payload XORed against the repeating mask key.
    assert frame[0] == 0x81
    assert frame[1] == 0x80 | 2
    assert frame[2:6] == b"\x01\x02\x03\x04"
    assert frame[6:8] == bytes(b ^ m for b, m in zip(b"hi", b"\x01\x02\x03\x04"))


def test_ws_build_frame_uses_extended_length_for_larger_payloads():
    payload = b"x" * 200
    frame = ws_build_frame(payload, mask=b"\x00\x00\x00\x00")

    assert frame[1] == 0x80 | 126
    assert frame[2:4] == (200).to_bytes(2, "big")


def test_ws_parse_frame_round_trips_a_masked_client_frame():
    frame = ws_build_frame(b"round trip", mask=b"\xaa\xbb\xcc\xdd")

    opcode, payload = ws_parse_frame(frame)

    assert opcode == 1  # text frame
    assert payload == b"round trip"


def test_ws_parse_frame_reads_an_unmasked_server_frame():
    # Real CDP server frames arrive unmasked, per RFC 6455.
    payload = b'{"id":1,"result":{}}'
    header = bytes([0x81, len(payload)])

    opcode, parsed = ws_parse_frame(header + payload)

    assert opcode == 1
    assert parsed == payload
