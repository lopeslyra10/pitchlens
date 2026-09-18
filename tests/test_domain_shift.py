from domain_shift import to_markdown


def test_table_shows_per_class_rates_and_ball_presence():
    results = {
        "teste (transmissão)": {
            "frames": 25,
            "classes": {
                "player": {"por_frame": 19.4, "presenca": 1.0, "confianca_media": 0.91},
                "ball": {"por_frame": 0.8, "presenca": 0.76, "confianca_media": 0.62},
            },
        },
        "drone": {"frames": 10, "classes": {}},
    }

    lines = to_markdown(results).splitlines()

    assert lines[0].startswith("| Fonte | Frames | jogador/frame | conf. jogador |")
    assert lines[2] == (
        "| teste (transmissão) | 25 | 19.4 | 0.91 | 0.0 | 0.00 | 0.0 | 0.00 | 0.8 | 0.62 | 76% |"
    )
    assert lines[3].endswith("| 0% |")
